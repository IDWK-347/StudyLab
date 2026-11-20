"""认证模块的 ORM 模型。

职责：`user_refresh_tokens` 表。

字段与索引以 v1.0项目文档.md 第 4.3 / 4.4 节为准：
    id / user_id / token_id（明文，供索引）/ token_hash（摘要）
    expires_at / revoked_at（NULL = 有效）/ created_at

约束：
- `users` 表归 modules/users，此处**以字符串引用**其主键（`ForeignKey("users.id")`），
  不 import 该模块——避免两个领域模块互相 import。
- `token_hash` 是 **SHA-256 的 hex**（已定 2026-10-11），长度恰 64 字符。
- 同一 `user_id` 可有多行**同时有效**（**多设备**，已定 2026-10-11），每台设备一行；
  `token_id` 才是唯一的定位键。
- 时间列统一 TIMESTAMPTZ；表结构由 Alembic 迁移生成，**不写 schema.sql**。

"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


# refresh token 记录
class UserRefreshToken(Base):
    __tablename__ = "user_refresh_tokens"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
    )

    token_id: Mapped[str] = mapped_column(
        String(64),
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
    )

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        Index("idx_refresh_token_token_id", "token_id", unique=True),
        Index("idx_refresh_token_user_active", "user_id", "revoked_at", "expires_at"),
    )
