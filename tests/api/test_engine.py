import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_and_db():
    from api.main import app
    from data.store import ScouterDB
    db = ScouterDB(":memory:")

    from api.dependencies import get_db as orig_get_db

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


class TestEngineEndpoint:
    def test_no_engine_registered(self, client):
        resp = client.get("/api/engine")
        assert resp.status_code == 404

    def test_active_engine(self, client, db):
        from data.evaluator import EvaluationRunner
        EvaluationRunner(db)._ensure_engine_version()
        resp = client.get("/api/engine")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "v2.0"
        assert data["structural_weight"] == 0.857
        assert data["min_difference"] == 20

    def test_engine_versions_list(self, client, db):
        from data.evaluator import EvaluationRunner
        EvaluationRunner(db)._ensure_engine_version()
        resp = client.get("/api/engine/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
