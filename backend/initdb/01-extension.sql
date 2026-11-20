-- 启用 pgvector 扩展。
--
-- 执行时机：postgres 容器**首次**创建数据卷时，由 /docker-entrypoint-initdb.d 自动执行。
-- 数据卷已存在则不会再跑 —— 那时改用 Alembic 迁移或手动执行（README 12.1）。
--
-- 职责划分（已确认）：
--   扩展       → 本脚本 或 首个 Alembic 迁移，二者择一
--   业务表 / vector(1024) 列 / 向量索引 → Alembic 迁移

CREATE EXTENSION IF NOT EXISTS vector;
