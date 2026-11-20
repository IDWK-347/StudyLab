"""SQLAlchemy 声明式基类。

职责：定义 DeclarativeBase，供业务模型继承，并作为 Alembic 的 target_metadata 来源。

TODO(阶段 2)：业务模型开始继承本基类。
"""

from sqlalchemy.orm import DeclarativeBase


# 声明基类
class Base(DeclarativeBase):
    pass
