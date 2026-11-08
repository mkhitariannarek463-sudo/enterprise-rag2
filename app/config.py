from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RAG Platform"
    environment: str = "development"
    log_level: str = "INFO"
    anthropic_api_key: str = ""
    database_url: str = ""
    qdrant_url: str = ""
    llm_model: str = "claude-haiku-5-5"
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()