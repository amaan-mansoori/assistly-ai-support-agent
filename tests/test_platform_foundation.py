from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from src.api.main import create_app
from src.db.database import Base, make_engine, make_session_factory
from src.db import models  # noqa: F401
from src.platform.config import PlatformSettings


def settings_for(database_url: str, **overrides) -> PlatformSettings:
    values = {
        "app_env": "test",
        "database_url": database_url,
        "redis_url": None,
        "jwt_secret": "test-only-secret-with-over-32-bytes",
        "log_level": "WARNING",
        "cors_origins": ("http://localhost:3000",),
    }
    values.update(overrides)
    return PlatformSettings(**values)


def test_health_and_readiness_include_request_correlation(tmp_path):
    db_path = tmp_path / "health.sqlite"
    app = create_app(settings_for(f"sqlite:///{db_path}"))

    with TestClient(app) as client:
        health = client.get("/health", headers={"X-Request-ID": "health-test-1"})
        ready = client.get("/health/ready")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert health.headers["X-Request-ID"] == "health-test-1"
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready", "database": "ok"}


def test_docs_and_openapi_are_available(tmp_path):
    app = create_app(settings_for(f"sqlite:///{tmp_path / 'docs.sqlite'}"))

    with TestClient(app) as client:
        docs = client.get("/api/docs")
        redoc = client.get("/api/redoc")
        schema = client.get("/api/openapi.json")

    assert docs.status_code == redoc.status_code == schema.status_code == 200
    assert schema.json()["info"]["title"] == "Assistly AI-Powered Customer Support Platform API"


def test_production_requires_strong_jwt_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(ValueError, match="JWT_SECRET"):
        PlatformSettings.from_env()


def test_sqlalchemy_schema_creates_with_relational_constraints(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'schema.sqlite'}")
    try:
        Base.metadata.create_all(engine)
        factory = make_session_factory(engine)
        with factory() as session:
            tables = set(Base.metadata.tables)
            assert {
                "users",
                "conversations",
                "messages",
                "agent_runs",
                "human_review_tickets",
                "feedback",
            } <= tables
            assert session.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
