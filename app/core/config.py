from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_prefix="APP_")

    postgres_host: str | None = "127.0.0.1"
    postgres_port: int | None = 5432
    postgres_database: str | None = "ecr_financy"
    postgres_username: str | None = "postgres"
    postgres_password: str | None = "postgres"

    environment: str = "production"

    jwt_secret_key: str = "seu-segredo-super-seguro"
    jwt_algorithm: str = "HS256"


settings = Settings()
