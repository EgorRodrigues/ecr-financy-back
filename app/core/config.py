from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_prefix="APP_")

    postgres_host: Optional[str] = "127.0.0.1"
    postgres_port: Optional[int] = 5432
    postgres_database: Optional[str] = "ecr_financy"
    postgres_username: Optional[str] = "postgres"
    postgres_password: Optional[str] = "postgres"


settings = Settings()
