"""用户模块的权限判定。

职责：管理员端点的 ADMIN 角色校验——**由 `app.api.dependencies.AdminUserDep` 提供**，
      本模块不重复实现。`modules/auth/permissions.py` 同此处理（认证接口全部匿名）。

约束：服务端独立校验，不得依赖前端（README 第 18 节）。

说明：本文件暂无代码。角色判定是**通用的认证守卫**，由所有领域模块共用，因此放在
      `app/api/dependencies.py`；各模块的 `permissions.py` 只负责领域内的细粒度授权，
      当前 V1.0 没有这类规则。
"""
