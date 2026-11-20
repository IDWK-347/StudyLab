"""pytest 公共 fixture。

TODO(阶段 2)：测试用数据库会话 fixture（事务回滚隔离）。
"""

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        # 让 HTTPX 将请求直接交给 FastAPI 应用处理
        transport=ASGITransport(
            app=app,
            raise_app_exceptions=False,
        ),
        base_url="https://testserver",
    ) as ac:
        yield ac
