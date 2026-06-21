# gaocui-project backend

AI商品推荐平台后端骨架，基于 FastAPI、PostgreSQL、SQLAlchemy 2.0、Redis，并预留 pgvector embedding 字段。

## Run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

## Database

默认数据库连接在 `.env` 中：

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/gaocui_project
```

如果需要启动时自动建表，将 `.env` 中的配置改为：

```env
AUTO_CREATE_TABLES=true
ENABLE_PGVECTOR_EXTENSION=true
```

PostgreSQL 需要已安装 pgvector 扩展；应用启动时会执行：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

