"""FastAPI 应用入口。

职责：创建 FastAPI 实例、注册 lifespan、挂载路由与全局异常处理器、注册 CORS 中间件。

约束：本文件只做**组装**，不承载任何业务逻辑（README 第 4 节分层约束）。
"""

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
    )

    register_exception_handlers(app)

    return app


app = create_app()
