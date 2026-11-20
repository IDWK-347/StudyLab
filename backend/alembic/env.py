import asyncio
import logging
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

import app.modules
import app.modules.auth.models
import app.modules.groups.models
import app.modules.users.models

# Side effect import: register the model into Base.metadata; will migrate to model_registry.py later
from alembic import context
from app.core.config import get_settings
from app.infrastructure.database.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")


# MetaData used by Alembic when automatically generating migrations
target_metadata = Base.metadata

# Find all models.py in the project and generate the set of modules that should be loaded
modules_dir = Path(app.modules.__file__).parent

expected_modules = {
    f"app.modules.{path.parent.name}.models" for path in modules_dir.glob("*/models.py")
}

# Check the modules that are actually loaded
loaded_modules = {name for name in expected_modules if name in sys.modules}

# Check if there are any modules not loaded
missing_modules = expected_modules - loaded_modules

if missing_modules:
    missing_list = "\n".join(f" - {name}" for name in sorted(missing_modules))

    raise RuntimeError(
        "以下模型模块尚未导入：\n"
        f"{missing_list}\n"
        "请在 alembic/env.py 的模型导入区补充导入"
        "（将来统一放到 model_registry.py）。\n"
        "否则 --autogenerate 会漏表，且不报错。"
    )

# Check if at least one table is registered
if not target_metadata.tables:
    raise RuntimeError(
        "模型模块已导入，但 Base.metadata.tables 为空。\n"
        "这与模型模块未导入是不同的问题："
        "可能是 ORM 模型未正确继承 Base，"
        "或者使用了不同的 MetaData，导致没有注册表。"
    )

# Verification passed, outputting the registered table list
logger.info(
    "已注册 %d 张表：%s",
    len(target_metadata.tables),
    ", ".join(sorted(target_metadata.tables)),
)


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
