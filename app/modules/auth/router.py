"""认证模块的 HTTP 接口。

职责：只做参数解析、依赖注入与响应封装。不承载业务逻辑，不直接访问数据库。

接口清单（v1.0项目文档.md 第 6.1 节）：

    POST /api/v1/auth/register   注册
    POST /api/v1/auth/login      登录，返回 access token 并下发 refresh token Cookie
    POST /api/v1/auth/refresh    从 Cookie 读 refresh token，轮换双令牌
    POST /api/v1/auth/logout     吊销 refresh token，清除 Cookie

注意：refresh 与 logout 从 **Cookie** 读取令牌，不读请求体。

约束：
- 业务逻辑全部在 `service`，本层**不直接访问数据库**（README 第 4 节）。
- 所有响应走 `ApiResponse`（硬性约定 2）；**不捕获异常**，交给全局处理器（硬性约定 3）。
- refresh token 只走 **HttpOnly Cookie**，**不进响应体**；登录、刷新、登出三处的 Cookie 属性
  必须完全一致，否则浏览器不会覆盖或删除它。
- Cookie 的 `path` 由 `API_PREFIX` 推导，**不写死**。
- 依赖一律用 `Annotated[...]` 声明，不在参数默认值里调用 `Depends`（ruff B008）。
"""

from typing import Annotated

from fastapi import APIRouter, Cookie, Response, status

from app.api.dependencies import DbSession
from app.common.schemas import ApiResponse
from app.core.config import get_settings
from app.modules.auth import service
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
)

router = APIRouter(prefix="/auth", tags=["认证"])

COOKIE_NAME = "refresh_token"

RefreshTokenCookie = Annotated[str | None, Cookie()]


def _cookie_options() -> dict:
    """登录 / 刷新 / 登出共用的 Cookie 属性。

    三处必须完全一致，否则浏览器不会覆盖旧 Cookie，也不会真正删除它。
    """
    settings = get_settings()
    return {
        "key": COOKIE_NAME,
        # 只在认证接口上发送，不随每个 API 请求携带
        "path": f"{settings.api_prefix}/auth",
        "httponly": True,
        # 开发环境走 http，secure=True 会让浏览器直接丢弃 Cookie
        "secure": settings.app_env == "production",
        "samesite": "lax",
    }


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    session: DbSession,
) -> ApiResponse[RegisterResponse]:
    """公开注册；新用户恒为 USER。"""
    data = await service.register(session, payload)
    return ApiResponse.ok(data=data)


@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
    session: DbSession,
) -> ApiResponse[LoginResponse]:
    """登录：返回 access token，并通过 Set-Cookie 下发 refresh token。"""
    settings = get_settings()

    data, raw_refresh_token = await service.login(session, payload)
    response.set_cookie(
        value=raw_refresh_token,
        max_age=settings.refresh_token_expire_days * 86400,
        **_cookie_options(),
    )
    return ApiResponse.ok(data=data)


@router.post("/refresh")
async def refresh(
    response: Response,
    session: DbSession,
    refresh_token: RefreshTokenCookie = None,
) -> ApiResponse[RefreshResponse]:
    """从 Cookie 读取令牌并轮换；成功时覆盖 Cookie。"""
    settings = get_settings()

    data, raw_refresh_token = await service.refresh(session, refresh_token or "")
    response.set_cookie(
        value=raw_refresh_token,
        max_age=settings.refresh_token_expire_days * 86400,
        **_cookie_options(),
    )
    return ApiResponse.ok(data=data)


@router.post("/logout")
async def logout(
    response: Response,
    session: DbSession,
    refresh_token: RefreshTokenCookie = None,
) -> ApiResponse[None]:
    """登出：只吊销当前设备，并清除 Cookie。始终成功。"""
    await service.logout(session, refresh_token)
    response.delete_cookie(**_cookie_options())
    return ApiResponse.ok()
