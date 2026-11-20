"""群组模块的权限判定。

职责：按「请求人在目标群组中的角色」判定群组内操作——成员关系、`OWNER` / `MANAGER` 的边界、
      `ADMIN` 不得入群。通用认证与系统角色守卫由 `app/api/dependencies.py` 提供。

约束：权限必须在**服务端独立校验**，不能只靠前端拦截（README 第 18 节）。

V1.1 已确认的规则（v1.1项目文档.md 第 1 节，2026-11-11）：
- 系统角色为 `USER` 的账号可创建群组，创建者写入 `role='OWNER'`；`ADMIN` 不得创建。
- 只有 `OWNER` 可任命 `MANAGER`、转让所有权、批准加入申请。
- `OWNER` 可移除或降级 `MANAGER`；`MANAGER` 只能移除群组角色为 `MEMBER` 的成员。
- 邀请权限仅 `OWNER` / `MANAGER`；`MEMBER` 无邀请权。
- `MANAGER` 可主动退群；`OWNER` 退群按转让后退出或视为解散处理。

TODO(阶段 2 / V1.1)：待实现。
"""
