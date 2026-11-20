"""异步引擎与 Session 工厂。

职责：用 DATABASE_URL 创建 async engine 与 async_sessionmaker，供依赖注入取用。

约束：
- engine 是模块级的，生命周期归 core/lifespan.py 的 shutdown dispose()，本模块不 dispose。
- 连接池参数取自配置（DB_POOL_SIZE / DB_MAX_OVERFLOW / DB_POOL_TIMEOUT），不得写死。
- 一律使用 AsyncSession；**不得**把它保存为全局单例会话。

"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,
)

# 创建一个可配置的AsyncSession工厂
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
