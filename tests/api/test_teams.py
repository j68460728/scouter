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


class TestGetTeam:
    def test_not_found(self, client):
        resp = client.get("/api/teams/99999")
        assert resp.status_code == 404

    def test_found(self, client, db):
        db.get_or_create_team(57, "Arsenal FC", "Arsenal")
        resp = client.get("/api/teams/57")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Arsenal FC"
        assert data["short_name"] == "Arsenal"

    def test_with_history(self, client, db):
        db.get_or_create_team(1, "Team A")
        pl_cid = db.get_or_create_competition("PL", "Premier League")
        s23 = db.get_or_create_season("2023/2024", 2023, 2024)
        cs23 = db.get_or_create_competition_season(pl_cid, s23)
        db.store_standings_snapshot(cs23, [
            {"team_id": 1, "position": 3, "played": 38, "points": 70,
             "goal_difference": 15, "ppg": 1.84},
        ], "2024-05-19")
        resp = client.get("/api/teams/1")
        data = resp.json()
        assert len(data["history"]) == 1
        assert data["history"][0]["season_name"] == "2023/2024"


class TestTeamHistory:
    def test_empty(self, client, db):
        db.get_or_create_team(99, "Ghost")
        resp = client.get("/api/teams/99/history")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_not_found(self, client):
        resp = client.get("/api/teams/99999/history")
        assert resp.status_code == 404
