"""统一响应模型。

职责：定义所有接口共用的 Pydantic 响应模型（如 success / data / message），
供 Router 层与全局异常处理器复用。
"""

from pydantic import BaseModel


class ApiResponse[T](BaseModel):
    success: bool
    data: T | None = None
    message: str | None = None

    @classmethod
    def ok(cls, data: T | None = None) -> "ApiResponse[T]":
        return cls(
            success=True,
            data=data,
            message=None,
        )

    @classmethod
    def fail(cls, message: str) -> "ApiResponse[T]":
        return cls(
            success=False,
            data=None,
            message=message,
        )
