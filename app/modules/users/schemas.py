"""用户模块的请求与响应模型。

职责：当前用户资料、修改密码请求、管理员视角的用户条目与详情、状态变更请求；
以及 `CurrentUser`——注入给依赖层的轻量身份，**不携带 ORM 对象**（硬性约定 5）。

约束：
- 响应模型一律 `ConfigDict(from_attributes=True)`，由 service 从 ORM 对象转换。
- **不得**在响应模型中包含 `password_hash`。
- 状态变更请求的 `status` 取 `UserStatus` 的**成员名**（`ACTIVE` / `DISABLED`，大写），
  非法值由 Pydantic 拦截为 422。
- 新密码受 `MIN_PASSWORD_LENGTH` 约束；**旧密码只校验非空**（与登录同理，避免调高下限后
  把存量用户锁在外面）。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import SystemRole, UserStatus
from app.core.security import MIN_PASSWORD_LENGTH


class CurrentUser(BaseModel):
    """已认证的请求者身份；不携带 ORM 对象。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    system_role: SystemRole
    status: UserStatus


class UserSummary(BaseModel):
    """用户条目：`/users/me` 与管理员列表的 `items[]` 共用。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    email: str
    system_role: SystemRole


class UserDetail(UserSummary):
    """管理员视角的用户详情。"""

    status: UserStatus
    created_at: datetime


class UserListResponse(BaseModel):
    """管理员列表：一次性返回全部用户，不分页。"""

    total: int
    items: list[UserSummary]


class ChangePasswordRequest(BaseModel):
    """修改当前用户密码。"""

    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(
        min_length=MIN_PASSWORD_LENGTH,
        max_length=128,
    )


class UserStatusUpdate(BaseModel):
    """管理员的启用 / 禁用请求。"""

    status: UserStatus
