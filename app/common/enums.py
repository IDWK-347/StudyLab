"""公共枚举。

职责：定义跨模块复用的枚举——系统角色、用户状态；后续阶段的群组角色、文档状态机、
对话模式也归此处。

约束：
- 枚举以**成员名（`.name`）**映射为 `VARCHAR` 存入数据库，**不使用**数据库原生 `ENUM`
  （v1.0项目文档.md 第 5.5 节）。
- 因此各成员的**名与值故意写成一致**（`ADMIN = "ADMIN"`），令 `.name` 与 `.value` 重合，
  避免二者混用却不报错。
- 纯定义：不承载逻辑，不依赖本项目其他模块。

TODO(阶段 2 / V1.1)：群组角色 OWNER / MANAGER / MEMBER。
TODO(阶段 3)：文档状态机（UPLOADING → ... → COMPLETED / FAILED，见 README 第 5 节）。
TODO(阶段 6)：对话模式 CHAT / KB_SEARCH。
"""

from enum import StrEnum


class SystemRole(StrEnum):
    ADMIN = "ADMIN"
    USER = "USER"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
