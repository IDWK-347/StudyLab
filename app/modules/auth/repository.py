"""认证模块的数据访问。

职责：`user_refresh_tokens` 的写入、按 token_id 查找、吊销。
      用户查询归 `app/modules/users/repository.py`。

约束：一律使用注入的 AsyncSession，不持有全局会话；
      不把 ORM 对象泄露给 Router（README 第 4 节分层约束）。
"""

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import UserRefreshToken


async def create_refresh_token(
    session: AsyncSession,
    user_id: int,
    token_id: str,
    token_hash: str,
    expires_at: datetime,
) -> None:
    token = UserRefreshToken(
        user_id=user_id,
        token_id=token_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    session.add(token)
    await session.flush()


async def get_refresh_token_by_token_id(
    session: AsyncSession,
    token_id: str,
) -> UserRefreshToken | None:
    result = await session.execute(
        select(UserRefreshToken).where(UserRefreshToken.token_id == token_id)
    )
    return result.scalar_one_or_none()


async def revoke_refresh_token(
    session: AsyncSession,
    token_id: str,
) -> int:
    """吊销单条记录；返回受影响行数（0 表示不存在或已被吊销）。"""
    result = await session.execute(
        update(UserRefreshToken)
        .where(
            UserRefreshToken.token_id == token_id,
            UserRefreshToken.revoked_at.is_(None),
        )
        .values(
            revoked_at=func.now(),
        )
    )
    return result.rowcount


async def revoke_all_refresh_token_for_users(
    session: AsyncSession,
    user_id: int,
) -> int:
    """吊销某用户所有仍有效的记录；返回受影响行数。"""
    result = await session.execute(
        update(UserRefreshToken)
        .where(
            UserRefreshToken.user_id == user_id,
            UserRefreshToken.revoked_at.is_(None),
        )
        .values(
            revoked_at=func.now(),
        )
    )
    return result.rowcount
