from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    project_name: str
    app_env: str
    app_host: str
    app_port: int
    timezone: str
    log_level: str
    database_url: str
    sqlite_fallback_url: str
    raw_storage_path: Path
    processed_storage_path: Path
    source_config_path: Path
    retention_config_path: Path
    use_demo_on_failure: bool
    openai_api_key: str | None
    openai_model: str
    openai_reasoning_effort: str
    chat_use_openai: bool
    api_base_url: str
    experimental_retrieval_enabled: bool
    experimental_retrieval_model: str
    experimental_retrieval_min_score: float
    experimental_retrieval_limit: int

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "prod"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_env_file(ROOT_DIR / ".env")

    raw_storage_path = ROOT_DIR / os.getenv("RAW_STORAGE_PATH", "data/raw")
    processed_storage_path = ROOT_DIR / os.getenv("PROCESSED_STORAGE_PATH", "data/processed")
    source_config_path = ROOT_DIR / os.getenv("SOURCE_CONFIG_PATH", "config/sources.yml")
    retention_config_path = ROOT_DIR / os.getenv("RETENTION_CONFIG_PATH", "config/retention.yml")

    return Settings(
        project_name=os.getenv("APP_NAME", "nen-tang-du-lieu-tin-tuc-vn"),
        app_env=os.getenv("APP_ENV", "dev"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        timezone=os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        database_url=os.getenv("DATABASE_URL")
        or os.getenv("SQLITE_FALLBACK_URL", "sqlite:///./data/app.db"),
        sqlite_fallback_url=os.getenv("SQLITE_FALLBACK_URL", "sqlite:///./data/app.db"),
        raw_storage_path=raw_storage_path,
        processed_storage_path=processed_storage_path,
        source_config_path=source_config_path,
        retention_config_path=retention_config_path,
        use_demo_on_failure=_as_bool(os.getenv("USE_DEMO_ON_FAILURE"), True),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
        openai_reasoning_effort=os.getenv("OPENAI_REASONING_EFFORT", "medium"),
        chat_use_openai=_as_bool(os.getenv("CHAT_USE_OPENAI"), True),
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
        experimental_retrieval_enabled=_as_bool(
            os.getenv("EXPERIMENTAL_RETRIEVAL_ENABLED"), False
        ),
        experimental_retrieval_model=os.getenv(
            "EXPERIMENTAL_RETRIEVAL_MODEL", "experimental-local-sparse-v1"
        ),
        experimental_retrieval_min_score=float(
            os.getenv("EXPERIMENTAL_RETRIEVAL_MIN_SCORE", "0.025")
        ),
        experimental_retrieval_limit=int(os.getenv("EXPERIMENTAL_RETRIEVAL_LIMIT", "6")),
    )
