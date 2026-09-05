import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Config
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    FRONTEND_URL: str = "http://localhost:3000"

    # Database Configuration (Defaults to local postgres/postgres@localhost:5432/lennys_growth_db)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lennys_growth_db"

    # LLM Provider Controls
    DEFAULT_LLM_PROVIDER: str = "ollama"
    AUTO_FALLBACK_TO_CLOUD: bool = False

    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    # Cloud LLM Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""

    # Retrieval Configuration
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_DISTANCE_THRESHOLD: float = 0.4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

