import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_and_db():
    from api.main import app
    from api.dependencies import get_db as orig_get_db
    from data.store import ScouterDB

    db = ScouterDB(":memory:")

    def _get_db():
        return db

    app.dependency_overrides.clear()
    app.dependency_overrides[orig_get_db] = _get_db
    yield app, db
    db.close()
    app.dependency_overrides.clear()


@pytest.fixture
def client(app_and_db):
    app, _ = app_and_db
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db(app_and_db):
    _, db = app_and_db
    return db


class TestHealth:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["db"] == "connected"

    def test_health_shows_engine(self, client, db):
        from data.evaluator import EvaluationRunner
        EvaluationRunner(db)._ensure_engine_version()
        resp = client.get("/api/health")
        assert resp.json()["engine_version"] == "v2.0"
