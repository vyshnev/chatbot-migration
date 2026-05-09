"""
core/config.py
--------------
Single source of truth for all environment variables and application settings.
Every other module reads configuration from here, never directly from os.getenv().
"""

import os
from dotenv import load_dotenv

# Load .env file once, at import time.
load_dotenv()


def _required_env(name: str) -> str:
    """Return a required environment variable or fail with a clear startup error."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it in your .env file before starting the backend."
        )
    return value


def _csv_env(name: str, default: str) -> list[str]:
    """Return a comma-separated environment variable as a trimmed string list."""
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")  # Override in .env to switch models.

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS: list[str] = _csv_env(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)

# ---------------------------------------------------------------------------
# LangSmith (optional tracing/observability)
# ---------------------------------------------------------------------------
LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT", "")

# ---------------------------------------------------------------------------
# External APIs
# ---------------------------------------------------------------------------
ALPHA_VANTAGE_KEY: str = os.getenv("ALPHA_VANTAGE_KEY", "")

# ---------------------------------------------------------------------------
# Cache (Upstash Redis, optional)
# ---------------------------------------------------------------------------
UPSTASH_REDIS_REST_URL: str = os.getenv("UPSTASH_REDIS_REST_URL", "")
UPSTASH_REDIS_REST_TOKEN: str = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")

# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------
DATABASE_URL: str = _required_env("DATABASE_URL")
