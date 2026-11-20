"""路由聚合。

职责：汇总各领域模块的 router，统一挂在 API_PREFIX（/api/v1）之下。

约束：只做聚合，不承载业务逻辑；不在 Router 层写复杂 SQL（README 第 4 节）。
"""

from fastapi import APIRouter

from app.core.config import get_settings
from app.modules.auth.router import router as auth_router
from app.modules.users.router import admin_router
from app.modules.users.router import router as users_router

router = APIRouter(prefix=get_settings().api_prefix)

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(admin_router)
