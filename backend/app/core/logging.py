"""结构化日志与请求追踪。

职责：配置日志格式与级别（读取 LOG_LEVEL），注入请求 ID，使同一次请求的多条日志可关联。

"""

import logging
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import get_settings

# 保存请求ID
request_id: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)


# 产生日志并输出
class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id.get()

        # 继续输出日志
        return True


# 格式化记录
class RequestIdFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not getattr(record, "request_id", None):
            record.request_id = "-"

        return super().format(record)


def setup_logging() -> None:
    # 获取配置
    settings = get_settings()
    # 设置等级
    level = settings.log_level.upper()
    # 实例化
    request_id_filter = RequestIdFilter()

    # 创建 formatter
    formatter = RequestIdFormatter(
        "%(asctime)s -  %(levelname)s -[%(request_id)s] -%(name)s - %(message)s"
    )

    # 创建 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 找自己创建的 handler
    handler = next(
        (
            handler
            for handler in root_logger.handlers
            if handler.get_name() == "studylab.console"
        ),
        None,
    )

    # 没有我们自己的 handler，才创建
    if handler is None:
        handler = logging.StreamHandler()
        handler.set_name("studylab.console")
        root_logger.addHandler(handler)

    handler.setLevel(level)
    handler.setFormatter(formatter)

    # 防止 setup_logging() 多次调用时重复添加 Filter
    if not any(isinstance(filter_, RequestIdFilter) for filter_ in handler.filters):
        handler.addFilter(request_id_filter)


# 创建中间件
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request,
        call_next,
    ) -> Response:
        current_id = uuid.uuid4().hex

        # 把 current_id 存入 ContextVar，并保存 set() 返回的 token
        token = request_id.set(current_id)

        # 同一个ID也保存到当前request
        request.state.request_id = current_id

        try:
            response = await call_next(request)

            # 把Request ID 写进响应头
            response.headers["X-Request-ID"] = current_id

            return response

        finally:
            # 返回之前的上下文状态
            request_id.reset(token)
