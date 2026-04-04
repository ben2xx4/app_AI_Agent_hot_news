from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture()
def db_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("SQLITE_FALLBACK_URL", url)
    monkeypatch.setenv("CHAT_USE_OPENAI", "false")
    monkeypatch.setenv("USE_DEMO_ON_FAILURE", "true")
    return url


@pytest.fixture()
def db_session_factory(db_url: str) -> sessionmaker[Session]:
    from app.core.settings import get_settings
    from app.db.session import get_engine, get_session_factory, set_session_factory_override

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    set_session_factory_override(None)

    import app.models  # noqa: F401
    from app.db.base import Base

    engine = create_engine(db_url, future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@pytest.fixture()
def seeded_db(db_session_factory: sessionmaker[Session]) -> sessionmaker[Session]:
    from app.db.session import get_engine, get_session_factory, set_session_factory_override

    get_engine.cache_clear()
    get_session_factory.cache_clear()
    set_session_factory_override(db_session_factory)

    from app.pipelines.news.pipeline import NewsPipeline
    from app.pipelines.policy.pipeline import PolicyPipeline
    from app.pipelines.price.pipeline import PricePipeline
    from app.pipelines.traffic.pipeline import TrafficPipeline
    from app.pipelines.weather.pipeline import WeatherPipeline

    for pipeline_cls in [
        NewsPipeline,
        PricePipeline,
        WeatherPipeline,
        PolicyPipeline,
        TrafficPipeline,
    ]:
        pipeline_cls(demo_only=True).run()

    return db_session_factory


@pytest.fixture()
def client(seeded_db: sessionmaker[Session]) -> TestClient:
    from app.db.session import get_db
    from app.main import app

    def override_get_db():
        db = seeded_db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
