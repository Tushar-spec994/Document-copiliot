import os
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings and environment configuration.

    Single source of truth for backend configuration. Reads from backend/.env
    or system environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=(ENV_PATH, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Supabase configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Postgres / Alembic connection string (direct connection preferred for migrations)
    database_url: str

    # Gemini (Google GenAI) configuration
    gemini_api_key: str = ""
    gemini_embedding_model: str = "gemini-embedding-2"
    gemini_embedding_dimensions: int = 768
    gemini_chat_model: str = "gemini-1.5-flash"

    # Server configuration
    environment: str = "development"
    allowed_origins: str | list[str] = ["http://localhost:5173"]

    @field_validator("allowed_origins", mode="after")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                import json

                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return []


# Single source of truth instance instantiated on import (fails fast if config is invalid)
settings = Settings()

# Mirror keys for external SDKs that inspect os.environ directly
if settings.gemini_api_key:
    os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
    os.environ.setdefault("GOOGLE_API_KEY", settings.gemini_api_key)
