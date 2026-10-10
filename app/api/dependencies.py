"""依赖注入。

职责：提供可注入的公共依赖，阶段 1 只要一个 AsyncSession 依赖。

约束：Session 必须通过依赖注入获取，**不得保存为全局变量**（README 第 4 节）。

TODO(阶段 2)：当前用户 / 权限校验依赖。
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import async_session_factory


async def get_db() -> AsyncIterator[AsyncSession]:

    # 创建 session
    async with async_session_factory() as session:
        # 提供 session
        yield session
