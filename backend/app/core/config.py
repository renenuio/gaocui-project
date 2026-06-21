from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "gaocui-project"
    API_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/gaocui_project"
    REDIS_URL: str = "redis://localhost:6379/0"
    SQL_ECHO: bool = False

    EMBEDDING_DIMENSIONS: int = 1536
    EMBEDDING_PROVIDER: str = "openai"
    OPENAI_API_KEY: str | None = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    SENTENCE_TRANSFORMERS_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ENABLE_PGVECTOR_EXTENSION: bool = True
    AUTO_CREATE_TABLES: bool = False

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")


settings = Settings()
