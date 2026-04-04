from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoSuchModuleError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.logging import get_logger
from app.core.settings import Settings, get_settings
from app.db.base import Base

logger = get_logger(__name__)
_OVERRIDE_SESSION_FACTORY: sessionmaker | None = None


def _build_sqlite_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.sqlite_fallback_url,
        future=True,
        connect_args={"check_same_thread": False},
    )


def _create_engine(database_url: str, settings: Settings, *, probe: bool = False) -> Engine:
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    elif probe:
        connect_args["connect_timeout"] = 2

    try:
        return create_engine(
            database_url,
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    except (ModuleNotFoundError, NoSuchModuleError) as exc:
        if settings.is_production:
            raise
        logger.warning(
            "Khong tao duoc engine cho %s, fallback sang SQLite: %s",
            database_url,
            exc,
        )
        return _build_sqlite_engine(settings)


def resolve_database_url(settings: Settings | None = None) -> str:
    runtime_settings = settings or get_settings()
    database_url = runtime_settings.database_url

    if database_url.startswith("sqlite"):
        return database_url

    probe_engine = _create_engine(database_url, runtime_settings, probe=True)
    if probe_engine.url.drivername.startswith("sqlite"):
        return runtime_settings.sqlite_fallback_url

    try:
        with probe_engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except OperationalError as exc:
        if runtime_settings.is_production:
            raise
        logger.warning(
            "Khong ket noi duoc %s, fallback sang SQLite: %s",
            database_url,
            exc,
        )
        return runtime_settings.sqlite_fallback_url
    finally:
        probe_engine.dispose()

    return database_url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    return _create_engine(resolve_database_url(settings), settings)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker:
    if _OVERRIDE_SESSION_FACTORY is not None:
        return _OVERRIDE_SESSION_FACTORY
    return sessionmaker(
        bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False
    )


def set_session_factory_override(session_factory: sessionmaker | None) -> None:
    global _OVERRIDE_SESSION_FACTORY
    _OVERRIDE_SESSION_FACTORY = session_factory
    get_session_factory.cache_clear()


def get_db() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ensure_sqlite_schema() -> None:
    engine = get_engine()
    if engine.url.drivername.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
