"""依赖注入。

职责：提供可注入的公共依赖——数据库会话、当前用户、管理员守卫。

约束：
- Session 必须通过依赖注入获取，**不得保存为全局变量**（README 第 4 节）。
- 当前用户按 access token 的 `sub` **查一次 users 表**换取 `role` / `status`（v1.0项目文档.md
  第 7.2 节，A 方案），使禁用 / 降权**立即生效**。
- **只向 Router 暴露 schema（`CurrentUser`），不暴露 ORM 对象**（硬性约定 5）。
- 未认证一律 401；已认证但无权限才 403。
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import SystemRole, UserStatus
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.infrastructure.database.session import async_session_factory
from app.modules.users.repository import get_user_by_id
from app.modules.users.schemas import CurrentUser


async def get_db() -> AsyncIterator[AsyncSession]:
    """每个请求一个 AsyncSession；**不 commit**——事务边界归 Service。"""
    async with async_session_factory() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]

# auto_error=False：缺凭据时返回 None，由本模块统一抛 401（默认行为是 403）
_bearer_scheme = HTTPBearer(auto_error=False)

BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(_bearer_scheme),
]


async def get_current_user(
    session: DbSession,
    credentials: BearerCredentials,
) -> CurrentUser:
    """解析 Bearer token 并返回请求者身份；任何失败都是 401。"""
    if credentials is None:
        raise UnauthorizedException("未提供认证凭据")

    payload = decode_access_token(credentials.credentials)

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise UnauthorizedException("令牌无效") from None

    user = await get_user_by_id(session, user_id)
    if user is None:
        raise UnauthorizedException("令牌无效")

    if user.status != UserStatus.ACTIVE:
        raise UnauthorizedException("账号已被禁用")

    return CurrentUser.model_validate(user)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


async def get_current_admin(
    current_user: CurrentUserDep,
) -> CurrentUser:
    """管理员守卫：已认证但角色不是 ADMIN 时返回 403。"""
    if current_user.system_role != SystemRole.ADMIN:
        raise ForbiddenException("需要管理员权限")
    return current_user


AdminUserDep = Annotated[CurrentUser, Depends(get_current_admin)]
