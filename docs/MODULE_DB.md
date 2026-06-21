# 数据库模块说明（MODULE_DB.md）

## 职责
负责数据库连接、表结构与pgvector支持

---

## 技术

- PostgreSQL
- SQLAlchemy 2.0
- asyncpg
- pgvector

---

## 功能

- 数据库连接管理
- ORM模型定义
- 向量字段支持
- 会话管理

---

## 当前状态

- 数据库已设计
- 未实际运行（PostgreSQL未安装）

---

## 禁止行为

- 不允许写业务逻辑
- 不允许写AI逻辑