"""make refresh token id unique

Revision ID: 99a8b653b8b7
Revises: 490e1e29c50d
Create Date: 2026-10-22 01:35:54.331227

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "99a8b653b8b7"
down_revision: str | None = "490e1e29c50d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 删除原来的非唯一索引
    op.drop_index(
        "idx_refresh_token_token_id",
        table_name="user_refresh_tokens",
    )

    # 创建新的唯一索引
    op.create_index(
        "idx_refresh_token_token_id",
        "user_refresh_tokens",
        ["token_id"],
        unique=True,
    )


def downgrade() -> None:
    # 删除唯一索引
    op.drop_index(
        "idx_refresh_token_token_id",
        table_name="user_refresh_tokens",
    )

    # 恢复原来的非唯一索引
    op.create_index(
        "idx_refresh_token_token_id",
        "user_refresh_tokens",
        ["token_id"],
        unique=False,
    )
