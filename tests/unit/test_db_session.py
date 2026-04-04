from __future__ import annotations

from app.core.settings import get_settings
from app.db.session import (
    get_engine,
    get_session_factory,
    resolve_database_url,
    set_session_factory_override,
)


def test_fallback_to_sqlite_when_postgres_unreachable(
    monkeypatch,
    tmp_path,
) -> None:
    sqlite_url = f"sqlite:///{tmp_path / 'fallback.db'}"

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://app_user:app_password@localhost:65432/news_ai_db",
    )
    monkeypatch.setenv("SQLITE_FALLBACK_URL", sqlite_url)
    monkeypatch.setenv("APP_ENV", "dev")

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    set_session_factory_override(None)

    assert resolve_database_url() == sqlite_url
    assert get_engine().url.render_as_string(hide_password=False) == sqlite_url

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    set_session_factory_override(None)
