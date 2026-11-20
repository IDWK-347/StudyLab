# StudyLab

> 一个基于 **FastAPI + LangGraph + 本地 Ollama** 的企业级知识库与 AI 问答平台，以群组为隔离单位，提供混合检索、引用溯源与流式问答。

---

## 0. 项目现状：去哪看

> **现状以代码为准。** 本文档其余章节只描述**目标设计**，不再重复现状 ——
> 现状曾被抄写在两份文档十余处，这正是它们此前长期失准的原因。**别再造第三份。**

| 想知道什么 | 去哪看 |
| --- | --- |
| **怎么写 V1.0 的代码** | **`v1.0项目文档.md`** —— 施工规格，每项带 `✅ 已完成` / `🚧 部分完成` / `⛔ 待实现` 标注 |
| **V1.0 范围内每项功能的状态** | `v1.0项目文档.md` **第 1.2 节**状态表 |
| **阶段 0–7 的全景进度** | 本文档**第 22 节**路线图的勾选 |
| 本机环境与已声明依赖的实际版本 | `v1.0项目文档.md` 第 2.1 节、第 8.1 节 |
| 尚未拍板的设计点 | `v1.0项目文档.md` 第 9 节 |
| 后续版本（V1.1+）的目标设计 | 本文档第 4–7、18–19 节 |

**当前**：**V1.0 已完成**——阶段 1 基础设施 13/13，阶段 2 的 V1.0 部分（认证 / 用户 / 权限）已实现并端到端实测。**V1.1 已开工**：四张群组表（`groups` / `group_members` / `group_invitations` / `group_join_requests`）的枚举、ORM 与迁移已落地并实测，业务代码（repository / service / router）未开始。

**遗留待清理**：`backend/.git`（零提交空仓库，已决定移除，尚未执行）。根目录的阶段 0 `main.py` 已于 2026-11-09 删除。

本文档**不含**压测数据、并发指标或"企业级"能力断言——这些尚无任何依据。

---

## 1. 项目目标

为中小团队构建一个**私有化部署、数据不出域**的知识库问答平台：

1. **知识资产集中管理** —— 文档统一入库、解析、切片、索引，形成可检索的知识底座。
2. **群组级数据隔离** —— 文档与会话归属群组，跨群组数据在数据访问层强制不可见。
3. **回答有据可查** —— 混合检索 + 引用溯源，答案必须能定位到原文切片；证据不足时明确拒答而非编造。
4. **模型完全本地化** —— 对话与嵌入模型均由本机 Ollama 提供，无云端 API 调用成本。
5. **工程规范可维护** —— 异步 IO、领域模块划分、统一异常与日志、可测试。

**目标用户**：需要在内部沉淀文档并快速检索问答的团队，且对数据外发有顾虑。

---

## 2. 与 Argus 的关系

本项目在**产品功能、业务模块划分、RAG 流程与交互设计**上参考了开源项目 [Argus](https://github.com/DevYangJC/Argus)，但**技术实现完全重写**，不是代码移植。

**参考项目 Argus 的实际情况**（据其仓库说明整理，仅供参考）：

| 维度 | Argus |
| --- | --- |
| 语言 / 框架 | Java 21 + Spring Boot 3.5.0 |
| ORM | MyBatis-Plus |
| AI 编排 | Spring AI Alibaba（DashScope / 通义千问） |
| 嵌入模型 | 云端 `text-embedding-v3`（512 维） |
| 向量库 | PostgreSQL + pgvector（HNSW，COSINE_DISTANCE） |
| 全文检索 | Elasticsearch 8.x + IK 分词 + BM25 |
| 对象存储 | MinIO |
| 前端 | Vue 3.5 + TypeScript + Vite + Pinia + Element Plus + Axios |
| 许可证 | MIT |

**本项目的差异**：

| 维度 | Argus（Java） | StudyLab（本项目） |
| --- | --- | --- |
| 语言 | Java 21 | Python 3.12+ |
| Web 框架 | Spring Boot | FastAPI |
| ORM | MyBatis-Plus | SQLAlchemy 2.x 异步 |
| AI 编排 | Spring AI Alibaba | LangChain + LangGraph |
| 模型来源 | 阿里云百炼（云端 API） | **本机 Ollama（完全本地）** |
| 嵌入模型 | text-embedding-v3 | **`bge-m3`**（本地 Ollama 部署） |

**边界说明**：

- 本项目**未使用** Spring Boot、Spring AI、MyBatis-Plus 或任何 Java 组件。
- 本项目**未复制** Argus 的源代码或宣传文案；Java 类未做逐类翻译，模块划分按 FastAPI / SQLAlchemy / LangGraph 的习惯重新设计。
- 原项目采用 MIT 许可证。**若后续在本仓库中引入或改编了 Argus 的任何代码，必须保留其版权声明与 MIT 许可证文本**，并在「致谢」一节中注明。当前仓库不包含 Argus 代码，故暂无此义务。
- 本项目当前**尚未选择开源许可证**，详见文末「License」一节。

---

## 3. 功能状态

> 按本仓库的**实际代码**判定，不按计划判定。逐项状态见 **`v1.0项目文档.md` 第 1.2 节**状态表。

### ✅ 已实现

**基础设施**（非业务功能）：统一配置系统（含启动校验）、统一响应模型、全局异常处理、结构化日志与请求 ID、异步引擎与 `AsyncSession` 依赖注入、应用生命周期、`/health` 健康检查、Alembic 迁移（4 条，当前 head `b7c1e4d92f30`）。

**阶段 2 · V1.0**（2026-11-09 端到端实测）：注册、登录（access token + HttpOnly refresh Cookie）、令牌轮换（`rowcount` 并发守卫）、登出、当前用户、修改密码（改密吊销全部 refresh token）、管理员用户列表 / 详情 / 启用禁用（禁用即时生效，不能禁用自己）。共 **9 个接口**。

**数据模型：已落地。** `users`（12 列）、`user_refresh_tokens`（7 列），索引与约束已核对 §4.2–§4.4；V1.1 四张群组表（`groups` 8 列、`group_members` 6 列、`group_invitations` 9 列、`group_join_requests` 9 列）已由迁移 `b7c1e4d92f30` 建表，对照 `v1.1项目文档.md` §4.3–4.7 核对。

### 🚧 开发中

**V1.0 已完成**（阶段 1 基础设施 13/13 + 阶段 2 的 V1.0 部分）。下一步是 **V1.1**：群组 CRUD、成员管理与邀请、群组级角色、知识库与群组数据隔离。

> 遗留：`backend/.git` 空仓库；`tests/` 仍无测试。（根 `main.py` 与 `_scratch_ini_lab/` 已于 2026-11-09 清理。）

### 📋 规划中

以下能力**全部为规划中**，分阶段交付，详见第 22 节「开发路线图」：

- 用户注册、登录、登出，JWT 双令牌与 Refresh Token Rotation
- 系统角色与群组角色权限模型
- 群组 CRUD、成员管理、邀请
- 知识库与群组的数据隔离
- 文档上传、预览、下载、软删除
- PDF / DOCX / Markdown / TXT 解析
- 文本清洗与结构化切片
- 文档异步 ETL 流水线（含状态机与失败重试）
- pgvector 向量检索
- Elasticsearch BM25 关键词检索（IK 分词）
- 向量 + 关键词混合检索与 RRF 排名融合
- 查询改写与查询拆解
- 检索证据评估与拒答策略
- RAG 问答与引用溯源
- 普通对话 / 知识库问答双模式
- LangGraph 工作流编排
- 对话历史与短期记忆
- SSE 流式输出
- 操作日志与错误追踪

---

## 4. 系统架构

> 下图为**目标架构**。各组件在本机的就绪状态见 **`v1.0项目文档.md` 第 1.2 节**，此处不再重复标注。

```mermaid
flowchart TB
    subgraph Client["客户端"]
        FE["Vue 3 + TypeScript + Element Plus<br/>（../frontend 目录当前为空）"]
    end

    subgraph Edge["接入层"]
        NG["Nginx<br/>静态资源 / 反向代理 / SSE 透传<br/>（未部署）"]
    end

    subgraph App["应用层 — FastAPI（V1.0 已交付 9 个接口）"]
        API["API 路由层<br/>参数解析 · 依赖注入 · 响应"]
        SVC["业务服务层<br/>领域模块 service"]
        LG["LangGraph 编排<br/>CHAT / KB_SEARCH"]
        RAG["RAG 检索管线<br/>向量召回 ∥ BM25 → RRF → 证据评估"]
    end

    subgraph Infra["基础设施层"]
        PG[("PostgreSQL 16 容器 + pgvector<br/>容器 5432 → 宿主 5433<br/>（未启动）")]
        ES[("Elasticsearch 8.x + IK<br/>（未部署）")]
        MIO[("MinIO<br/>（未部署）")]
        OLL["Ollama 127.0.0.1:11434<br/>qwen3.8 ✅ 已就绪<br/>bge-m3 ✅ 已就绪（1024 维）"]
        RD[("Redis<br/>（未部署 · 可选）")]
    end

    FE --> NG
    NG --> API
    API --> SVC
    SVC --> LG
    LG --> RAG
    RAG --> PG
    RAG --> ES
    SVC --> MIO
    LG --> OLL
    SVC -.-> RD

    style PG fill:#ffe6e6
    style ES fill:#f0f0f0
    style MIO fill:#f0f0f0
    style RD fill:#f0f0f0
```

### 分层约束（设计要求）

| 层 | 职责 | 禁止 |
| --- | --- | --- |
| Router | 参数解析、依赖注入、响应封装 | 编写复杂 SQL、承载业务逻辑 |
| Service | 业务逻辑、事务边界 | 直接持有全局 Session |
| Repository | 数据库访问 | 泄露 ORM 对象到 Router |
| Infrastructure | 外部服务适配（MinIO / ES / Ollama / Redis） | 被业务层直接实例化 |

- 所有数据库操作使用 `AsyncSession`，Session 通过依赖注入获取，**不得保存为全局变量**。
- 禁止在 async 接口中执行阻塞式文件解析或同步网络请求；PDF / DOCX 解析等 CPU 密集或阻塞任务须放入线程池或独立 Worker。
- 外部服务统一通过独立 Client / Adapter 封装，在 FastAPI `lifespan` 中初始化与关闭。

---

## 5. 文档 ETL 流程

> **规划中**。当前无任何解析、切片或入库代码。

```mermaid
flowchart TB
    A["上传文件"] --> B["联合校验<br/>扩展名 + MIME + 文件头 + 大小"]
    B -->|校验失败| X["FAILED<br/>记录失败原因"]
    B --> C["计算 SHA-256"]
    C --> D["写入 MinIO"]
    D --> E["创建 documents 记录<br/>状态 UPLOADING → UPLOADED"]
    E --> F["创建 ingestion_jobs 任务"]
    F --> G["PARSING<br/>解析 PDF / DOCX / MD / TXT"]
    G --> H["文本清洗"]
    H --> I["CHUNKING<br/>结构化切片 + 重叠窗口"]
    I --> J["EMBEDDING<br/>调用嵌入模型生成向量"]
    J --> K["INDEXING<br/>写 PostgreSQL / pgvector"]
    K --> L["写入 Elasticsearch"]
    L --> M["COMPLETED"]

    G -->|异常| X
    H -->|异常| X
    J -->|异常| X
    X --> R["重试计数 +1<br/>可恢复则回到失败阶段"]

    style X fill:#ffe6e6
```

### 文档状态机

```text
UPLOADING → UPLOADED → PARSING → CHUNKING → EMBEDDING → INDEXING → COMPLETED
                └──────────────┴──────────┴───────────┴──────────┘
                                 任一阶段失败 → FAILED
```

### ETL 设计要求

| 要求 | 说明 |
| --- | --- |
| 分阶段持久化 | 每个阶段开始与结束都写入状态，便于断点定位 |
| 失败可诊断 | 保存失败原因（`error_message`）与重试次数（`retry_count`） |
| **幂等性** | ETL 操作必须幂等：重试前先按 `document_id` 清理已有切片，**不得产生重复切片** |
| 部分成功可恢复 | PostgreSQL 与 Elasticsearch 写入不一致时，以 `ingestion_jobs` 记录为凭据重放未完成阶段 |
| 删除级联 | 删除文档时同步清理 MinIO 对象、pgvector 向量与 Elasticsearch 文档（软删除仅标记业务记录） |
| 首版实现方式 | 使用 FastAPI `BackgroundTasks`，**其局限见下** |
| 上传方式 | 首版仅支持**小文件直接上传**；分片上传列入后续版本 |

### 关于 `BackgroundTasks` 的局限（必须知情）

首版采用 `BackgroundTasks` 是刻意的简化，但它有明确缺陷：

- **进程内执行** —— 任务与 Web 进程同生命周期，服务重启或崩溃将丢失进行中的任务。
- **无持久化队列** —— 没有重试、优先级、可见性或并发控制。
- **多 Worker 不可控** —— 使用 Gunicorn 多 Worker 时，任务落在哪个 Worker 不确定，无法横向扩展。
- **无背压** —— 大文件或并发上传会挤占 Web 进程资源。

生产环境应替换为 **Redis + Celery / Dramatiq / ARQ**。**该替换尚未进行，须经确认后再实施。**

---

## 6. RAG 检索流程

> **规划中**。本节描述目标链路与硬性约束。

```mermaid
flowchart TB
    Q["用户提问"] --> P["权限检查<br/>确定可见的 group_id / knowledge_base_id 范围"]
    P --> PP["查询预处理"]
    PP --> PL["查询规划<br/>改写 / 拆解"]
    PL --> V["pgvector 语义检索"]
    PL --> K["Elasticsearch BM25 检索"]
    V --> R["RRF 排名融合"]
    K --> R
    R --> DD["去重"]
    DD --> NB["相邻切片扩展"]
    NB --> EV{"证据充分?"}
    EV -->|不足| RJ["拒答<br/>说明知识库中信息不足"]
    EV -->|充分| CT["构造上下文<br/>资料内容视为不可信输入"]
    CT --> GEN["Qwen3-8B 生成回答"]
    GEN --> CIT["返回回答 + 引用来源"]

    style RJ fill:#ffe6e6
```

### 硬性约束

| # | 约束 |
| --- | --- |
| 1 | pgvector 检索与 Elasticsearch 检索**并行执行** |
| 2 | 两路检索必须使用**相同的** `group_id` / `knowledge_base_id` 过滤条件 |
| 3 | RRF 的平滑常数 `k` 与各通道 `top_k` **必须可配置**，不得写死 |
| 4 | 每条结果保留 `document_id`、`chunk_id`、文件名与分数 |
| 5 | **向量距离 ≠ 相似度**，两者不得混用或互相替代 |
| 6 | 不同通道的原始分数**不得直接相加**（量纲不同） |
| 7 | 融合一律基于**排名**（RRF），不基于原始分数 |
| 8 | 引用必须关联真实的 `document_chunks` 记录 |
| 9 | 模型**不得生成不存在的引用**；引用需在服务端校验后才返回 |
| 10 | 证据不足时明确拒答，不强行生成 |
| 11 | Prompt 中的文档内容按**不可信输入**处理，防范文档内提示词注入 |
| 12 | 记录检索耗时、模型耗时与总耗时 |

---

## 7. LangGraph 工作流

> **规划中**。目标是用状态图编排问答，而非为用 LangGraph 而过度设计。

### 状态字段

| 字段 | 说明 |
| --- | --- |
| `user_id` | 当前用户 |
| `group_id` | 群组隔离标识 |
| `knowledge_base_id` | 目标知识库（可为空） |
| `session_id` | 会话标识 |
| `mode` | `CHAT` / `KB_SEARCH` |
| `messages` | 消息列表 |
| `original_query` | 原始问题 |
| `rewritten_queries` | 改写 / 拆解后的问题列表 |
| `retrieved_documents` | 检索到的切片 |
| `evidence_level` | 证据充分度 |
| `answer` | 生成的回答 |
| `citations` | 引用来源 |
| `error` | 错误信息 |

### 节点流程

```mermaid
flowchart TB
    S((START)) --> VR["validate_request<br/>校验参数与权限"]
    VR -->|校验失败| HE["handle_error"]
    VR --> LM["load_memory<br/>加载近期消息窗口"]
    LM --> MD{"mode"}

    MD -->|CHAT| GA["generate_answer<br/>直接对话，不检索"]
    MD -->|KB_SEARCH| PQ["plan_query<br/>改写 / 拆解"]

    PQ --> VRt["vector_retrieve"]
    PQ --> KR["keyword_retrieve"]
    VRt --> FR["fuse_results<br/>RRF 融合 + 去重 + 邻接扩展"]
    KR --> FR
    FR --> EE["evaluate_evidence<br/>证据充分度评估"]
    EE --> GA

    GA --> SM["save_message<br/>持久化到 PostgreSQL"]
    SM --> E((END))
    HE --> E

    style HE fill:#ffe6e6
```

### 节点契约（设计要求）

| 节点 | 输入 | 输出 | 异常行为 |
| --- | --- | --- | --- |
| `validate_request` | 请求参数、当前用户 | 校验通过的上下文，或错误 | 参数非法 / 无权限 → 转 `handle_error` |
| `load_memory` | `session_id` | 最近 N 条消息 | 会话不存在 → 新建空会话 |
| `plan_query` | `original_query` | `rewritten_queries` | 规划失败 → 回退为原始问题 |
| `vector_retrieve` | 查询向量、权限范围 | 候选切片（带排名） | 服务不可用 → 记录错误，返回空列表 |
| `keyword_retrieve` | 查询文本、权限范围 | 候选切片（带排名） | 服务不可用 → 记录错误，返回空列表 |
| `fuse_results` | 两路候选 | 融合后的有序候选 | 单路为空时退化为另一路结果 |
| `evaluate_evidence` | 融合候选 | `evidence_level` | 评估失败 → 保守降级为"证据不足" |
| `generate_answer` | 上下文、历史消息 | `answer`、`citations` | 模型超时 → 转 `handle_error` |
| `save_message` | 完整状态 | 持久化结果 | 写入失败 → 记录错误，不阻断已生成内容 |
| `handle_error` | `error` | 结构化错误 | 终止流转 |

### 其他约束

1. 每个节点的输入、输出与异常行为必须显式定义。
2. **Agent 不得无限循环调用检索工具**；每轮最大工具调用次数需设上限。
3. 模型输出需做**结构化校验**后再采信。
4. LangGraph 状态中**不得保存不可序列化对象**（如数据库连接、HTTP 客户端实例）。
5. 对话历史持久化到 PostgreSQL。
6. Redis 仅作**可选**缓存或临时状态，**不是唯一数据源**。
7. **首版只实现最近消息窗口**，摘要记忆后续再逐步引入；**首版不实现复杂的三级记忆压缩**。

---

## 8. 技术栈

> 下表的「实际版本」列以 `pyproject.toml` 的约束为准；**V1.0 范围内的精确版本以
> `v1.0项目文档.md` 第 2.1 节为准**（该表取自 `uv.lock`）。
> 标注为「规划」者**尚未安装**，属目标选型。

| 分类 | 选型 | 实际版本 | 来源 |
| --- | --- | --- | --- |
| 语言 | Python | **`>=3.12`**（要求）；本机 uv 可用 3.12.13 | `pyproject.toml` |
| 项目版本 | studylab-backend | **0.1.0** | `pyproject.toml` |
| 包管理 | uv | **0.11.26** | 本机实测 |
| Web 框架 | FastAPI | **`>=0.141.1`** | `pyproject.toml` |
| 数据校验 | Pydantic 2.x | 随 FastAPI 安装；`pydantic-settings` **`>=2.15.0`** | `pyproject.toml` |
| ORM | SQLAlchemy 2.x（异步） | **`>=2.0.53`**（`sqlalchemy[asyncio]`） | `pyproject.toml` |
| PG 驱动 | asyncpg | **`>=0.31.0`** | `pyproject.toml` |
| 迁移 | Alembic | **`1.13.0`** | `pyproject.toml` |
| AI 编排 | LangChain + LangGraph | 未锁定 | 规划 |
| 对话模型 | **`qwen3.8`**（已确认） | `qwen3.8:latest` · 27.3B · Q4_K_M · ctx 262144 | Ollama `/api/tags` 实测 |
| 嵌入模型 | **`bge-m3`**（已确认） | `bge-m3:latest` · **1024 维** · 约 1.2 GB | Ollama `/api/embed` 实测 |
| 关系数据库 | PostgreSQL | **16**（容器 `pgvector/pgvector:pg16`，容器内 5432 → 宿主 5433） | 已确认方案 |
| 向量扩展 | pgvector | 随镜像提供，由初始化 SQL 或首个迁移启用 | 已确认方案 |
| 全文检索 | Elasticsearch 8.x + IK | 未部署 | 规划 |
| 对象存储 | MinIO | 未部署 | 规划 |
| 认证 | FastAPI Security + PyJWT（HS256）双令牌；pwdlib[argon2] 密码哈希 | **PyJWT 2.15.1** · **pwdlib 0.3.1** | `uv.lock` |
| 缓存（可选） | Redis | 未部署 | 规划 |
| 前端 | Vue 3 + TypeScript + Element Plus | ❌ 无 `package.json`，无法确认 | — |
| 状态管理 | Pinia | 未锁定 | 规划 |
| HTTP 客户端 | Axios | 未锁定 | 规划 |
| 部署 | Docker Compose | **29.6.1 / Compose v5.2.0**（守护进程未运行） | 本机实测 |
| 应用服务器 | Uvicorn；生产 Gunicorn | Uvicorn **`>=0.53.0`**；Gunicorn 未锁定 | `pyproject.toml` / 规划 |
| 反向代理 | Nginx | 未部署 | 规划 |
| 测试 | pytest + pytest-asyncio + httpx | pytest **`>=9.1.1`**、pytest-asyncio **`>=1.4.0`**、httpx **`>=0.28.1`** | `pyproject.toml` |
| 代码质量 | Ruff + mypy | ruff **`>=0.16.7`**、mypy **`>=2.3.1`** | `pyproject.toml` |

---

## 9. 项目目录结构

### 现状（实测）

> 各文件就绪状态见 **`v1.0项目文档.md` 第 3.1 节**的现状树。

```text
StudyLab/                     ← 主仓库 github.com/IDWK-347/StudyLab.git
├── backend/
│   ├── .git/                 ⚠️ 零提交的空仓库 —— 已决定移除（尚未执行）
│   ├── app/                  # V1.0 已实现（基础设施 + 认证 / 用户 / 权限）
│   ├── initdb/
│   │   └── 01-extension.sql
│   ├── tests/                # 只有 conftest.py
│   ├── docker-compose.yml
│   ├── .env.example  .env  .gitignore
│   ├── pyproject.toml
│   ├── uv.lock
│   └── README.md
└── frontend/                 # 空目录 —— 已决定建仓
```

**版本控制决策（已确认）**：移除 `backend/.git`，前后端统一由外层 `StudyLab` 仓库管理。

### 目标结构（`app/` 骨架已建，其余随阶段推进）

```text
backend/
├── app/
│   ├── main.py               # FastAPI 应用入口
│   ├── api/
│   │   ├── dependencies.py   # 依赖注入
│   │   └── router.py         # 路由聚合
│   ├── core/
│   │   ├── config.py         # Pydantic Settings
│   │   ├── security.py       # JWT / 密码哈希
│   │   ├── exceptions.py     # 统一异常
│   │   ├── logging.py
│   │   └── lifespan.py       # 资源初始化与释放
│   ├── common/
│   │   ├── schemas.py        # 统一响应模型
│   │   ├── pagination.py
│   │   └── enums.py
│   ├── modules/              # 领域模块，按业务划分
│   │   ├── auth/
│   │   ├── users/
│   │   ├── groups/
│   │   ├── knowledge_bases/
│   │   ├── documents/
│   │   ├── ingestion/        # 文档 ETL
│   │   ├── retrieval/        # 向量 + BM25 + RRF
│   │   ├── qa/               # RAG 问答
│   │   └── assistant/        # LangGraph 对话
│   ├── infrastructure/
│   │   ├── database/
│   │   ├── elasticsearch/
│   │   ├── minio/
│   │   ├── redis/
│   │   └── llm/              # Ollama / Qwen 适配
│   └── workers/              # ETL 执行器
├── alembic/                  # 数据库迁移
├── tests/
├── pyproject.toml
├── alembic.ini
├── Dockerfile
└── .env.example
```

每个业务模块内部按需包含：`router.py`、`schemas.py`、`models.py`、`repository.py`、`service.py`、`permissions.py`、`exceptions.py`。

> 该结构为**建议约定**，实现时可按实际情况调整。

---

## 10. 环境要求

### 实测的本机环境

| 依赖 | 实测版本 | 是否满足 |
| --- | --- | --- |
| Python（系统） | 3.11.9 | ❌ 不满足 `>=3.12` |
| Python（uv 管理） | 3.12.13 已就绪 | ✅ |
| uv | 0.11.26 | ✅ |
| Node.js | v24.18.0 | ✅ |
| npm | 11.16.0 | ✅ |
| Git | 2.55.0.windows.2 | ✅ |
| Docker | 29.6.1 | ⚠️ 守护进程未运行 |
| Docker Compose | v5.2.0 | ⚠️ 同上 |
| PostgreSQL | 18.4（本机原生 Windows 服务） | ➖ **本项目不使用**，将由容器 PG 16 取代 |
| Ollama | 运行中，0.34.0 | ✅ `bge-m3` 已安装（1024 维，见 12.5） |

### 硬件前提（针对本机实际模型）

> 以下基于 Ollama 回报的**真实模型参数**推算，非实测结论。

| 场景 | 模型 | 磁盘 | 内存 / 显存 |
| --- | --- | --- | --- |
| 对话 | `qwen3.8:latest`（27.3B, Q4_K_M）—— **已确认采用** | **约 17.7 GB** | 建议 **≥ 24 GB 内存**，或有足够显存（约 20 GB 级）的 GPU；纯 CPU 可运行但速度显著下降 |
| 嵌入 | `bge-m3:latest` —— **已确认采用** | **约 1.2 GB**（实测） | 占用低，CPU 即可 |
| 检索 | Elasticsearch | 建议 ≥ 2 GB 堆内存 | — |

⚠️ 规格文档中称对话模型为"Qwen3-8B"，但本机实际模型为 **27.3B**，两者硬件需求差距很大。请以实际模型为准。

---

## 11. 环境变量说明

> `app/core/config.py` 与 `.env.example` **均已落地**（逐项状态见 **`v1.0项目文档.md` 第 1.2 节**）。
> 下方清单中，**应用与数据库部分已在代码中定义并校验**，其余为后续阶段的契约草案。
> 变量名与 `docker-compose.yml` 必须一致。**请勿直接使用示例中的密码或密钥。**

### 应用

| 变量 | 说明 | 取值 |
| --- | --- | --- |
| `APP_NAME` | 应用名 | `StudyLab` |
| `APP_ENV` | 运行环境 | `development` / `production` |
| `DEBUG` | 调试开关 | `false` |
| `API_PREFIX` | API 前缀 | `/api/v1` |
| `HOST` | 监听地址 | `0.0.0.0` |
| `PORT` | 监听端口 | `8000` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

### 数据库

> **宿主机端口固定为 `5433`**，用于避开本机原生 PostgreSQL 18.4 占用的 `5432`。
> 容器内部端口仍为 `5432`。`DATABASE_URL` 的取值**取决于后端运行位置**，两者不可混用。

| 后端运行位置 | `DATABASE_URL` |
| --- | --- |
| 宿主机（`uv run uvicorn`） | `postgresql+asyncpg://USER:PASSWORD@localhost:5433/studylab` |
| Docker Compose 内 | `postgresql+asyncpg://USER:PASSWORD@postgres:5432/studylab` |

| 变量 | 说明 | 取值 |
| --- | --- | --- |
| `DATABASE_URL` | 异步连接串 | 见上表 |
| `DB_POOL_SIZE` | 连接池大小 | `10` |
| `DB_MAX_OVERFLOW` | 溢出连接数 | `20` |
| `DB_POOL_TIMEOUT` | 获取连接超时（秒） | `30` |

### 认证

| 变量 | 说明 | 取值 |
| --- | --- | --- |
| `JWT_ACCESS_SECRET` | Access Token 签名密钥，**必须自行生成**。这是**唯一**的签名密钥 | `CHANGE_ME` |
| `JWT_ALGORITHM` | 签名算法 | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 有效期（分钟） | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 有效期（天） | `7` |

生成密钥：

```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 模型服务（Ollama）

> **已确认的设计决策**：对话与嵌入模型**全部走 Ollama 原生 API**，
> **不使用 OpenAI 兼容端点**（即不设 `QWEN_BASE_URL` / `QWEN_API_KEY`），
> 因为两者实际指向同一服务，保留两套变量只会造成配置漂移。
> 对应的 LangChain 组件为 `langchain-ollama` 的 `ChatOllama` 与 `OllamaEmbeddings`。

| 变量 | 说明 | 取值 |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | Ollama 原生 API 地址 | **`http://localhost:11434`**（实测） |
| `OLLAMA_CHAT_MODEL` | 对话模型标签 | **`qwen3.8`**（实测存在于 Ollama） |
| `OLLAMA_EMBEDDING_MODEL` | 嵌入模型标签 | **`bge-m3`** |
| `EMBEDDING_DIMENSION` | 向量维度 | **`1024`** —— 本机 `bge-m3` 实测（见 12.5） |

**不设置 API Key** —— Ollama 不校验密钥，无需 `QWEN_API_KEY`。

> 变量名 `OLLAMA_CHAT_MODEL` / `OLLAMA_EMBEDDING_MODEL` 为本文档的命名建议（原规格中的 `QWEN_MODEL` / `EMBEDDING_MODEL` 已随 `QWEN_*` 一并废弃）。**如需沿用旧名请在实现前说明。**

### 检索

| 变量 | 说明 | 取值 |
| --- | --- | --- |
| `ELASTICSEARCH_URL` | ES 地址 | `http://localhost:9200` |
| `ELASTICSEARCH_USERNAME` | ES 用户名（关闭安全认证时留空） | 空 |
| `ELASTICSEARCH_PASSWORD` | ES 密码 | 空 |
| `ELASTICSEARCH_INDEX_PREFIX` | 索引前缀 | `studylab` |

### 对象存储

| 变量 | 说明 | 取值 |
| --- | --- | --- |
| `MINIO_ENDPOINT` | MinIO 地址 | `localhost:9000` |
| `MINIO_ACCESS_KEY` | 访问密钥 | `CHANGE_ME` |
| `MINIO_SECRET_KEY` | 私钥 | `CHANGE_ME` |
| `MINIO_BUCKET` | 存储桶 | `studylab-documents` |
| `MINIO_SECURE` | 是否 HTTPS | `false` |

### 缓存与跨域

| 变量 | 说明 | 取值 |
| --- | --- | --- |
| `REDIS_ENABLED` | 是否启用 Redis | `false` |
| `REDIS_URL` | Redis 连接串 | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | 允许的跨域来源（逗号分隔） | `http://localhost:5173` |
| `FRONTEND_URL` | 前端地址 | `http://localhost:5173` |

### 配置系统设计要求

1. 使用 `pydantic-settings` 建立统一配置，全部通过环境变量注入。
2. 提供 `.env.example`，**不得写入真实密钥**。
3. `.env` 必须加入 `.gitignore`（✅ 已落地：`.gitignore` 已存在并忽略 `.env`）。
4. 关键配置在启动时校验；缺失或非法应直接启动失败并给出明确提示。
5. Qwen / Ollama / PostgreSQL / Elasticsearch / MinIO 连接失败时，须给出明确错误信息。
6. 可选组件（Redis）支持开关；关闭时不得影响主流程。
7. **不得在代码中硬编码地址、端口、密码或模型名称。**
8. 配置字段、环境变量名与 Docker Compose 必须保持一致。

> **落地情况**：第 1–4 项 ✅ 已实现（`app/core/config.py`）；第 5–8 项随各阶段推进。

---

## 12. 基础设施配置指南

### 12.1 PostgreSQL 与 pgvector

> **方案已确认。** 不使用本机原生 PostgreSQL 18.4 作为本项目数据库 —— 它未安装 pgvector 扩展，
> 且在 Windows 上为 PG 18 获取可用的 pgvector 预编译包存在不确定性。
> 本项目通过 Docker Compose 运行 `pgvector/pgvector:pg16`，与宿主机上的原生 PG **完全隔离**。
>
> ✅ **已落地**：`docker-compose.yml` 在仓库根目录（当前只含 postgres）。Docker 守护进程运行中，
> **容器已启动并 healthy**（`studylab-postgres`，2026-10-10 实测），`vector` 扩展已装。
> 以下配置以该文件为准，本节只是节选。

#### 端口与连接串

| 项 | 取值 |
| --- | --- |
| 容器内部端口 | `5432` |
| **宿主机映射端口** | **`5433`** —— 避开本机原生 PG 18.4 占用的 `5432` |
| 宿主机访问 | `localhost:5433` |
| 容器间访问 | `postgres:5432` |
| 持久化 | **named volume** |

> 本机原生 PostgreSQL 服务（`postgresql-x64-18`，监听 5432）**保持不动**，本项目不连接也不修改它。

#### Compose 配置

> 以下为实际文件的节选，**以仓库根目录的 `docker-compose.yml` 为准**。

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: studylab
      POSTGRES_USER: studylab
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5433:5432"          # 宿主机 5433 → 容器 5432
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./initdb:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U studylab -d studylab"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

#### 启用 pgvector 扩展

**责任方是首个 Alembic 迁移**（基线 `5fca7b62bced_baseline`，**已定 2026-10-10**）。它的 `upgrade()` 执行：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

这条基线**不创建任何业务表**——后续业务表结构统一通过 Alembic 迁移管理。`IF NOT EXISTS` 保证它在两种库上都安全：扩展已装时是空操作，扩展缺失时完成初始化；前提是迁移账号具有相应权限，本项目的 `studylab` 是容器初始化时创建的超级用户，满足。

`initdb/01-extension.sql` 仍在原处、内容相同，作为**冗余保险**保留：它在数据卷首次创建时由 entrypoint 更早执行。两者幂等，不冲突。

> ⚠️ `/docker-entrypoint-initdb.d` 中的脚本**只在数据卷为空时执行**。数据卷已存在、或换到没有该脚本的环境时它不会生效 —— 这正是由迁移兜底的原因。

#### 职责划分（已确认）

| 责任方 | 内容 |
| --- | --- |
| **首个 Alembic 迁移**（基线） | `CREATE EXTENSION IF NOT EXISTS vector;`，**不建业务表** |
| 后续 **Alembic 迁移** | 业务表、约束、`vector(N)` 字段、向量索引 |
| `initdb/01-extension.sql` | 冗余保险：数据卷首次创建时更早启用扩展（幂等） |

**向量列与索引**（`N = 1024`，为本机 `bge-m3` 实测维度，见 12.5）：

```sql
-- ⚠️ 维度必须等于 EMBEDDING_DIMENSION，且必须由模型实际输出确认，不可猜测
CREATE TABLE document_chunks (
    id          BIGSERIAL PRIMARY KEY,
    group_id    BIGINT      NOT NULL,
    document_id BIGINT      NOT NULL,
    content     TEXT        NOT NULL,
    metadata    JSONB       NOT NULL DEFAULT '{}'::jsonb,
    embedding   vector(1024),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chunks_group ON document_chunks (group_id);

-- HNSW 索引的操作符类必须与查询使用的距离函数一致
-- vector_cosine_ops  ↔  <=>  （余弦距离）
CREATE INDEX idx_chunks_embedding ON document_chunks
    USING hnsw (embedding vector_cosine_ops);
```

**三方维度一致性要求**：`EMBEDDING_DIMENSION` 环境变量、SQLAlchemy 模型中的 `Vector(n)`、以及 Alembic 迁移生成的 `vector(n)` **必须完全一致**，且该 `n` 必须来自嵌入模型的真实输出。

> ⚠️ `CREATE EXTENSION IF NOT EXISTS vector;` 必须存在 —— 由初始化 SQL 或首个 Alembic 迁移提供（见上方「启用 pgvector 扩展」）。
> 参考项目 Argus 使用 `vector_cosine_ops` + `<=>`，本项目沿用该距离度量。

### 12.2 Elasticsearch 与 IK 分词

**当前状态：未部署。** 9200 端口无监听。

要点：

1. Elasticsearch 官方镜像**不含** IK 插件，需自定义 Dockerfile 安装。
2. **IK 插件版本必须与 Elasticsearch 版本严格一致**（同为 `8.x.y`），否则安装失败。
3. 中文场景下索引字段分析器应配置为 `ik_max_word`（写入）与 `ik_smart`（查询）；默认 `standard` 分析器会把中文切成单字，召回质量差。
4. 单节点部署下副本分片无法分配，集群呈 `yellow` 属正常；将索引副本数设为 `0` 即为 `green`。
5. **检索必须附加与 pgvector 相同的 `group_id` / `knowledge_base_id` 过滤**，否则会跨群组泄露数据。

```dockerfile
# 版本 tag 必须与 IK 插件版本完全一致
FROM docker.elastic.co/elasticsearch/elasticsearch:8.x.y
RUN bin/elasticsearch-plugin install --batch \
    https://get.infini.cloud/elasticsearch/analysis-ik/8.x.y
```

### 12.3 MinIO

**当前状态：未部署。** 9000 / 9001 端口无监听。

- 对象存储桶需在应用启动时**自动创建**，或通过独立的初始化服务创建。
- 文件在 MinIO 中的路径建议包含 `group_id` 前缀，便于按群组清理与审计。
- 删除文档时须同步删除对象；软删除仅标记数据库记录。

### 12.4 对话模型（qwen3.8）

**当前状态：✅ 就绪且已确认采用**，由本机 Ollama 提供。

```bash
# 确认模型存在
curl http://localhost:11434/api/tags
```

实测参数：`qwen3.8:latest` · 家族 `qwen35` · **参数量 27.3B** · Q4_K_M · 上下文 262144 · 体积约 17.7 GB。

调用方式（**Ollama 原生 API，本项目采用**）：

```bash
curl http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.8",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

LangChain 侧对应 `ChatOllama(model="qwen3.8", base_url=OLLAMA_BASE_URL)`。

> ⚠️ **命名澄清**：规格文档曾称该模型为 "Qwen3-8B"，但 Ollama 回报其为 `qwen35` 家族、
> **27.3B 参数**、父模型 `qwen3.8:27b-q4_K_M`。**已确认采用的就是这个 27.3B 模型**，
> 并非 8B 级模型 —— 硬件需求请按第 10 节规划。
>
> 该模型 `capabilities` 含 `thinking`，Qwen3 系列默认输出思维链。RAG 场景通常需要关闭，
> 否则推理过程会混入答案并显著增加延迟与 token 消耗。**具体关闭方式须在实现时按 LangChain 版本确认。**

### 12.5 嵌入模型（bge-m3）

**已确认采用 `bge-m3`**，通过 Ollama 本地部署。**已安装完成。**

本机实测（2026-09-15）：

| 项 | 取值 | 来源 |
| --- | --- | --- |
| 模型标签 | `bge-m3:latest` | `ollama list` |
| 模型 ID | `790764642607` | `ollama list` |
| 体积 | 约 1.2 GB | `ollama list` |
| **输出维度** | **`1024`** | `/api/embed` 响应中 `embeddings[0]` 的长度 |

安装：

```bash
ollama pull bge-m3
```

> **拉取波折记录（已解决）**：首次执行 `ollama pull bge-m3` 时下载持续停顿，日志反复出现
> `part N stalled; retrying` 与 `unexpected EOF`，blob 分片始终为 0 字节。当时本机 Ollama 的
> 出站连接指向 `198.18.0.95:443`（`198.18.0.0/15` 为代理软件常用的 fake-IP 段），推测与代理 / VPN 有关。
> **该问题后自行恢复，模型已成功拉取，无需再处理。** 记录于此仅供日后再次遇到同类症状时参考。

**维度已用真实响应确认**，不得凭记忆、文档或他人经验填写。换模型或换机器时须重新执行：

```bash
curl http://localhost:11434/api/embed \
  -H "Content-Type: application/json" \
  -d '{"model": "bge-m3", "input": "维度确认"}'
# 返回 JSON 中 embeddings[0] 的长度即为真实维度 → 填入 EMBEDDING_DIMENSION
```

本机实测返回 `embeddings` 长度为 1、`embeddings[0]` 长度为 **1024**。该值需在**三处保持一致**：`.env` 的 `EMBEDDING_DIMENSION`、SQLAlchemy 模型中的 `Vector(1024)`、Alembic 迁移生成的 `vector(1024)`。

> ⚠️ **不要沿用 `nomic-embed-text`（768 维）或其他模型的维度**。本机同时装有该模型，是最容易误取的值。

---

## 13. 本地开发启动

> 步骤 1–4 现已可用；步骤 5 待 Alembic 初始化；步骤 6 待阶段 7；步骤 7 待前端落地。
> 详见 **`v1.0项目文档.md` 第 8 节**开头的就绪说明。

### 1. 启动后端（开发模式）—— 现已可用

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# 实测可出 /docs，含 9 个业务接口
```

> 仓库根目录的阶段 0 残留 `main.py` 已于 2026-11-09 删除；启动命令始终是 `app.main:app`。

### 2. 安装依赖 —— 现已可用

```bash
uv sync
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 按第 11 节填写；所有密钥请自行生成
```

### 4. 启动基础设施

见第 14 节「Docker Compose 启动」。

### 5. 初始化数据库 —— ⛔ 尚不可用

```bash
uv run alembic init -t async alembic    # 必须先做这一步
uv run alembic upgrade head
```

> ⚠️ Alembic **尚未初始化**（无 `alembic.ini`、无 `alembic/`）。

### 6. 生产模式启动 —— 阶段 7 可用

```bash
uv run gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -w 4 \
    -b 0.0.0.0:8000 \
    --timeout 120
```

> ⚠️ Gunicorn **尚未加入依赖**，Nginx 未部署。

### 7. 启动前端

❌ `../frontend/` 目录**当前为空**，没有 `package.json`，无法启动。
**已确认会建仓**，但尚未开始。

预期命令（待前端落地后确认）：

```bash
cd ../frontend
npm install
npm run dev        # Vite 默认 http://localhost:5173
```

---

## 14. Docker Compose 启动

**当前状态：`docker-compose.yml` 已存在（只含 postgres）；本机 Docker 守护进程未运行**（`docker ps` 报 `dockerDesktopLinuxEngine` 连接失败），**容器从未启动过**。详见 **`v1.0项目文档.md` 第 8.2 节**。

### 规划的服务清单

| 服务 | 镜像 | 说明 |
| --- | --- | --- |
| `backend` | 本地构建 | FastAPI 应用 |
| `frontend` | 本地构建 | Vue 3 应用 |
| `postgres` | `pgvector/pgvector:pg16` | ✅ **已配置**（`docker-compose.yml`）；宿主 **5433** → 容器 5432 |
| `elasticsearch` | 本地构建（官方镜像 + IK） | 插件版本须与 ES 版本一致 |
| `minio` | `minio/minio` | 配初始化服务创建 Bucket |
| `redis` | `redis:7-alpine` | **可选**，通过 `REDIS_ENABLED` 开关 |
| `nginx` | `nginx` | 反向代理 |
| `ollama` | `ollama/ollama` | 见下方说明 |

### 编排要求

1. PostgreSQL 镜像**必须支持 pgvector**。
2. Elasticsearch 与 IK 插件版本**必须兼容**。
3. MinIO 需**自动创建 Bucket**，或提供独立的初始化服务。
4. 使用 `healthcheck` 与 `depends_on: condition: service_healthy`。
5. 使用 **named volume** 持久化数据。
6. 所有密钥通过 `.env` 注入，**不得写入 compose 文件**。
7. 明确区分**宿主机端口**与**容器内部端口**。
8. 容器之间**通过服务名称访问**，不得使用 `localhost`。
9. **不得把宿主机专用地址硬编码到应用配置**。
10. Nginx 须正确代理普通 API、上传接口与 SSE 接口。

### 关于 Ollama 与模型服务

- 本机 Ollama 当前以**宿主机原生进程**运行于 `127.0.0.1:11434`，**不由 Docker Compose 管理**。
- 若 Ollama 改为容器化，应用配置须从 `localhost:11434` 改为服务名（例如 `http://ollama:11434`），**且需同步修改 `.env`**。
- 若 Ollama 保持在宿主机：容器内访问宿主机需使用 `host.docker.internal`（Windows / macOS），**不能写 `localhost`**。
- **上述二选一尚未决定，需人工确认。**

### GPU 说明

Ollama 使用 NVIDIA GPU 需宿主机安装 `nvidia-container-toolkit`。本机对话模型为 27.3B（Q4_K_M，约 17.7 GB），**纯 CPU 运行可行但速度显著下降**。实际硬件配置未经验证，本 README 不提供实测数据。

### Nginx 的 SSE 配置要点

SSE 接口必须关闭代理缓冲，否则前端收不到逐字效果：

```nginx
location /api/v1/assistant/stream {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 300s;
    chunked_transfer_encoding off;
}
```

---

## 15. Alembic 迁移

**当前状态：已初始化**（2026-10-10）。`alembic.ini` + `alembic/` 就绪；`env.py` 已接 `get_settings()` 取连接串、`Base.metadata` 作 `target_metadata`、用 `create_async_engine(..., poolclass=NullPool)` 自建引擎（**不**复用 `app/infrastructure/database/session.py` 的模块级 engine）。基线迁移 `5fca7b62bced_baseline` 负责启用 `vector` 扩展。Alembic **已声明为依赖**（`1.13.0`）。

初始化（阶段 1 执行）：

```bash
uv run alembic init -t async alembic
```

常用命令（配置完成后可用）：

```bash
uv run alembic revision --autogenerate -m "描述"
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic current
uv run alembic history
```

### 迁移设计要求

- `CREATE EXTENSION IF NOT EXISTS vector;` 由**首个迁移（基线）**提供，该迁移**不建业务表**；`initdb/01-extension.sql` 保留为冗余保险（见 12.1）。基线为**空业务 + 一条扩展语句**，不是 autogenerate 产物。
- 向量列维度取 **`1024`**（`bge-m3` 实测值，见 12.5）。生成迁移时须与 `EMBEDDING_DIMENSION`、SQLAlchemy 的 `Vector(n)` 复核一致。
- 向量索引优先 HNSW，且**索引操作符类必须与查询距离函数一致**。
- `--autogenerate` 对 pgvector 类型与扩展的识别可能不完整，**生成后必须人工复核**。

---

## 16. API 文档地址

| 地址 | 说明 | 状态 |
| --- | --- | --- |
| `http://localhost:8000/docs` | Swagger UI | ✅ 可用 |
| `http://localhost:8000/redoc` | ReDoc | ✅ 可用 |
| `http://localhost:8000/openapi.json` | OpenAPI Schema | ✅ 可用 |

**现已可访问** —— 共展示 **9 个业务接口**（auth 4 + users 2 + admin 3）；`/health` 按设计不进 schema（见 **`v1.0项目文档.md` 第 6.5 节**）。

---

## 17. API 概览

### 已实现 API

**无。** 本仓库当前**没有任何 FastAPI Router**，因此没有任何已实现接口。

### 规划接口（设计草案，未实现，路径可能调整）

> 以下为按项目规格整理的目标接口，**不是从代码推导的现状**。统一前缀 `/api/v1`。

| 模块 | 方法 | 路径 | 说明 |
| --- | --- | --- | --- |
| auth | POST | `/auth/register` | 注册 |
| auth | POST | `/auth/login` | 登录 |
| auth | POST | `/auth/refresh` | 刷新令牌 |
| auth | POST | `/auth/logout` | 登出 |
| users | GET | `/users/me` | 当前用户 |
| users | PUT | `/users/me/password` | 修改密码 |
| admin | GET | `/admin/users` | 用户列表（仅 ADMIN） |
| admin | GET | `/admin/users/{id}` | 用户详情（仅 ADMIN） |
| admin | PATCH | `/admin/users/{id}/status` | 启用 / 禁用用户（仅 ADMIN） |
| groups | GET/POST | `/groups` | 群组列表 / 创建 |
| groups | GET/PUT/DELETE | `/groups/{id}` | 群组详情 / 更新 / 删除 |
| groups | GET/POST | `/groups/{id}/members` | 成员管理 |
| groups | POST | `/groups/{id}/invitations` | 邀请 |
| knowledge_bases | GET/POST | `/knowledge-bases` | 知识库列表 / 创建 |
| documents | POST | `/documents/upload` | 上传（首版：小文件直传） |
| documents | GET | `/documents` | 文档列表 |
| documents | GET | `/documents/{id}` | 详情 |
| documents | GET | `/documents/{id}/download` | 下载 |
| documents | GET | `/documents/{id}/preview` | 预览 |
| documents | DELETE | `/documents/{id}` | 软删除 |
| documents | GET | `/documents/{id}/status` | ETL 状态 |
| retrieval | POST | `/retrieval/search` | 混合检索 |
| qa | POST | `/qa/ask` | RAG 问答（非流式） |
| assistant | POST | `/assistant/chat` | 对话（CHAT / KB_SEARCH） |
| assistant | POST | `/assistant/stream` | 对话（SSE 流式） |

> **版本归属**：`admin` 三个接口属 **V1.0**；`groups` 与 `knowledge_bases` 相关接口属 **V1.1**。版本与阶段的对应关系见第 22 节。
>
> 表中**没有健康检查接口**——它在第 22 节阶段 1 的交付项里。路径**已定（2026-10-07）为 `/health`**，是**唯一的前缀外接口**（不带 `API_PREFIX` / 版本号），故不属业务接口表；且**不探测数据库**（纯 liveness）。它同时设了 `include_in_schema=False`，因此它也是全项目**唯一已实现、却不出现在 `/docs` 与 `openapi.json` 里的**接口。

---

## 18. JWT 认证说明

> **规划中。** 无任何认证代码。

### 令牌模型

| 令牌 | 传递方式 | 有效期 | 存储 |
| --- | --- | --- | --- |
| Access Token | `Authorization: Bearer <token>` | 30 分钟（可配） | 前端内存 |
| Refresh Token | **HttpOnly Cookie**（优先） | 7 天（可配） | 服务端仅存 **SHA-256 摘要** |

### 认证设计要求

1. **Refresh Token 不得明文入库**。令牌格式为 `<token_id>.<secret>`（`uuid4().hex` + `token_urlsafe(32)`）；库中只存 `token_id` 与 `SHA-256(secret)` 的 hex（`VARCHAR(64)`）。详见 `v1.0项目文档.md` 第 5.7 节。
2. **Refresh Token Rotation** —— 每次刷新后旧令牌立即失效，签发新令牌。
3. **登出时撤销** Refresh Token（服务端标记失效）。
4. Cookie 须正确配置 `HttpOnly`、`Secure`；`SameSite` 按部署场景配置（前后端同站用 `Lax`/`Strict`，跨站需 `None` + `Secure`）。
5. **只有 Access Token 是 JWT、有签名密钥**（`JWT_ACCESS_SECRET`）。Refresh Token 是 **opaque 随机串，不签名、无第二个密钥**——存库时只存其 SHA-256 摘要。
6. 密码使用 **Argon2id** 哈希（`pwdlib[argon2]`，已定 2026-10-11）。
7. CORS 必须与 Cookie credentials 配合：**允许凭证时不得使用 `*` 通配来源**，须显式列出来源。

### 权限模型

| 层级 | 角色 |
| --- | --- |
| 系统级 | `ADMIN` / 普通用户 |
| 群组级 | `OWNER` / `MANAGER` / `MEMBER` |

### 安全红线

- **权限不能只在前端控制**，服务端必须独立校验。
- PostgreSQL 查询必须进行 `group_id` 或 `knowledge_base_id` 校验。
- **pgvector 检索与 Elasticsearch 检索都必须附加权限过滤。**
- **防止通过篡改 `document_id` 访问他人文档** —— 所有按 ID 访问的接口必须先校验资源归属。

---

## 19. SSE 调用说明

> **规划中。** 无任何 SSE 实现。

### 事件类型

| 事件 | 说明 |
| --- | --- |
| `start` | 流开始，携带会话与消息标识 |
| `delta` | 增量文本片段 |
| `citation` | 引用来源 |
| `done` | 流正常结束 |
| `error` | 结构化错误 |

### 事件样例（目标格式）

```text
event: start
data: {"session_id": "..."}

event: delta
data: {"content": "根据"}

event: citation
data: {"document_id": 88, "chunk_id": 1024, "document_name": "handbook.pdf"}

event: done
data: {"finish_reason": "stop"}
```

### 实现要求

1. 使用 FastAPI `StreamingResponse`，`Content-Type: text/event-stream`。
2. 每个事件必须是合法 SSE 格式（`event:` / `data:` 字段，事件间以空行分隔）。
3. 必须处理客户端主动断开（`asyncio.CancelledError` / `request.is_disconnected()`）。
4. **完整回答结束后再持久化最终消息**，避免半截回答入库。
5. 正常结束必须发送 `done` 事件。
6. 异常时必须发送**结构化** `error` 事件，而非直接断开。
7. **不得重复发送已输出的 token。**
8. Nginx 必须对 SSE 接口关闭代理缓冲（见第 14 节）。
9. 设置合理的超时与心跳机制，防止中间代理因空闲而断开连接。
10. Redis 仅作为可选缓存，不作为流的唯一状态源。

### 前端调用示例（规划）

```ts
const res = await fetch('/api/v1/assistant/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${accessToken}`,
  },
  body: JSON.stringify({ session_id, mode: 'KB_SEARCH', message }),
})

const reader = res.body!.getReader()
const decoder = new TextDecoder()
// 解析 event: / data: 行，按空行切分事件
```

> 前端为独立目录（`../frontend/`），当前为空。使用 `EventSource` 时无法自定义 `Authorization` 头，故规划使用 `fetch` + `ReadableStream`。

---

## 20. 测试、格式化与类型检查

**当前状态：工具已可用，配置未编写。** `ruff` / `mypy` / `pytest` / `pytest-asyncio` / `httpx`
**均已声明并安装**，可直接执行；但 `[tool.ruff]` / `[tool.mypy]` / `[tool.pytest.ini_options]`
**尚未配置**，走各自默认规则（见 **`v1.0项目文档.md` 第 8.8 节**）。

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
uv run pytest --cov=app --cov-report=term-missing   # ⛔ 需先 uv add --dev pytest-cov
```

> ⚠️ 默认规则**查不出** `== None`（E711）这类问题 —— `ruff check` 报 `All checks passed`
> 的含义比看上去弱。编写 `[tool.ruff]` 时需显式补上规则集。
> ⚠️ `uv run pytest` 目前以 **exit 5** 退出（no tests ran）：`tests/` 下只有 `conftest.py`。

---

## 21. 常见问题

### 环境与依赖

**Q：`python --version` 显示 3.11.9，但项目要求 3.12+？**
A：本机系统 Python 为 3.11.9，不满足 `requires-python = ">=3.12"`。请使用 uv 管理的解释器（本机已有 3.12.13），命令一律用 `uv run` 前缀，不要直接用系统 `python`。

**Q：执行 `uv run ruff` / `uv run pytest` 报错找不到命令？**
A：这些工具**已声明并安装**，正常应能执行。若仍报找不到，多半是没走 `uv run`（见上一条），或 `.venv` 未同步 —— 先执行 `uv sync`。

**Q：`pyproject.toml` 里的项目名是 `rag-demo`，不是 StudyLab？**
A：**已改为 `studylab-backend`**（2026-09-20 核对）。曾残留的阶段 0 `main.py` 已于 2026-11-09 删除。

### 数据库与 pgvector

**Q：`CREATE EXTENSION vector` 报错 `could not open extension control file`？**
A：说明连的不是带 pgvector 的实例。本机原生 PostgreSQL 18.4 **未安装 pgvector**，本项目不使用它 —— 请连 Docker Compose 里的 `pgvector/pgvector:pg16`（宿主机端口 **5433**）。

**Q：宿主机已经有 PostgreSQL 占着 5432，会冲突吗？**
A：不会。本项目容器的**宿主机映射端口是 5433**，容器内部仍是 5432。后端跑在宿主机时连 `localhost:5433`；跑在 Compose 内时连 `postgres:5432`。两者不可混用。

**Q：向量维度该填多少？**
A：**`1024`** —— 本机 `bge-m3` 的 `/api/embed` 实测值，见 12.5。**不得凭记忆或文档猜测** —— 维度写错会导致建表成功但写入失败，或 HNSW 索引无法使用。

**Q：向量维度三方不一致会怎样？**
A：`EMBEDDING_DIMENSION`、SQLAlchemy 的 `Vector(n)`、迁移中的 `vector(n)` 必须完全一致。更换嵌入模型时必须**重新向量化全部历史文档**。

**Q：异步 ORM 报 `MissingGreenlet`？**
A：SQLAlchemy 异步模式下访问未预加载的关联属性会触发该错误，需显式使用 `selectinload` 等预加载策略。

### 模型

**Q：模型回答里混入了思维链内容？**
A：本机 `qwen3.8` 的 capabilities 包含 `thinking`，Qwen3 系列默认输出推理过程。RAG 场景通常需要关闭。具体关闭方式须按实际使用的 LangChain 版本确认。

**Q：规格写 Qwen3-8B，实际却是 27.3B？**
A：Ollama 回报 `qwen3.8:latest` 为 `qwen35` 家族、**27.3B 参数**、Q4_K_M、体积约 17.7 GB。**已确认采用这个 27.3B 模型**，硬件需求请按第 10 节规划。

**Q：为什么用 `OLLAMA_BASE_URL` 而不是 OpenAI 兼容端点？**
A：已确认统一走 Ollama **原生 API**（`http://localhost:11434`），不使用 `/v1` 兼容端点，因此**不设 `QWEN_BASE_URL` / `QWEN_API_KEY` / `QWEN_MODEL`** —— 两套变量指向同一服务，只会造成配置漂移。Ollama 不校验密钥，无需 API Key。

**Q：Ollama 报模型不存在？**
A：先确认模型已就绪：`curl http://localhost:11434/api/tags`。对话模型 `qwen3.8` 与嵌入模型 `bge-m3` 都需预先 `ollama pull`。

### 检索与流式

**Q：中文检索召回效果差？**
A：确认索引字段分析器为 `ik_max_word`（写入）与 `ik_smart`（查询），而非默认 `standard`（会把中文切成单字）。

**Q：单节点 Elasticsearch 状态为 yellow？**
A：单节点下副本分片无法分配属正常，将索引副本数设为 `0` 即转为 green。

**Q：SSE 在前端"一次性全部出现"，没有逐字效果？**
A：多为 Nginx 缓冲导致。需在 SSE 接口的 location 中关闭缓冲（`proxy_buffering off;`、`proxy_cache off;`），并调大 `proxy_read_timeout`；同时确认响应头为 `Content-Type: text/event-stream`。

**Q：CORS 报错？**
A：将前端地址加入 `CORS_ORIGINS`。携带凭证时**不能使用 `*` 通配**。

**Q：容器里连不上 Ollama / PostgreSQL？**
A：容器之间用**服务名**互联；容器访问宿主机原生服务需用 `host.docker.internal`。**不能写 `localhost`。**

### 仓库与版本控制

**Q：`backend/` 里有一个空的 `.git` 目录？**
A：实测存在但**没有任何提交**。已确认**移除**，前后端统一由外层 `StudyLab` 仓库（`github.com/IDWK-347/StudyLab.git`）管理。

**Q：仓库没有 `.gitignore`，`.env` 会不会被提交？**
A：**已建立 `.gitignore`**，其中忽略 `.env` 与 `.env.*`，但放行 `.env.example`。
注意 `.env` **已存在且写有真实值** —— 修改它时**不要 `git add -f`**。

---

## 22. 开发路线图

> 全部功能均为**规划中**。每完成一个阶段需通过格式检查、类型检查与测试，并等待确认后再进入下一阶段。

### 版本与阶段的对应

本节按**阶段**编排，`v1.0项目文档.md` 按**版本**编排。两者对应关系如下：

| 版本 | 对应阶段 | 范围 |
| --- | --- | --- |
| V1.0 | 阶段 1 + 阶段 2 的 V1.0 部分 | 骨架、配置、数据库、异常与日志、健康检查、认证、用户管理 |
| V1.1 | 阶段 2 的 V1.1 部分 | 群组、成员管理与邀请、群组级角色、知识库与群组数据隔离 |
| V1.2 | 阶段 3 | 文档管理 |
| V1.3 | 阶段 4 | 基础 RAG |
| V1.4 | 阶段 5 | 混合检索 |
| V1.5 | 阶段 6 | 对话系统 |
| V1.6 | 阶段 7 | 工程化与前端 |

> V1.0 的划分对齐参考项目 Argus 的版本编排——Argus 的 V1.0 同样只含骨架、认证与用户管理，群组被它放到 V1.1。

### 阶段 0：项目事实检查 ✅ 已完成

- [x] 扫描仓库现状
- [x] 输出已存在功能、缺失功能、技术冲突与风险
- [x] 生成本 README

### 阶段 1：基础设施 —— 已完成

> 逐项状态见 **`v1.0项目文档.md` 第 1.2 节**状态表 —— 本节按**阶段**编排，该表按**功能**编排，
> 是同一套排期的两种记法。

- [x] FastAPI 项目骨架与领域模块目录结构
- [x] `pydantic-settings` 统一配置系统
- [x] 启动时配置校验与依赖连通性检查 —— 配置项校验与 `lifespan` startup 的连通性探测（`SELECT 1`，失败 fail-fast）均已完成
- [x] SQLAlchemy 2.x 异步引擎与 `AsyncSession` 依赖注入 —— 引擎 + 会话工厂 + `get_db`，事务边界归 Service
- [x] Docker Compose 起 `pgvector/pgvector:pg16`（宿主 5433 → 容器 5432，named volume）—— 容器已启动并 healthy，`vector` 扩展已装
- [x] Alembic 初始化与首个迁移 —— 基线 `5fca7b62bced_baseline` 负责启用 `vector` 扩展、不建业务表；`upgrade head` 与 `downgrade base` 往返均已实测
- [x] 统一响应格式与全局异常处理
- [x] 结构化日志与请求追踪
- [x] 健康检查接口 —— `/health`，前缀外、纯 liveness、不进 schema
- [x] `.gitignore` 与 `.env.example`

### 阶段 2：认证与权限

> 本阶段**分两批交付**：**V1.0** 只做认证与用户管理，**V1.1** 再做群组与数据隔离。
> 划分依据见上方「版本与阶段的对应」，与参考项目 Argus 的 V1.0 / V1.1 边界一致。

**V1.0 交付**

- [x] 用户模型与注册
- [x] 登录与 JWT 双令牌签发
- [x] Refresh Token Rotation（含哈希入库）
- [x] 登出与令牌撤销
- [x] 当前用户信息、密码修改
- [x] 系统角色 `ADMIN` / `USER`
- [x] 管理员用户管理：用户列表 / 详情 / 启用禁用

**V1.1 交付**

- [ ] 群组级角色 `OWNER` / `MANAGER` / `MEMBER`
- [ ] 群组 CRUD、成员管理与邀请
- [ ] 知识库与群组数据隔离（数据访问层强制过滤）

### 阶段 3：文档管理

- [ ] MinIO 接入与 Bucket 自动创建
- [ ] 小文件直接上传（扩展名 / MIME / 文件头 / 大小联合校验）
- [ ] SHA-256 计算与文档记录
- [ ] PDF / DOCX / Markdown / TXT 解析（走线程池）
- [ ] 文档预览、下载与软删除
- [ ] ETL 状态机与 `ingestion_jobs` 任务记录
- [ ] 失败原因记录与重试计数
- [ ] 删除时同步清理 MinIO / pgvector / Elasticsearch

### 阶段 4：基础 RAG

- [ ] 文本清洗与结构化切片
- [ ] 嵌入模型接入（**前置已满足**：模型已安装，维度实测为 `1024`，见 12.5）
- [ ] `document_chunks` 表与 pgvector 向量入库
- [ ] HNSW 索引（操作符类与距离函数一致）
- [ ] 向量语义检索（含权限过滤）
- [ ] Qwen3-8B 问答生成
- [ ] 引用溯源与来源校验

### 阶段 5：混合检索

- [ ] Elasticsearch 部署与 IK 分词配置
- [ ] 切片索引构建（`ik_max_word` / `ik_smart`）
- [ ] BM25 关键词检索（含权限过滤）
- [ ] 向量与关键词并行检索
- [ ] RRF 排名融合（`k` 与各通道 `top_k` 可配置）
- [ ] 去重与相邻切片扩展
- [ ] 查询改写与查询拆解
- [ ] 证据充分度评估与拒答策略

### 阶段 6：对话系统

- [ ] 会话与消息模型
- [ ] LangGraph 状态图与节点实现
- [ ] `CHAT` / `KB_SEARCH` 双模式
- [ ] 工具调用次数上限控制
- [ ] 最近消息窗口短期记忆
- [ ] SSE 流式输出（含断开处理与心跳）
- [ ] 操作日志与错误追踪

### 阶段 7：工程化

- [ ] Docker Compose 编排（含 healthcheck 与 named volume）
- [ ] Nginx 反向代理（API / 上传 / SSE 分别配置）
- [ ] 前端应用（Vue 3 + TypeScript + Element Plus）
- [ ] pytest 测试体系与覆盖率
- [ ] Ruff + mypy 配置并接入 CI
- [ ] 性能与安全检查
- [ ] 文档完善

### 后续规划（未排期）

- [ ] 分片上传与断点续传
- [ ] 基于 SHA-256 的秒传
- [ ] 摘要记忆与多级记忆压缩（**首版明确不做**）
- [ ] 重排序模型（Rerank）
- [ ] 检索效果评测集与自动化回归
- [ ] 可观测性（链路追踪、Token 用量统计）
- [ ] 生产级任务队列（Redis + Celery / Dramatiq / ARQ）替换 `BackgroundTasks`

---

## 待确认事项

> 阶段 0 提出的 10 项阻塞问题**已全部由项目负责人裁定**。以下为确认结论与剩余待定项。

### 已确认的决策

| # | 决策 |
| --- | --- |
| 1 | **嵌入模型**：安装并使用 `bge-m3` —— **已完成**，实测输出 **1024 维**（见 12.5） |
| 2 | **对话模型**：采用 `qwen3.8`（27.3B） |
| 3 | **`pyproject.toml` 名称**：改为 `studylab-backend` —— ✅ **已完成**（2026-09-20 核对） |
| 4 | **数据库**：不使用本机原生 PG 18.4；改用 Docker Compose 运行 `pgvector/pgvector:pg16`；容器内 `5432` → 宿主机 **`5433`**；named volume 持久化；扩展由初始化 SQL 或首个迁移启用；业务表、`vector(N)`、向量索引由 Alembic 负责 |
| 5 | **版本控制**：移除 `backend/.git`，统一使用外层 `StudyLab` 仓库 —— ⚠️ **尚未执行**（`backend/.git` 仍在） |
| 6 | **前端**：一并建仓（**尚未开始**） |
| 7 | **模型调用方式**：统一走 Ollama 原生 API，**不使用 OpenAI 兼容端点**，不设 `QWEN_*` 变量与 API Key |
| 8 | **旧 README**：允许覆盖（已完成） |

### 仍需在实现时确定

| # | 事项 | 何时确定 |
| --- | --- | --- |
| 1 | 对话模型是否关闭 `thinking`，以及具体参数名 | 阶段 4 接入 LangChain 时按所用版本确认 |
| 2 | Ollama 是否容器化（影响 `OLLAMA_BASE_URL` 取值） | 阶段 7 编排 Compose 时确定 |
| 3 | 剩余未锁定依赖（LangChain / LangGraph、MinIO、ES 客户端等） | 各阶段 `uv add` 时确定 |
| 4 | 本项目开源许可证类型 | 发布前确定 |

> `EMBEDDING_DIMENSION` 的原待定项已于 2026-09-15 消除：`bge-m3` 安装完成，实测维度 **1024**（见 12.5）。

---

## 致谢

- 感谢 [Argus](https://github.com/DevYangJC/Argus)（作者 DevYangJC）在产品功能、模块划分与 RAG 流程设计上提供的参考。Argus 采用 MIT 许可证。
- 感谢以下开源项目：FastAPI、Pydantic、SQLAlchemy、Alembic、LangChain、LangGraph、PostgreSQL、pgvector、Elasticsearch、MinIO、Redis、Ollama、Vue.js、Element Plus。

---

## License

**本项目尚未添加开源许可证。**

在仓库根目录添加 `LICENSE` 文件之前，本项目默认适用著作权法——**保留所有权利**，他人无权复制、修改或分发本项目代码。本 README **不声明**本项目采用 MIT 或任何其他许可证。

**关于参考项目**：Argus 采用 MIT 许可证。本仓库当前**不包含** Argus 的代码，故暂无许可证继承义务。**若后续引入或改编 Argus 的任何代码，必须保留其原始版权声明与 MIT 许可证文本**，并在「致谢」一节中注明。

**待办**：确定本项目许可证类型后，在此处补充说明并添加 `LICENSE` 文件，同时更新本文档顶部的状态声明。

---

*本文档由仓库实际代码与实测环境生成。**现状的查询入口是第 0 节**（最近核对 2026-11-09），其余章节为目标设计；未实现的能力一律标注为"规划中"。文中所有"实测"结论均来自对本机环境的只读探测。*
