"""FastAPI 应用入口。

职责：创建 FastAPI 实例、注册 lifespan、挂载路由与全局异常处理器、注册 CORS 中间件。

约束：本文件只做**组装**，不承载任何业务逻辑（README 第 4 节分层约束）。
"""

import logging

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.router import router as api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.lifespan import lifespan
from app.core.logging import (
    RequestIdMiddleware,
    setup_logging,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    # 业务路由：统一挂在 API_PREFIX（/api/v1）之下
    app.include_router(api_router)

    # 健康检查：前缀外单独挂载，且不进 schema
    app.include_router(health_router)

    return app


app = create_app()
