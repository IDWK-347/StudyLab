# Argus-Python

> **项目状态：设计阶段** —— 本仓库当前仅包含 `uv` 脚手架，尚未包含实现代码。
> 本文档描述**目标形态与接口契约**，其中标注「规划中」的能力尚未实现，标注 `TODO` 的位置为待确认信息。
> 请勿将本文档中的命令与接口视为可运行的现状说明。

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-orchestration-1C3C3C.svg)](https://python.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-agent-FF6F61.svg)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg)](https://github.com/pgvector/pgvector)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.x-005571.svg)](https://www.elastic.co/)
[![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-000000.svg)](https://ollama.com/)
[![License](https://img.shields.io/badge/license-TODO-lightgrey.svg)](#license)

<!-- TODO: 仓库创建后，将下方 YOUR_ORG 替换为真实 GitHub 用户名或组织名 -->
<!--
[![Stars](https://img.shields.io/github/stars/YOUR_ORG/Argus-Python?style=flat)](https://github.com/YOUR_ORG/Argus-Python)
[![Issues](https://img.shields.io/github/issues/YOUR_ORG/Argus-Python)](https://github.com/YOUR_ORG/Argus-Python/issues)
-->

一个基于 **FastAPI + LangChain/LangGraph + Ollama** 的企业级 RAG 知识库平台，支持群组数据隔离、混合检索、引用溯源和 AI Agent 对话。

---

## 项目简介

Argus-Python 是 Java 版 [Argus](https://github.com/DevYangJC/Argus) 的 Python 复刻。原项目基于 Spring Boot 与 Spring AI Alibaba，模型依赖阿里云百炼的云端 API；本项目将后端整体迁移到 Python 生态，并把模型推理全部下沉到**本地部署的 Ollama**，从而获得完全离线、数据不出域、无 API 调用成本的部署形态。

### 与原版的核心差异

| 维度 | Java 版 Argus | Argus-Python |
| --- | --- | --- |
| 应用框架 | Spring Boot | FastAPI |
| AI 编排 | Spring AI Alibaba | LangChain / LangGraph |
| 对话模型 | 阿里云百炼（云端 API） | Ollama 本地部署 `qwen3.8b`（基于 `qwen3:8b` 自建） |
| 嵌入模型 | 云端 Embedding API | Ollama 本地部署 `bge-m3` |
| 持久化 | MyBatis / JPA | SQLAlchemy 2.x 异步 ORM |
| 部署 | JVM + Maven | Python 3.12 + uv |

**目标场景**：企业内部知识库问答。多名用户以「群组」为单位组织，同一群组内的文档互相可见、跨群组严格隔离；提问时系统在群组可见范围内做混合检索，并返回带原文引用的答案。

---

## 功能特性

> 以下为该平台的目标能力。除标注外均为**规划中**，按[开发路线图](#开发路线图)分阶段交付。

### 1. 用户认证与群组协作

- JWT **双令牌**机制（Access Token + Refresh Token），支持令牌续期。
- 三级角色权限模型：`ADMIN`（系统管理员）/ `GROUP_OWNER`（群组所有者）/ `MEMBER`（群组成员）。
- **群组数据隔离**：文档、切片、会话均归属群组，检索链路在数据访问层强制注入群组过滤条件，跨群组数据不可见。

### 2. 文档管理与智能解析

- **分片上传**：大文件切块上传，支持失败重试，最终合并入对象存储。
- **MinIO 对象存储**：原始文件与解析产物统一落对象存储，数据库仅保存元数据与指针。
- **多格式解析**：PDF、Word（`.docx`）、Excel（`.xlsx`）、Markdown。
- **文本切片**：按语义边界切分并保留重叠窗口，切片携带来源定位信息（页码 / 段落），用于后续引用溯源。
- **向量化与索引**：调用 Ollama `bge-m3` 生成嵌入，写入 PostgreSQL + pgvector；同步构建 Elasticsearch 全文索引。

### 3. 混合检索与 RAG 问答

- **语义检索**：pgvector 向量近邻召回。
- **关键词检索**：Elasticsearch BM25 召回，配合 IK 中文分词。
- **RRF 融合排序**：Reciprocal Rank Fusion 合并两路召回结果，规避分数量纲不一致问题。
- **证据评估**：对融合后的候选片段做相关性判定，证据不足时拒答而非强行生成。
- **引用溯源**：生成回答时附带引用来源（文档名 + 片段定位），前端可点击跳转原文。

### 4. AI Agent 对话系统

- **LangGraph Agent**：以图结构编排「理解意图 → 调用工具 → 汇总生成」流程。
- **双模式切换**：
  - `CHAT` —— 纯对话，不检索知识库；
  - `KB_SEARCH` —— 强制走知识库检索链路后再作答。
- **工具编排**：检索工具、文档元数据查询工具等按需调用。
- **SSE 流式输出**：回答逐 token 推送，首字延迟更优。
- **三级短期记忆压缩**：会话上下文超限时分层摘要压缩，控制长对话的 token 开销。

---

## 技术栈

| 分类 | 选型 |
| --- | --- |
| 语言 | Python 3.12+ |
| Web 框架 | FastAPI |
| ORM | SQLAlchemy 2.x（异步） |
| AI 编排 | LangChain、LangGraph |
| 对话模型 | Qwen3-8B（本地自建模型 `qwen3.8b`） |
| 嵌入模型 | bge-m3（Ollama 标签 `bge-m3`） |
| 关系库 | PostgreSQL + pgvector |
| 全文检索 | Elasticsearch 8.x + IK 中文分词 |
| 对象存储 | MinIO |
| 认证 | FastAPI Security + JWT 双令牌 |
| 缓存（可选） | Redis |
| 前端 | Vue 3 + TypeScript + Element Plus |
| 部署 | Docker Compose、Uvicorn / Gunicorn、Nginx |

---

## 系统架构说明

### 整体架构

```text
                          ┌──────────────────┐
                          │  Vue 3 前端 SPA   │
                          └────────┬─────────┘
                                   │ HTTPS
                          ┌────────▼─────────┐
                          │      Nginx       │  静态资源 / 反向代理 / SSE
                          └────────┬─────────┘
                                   │
        ┌──────────────────────────▼───────────────────────────┐
        │            FastAPI 应用（Uvicorn / Gunicorn）          │
        │                                                       │
        │  ┌──────────┬──────────┬──────────┬───────────────┐   │
        │  │ 认证/群组 │ 文档管理  │ 检索 API  │ 对话 / Agent  │   │
        │  └──────────┴──────────┴──────────┴───────────────┘   │
        │                       │                               │
        │  ┌────────────────────▼───────────────────────────┐   │
        │  │        LangGraph Agent 编排层                   │   │
        │  │  意图路由 → 工具调用 → 证据评估 → 生成          │   │
        │  └────────────────────┬───────────────────────────┘   │
        │                       │                               │
        │  ┌────────────────────▼───────────────────────────┐   │
        │  │            RAG 检索管线                         │   │
        │  │  向量召回 ┐                                    │   │
        │  │           ├─→ RRF 融合 → 证据评估 → Prompt     │   │
        │  │  BM25 召回 ┘                                   │   │
        │  └────────────────────────────────────────────────┘   │
        └───┬──────────┬──────────┬──────────┬──────────┬───────┘
            │          │          │          │          │
      ┌─────▼───┐ ┌────▼────┐ ┌───▼────┐ ┌───▼─────┐ ┌──▼────┐
      │   PG    │ │  ES 8   │ │ MinIO  │ │ Ollama  │ │ Redis │
      │+pgvector│ │  + IK   │ │        │ │qwen3.8b │ │(可选) │
      │         │ │         │ │        │ │bge-m3   │ │       │
      └─────────┘ └─────────┘ └────────┘ └─────────┘ └───────┘
```

### 关键链路说明

**文档入库链路**（写入侧）

```text
上传分片 → 合并入 MinIO → 格式解析(PDF/Word/Excel/MD)
        → 文本切片(带定位元数据) → bge-m3 向量化 → 写入 pgvector
                                  └→ 写入 Elasticsearch 索引
```

**问答链路**（读取侧）

```text
用户提问
  → 群组权限校验（确定可见范围）
  → 并行召回：pgvector 语义检索 ∥ ES BM25 关键词检索
  → RRF 融合排序
  → 证据评估 ──证据不足──→ 拒答 / 提示补充信息
  → 构造 Prompt（含切片上下文编号）
  → ChatOllama 生成（SSE 流式）
  → 输出回答 + 引用来源列表
```

### 数据隔离策略

- 所有业务实体（文档、切片、会话、消息）携带 `group_id`。
- 检索请求在拼装 SQL / ES 查询时**强制注入** `group_id` 过滤，不依赖调用方传参。
- 角色权限在依赖注入层（FastAPI `Depends`）统一校验，业务代码不重复判断。

---

## 目录结构

> **TODO**：以下为**建议约定**，尚未最终确定，可按实际实现调整。

```text
Argus-Python/
├── app/
│   ├── main.py                  # FastAPI 应用入口
│   ├── api/
│   │   ├── deps.py              # 依赖注入：当前用户、群组权限、DB Session
│   │   └── v1/
│   │       ├── auth.py          # 登录 / 刷新 / 登出
│   │       ├── groups.py        # 群组与成员管理
│   │       ├── documents.py     # 文档上传、解析状态、删除
│   │       ├── retrieval.py     # 检索接口
│   │       ├── chat.py          # RAG 问答
│   │       └── agent.py         # Agent 对话（SSE）
│   ├── core/
│   │   ├── config.py            # Pydantic Settings，读取 .env
│   │   ├── security.py          # JWT 签发 / 校验、密码哈希
│   │   └── logging.py
│   ├── db/
│   │   ├── session.py           # 异步引擎与 Session 工厂
│   │   └── base.py              # ORM Base
│   ├── models/                  # SQLAlchemy 模型
│   ├── schemas/                 # Pydantic 请求/响应模型
│   ├── services/                # 业务逻辑层
│   ├── clients/                 # 外部服务客户端：MinIO / ES / Ollama
│   ├── rag/
│   │   ├── parsers/             # PDF / Word / Excel / Markdown 解析器
│   │   ├── splitter.py          # 文本切片
│   │   ├── embedding.py         # bge-m3 向量化
│   │   ├── vector_store.py      # pgvector 读写
│   │   ├── es_store.py          # Elasticsearch 索引与检索
│   │   ├── fusion.py            # RRF 融合
│   │   └── pipeline.py          # 检索管线编排
│   └── agent/
│       ├── graph.py             # LangGraph 图定义
│       ├── tools.py             # Agent 工具
│       └── memory.py            # 短期记忆压缩
├── alembic/                     # 数据库迁移（TODO：确认是否采用）
├── deploy/
│   ├── docker-compose.yml       # 基础设施编排
│   ├── nginx/
│   ├── elasticsearch/
│   │   └── Dockerfile           # 官方镜像 + IK 插件
│   └── ollama/
│       └── Modelfile            # 自建 qwen3.8b 的模型定义
├── scripts/
│   └── init_db.sql              # 建库、pgvector 扩展、初始表结构
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

**前端**：单独仓库维护，不在此目录内。**TODO**：补充前端仓库地址。

---

## 快速开始

> ⚠️ **本节描述目标形态**。仓库当前为空脚手架，下述命令与配置文件（`deploy/docker-compose.yml`、`.env.example`、`scripts/init_db.sql` 等）**尚不存在**，将随 V1.0 一并落地。请以实际提交为准。

### 环境要求

| 依赖 | 版本 | 说明 |
| --- | --- | --- |
| Python | **3.12+** | 见 `pyproject.toml` 的 `requires-python` |
| uv | 最新版 | 依赖与虚拟环境管理 |
| Docker / Docker Compose | 24+ / v2 | 运行基础设施 |
| Node.js | 20 LTS（建议） | 前端为独立仓库，版本要求以其说明为准 |
| 硬件 | 建议 16GB 内存以上 | GPU 可显著加速（8B 量化模型约需 6–8GB 显存）；纯 CPU 亦可运行但较慢。**TODO**：补充实测配置 |

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_ORG/Argus-Python.git   # TODO：替换为实际仓库地址
cd Argus-Python
```

### 2. 启动基础设施（PostgreSQL / Elasticsearch / MinIO / Ollama）

将以下内容保存为 `deploy/docker-compose.yml`：

```yaml
# TODO: 镜像版本号（尤其是 Elasticsearch）需与 IK 插件版本严格一致，请确认后再固定
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: argus-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-argus}
      POSTGRES_USER: ${POSTGRES_USER:-argus}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-YOUR_POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-argus}"]
      interval: 10s
      timeout: 5s
      retries: 5

  elasticsearch:
    build:
      context: ./elasticsearch          # 官方镜像 + IK 中文分词插件
    container_name: argus-elasticsearch
    restart: unless-stopped
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"
      ES_JAVA_OPTS: "-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ulimits:
      memlock: { soft: -1, hard: -1 }
    healthcheck:
      test: ["CMD-SHELL", "curl -fs http://localhost:9200/_cluster/health || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 10

  minio:
    image: minio/minio:latest
    container_name: argus-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-YOUR_MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-YOUR_MINIO_SECRET_KEY}
    ports:
      - "9000:9000"   # S3 API
      - "9001:9001"   # 控制台
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD-SHELL", "mc ready local || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 5

  ollama:
    image: ollama/ollama:latest
    container_name: argus-ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    # GPU 加速（NVIDIA）需要宿主机安装 nvidia-container-toolkit，取消下方注释：
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: all
    #           capabilities: [gpu]

  redis:
    image: redis:7-alpine
    container_name: argus-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  es_data:
  minio_data:
  ollama_data:
  redis_data:
```

Elasticsearch 官方镜像**不包含** IK 分词插件，需在 `deploy/elasticsearch/Dockerfile` 中自行安装：

```dockerfile
# TODO: 镜像 tag 与下方 IK 插件版本必须完全一致，否则插件安装会失败
FROM docker.elastic.co/elasticsearch/elasticsearch:8.x.y

# TODO: 确认与上方版本号严格一致的 IK 插件下载地址
RUN bin/elasticsearch-plugin install --batch \
    https://get.infini.cloud/elasticsearch/analysis-ik/8.x.y
```

启动：

```bash
cd deploy
docker compose up -d
docker compose ps          # 确认各服务 healthy
```

### 3. 配置 .env

```bash
cp .env.example .env
# 按「环境变量说明」章节填写；所有密钥类字段请自行生成，勿使用示例值
```

生成一个 JWT 密钥的参考方式：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 4. 准备 Ollama 模型

> ⚠️ 本项目使用的对话模型名为 `qwen3.8b`，它**不在 Ollama 官方仓库中，无法直接 `ollama pull`**。
> 需先拉取官方基座模型 `qwen3:8b`，再通过 `ollama create` 以该名称注册为本地模型。
> 下方的 `ollama pull qwen3:8b` 指的是**官方基座模型**，并非可以直接改成 `qwen3.8b`。

```bash
# 1) 拉取基座模型与嵌入模型
#    若 Ollama 运行在容器中：
docker exec -it argus-ollama ollama pull qwen3:8b
docker exec -it argus-ollama ollama pull bge-m3

#    若使用宿主机安装的 Ollama，则直接执行：
# ollama pull qwen3:8b
# ollama pull bge-m3

# 2) 基于基座模型创建 qwen3.8b
docker cp deploy/ollama/Modelfile argus-ollama:/tmp/Modelfile
docker exec -it argus-ollama ollama create qwen3.8b -f /tmp/Modelfile

# 3) 验证：列表中应同时出现 qwen3:8b、qwen3.8b、bge-m3
docker exec -it argus-ollama ollama list
curl http://localhost:11434/api/tags
```

`deploy/ollama/Modelfile` 参考内容：

```dockerfile
FROM qwen3:8b

# TODO: 如需固定推理参数（例如关闭 Qwen3 思考模式），在此追加 PARAMETER 指令
```

### 5. 初始化数据库与 pgvector 扩展

```bash
docker exec -i argus-postgres psql -U argus -d argus < scripts/init_db.sql
```

`scripts/init_db.sql` 参考内容：

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- 向量表结构参考；实际表结构以 ORM 模型为准
-- TODO: 确认向量维度与 bge-m3 输出维度一致（bge-m3 稠密向量为 1024 维）
CREATE TABLE IF NOT EXISTS document_chunks (
    id          BIGSERIAL PRIMARY KEY,
    group_id    BIGINT      NOT NULL,
    document_id BIGINT      NOT NULL,
    content     TEXT        NOT NULL,
    metadata    JSONB       NOT NULL DEFAULT '{}'::jsonb,
    embedding   vector(1024),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chunks_group ON document_chunks (group_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

### 6. 启动后端

```bash
# 安装依赖
uv sync

# 开发模式（热重载）
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uv run gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -w 4 \
    -b 0.0.0.0:8000 \
    --timeout 120
```

接口文档：<http://localhost:8000/docs>

> **TODO**：若最终不采用 uv，请将上述命令替换为 `python -m venv .venv` + `pip install -e .` 的等价写法。

### 7. 启动前端

前端为独立仓库，**TODO**：补充仓库地址与启动方式。

```bash
# TODO: 替换为实际前端仓库
git clone https://github.com/YOUR_ORG/Argus-Python-Web.git
cd Argus-Python-Web
npm install
npm run dev        # 默认 http://localhost:5173
```

---

## 环境变量说明

> 以下为建议变量清单与**推荐默认值**，实现阶段可按需调整。**请勿直接使用示例中的密码或密钥。**

| 变量名 | 说明 | 示例 / 默认值 |
| --- | --- | --- |
| `APP_ENV` | 运行环境 | `development` |
| `APP_HOST` / `APP_PORT` | 服务监听地址 | `0.0.0.0` / `8000` |
| `JWT_SECRET` | JWT 签名密钥，**必须自行生成** | `YOUR_JWT_SECRET` |
| `JWT_ALGORITHM` | 签名算法 | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 有效期（分钟） | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 有效期（天） | `7` |
| `POSTGRES_HOST` / `POSTGRES_PORT` | PostgreSQL 地址 | `localhost` / `5432` |
| `POSTGRES_DB` / `POSTGRES_USER` | 数据库名 / 用户 | `argus` / `argus` |
| `POSTGRES_PASSWORD` | 数据库密码 | `YOUR_POSTGRES_PASSWORD` |
| `DATABASE_URL` | 异步连接串 | `postgresql+asyncpg://argus:YOUR_POSTGRES_PASSWORD@localhost:5432/argus` |
| `ES_HOSTS` | Elasticsearch 地址（逗号分隔） | `http://localhost:9200` |
| `ES_INDEX_CHUNKS` | 切片索引名 | `argus_chunks` |
| `ES_USERNAME` / `ES_PASSWORD` | ES 凭据（关闭安全认证时留空） | 空 |
| `MINIO_ENDPOINT` | MinIO 地址 | `localhost:9000` |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | MinIO 凭据 | `YOUR_MINIO_ACCESS_KEY` / `YOUR_MINIO_SECRET_KEY` |
| `MINIO_BUCKET` | 存储桶名 | `argus-documents` |
| `MINIO_SECURE` | 是否启用 HTTPS | `false` |
| `OLLAMA_BASE_URL` | Ollama 服务地址 | `http://localhost:11434` |
| `LLM_MODEL` | 对话模型 | `qwen3.8b` |
| `EMBEDDING_MODEL` | 嵌入模型 | `bge-m3` |
| `EMBEDDING_DIM` | 向量维度，须与 pgvector 表结构一致 | `1024` |
| `LLM_TEMPERATURE` | 生成温度 | `0.2` |
| `LLM_THINKING` | 是否启用 Qwen3 思维链 | `false`（RAG 场景建议关闭） |
| `REDIS_URL` | Redis 连接串（可选） | `redis://localhost:6379/0` |
| `UPLOAD_CHUNK_SIZE` | 分片大小（字节） | `5242880`（5 MiB） |
| `RETRIEVAL_TOP_K` | 单路召回条数 | `20`（融合后取 top 5） |
| `RRF_K` | RRF 融合平滑常数 | `60` |
| `CORS_ORIGINS` | 允许的跨域来源 | `http://localhost:5173` |

---

## API 示例

> ⚠️ 以下为**目标接口设计**（契约草案），尚未实现，路径与字段可能调整。统一前缀 `/api/v1`。

### 登录取令牌

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "YOUR_PASSWORD"
  }'
```

```json
{
  "access_token": "YOUR_ACCESS_TOKEN",
  "refresh_token": "YOUR_REFRESH_TOKEN",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 刷新令牌

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### 文档分片上传

```bash
# 1) 初始化上传，获取 upload_id
curl -X POST http://localhost:8000/api/v1/documents/upload/init \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 1,
    "filename": "handbook.pdf",
    "file_size": 10485760,
    "chunk_total": 3
  }'

# 2) 逐片上传
curl -X POST http://localhost:8000/api/v1/documents/upload/UPLOAD_ID/chunk \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "index=0" \
  -F "file=@./part_0.bin"

# 3) 合并并触发解析
curl -X POST http://localhost:8000/api/v1/documents/upload/UPLOAD_ID/complete \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 混合检索

```bash
curl -X POST http://localhost:8000/api/v1/retrieval/search \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 1,
    "query": "差旅报销的标准是什么？",
    "top_k": 5
  }'
```

```json
{
  "items": [
    {
      "chunk_id": 1024,
      "document_id": 88,
      "document_name": "handbook.pdf",
      "content": "……",
      "score": 0.0321,
      "source": "rrf",
      "locator": { "page": 12 }
    }
  ]
}
```

### RAG 问答（带引用）

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 1,
    "question": "差旅报销的标准是什么？",
    "stream": false
  }'
```

```json
{
  "answer": "根据《员工手册》……",
  "citations": [
    {
      "document_id": 88,
      "document_name": "handbook.pdf",
      "chunk_id": 1024,
      "locator": { "page": 12 }
    }
  ]
}
```

### Agent 对话（SSE 流式）

```bash
curl -N -X POST http://localhost:8000/api/v1/agent/stream \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "group_id": 1,
    "session_id": "YOUR_SESSION_ID",
    "mode": "KB_SEARCH",
    "message": "总结一下这份手册里关于报销的部分"
  }'
```

```text
event: token
data: {"content": "根据"}

event: citation
data: {"document_name": "handbook.pdf", "chunk_id": 1024, "locator": {"page": 12}}

event: done
data: {"finish_reason": "stop"}
```

> **TODO**：`mode` 枚举值、SSE 事件名与 payload 结构待实现时最终确认。

---

## 开发路线图

### V1.0 —— 用户认证与群组协作

- [ ] JWT 双令牌（签发 / 校验 / 刷新 / 登出）
- [ ] 三级角色权限模型：`ADMIN` / `GROUP_OWNER` / `MEMBER`
- [ ] 群组 CRUD 与成员管理
- [ ] 群组数据隔离机制（数据访问层强制过滤）
- [ ] 项目骨架、配置管理、数据库连接与迁移

### V2.0 —— 文档管理与智能解析

- [ ] 分片上传与合并，MinIO 对象存储接入
- [ ] PDF / Word / Excel / Markdown 解析
- [ ] 文本切片（含定位元数据）
- [ ] Ollama Embedding 接入（`bge-m3`）
- [ ] pgvector 向量入库
- [ ] Elasticsearch 索引构建（IK 分词）
- [ ] 文档处理状态追踪与失败重试

### V3.0 —— 混合检索与 RAG 问答

- [ ] 向量语义检索
- [ ] ES BM25 关键词检索
- [ ] RRF 融合排序
- [ ] 证据评估与拒答策略
- [ ] Prompt 构造（含上下文编号）
- [ ] ChatOllama 生成回答
- [ ] 引用溯源与来源返回

### V4.0 —— AI Agent 对话系统

- [ ] LangGraph Agent 图编排
- [ ] `CHAT` / `KB_SEARCH` 双模式切换
- [ ] 检索工具与工具调用编排
- [ ] SSE 流式输出
- [ ] 三级短期记忆压缩
- [ ] 会话持久化与历史管理

### 后续规划（未排期）

- [ ] 重排序模型（Rerank）接入
- [ ] 多模态文档解析（图片 OCR）
- [ ] 检索效果评测集与自动化回归
- [ ] 可观测性（链路追踪、Token 用量统计）

---

## FAQ

### Ollama 相关

**Q：拉取基座模型 `qwen3:8b` 很慢或超时？**
A：模型体积较大（数 GB）。可配置镜像加速，或手动下载 GGUF 后通过 `ollama create` 导入。国内网络环境下建议先确认容器内的网络连通性。

**Q：显存不足，加载 `qwen3.8b` 失败？**
A：8B 模型在 FP16 下约需 16GB 显存，换用量化版本可显著降低需求——做法是拉取官方量化 tag 后重新 `ollama create` 注册。也可改用更小参数量的模型，但需同步调整 `.env` 中的 `LLM_MODEL`。**TODO**：补充本项目实际验证过的硬件配置。

**Q：模型回答里混入了思维链内容？**
A：Qwen3 默认开启思考模式，会在 `<think>` 标签内输出推理过程。RAG 场景通常需要关闭，否则思维链会混入答案并大幅增加延迟与 token 消耗。可行方式包括在 prompt 中追加 `/no_think` 指令，或通过 `ChatOllama` 的推理开关控制。**TODO**：确认所用 LangChain 版本对应的具体参数名。

**Q：嵌入维度与 pgvector 表结构不匹配？**
A：`bge-m3` 稠密向量为 1024 维，建表时 `vector(1024)` 必须与之严格一致。若更换嵌入模型，需同步修改表结构并**重新向量化全部历史文档**。

### Elasticsearch 相关

**Q：IK 插件安装失败？**
A：IK 插件版本必须与 Elasticsearch 版本**完全一致**（`8.x.y` 对 `8.x.y`），跨小版本通常会安装失败。升级 ES 时需同步更新插件。

**Q：中文检索召回效果差？**
A：确认索引字段的 analyzer 已配置为 `ik_max_word`（写入）与 `ik_smart`（查询），而非默认的 `standard` 分词器——默认分词器会把中文切成单字。

**Q：单节点 ES 启动后状态为 yellow？**
A：单节点部署下副本分片无法分配属正常现象，将索引副本数设为 `0` 即可转为 green。

### 数据库相关

**Q：`CREATE EXTENSION vector` 报错找不到扩展？**
A：说明使用的不是带 pgvector 的镜像。请确认使用 `pgvector/pgvector:pg16`，而非官方 `postgres` 镜像。

**Q：异步 ORM 报 `MissingGreenlet` 错误？**
A：SQLAlchemy 异步模式下访问未加载的关联属性会触发该错误，需显式使用 `selectinload` 等预加载策略。

### 部署与网络

**Q：SSE 流式输出在前端「一次性全部出现」，没有逐字效果？**
A：多为 Nginx 缓冲导致。需在 SSE 接口的 location 中关闭缓冲：`proxy_buffering off;`、`proxy_cache off;`，并将 `proxy_read_timeout` 调大。同时确认响应头为 `Content-Type: text/event-stream`。

**Q：CORS 报错？**
A：将前端地址加入 `CORS_ORIGINS`。注意携带凭证时不能使用 `*` 通配。

**Q：MinIO 控制台能登录，但应用上传报 403？**
A：检查 `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` 是否与容器环境变量一致，以及目标 bucket 是否已创建。

---

## 贡献指南

本项目处于早期设计阶段，欢迎通过 Issue 讨论架构选型与接口设计。

### 流程

1. Fork 本仓库并从 `main` 创建分支：

   ```bash
   git checkout -b feat/your-feature
   ```

2. 提交前请确保通过本地检查：

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run pytest        # TODO：测试体系建立后生效
   ```

3. 提交信息建议遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

   ```text
   feat(rag): 支持 RRF 融合排序
   fix(auth): 修复 refresh token 过期校验
   docs: 补充部署说明
   ```

4. 发起 Pull Request，说明改动动机、实现方式与验证结果。

### 约定

- 所有 I/O 操作使用异步接口，避免阻塞事件循环。
- 涉及群组数据的查询必须显式带上群组过滤条件。
- 新增外部依赖需在 PR 中说明理由。
- **TODO**：代码风格、类型检查（mypy）、提交钩子等规范待项目进入实现阶段后补充。

---

## License

本项目**尚未添加开源许可证**。

在仓库中添加 `LICENSE` 文件之前，默认适用著作权法——即保留所有权利，他人无权复制、修改或分发本项目代码。

**TODO**：确定许可证类型后，在此处补充说明并添加 `LICENSE` 文件。

> 原项目 [Argus](https://github.com/DevYangJC/Argus) 的许可证情况请自行确认；若本项目包含或改编自其代码，需遵守其原有许可条款。
