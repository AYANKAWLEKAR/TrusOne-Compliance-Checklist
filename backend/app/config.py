from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from the backend package root (not cwd), so tests and `uv run` work from any directory.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


def _normalize_database_url_for_psycopg3(url: str) -> str:
    """SQLAlchemy maps postgresql:// to psycopg2; this project uses psycopg v3 only."""
    if url.startswith("postgresql+") or url.startswith("postgres+"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    return url


def _ensure_sslmode_for_supabase(url: str) -> str:
    """Hosted Supabase requires TLS; add sslmode if missing."""
    if "supabase.co" not in url or "sslmode=" in url:
        return url
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}sslmode=require"


def _validate_database_url_template(url: str) -> str:
    placeholders = (
        "<your-project-ref>",
        "<project-ref>",
        "<your-password>",
        "<password>",
    )
    if any(token in url for token in placeholders):
        raise ValueError(
            "DATABASE_URL still contains template placeholders. Replace it with a real database URL "
            "from your Supabase or PostgreSQL instance."
        )
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    api_timeout_seconds: int = 15
    database_url: str = Field(
        default=(
            "postgresql+psycopg://postgres.<your-project-ref>:<your-password>"
            "@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
        ),
        alias="DATABASE_URL",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def database_url_use_psycopg3(cls, v: object) -> object:
        if isinstance(v, str):
            u = _normalize_database_url_for_psycopg3(v)
            return _ensure_sslmode_for_supabase(u)
        return v

    supabase_project_url: str | None = Field(default=None, alias="SUPABASE_PROJECT_URL")
    supabase_service_role_key: str | None = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")
    openai_chat_model: str = Field(default="gpt-4o-mini", alias="OPENAI_CHAT_MODEL")
    epa_comptox_api_key: str | None = Field(default=None, alias="EPA_COMPTOX_API_KEY")
    data_gov_api_key: str | None = Field(default=None, alias="DATA_GOV_API_KEY")
    geoip_base_url: str = Field(default="https://ipapi.co/json", alias="GEOIP_BASE_URL")
    ecfr_cache_ttl_seconds: int = Field(default=3600, alias="ECFR_CACHE_TTL_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
