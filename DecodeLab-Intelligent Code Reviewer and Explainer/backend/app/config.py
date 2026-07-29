"""
Central configuration for CodeFix AI backend.
Reads from environment variables (.env file) so no secrets ever live in code.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() in {"1", "true", "yes", "on"}

    # Source-size controls. Large submissions use a dedicated two-stage review path
    # that returns compact findings first and only then emits the complete corrected file.
    MAX_CODE_CHARS: int = max(100_000, int(os.getenv("MAX_CODE_CHARS", "100000")))
    LARGE_SOURCE_THRESHOLD: int = int(os.getenv("LARGE_SOURCE_THRESHOLD", "24000"))
    GEMINI_MAX_OUTPUT_TOKENS: int = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "65536"))


settings = Settings()

if not settings.GEMINI_API_KEY:
    print(
        "\n[CodeFix AI] WARNING: GEMINI_API_KEY is not set. "
        "Copy backend/.env.example to backend/.env and add your key.\n"
    )
