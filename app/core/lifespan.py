"""应用生命周期：资源初始化与释放。

职责：startup 校验依赖连通性；shutdown 阶段释放资源。

约束：外部服务统一在 lifespan 中初始化与关闭（README 第 4 节）。
      连接失败时须给出明确错误信息（README 第 11 节设计要求 5）。

注意：**不要**在这里同步阻塞地做重活，lifespan 是 async 上下文。

TODO(阶段 3+)：MinIO / Elasticsearch / Redis 客户端的初始化并入此处。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.database.session import engine

logger = logging.getLogger(__name__)


# 管理 FastAPI 的生命周期
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("正在校验数据库连通性")

        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            logger.info("数据库连通性校验成功")

        except (SQLAlchemyError, OSError) as exc:
            logger.error(
                "数据库连通性校验失败:host=%s port=%s error=%s: %s",
                engine.url.host,
                engine.url.port,
                type(exc).__name__,
                exc,
            )
            raise RuntimeError("数据库连通性校验失败") from exc

        yield

    finally:
        await engine.dispose()
        logger.info("释放数据库引擎")
