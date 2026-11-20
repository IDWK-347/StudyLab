"""认证模块的业务逻辑。

职责：注册、登录、令牌轮换、登出。事务边界在本层。

约束：
- refresh token 必须经过 **Rotation**：每次刷新后旧记录立即置 revoked_at
- 登出只标记撤销，不物理删除记录，且**只影响当前设备**
- **多设备策略**（已定 2026-10-11）：登录**不吊销**该用户既有令牌，每台设备各持一条有效记录
  （v1.0项目文档.md 第 4.3 / 7.1 / 7.4 节）
- 唯一需要**批量吊销**的场景：把用户置为 DISABLED（同文档第 6.3 节）
- **只返回 schema，不把 ORM 对象交给 Router**（硬性约定 5）
- refresh token 的格式、摘要与校验见第 5.7 节

"""

import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import SystemRole, UserStatus
from app.core.config import get_settings
from app.core.exceptions import (
    BusinessException,
    ForbiddenException,
    UnauthorizedException,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.repository import (
    create_refresh_token,
    get_refresh_token_by_token_id,
    revoke_refresh_token,
)
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    UserBrief,
)
from app.modules.users.models import User
from app.modules.users.repository import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_login_id,
    get_user_by_username,
)

# 登录时若用户不存在，也跑一次哈希校验，使耗时不暴露「账号是否存在」。
# 模块级只计算一次；这个哈希不可能匹配任何真实密码。
_DUMMY_PASSWORD_HASH = hash_password(token_urlsafe(16))


def _sha256_hex(value: str) -> str:
    """计算字符串的 SHA-256 十六进制摘要。"""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _generate_refresh_token() -> tuple[str, str, str]:
    """生成 (token_id, secret, token_hash)。"""
    token_id = uuid.uuid4().hex
    secret = token_urlsafe(32)
    return token_id, secret, _sha256_hex(secret)


def _parse_refresh_token(
    raw_token: str,
) -> tuple[str, str]:
    """解析 ``<token_id>.<secret>``；格式不合法抛 401。"""
    if not isinstance(raw_token, str):
        raise UnauthorizedException("令牌无效")

    parts = raw_token.split(".", 1)

    if len(parts) != 2 or not parts[0] or not parts[1] or "." in parts[1]:
        raise UnauthorizedException("令牌无效")

    token_id, secret = parts
    return token_id, secret


async def _issue_tokens(
    session: AsyncSession,
    user: User,
) -> tuple[str, str, int]:
    """签发一对令牌并落库，返回 (access_token, raw_refresh_token, expires_in)。"""
    settings = get_settings()

    token_id, secret, token_hash = _generate_refresh_token()
    raw_refresh_token = f"{token_id}.{secret}"

    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

    # Repository 不提交事务，commit 由本层负责
    await create_refresh_token(
        session,
        user_id=user.id,
        token_id=token_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    access_token = create_access_token(subject=str(user.id))

    # expires_in 的单位是秒
    expires_in = settings.access_token_expire_minutes * 60
    return access_token, raw_refresh_token, expires_in


async def register(
    session: AsyncSession,
    payload: RegisterRequest,
) -> RegisterResponse:
    """公开注册。新用户**恒为 USER**（v1.0项目文档.md 第 9.1 节）。"""
    if await get_user_by_username(session, payload.username) is not None:
        raise BusinessException("用户名已存在")

    if await get_user_by_email(session, payload.email) is not None:
        raise BusinessException("邮箱已被注册")

    user = User(
        user_code=payload.username,
        username=payload.username,
        email=payload.email,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
        system_role=SystemRole.USER,
        status=UserStatus.ACTIVE,
        must_change_password=False,
    )
    session.add(user)

    try:
        await session.commit()
    except IntegrityError:
        # 并发注册时，上面的预检查可能同时通过；唯一约束才是最终防线
        await session.rollback()
        raise BusinessException("用户名或邮箱已被注册") from None

    return RegisterResponse.model_validate(user)


async def login(
    session: AsyncSession,
    payload: LoginRequest,
) -> tuple[LoginResponse, str]:
    """登录：签发 access token 与新的 refresh token；**不吊销**其他设备。"""
    user = await get_user_by_login_id(session, payload.login_id)

    # 用户不存在时也跑一次校验，避免响应时间泄露账号是否存在
    if user is None:
        verify_password(payload.password, _DUMMY_PASSWORD_HASH)
        raise UnauthorizedException("用户名或密码错误")

    if not verify_password(payload.password, user.password_hash):
        raise UnauthorizedException("用户名或密码错误")

    # 先证明知道密码，再暴露账号状态
    if user.status != UserStatus.ACTIVE:
        raise ForbiddenException("账号已被禁用")

    user.last_login_at = datetime.now(UTC)

    access_token, raw_refresh_token, expires_in = await _issue_tokens(session, user)
    await session.commit()

    response = LoginResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserBrief.model_validate(user),
    )
    return response, raw_refresh_token


async def refresh(
    session: AsyncSession,
    raw_token: str,
) -> tuple[RefreshResponse, str]:
    """令牌轮换：旧记录立即吊销，返回新的一对令牌。"""
    token_id, secret = _parse_refresh_token(raw_token)

    stored = await get_refresh_token_by_token_id(session, token_id)
    if stored is None:
        raise UnauthorizedException("令牌无效")

    # 常数时间比较，避免计时攻击
    if not hmac.compare_digest(_sha256_hex(secret), stored.token_hash):
        raise UnauthorizedException("令牌无效")

    if stored.revoked_at is not None:
        raise UnauthorizedException("令牌无效")

    if stored.expires_at <= datetime.now(UTC):
        raise UnauthorizedException("令牌无效")

    user = await get_user_by_id(session, stored.user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise UnauthorizedException("令牌无效")

    # 并发守卫：同一 token 只允许一个请求轮换成功
    if await revoke_refresh_token(session, token_id) != 1:
        await session.rollback()
        raise UnauthorizedException("令牌无效")

    access_token, raw_refresh_token, expires_in = await _issue_tokens(session, user)
    await session.commit()

    return (
        RefreshResponse(access_token=access_token, expires_in=expires_in),
        raw_refresh_token,
    )


async def logout(
    session: AsyncSession,
    raw_token: str | None,
) -> None:
    """登出：只吊销**当前设备**的令牌。幂等——任何无效情况都视为成功。"""
    if not raw_token:
        return

    try:
        token_id, secret = _parse_refresh_token(raw_token)
    except UnauthorizedException:
        return

    stored = await get_refresh_token_by_token_id(session, token_id)
    if stored is None:
        return

    if not hmac.compare_digest(_sha256_hex(secret), stored.token_hash):
        return

    await revoke_refresh_token(session, token_id)
    await session.commit()
