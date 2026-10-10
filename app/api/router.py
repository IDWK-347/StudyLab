"""路由聚合。

职责：汇总各领域模块的 router，统一挂在 API_PREFIX（/api/v1）之下。

约束：只做聚合，不承载业务逻辑；不在 Router 层写复杂 SQL（README 第 4 节）。

TODO(阶段 1)：APIRouter 聚合。
TODO(阶段 2)：各业务模块 router 逐步并入。
"""
