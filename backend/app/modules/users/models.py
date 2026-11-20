"""用户模块的 ORM 模型。

职责：`users` 表。

字段与索引以 v1.0项目文档.md 第 4.2 / 4.4 节为准：
    id / user_code / username / email / display_name / password_hash
    system_role / status / must_change_password / last_login_at
    created_at / updated_at

约束：
- 枚举按**成员名**（`.name`）存为 VARCHAR，不存序号，也不用数据库原生 ENUM（第 5.5 节）
- 时间列统一 TIMESTAMPTZ
- 表结构由 Alembic 迁移生成

"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    String,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import SystemRole, UserStatus
from app.infrastructure.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    user_code: Mapped[str] = mapped_column(
        String(64),
    )

    username: Mapped[str] = mapped_column(
        String(64),
    )

    email: Mapped[str] = mapped_column(
        String(128),
    )

    display_name: Mapped[str] = mapped_column(
        String(128),
    )

    password_hash: Mapped[str] = mapped_column(
        String(256),
    )

    system_role: Mapped[SystemRole] = mapped_column(
        Enum(SystemRole, native_enum=False, length=16),
        server_default=SystemRole.USER.name,
    )

    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False, length=16),
        server_default=UserStatus.ACTIVE.name,
    )

    must_change_password: Mapped[bool] = mapped_column(
        Boolean,
        server_default=false(),
    )

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )
