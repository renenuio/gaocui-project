# 系统全局规则（SYSTEM.md）

## 项目名称
gaocui-project

## 技术栈
- FastAPI
- PostgreSQL + pgvector
- Redis
- SQLAlchemy 2.0

---

## 架构规范

- api/ 只负责接口路由（Controller层）
- services/ 只负责业务逻辑（Service层）
- models/ 定义数据库结构（ORM）
- db/ 负责数据库连接与会话管理

---

## 模块隔离规则（非常重要）

- AI模块不能修改用户模块
- 数据库模块不能包含业务逻辑
- 支付模块必须独立运行
- 各模块之间通过接口通信，不直接依赖内部实现

---

## 文档同步规则

所有模块必须通过以下文档同步状态：

- DEV_LOG.md（开发进度）
- API.md（接口协议）
- MODULE_*.md（模块说明）

---

## 开发原则

- 每个模块必须独立可运行
- 模块之间通过“接口契约”协作
- 禁止跨模块直接修改逻辑