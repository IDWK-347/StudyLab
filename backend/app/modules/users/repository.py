"""用户模块的数据访问。

职责：`users` 表的查询与更新——按 id / username / email / login_id 查找、
管理员列表、修改密码哈希、启用 / 禁用。

约束：
- 一律使用注入的 AsyncSession：**不创建 Session、不提交事务、不做业务判断**；
  事务边界归 Service（README 第 4 节）。
- 返回 ORM 对象给 Service 可以；**不得泄露给 Router**（硬性约定 5）。
- 按 id 操作是否越权由 Service 判定，本层不做权限判断。
"""

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import UserStatus
from app.modules.users.models import User


async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(
    session: AsyncSession,
    username: str,
) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_login_id(
    session: AsyncSession,
    login_id: str,
) -> User | None:
    result = await session.execute(
        select(User).where(
            or_(
                User.username == login_id,
                User.email == login_id,
            )
        )
    )
    return result.scalar_one_or_none()


async def list_users(session: AsyncSession) -> list[User]:
    """一次性返回全部用户，按 id 升序。"""
    result = await session.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


async def update_password(
    session: AsyncSession,
    user_id: int,
    password_hash: str,
) -> int:
    """更新密码哈希并清除 `must_change_password`；返回受影响行数。"""
    result = await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            password_hash=password_hash,
            must_change_password=False,
        )
    )
    return result.rowcount


async def update_status(
    session: AsyncSession,
    user_id: int,
    status: UserStatus,
) -> int:
    """更新用户状态；返回受影响行数（0 表示用户不存在）。"""
    result = await session.execute(
        update(User).where(User.id == user_id).values(status=status)
    )
    return result.rowcount
