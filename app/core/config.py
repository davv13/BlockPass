# app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- choose storage backend ----
    DB_BACKEND: str = "file"                    # 'file' or 'postgres'

    # ---- file backend ----
    FILE_PATH: str = "./blockpass_users.json"   # <-- exact field name

    # ---- postgres (for later) ----
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "blockpass"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"

    # ---- JWT ----
    JWT_SECRET: str = "supersecret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # vault encryption
    # VAULT_KEY: str  # must be a 32‑byte URL‑safe base64 key

    # tell pydantic where the .env file is **and** to ignore unknown keys
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()