"""用户模块的 HTTP 接口。

职责：只做参数解析、依赖注入与响应封装。

接口清单（v1.0项目文档.md 第 6.2 / 6.3 节）：

    GET   /api/v1/users/me                              当前用户信息
    PUT   /api/v1/users/me/password                     修改当前用户密码
    GET   /api/v1/admin/users                           用户列表（仅 ADMIN）
    GET   /api/v1/admin/users/{user_id}                 用户详情（仅 ADMIN）
    PATCH /api/v1/admin/users/{user_id}/status          启用 / 禁用（仅 ADMIN）

约束：
- 业务逻辑全部在 `service`，本层**不直接访问数据库**（README 第 4 节）。
- 所有响应走 `ApiResponse`（硬性约定 2）；**不捕获异常**，交给全局处理器（硬性约定 3）。
- 管理员端点通过 `AdminUserDep` 在**服务端**校验角色，不能只靠前端隐藏入口（README 第 18 节）。
- `set_status` 必须传入**当前管理员 id**，service 据此拒绝「禁用自己」。
- 依赖一律用 `Annotated[...]` 声明（ruff B008）。
"""

from fastapi import APIRouter

from app.api.dependencies import AdminUserDep, CurrentUserDep, DbSession
from app.common.schemas import ApiResponse
from app.modules.users import service
from app.modules.users.schemas import (
    ChangePasswordRequest,
    UserDetail,
    UserListResponse,
    UserStatusUpdate,
    UserSummary,
)

router = APIRouter(prefix="/users", tags=["用户"])
admin_router = APIRouter(prefix="/admin/users", tags=["管理员"])


@router.get("/me")
async def get_me(
    user: CurrentUserDep,
    session: DbSession,
) -> ApiResponse[UserSummary]:
    """当前用户信息。"""
    data = await service.get_me(session, user.id)
    return ApiResponse.ok(data=data)


@router.put("/me/password")
async def change_password(
    payload: ChangePasswordRequest,
    user: CurrentUserDep,
    session: DbSession,
) -> ApiResponse[None]:
    """修改当前用户密码；成功后该用户所有设备需重新登录。"""
    await service.change_password(session, user.id, payload)
    return ApiResponse.ok()


@admin_router.get("")
async def list_users(
    admin: AdminUserDep,
    session: DbSession,
) -> ApiResponse[UserListResponse]:
    """用户列表：一次性返回全部。"""
    data = await service.list_users(session)
    return ApiResponse.ok(data=data)


@admin_router.get("/{user_id}")
async def get_user_detail(
    user_id: int,
    admin: AdminUserDep,
    session: DbSession,
) -> ApiResponse[UserDetail]:
    """用户详情。"""
    data = await service.get_user_detail(session, user_id)
    return ApiResponse.ok(data=data)


@admin_router.patch("/{user_id}/status")
async def set_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    admin: AdminUserDep,
    session: DbSession,
) -> ApiResponse[UserDetail]:
    """启用 / 禁用用户；**不能禁用自己**。"""
    data = await service.set_status(session, user_id, payload, admin.id)
    return ApiResponse.ok(data=data)
