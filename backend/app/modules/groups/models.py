"""群组模块的 ORM 模型。

职责：`groups` / `group_members` / `group_invitations` / `group_join_requests` 四张表。

字段、类型、约束名与索引名逐一对应 v1.1项目文档.md 第 4.3–4.6 节，索引汇总见 4.7。

约束：
- 枚举用 `Enum(..., native_enum=False, length=16)` 由 SQLAlchemy **自动转换**（2026-11-12 决定），
  落库为 `VARCHAR(16)`、存**成员名**（`.name`）；不建数据库原生 `ENUM`，也不建 `CHECK`
  （硬性约定 7）。
- 时间列统一 `TIMESTAMPTZ`；`updated_at` 的刷新由 `onupdate=func.now()` 在 ORM 侧完成。
- 外键**不设** `ON DELETE CASCADE`：解散群组时由 Service 在同一事务内显式清理（4.8）。
- 表之间**不建 `relationship()`**，与 V1.0 的两个模型保持一致；跨表读取走显式 join，
  避免异步会话下访问未加载属性触发 `MissingGreenlet`（硬性约定 5）。
- `OWNER` 不单独占列，只存于 `group_members.role`（第 1 节 2026-11-11 决定）。
- 表结构由 Alembic 迁移生成（硬性约定 9）；本文件落盘后须在 `alembic/env.py` 的模型导入区
  确认 `app.modules.groups.models` 已注册，否则元数据完整性校验会拦下迁移命令。
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import (
    GroupRole,
    GroupStatus,
    InvitationStatus,
    JoinRequestStatus,
)
from app.infrastructure.database.base import Base


# 群组
class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    group_code: Mapped[str] = mapped_column(
        String(64),
    )

    group_name: Mapped[str] = mapped_column(
        String(128),
    )

    description: Mapped[str] = mapped_column(
        Text,
        server_default="",
    )

    status: Mapped[GroupStatus] = mapped_column(
        Enum(GroupStatus, native_enum=False, length=16),
        server_default=GroupStatus.ACTIVE.name,
    )

    dissolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (UniqueConstraint("group_code", name="uq_groups_group_code"),)


# 成员关系
class GroupMember(Base):
    __tablename__ = "group_members"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    group_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("groups.id", name="fk_membership_group"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_membership_user"),
    )

    role: Mapped[GroupRole] = mapped_column(
        Enum(GroupRole, native_enum=False, length=16),
        server_default=GroupRole.MEMBER.name,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_membership_group_user"),
        Index("idx_membership_user", "user_id"),
        Index("idx_membership_group_role", "group_id", "role"),
    )


# 定向邀请
class GroupInvitation(Base):
    __tablename__ = "group_invitations"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    group_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("groups.id", name="fk_invitation_group"),
    )

    inviter_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_invitation_inviter"),
    )

    invitee_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_invitation_invitee"),
    )

    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus, native_enum=False, length=16),
        server_default=InvitationStatus.PENDING.name,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_invitation_invitee_status", "invitee_user_id", "status"),
        Index("idx_invitation_group_invitee", "group_id", "invitee_user_id"),
    )


# 加入申请
class GroupJoinRequest(Base):
    __tablename__ = "group_join_requests"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    group_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("groups.id", name="fk_join_request_group"),
    )

    applicant_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_join_request_applicant"),
    )

    status: Mapped[JoinRequestStatus] = mapped_column(
        Enum(JoinRequestStatus, native_enum=False, length=16),
        server_default=JoinRequestStatus.PENDING.name,
    )

    decided_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_join_request_decider"),
    )

    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_join_request_group_status", "group_id", "status"),
        Index("idx_join_request_applicant", "applicant_user_id"),
    )
