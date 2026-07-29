"""
Central configuration for the Lexora AI Tone Studio.

All environment-driven settings live here so the rest of the codebase
never touches os.environ directly (single source of truth).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    max_concurrent_requests: int = 10
    frontend_origin: str = "http://localhost:5173"
    max_request_bytes: int = 1_000_000
    max_bulk_file_bytes: int = 2_000_000
    rate_limit_per_minute: int = 60
    database_path: str = "data/lexora.sqlite3"
    upload_dir: str = "data/uploads"
    session_cookie_name: str = "lexora_session"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Settings are cached so the .env file is only parsed once per process."""
    return Settings()
