import pytest
from fastapi.testclient import TestClient
from unittest import mock


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


class TestSync:
    @mock.patch("data.ingest_api._api_standings", return_value={})
    @mock.patch("data.ingest_api._api_matches", return_value=[])
    def test_sync_returns_report(self, mock_m, mock_s, client):
        resp = client.post("/api/sync")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "leagues" in data


class TestEvaluate:
    def test_evaluate_empty(self, client):
        resp = client.post("/api/evaluate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["evaluated"] == 0

    def test_evaluate_pending(self, client, db):
        from data.evaluator import EvaluationRunner
        from data.ingest_api import _detect_season_label
        sl = _detect_season_label()
        cid = db.get_or_create_competition("PL")
        sid = db.get_or_create_season(sl, 2025, 2026)
        csid = db.get_or_create_competition_season(cid, sid)
        db.get_or_create_team(1, "A"); db.get_or_create_team(2, "B")
        db.store_match({"id": 1, "competition_season_id": csid, "matchday": 1,
                         "status": "SCHEDULED", "utc_date": "2026-08-21T19:00:00Z",
                         "home_team_id": 1, "away_team_id": 2})
        db.store_standings_snapshot(csid, [
            {"team_id": 1, "position": 1, "played": 5, "points": 15, "goal_difference": 20, "ppg": 3.0},
            {"team_id": 2, "position": 10, "played": 5, "points": 5, "goal_difference": -5, "ppg": 1.0},
        ], "2026-08-15")

        resp = client.post("/api/evaluate")
        assert resp.status_code == 200
        assert resp.json()["evaluated"] == 1
