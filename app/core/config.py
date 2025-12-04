from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_prefix="APP_")

    cassandra_hosts: List[str] = ["127.0.0.1"]
    cassandra_port: int = 9042
    cassandra_keyspace: str = "ecr_financy"
    cassandra_username: Optional[str] = None
    cassandra_password: Optional[str] = None
    cassandra_consistency: str = "LOCAL_QUORUM"


settings = Settings()

