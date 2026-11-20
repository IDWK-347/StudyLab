"""模型注册表：集中 import 各领域模块的 ORM 模型。

职责：副作用导入所有 `app/modules/*/models.py`，令各表注册进 `Base.metadata`；
供 `alembic/env.py` 在读取 `target_metadata` **之前** import。

约束：
- **只做导入**，不承载查询、常量或工具函数——本文件的价值在于「一眼看全，加一行就完事」。
  一旦掺入别的职责，往里加东西就会开始需要判断。
- **单向依赖**：`app.modules.*` 不 import 本模块，故不成环。这正是它优于「在 base.py 里
  import 模型」的地方——后者会与 `Base` 形成循环导入（模型 → base → 模型）。
- 新增领域模块的 `models.py` 后**必须回来补一行**；漏了会被 `alembic/env.py` 的
  元数据完整性校验拦下，不会静默生成空迁移。

TODO(后续版本)：待启用。V1.0 只有两个模型，导入直接写在 `alembic/env.py` 内；模型数量增加后
迁来此处，并把 env.py 里那段元数据完整性校验一并搬过来当守卫。
"""
