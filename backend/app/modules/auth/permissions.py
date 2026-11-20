"""认证模块的权限判定。

职责：认证接口（注册 / 登录 / 刷新 / 登出）**全部匿名可调**，本模块没有角色判定需求；
      ADMIN 校验由 `app.api.dependencies.AdminUserDep` 统一提供。

约束：权限必须在**服务端独立校验**，不能只靠前端拦截（README 第 18 节安全红线）。

说明：本文件暂无代码。分工见 `modules/users/permissions.py`——通用的角色守卫放在
      `app/api/dependencies.py`，领域模块的 `permissions.py` 只承载细粒度授权规则。
"""
