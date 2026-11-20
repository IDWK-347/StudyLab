# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目性质

StudyLab 是一个**教学项目**——从零搭建的 RAG 知识库平台后端（FastAPI + SQLAlchemy 2.x 异步 + 本地 Ollama）。

**代码由作者手写。** Claude 在这里的角色是讲解、审查、排错和给设计选项，**不是批量生成实现**。动手改代码前先确认。

## 权威文档

| 文件 | 作用 |
| --- | --- |
| `v1.0项目文档.md` | **V1.0 施工规格**（= 阶段 1 + 阶段 2 的 V1.0 部分）。**写 V1.0 代码时主要看它** |
| `README.md` | 项目全景与阶段 0–7 路线图；V1.1+ 的目标设计 |

**按「想知道什么」查，不按文件查：**

| 想知道什么 | 去哪看 |
| --- | --- |
| 怎么写 V1.0 的代码 | `v1.0项目文档.md` —— 施工规格 |
| V1.0 范围内每项功能的状态 | `v1.0项目文档.md` **第 1.2 节**状态表 |
| 阶段 0–7 的全景进度 | `README.md` **第 22 节**路线图勾选 |
| 后续版本（V1.1+）的设计 | `README.md` |
| **最终依据** | **代码** |

`README.md` 第 0 节是一张**路由表**，指向上表各项，本身不存现状 —— 现状曾被抄写在两份
文档十余处，这正是它们此前失准的原因。**别再造第三份。**

### 文档状态标注体系

`v1.0项目文档.md` 用三个标记**逐项**标注进度，**这是本项目追踪进度的实际机制**：

- `✅ 已完成` —— 真能跑，且已实测验证（作者会写清验证了什么）
- `🚧 部分完成` —— 有部分产出，或文件就绪但未运行
- `⛔ 待实现` —— **目标设计，不是现状**。字段名、路径、表结构都可能变

两条铁律：**未实现的一律标 `⛔`，不写「已完成」除非真能跑**；**更新时顺手把过期的标注改回真实**，
并同步 `v1.0项目文档.md` 顶部「最后更新」与「对应仓库状态」两行。

代码侧对应的是 `TODO(阶段 N)：待实现。`（见硬性约定第 11 条）。

`v1.0项目文档.md` 第 9 节是设计点的拍板记录——**V1.0 范围内已全部结清**（含 9.1 的两个子项：**公开注册**、初始化命令**交互输入**密码）。新增设计点仍记在该节；实现相关部分前先看它，**不要自己替作者选一个**。

## 当前进度

> **详细表格见 `README.md` 第 0 节「项目现状」—— 那是唯一事实源。**
> 本节是摘要（省得每次读全文）；两者不一致时，以 README 第 0 节与代码为准。

**V1.0 已完成**：阶段 1 基础设施 13/13，阶段 2 的 V1.0 部分（认证 / 用户 / 权限）已实现并通过
**真实应用的端到端实测**（9 个接口）。以下为 **2026-11-09 实测**。

**已完成**

- 目录骨架；`app/modules/{auth,users}/` 各 6 个文件（V1.0 已全部实现）
- 配置系统 `app/core/config.py`（`.env` 已存在且有真实值）、统一响应模型 `app/common/schemas.py`、
  全局异常处理 `app/core/exceptions.py`、结构化日志与请求 ID `app/core/logging.py`
- **数据库接入全链路**：`app/infrastructure/database/session.py`（模块级 engine + `async_session_factory`，
  池参数取自配置、`pool_pre_ping=True`）与 `app/api/dependencies.py` 的 `get_db`。
  **事务边界归 Service**：`get_db` 不 commit、不 rollback
- `app/core/lifespan.py` **已实现并挂进 `create_app()`**：startup 探测数据库（`SELECT 1`，失败 fail-fast），
  shutdown `engine.dispose()`
- 健康检查 `app/api/health.py`：`GET /health`，**前缀外**（不经 `API_PREFIX`）、纯 liveness 不探库、
  `include_in_schema=False`；由 `main.py` 单独挂载，**不经** `app/api/router.py`
- `docker-compose.yml`（只起 postgres）、`initdb/01-extension.sql`、`.env.example`、`.gitignore`
- **Alembic 已初始化**：`alembic.ini` + `alembic/`。`env.py` 用 `get_settings().database_url` 与
  `create_async_engine(..., poolclass=NullPool)` 自建引擎（**不**复用 `session.py` 的模块级 engine，
  避免事件循环冲突），`target_metadata = Base.metadata`。基线 `5fca7b62bced` 启用 `vector` 扩展、
  **不建业务表**，`upgrade head` 与 `downgrade base` 往返已实测
- **FastAPI 应用已可启动**：`from app.main import app` 成功；schema 中 **9 个业务接口**
  （`/health` 不进 schema）
- `uv run ruff check .` 与 `uv run ruff format --check .` 实测通过（42 个文件已格式化）
- **阶段 2 已落地的零件**（均已实测）：
  - `app/core/config.py` 新增 JWT 配置组：`jwt_access_secret`（必填、拒 `CHANGE_ME`）、
    `jwt_algorithm`、`access_token_expire_minutes`、`refresh_token_expire_days`
  - `app/common/enums.py`：`SystemRole` / `UserStatus`（`StrEnum`，**名与值一致**）
  - `app/core/security.py`：Argon2id 密码哈希、PyJWT access token 签发 / 解析；
    解码失败抛 `UnauthorizedException`（过期与无效**两条分支信息不同**）
  - 认证三项选型已定：PyJWT / `pwdlib[argon2]` / refresh token 摘要用 SHA-256
    （`v1.0项目文档.md` 第 2.3 节）
  - `app/modules/users/models.py` / `app/modules/auth/models.py`：两张表的 ORM 模型，
    DDL 已与 §4.2–§4.4 逐列核对
  - `alembic/env.py`：副作用导入两个模型 + **元数据完整性校验**（扫 `app/modules/*/models.py`
    与 `sys.modules` 求差集，模型漏注册即报错）+ 表清单日志
  - 迁移 `490e1e29c50d`：`users` + `user_refresh_tokens`，已 `upgrade head`，库中逐项核对通过
  - 迁移 `99a8b653b8b7`：`idx_refresh_token_token_id` 改为**唯一**索引，已应用（`--autogenerate`
    检不出 `unique` 标志变化，此迁移为手写）
  - `app/modules/auth/{schemas,repository,service}.py`：注册 / 登录 / 轮换 / 登出，**13 条实测通过**
    （含多设备并存、旧 token 复用被拒、**并发刷新只有一个成功**）
  - `app/modules/users/{schemas,repository,service}.py`：当前用户、改密（吊销全部 refresh token）、
    列表 / 详情 / 启停（**不能禁用自己**，禁用即时生效）；用户查询已从 auth 迁入 users
  - `app/api/dependencies.py`：`CurrentUser` 依赖（按 `sub` 查库，只向 Router 暴露 schema）+
    `AdminUserDep`；`auth/router.py` 4 个 + `users/router.py` 5 个接口；
    `app/api/router.py` 已聚合到 `API_PREFIX`，`main.py` 已挂载
  - `app/cli.py`：`create-admin`（交互输入、已存在即拒绝、唯一约束冲突回滚）
  - **端到端实测**：CLI 建管理员 → 注册 → 登录 → `/users/me` → 刷新 → 登出 → 管理员禁用 →
    被禁用者 access token 立即 401；schema 中 9 个接口、`/health` 仍不在 schema

**未实现（V1.0 范围之外）**

- **V1.1**：群组 CRUD、成员管理与邀请、群组级角色、知识库与群组数据隔离
- 收尾事项：`backend/.git`（零提交空仓库，已决定移除；**用户要求不要碰 git**，需其本人执行）

**环境事实**

- postgres 容器**运行中**（`studylab-postgres`，healthy，宿主 5433 → 容器 5432），`vector` 扩展已装；
  `public` 下有 `users`、`user_refresh_tokens`、`alembic_version` 三张表
- **没有任何测试**，`tests/` 只有 `conftest.py`，`uv run pytest` 以 exit 5（no tests ran）退出

## 常用命令

```bash
# 启动（开发模式）—— 现已可用；业务接口 9 个（/api/v1/*），另有前缀外的 /health
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 静态检查与格式化 —— 现已可用
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .
uv run ruff format --check .

# 类型检查
uv run mypy app

# 基础设施
docker compose up -d postgres      # 宿主 5433 → 容器 5432
uv run alembic upgrade head        # 当前 head = 99a8b653b8b7（含 token_id 唯一索引）

# 测试
uv run pytest
uv run pytest tests/test_x.py::test_y     # 单测（当前尚无任何测试文件）

# 依赖
uv add <pkg>
uv add --dev <pkg>
```

- **Docker 没起时应用会启动失败**：`lifespan` startup 探测数据库，连不上即 fail-fast（uvicorn 报
  `Application startup failed. Exiting.`）。这是设计，不是 bug——但意味着本地不起 Docker 就跑不了应用。
- **`uv run pytest` 会以 exit 5 退出**（no tests ran）：`tests/` 下只有 `conftest.py`，**没有任何测试**。
- **`[tool.ruff]` / `[tool.mypy]` / `[tool.pytest.ini_options]` 都还没配置**，走默认规则。实测默认规则**查不出** `== None`（E711）这类问题——`ruff check` 报 `All checks passed` 的含义比看上去弱。但也别低估它：实测默认规则**会**查出 `I001`（import 顺序）。

## 架构

### 分层

```text
Router（参数解析 / 依赖注入 / 响应封装）
  → Service（业务逻辑、事务边界）
    → Repository（数据库访问）
      → Infrastructure（外部服务适配）
```

领域模块放 `app/modules/<领域>/`，内部按 `router.py` / `schemas.py` / `models.py` / `repository.py` / `service.py` / `permissions.py` 划分。

### 组装层

`app/main.py` 是**唯一**知道所有部件存在的地方：创建 FastAPI 实例、注册异常处理器 / 中间件 / lifespan / 路由。部件之间**不互相 import 组装**。

启动命令写死了 `app.main:app`，这个对象名不能改——以后 Nginx 和 Docker Compose 都要跟这个写法对齐。

### 关键文件

| 文件 | 职责 |
| --- | --- |
| `app/core/config.py` | 唯一配置来源。`get_settings()` 带 `lru_cache`；启动时校验：必填缺失、`CHANGE_ME` 占位值、连接串内密码与 `POSTGRES_PASSWORD` 是否一致 |
| `app/common/schemas.py` | `ApiResponse[T]` —— 统一响应体 `{success, data, message}` |
| `app/core/exceptions.py` | `AppException` 基类 + 4 个子类（400/401/403/404）。**只给基类注册一个处理器**（Starlette 按 MRO 查找，子类自动命中）；另有 422 覆盖与 500 兜底。经 `register_exception_handlers(app)` 挂载 |
| `app/core/lifespan.py` | 资源初始化与释放。**已实现并挂载**：startup 探测数据库（`SELECT 1`，失败 fail-fast），shutdown `engine.dispose()` |
| `app/core/security.py` | 密码哈希（Argon2id）+ access token 签发 / 解析（PyJWT）。**已实现**：不碰数据库（refresh token 归 `modules/auth`）；`PasswordHash` 模块级单例；解码失败抛 401 |
| `app/core/logging.py` | 结构化日志 + 请求 ID（已实现） |
| `app/common/enums.py` | 公共枚举。**已实现**：`SystemRole` / `UserStatus`（`StrEnum`，名值一致，按 `.name` 存） |
| `app/infrastructure/database/` | 异步引擎与 Session 工厂。**已实现**：模块级 `engine` + `async_session_factory`，池参数取自配置，不连库即可构造 |
| `app/api/` | `dependencies.py`（`get_db`）与 `health.py`（`/health`，前缀外、不进 schema）**已实现**；`router.py` 的 `API_PREFIX` 聚合仍为占位 |
| `docker-compose.yml` | 阶段 1 只起 `postgres`（宿主 5433 → 容器 5432）。密码由 `.env` 注入，缺失即报错退出，不静默起弱密码实例 |
| `initdb/01-extension.sql` | `CREATE EXTENSION IF NOT EXISTS vector;` —— **仅在数据卷为空时执行一次** |

**只有 `app/main.py` 一个入口**（根目录的阶段 0 `main.py` 已于 2026-11-09 删除）：`app` 对象在
`app/main.py` 里，启动命令写死的 `app.main:app` 指的是它。

⚠️ `app/main.py` 在**模块级**执行 `app = create_app()`，所以**光是 import 它就会跑完整套 `Settings` 校验**——`.env` 缺失或值非法会直接抛异常。写测试 fixture 时要留意。

⚠️ 上面「组装层」描述的是**角色**。现状：`create_app()` 已注册异常处理器、请求 ID 中间件、lifespan，
并挂载了 `app/api/router.py`（聚合 auth / users / admin，挂在 `API_PREFIX` 下，共 9 个接口）
与 `app/api/health.py`（**前缀外**、不进 schema）。

## 硬性约定

1. **配置只能从 `get_settings()` 拿。** 任何地方不得 `import os` 读环境变量——那等于开了第二条配置来源。
2. **所有响应都走 `ApiResponse`**，成功和失败都是。JSON 字段一律 `snake_case`（所以不需要给 Pydantic 模型配别名生成器）。
3. **业务代码直接抛 `AppException` 子类**，Router 层不写 `try/except`。子类只负责写死自己的 `status_code`，调用方不传状态码。
4. **500 的响应体不得含堆栈**，堆栈只进日志。
5. `AsyncSession` 通过依赖注入获取，**不得保存为全局变量**；不把 ORM 对象泄露给 Router；访问关联属性要显式 `selectinload`，否则触发 `MissingGreenlet`。
6. 不得在代码中硬编码地址、端口、密码或模型名称。
7. 枚举按成员名（`.name`）存 `VARCHAR`，**不用**数据库原生 `ENUM`。
8. 时间列统一 `TIMESTAMPTZ`。
9. 表结构由 **Alembic 迁移**生成，**不写 `schema.sql`**。
10. 权限必须在服务端独立校验，不能只靠前端。
11. **每个文件写中文模块 docstring，体例固定**：首行一句话说明这是什么模块，随后 `职责：…`、`约束：…`（引 README 第 N 节），末尾以 `TODO(阶段 N)：待实现。` 收尾。这是这个仓库**追踪进度的实际机制**——新建文件照抄体例，实现完成后删掉对应的 `TODO` 行。

## 环境注意

- 系统 Python 是 **3.11.9，不满足** `requires-python = ">=3.12"`。一律用 `uv run`，不要直接用 `python`。
- 用户的终端是 **Git Bash (MINGW64)，不是 PowerShell**（已确认 2026-09-20）。给用户粘贴的命令、以及**三份文档里的所有示例命令**，一律用 bash 语法（`cp` 而非 `Copy-Item`）。
- **`alembic.ini` 必须保持纯 ASCII**（不能有中文注释）。alembic 读它用的是 `encoding="locale"`，中文 Windows 下 locale 是 GBK，UTF-8 中文会直接抛 `UnicodeDecodeError`，**且没有配置项可调**。（`docker-compose.yml` 里有中文注释没事——它由 Docker 解析、走 UTF-8。）
- `backend/.git` 是个**零提交的空仓库，已决定移除**；真正的仓库是外层的 `StudyLab/`。不要在 `backend/` 里提交。
- `frontend/` 目录存在但**完全为空**，属 V1.6。
