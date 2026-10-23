"""认证模块的请求与响应模型。

职责：注册请求、登录请求、令牌响应，以及登录/注册响应中内嵌的用户摘要。

约束：
- JSON 字段一律 **snake_case**；外层响应统一为 `{success, data, message}`
  （v1.0项目文档.md 第 9 节第 4 / 5 项，均已结清）。
- **输入要归一化**：`username` / `email` / `login_id` 一律去空白并转小写后**返回**——
  否则 repository 拿原值去查，命中不了库里的数据（第 6.1 节「账户输入策略」）。
- 用户名与密码规则取自 `app/core/security.py` 的 `USERNAME_PATTERN` / `MIN_PASSWORD_LENGTH`，
  **不在本文件另写正则或数字**；登录**不**套用密码下限。
- 注册请求**不得**包含 `system_role` / `status` / `user_code`——角色恒为 `USER`（第 9.1 节）。

"""

# 1. 导入 Pydantic 相关工具
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
)

from app.common.enums import SystemRole

# 2. 导入项目已有的用户名与密码规则
from app.core.security import MIN_PASSWORD_LENGTH, USERNAME_PATTERN

# 邮箱校验器
EMAIL_ADAPTER = TypeAdapter(EmailStr)


# 3. 定义 RegisterRequest
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr = Field(max_length=128)
    display_name: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)

    # 归一化
    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip().lower()
            if not USERNAME_PATTERN.fullmatch(value):
                raise ValueError("用户名格式不正确")
            return value
        return value

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("display_name", mode="before")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


# 4. 定义 LoginRequest
class LoginRequest(BaseModel):
    login_id: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)

    # 归一化
    @field_validator("login_id", mode="after")
    @classmethod
    def validate_login_id(cls, value: str) -> str:
        # 先归一化再校验：否则用户粘贴时带的首尾空白会导致误判
        value = value.strip().lower()

        if "@" in value:
            try:
                EMAIL_ADAPTER.validate_python(value)
            except ValidationError as e:
                raise ValueError("邮箱格式不正确") from e
        elif not USERNAME_PATTERN.fullmatch(value):
            raise ValueError("用户名格式不正确")

        return value


# 5. 定义 UserBrief
class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_code: str
    display_name: str
    system_role: SystemRole
    must_change_password: bool


# 6. 定义 LoginResponse
class LoginResponse(BaseModel):
    access_token: str
    expires_in: int
    user: UserBrief


# 7. 定义 RefreshResponse
class RefreshResponse(BaseModel):
    access_token: str
    expires_in: int


# 8. 定义 RegisterResponse
class RegisterResponse(UserBrief):
    pass
