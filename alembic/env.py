import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.core.config import get_settings
from app.infrastructure.database.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# 离线迁移
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # 获取数据库连接 URL
    url = get_settings().database_url

    # 配置离线迁移环境
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    # 运行离线迁移
    with context.begin_transaction():
        context.run_migrations()


# 配置 Alembic 的迁移环境，并运行迁移流程
def do_run_migrations(connection: Connection) -> None:

    # 配置迁移环境
    context.configure(connection=connection, target_metadata=target_metadata)

    # 建立迁移事务边界
    with context.begin_transaction():
        # 运行迁移流程
        context.run_migrations()


# 创建异步数据库引擎、获取数据库连接，并调用迁移函数
async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # 创建异步数据库引擎
    connectable = create_async_engine(
        poolclass=pool.NullPool,
        url=get_settings().database_url,
    )

    # 建立异步数据库连接
    async with connectable.connect() as connection:
        # 调用同步迁移函数
        await connection.run_sync(do_run_migrations)

    # 释放引擎持有的连接资源
    await connectable.dispose()


# 在线迁移
def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
