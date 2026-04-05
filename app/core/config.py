"""
Core configuration
==================
All runtime settings are read from environment variables (or a .env file)
via pydantic-settings, giving strong typing and validation for free.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ───────────────────────────────────────────────────────
    APP_NAME: str = "Finance Intelligence System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./finance.db"

    # ── JWT ───────────────────────────────────────────────────────────────
    SECRET_KEY: str = "insecure-default-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Seed / first admin ────────────────────────────────────────────────
    FIRST_ADMIN_EMAIL: str = "admin@finance.io"
    FIRST_ADMIN_PASSWORD: str = "Admin@1234"
    FIRST_ADMIN_NAME: str = "System Admin"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Singleton used throughout the application
settings = Settings()
