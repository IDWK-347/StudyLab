"""用户模块的业务逻辑。

职责：当前用户资料、修改密码（校验旧密码、更新哈希、清零 `must_change_password`、
      吊销全部 refresh token）、管理员对用户的列表 / 详情 / 启用禁用。事务边界在本层。

约束：
- 只向 Router 返回 schema，**不返回 ORM 对象**（硬性约定 5）。
- 改密后吊销该用户**所有设备**的 refresh token（v1.0项目文档.md 6.2）。
- 禁用用户时同时吊销其全部 refresh token；**管理员不能禁用自己**，但可以禁用其他管理员
  （同文档 6.3）。
- 由于 `get_current_user` 每次按 `sub` 查状态，用户被禁用后其 **access token 也立即失效**，
  不必等 30 分钟（同文档 7.2）。
- 跨模块：本层调用 `auth.repository` 吊销令牌；`users → auth` 单向依赖，不成环。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import UserStatus
from app.core.exceptions import BusinessException, NotFoundException
from app.core.security import hash_password, verify_password
from app.modules.auth.repository import revoke_all_refresh_token_for_users
from app.modules.users import repository
from app.modules.users.schemas import (
    ChangePasswordRequest,
    UserDetail,
    UserListResponse,
    UserStatusUpdate,
    UserSummary,
)


async def get_me(
    session: AsyncSession,
    user_id: int,
) -> UserSummary:
    """当前用户资料。"""
    user = await repository.get_user_by_id(session, user_id)
    if user is None:
        raise NotFoundException("用户不存在")
    return UserSummary.model_validate(user)


async def change_password(
    session: AsyncSession,
    user_id: int,
    payload: ChangePasswordRequest,
) -> None:
    """修改密码；成功后该用户所有设备需重新登录。"""
    user = await repository.get_user_by_id(session, user_id)
    if user is None:
        raise NotFoundException("用户不存在")

    if not verify_password(payload.old_password, user.password_hash):
        raise BusinessException("原密码错误")

    await repository.update_password(
        session,
        user_id,
        hash_password(payload.new_password),
    )
    # 改密视为凭据可能已泄露：踢掉所有设备
    await revoke_all_refresh_token_for_users(session, user_id)
    await session.commit()


async def list_users(
    session: AsyncSession,
) -> UserListResponse:
    """管理员视角：一次性返回全部用户。"""
    users = await repository.list_users(session)
    items = [UserSummary.model_validate(user) for user in users]
    return UserListResponse(total=len(items), items=items)


async def get_user_detail(
    session: AsyncSession,
    user_id: int,
) -> UserDetail:
    """管理员视角：单个用户详情。"""
    user = await repository.get_user_by_id(session, user_id)
    if user is None:
        raise NotFoundException("用户不存在")
    return UserDetail.model_validate(user)


async def set_status(
    session: AsyncSession,
    target_user_id: int,
    payload: UserStatusUpdate,
    current_user_id: int,
) -> UserDetail:
    """管理员启用 / 禁用用户。不能禁用自己；禁用时吊销其全部 refresh token。"""
    if payload.status == UserStatus.DISABLED and target_user_id == current_user_id:
        raise BusinessException("不能禁用自己的账号")

    user = await repository.get_user_by_id(session, target_user_id)
    if user is None:
        raise NotFoundException("用户不存在")

    await repository.update_status(session, target_user_id, payload.status)

    if payload.status == UserStatus.DISABLED:
        # 否则其 refresh token 还能换出新的 access token
        await revoke_all_refresh_token_for_users(session, target_user_id)

    await session.commit()

    # 批量 UPDATE 不会自动刷新已加载的 ORM 对象
    await session.refresh(user)
    return UserDetail.model_validate(user)
