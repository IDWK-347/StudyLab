"""健康检查接口。

职责：提供探活端点（纯进程存活判断，不探测任何依赖），供容器编排 / 反向代理 / 人工确认服务可用性。

约束：
- 路径**已定（2026-10-07）**：`/health`，位于 `API_PREFIX` 之外，不受版本前缀影响。
- 因此不得并入 `app/api/router.py` 的聚合（那个聚合统一挂 `/api/v1`），须单独挂载。
- **不探测数据库**（已定）：纯 liveness，只回答「进程还活着」；依赖抖动不得让本端点报不健康，故不引入 `get_db` 等任何依赖（`v1.0项目文档.md` 第 9 节第 6 项）。
- `include_in_schema=False`：探针不出现在 `/docs` 与 `openapi.json` 中。
- 响应一律走 `ApiResponse`，成功与失败都是，不得返回裸 dict 或纯文本（`app/common/schemas.py`）。
- 本文件属 Router 层：只做依赖注入与响应封装，不承载业务逻辑、不在 Router 层写复杂 SQL（README 第 4 节）。
- 探针必须轻量、快速返回：禁止阻塞式调用与重活（README 第 4 节）。

TODO(阶段 1)：探活端点待实现。
"""

from fastapi import APIRouter

from app.common.schemas import ApiResponse

router = APIRouter(prefix="/health")


@router.get("")
async def health_check() -> ApiResponse[None]:
    return ApiResponse.ok()
