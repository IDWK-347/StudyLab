"""create group tables

职责：建 V1.1 的四张群组表——`groups` / `group_members` / `group_invitations` /
`group_join_requests`，字段、约束与索引见 `v1.1项目文档.md` 第 4.3–4.7 节。

约束：枚举落 `VARCHAR(16)`、存成员名（硬性约定 7）；外键显式命名且**不级联**，
解散清理由 Service 在同一事务内完成（4.8）；四张表放在同一迁移内，建表顺序即依赖顺序。

Revision ID: b7c1e4d92f30
Revises: 99a8b653b8b7
Create Date: 2026-11-11 01:31:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c1e4d92f30"
down_revision: str | None = "99a8b653b8b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("group_code", sa.String(length=64), nullable=False),
        sa.Column("group_name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE", "DISSOLVED", name="groupstatus", native_enum=False, length=16
            ),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column("dissolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_code", name="uq_groups_group_code"),
    )

    op.create_table(
        "group_members",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "OWNER",
                "MANAGER",
                "MEMBER",
                name="grouprole",
                native_enum=False,
                length=16,
            ),
            server_default="MEMBER",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["groups.id"], name="fk_membership_group"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_membership_user"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "user_id", name="uq_membership_group_user"),
    )
    op.create_index("idx_membership_user", "group_members", ["user_id"], unique=False)
    op.create_index(
        "idx_membership_group_role", "group_members", ["group_id", "role"], unique=False
    )

    op.create_table(
        "group_invitations",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("inviter_user_id", sa.BigInteger(), nullable=False),
        sa.Column("invitee_user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "ACCEPTED",
                "REFUSED",
                "CANCELLED",
                name="invitationstatus",
                native_enum=False,
                length=16,
            ),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["groups.id"], name="fk_invitation_group"
        ),
        sa.ForeignKeyConstraint(
            ["inviter_user_id"], ["users.id"], name="fk_invitation_inviter"
        ),
        sa.ForeignKeyConstraint(
            ["invitee_user_id"], ["users.id"], name="fk_invitation_invitee"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_invitation_invitee_status",
        "group_invitations",
        ["invitee_user_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_invitation_group_invitee",
        "group_invitations",
        ["group_id", "invitee_user_id"],
        unique=False,
    )

    op.create_table(
        "group_join_requests",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("applicant_user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "APPROVED",
                "REJECTED",
                "CANCELLED",
                name="joinrequeststatus",
                native_enum=False,
                length=16,
            ),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("decided_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["groups.id"], name="fk_join_request_group"
        ),
        sa.ForeignKeyConstraint(
            ["applicant_user_id"], ["users.id"], name="fk_join_request_applicant"
        ),
        sa.ForeignKeyConstraint(
            ["decided_by_user_id"], ["users.id"], name="fk_join_request_decider"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_join_request_group_status",
        "group_join_requests",
        ["group_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_join_request_applicant",
        "group_join_requests",
        ["applicant_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_join_request_applicant", table_name="group_join_requests")
    op.drop_index("idx_join_request_group_status", table_name="group_join_requests")
    op.drop_table("group_join_requests")
    op.drop_index("idx_invitation_group_invitee", table_name="group_invitations")
    op.drop_index("idx_invitation_invitee_status", table_name="group_invitations")
    op.drop_table("group_invitations")
    op.drop_index("idx_membership_group_role", table_name="group_members")
    op.drop_index("idx_membership_user", table_name="group_members")
    op.drop_table("group_members")
    op.drop_table("groups")
