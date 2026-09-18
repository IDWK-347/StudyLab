"""统一异常与全局异常处理器。

职责：定义业务异常基类，注册 FastAPI exception_handler，统一响应格式，避免异常细节外泄。
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.schemas import ApiResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int,
    ):
        self.message = message
        self.status_code = status_code


class BusinessException(AppException):
    def __init__(self, message: str):
        super().__init__(message, 400)


class UnauthorizedException(AppException):
    def __init__(self, message: str):
        super().__init__(message, 401)


class ForbiddenException(AppException):
    def __init__(self, message: str):
        super().__init__(message, 403)


class NotFoundException(AppException):
    def __init__(self, message: str):
        super().__init__(message, 404)


async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    response = ApiResponse.fail(exc.message)

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    response = ApiResponse.fail("服务器内部错误")
    logger.exception("未处理的异常")

    return JSONResponse(
        status_code=500,
        content=response.model_dump(),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    response = ApiResponse.fail("请求参数校验失败")

    return JSONResponse(
        status_code=422,
        content=response.model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        AppException,
        app_exception_handler,
    )

    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
