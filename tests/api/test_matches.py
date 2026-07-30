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


def _make_season(db, code="PL", sname=None, syear=2024, teams=None):
    from data.ingest_api import _detect_season_label
    if sname is None:
        sname = _detect_season_label()
    cid = db.get_or_create_competition(code)
    sid = db.get_or_create_season(sname, syear, syear + 1)
    csid = db.get_or_create_competition_season(cid, sid)
    if teams:
        for tid, nm in teams.items():
            db.get_or_create_team(tid, nm)
    return cid, sid, csid


class TestListMatches:
    def test_empty(self, client):
        resp = client.get("/api/matches")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_with_data(self, client, db):
        _, _, csid = _make_season(db, teams={1: "A", 2: "B"})
        db.store_match({"id": 1, "competition_season_id": csid, "matchday": 1,
                         "status": "SCHEDULED", "utc_date": "2026-08-21T19:00:00Z",
                         "home_team_id": 1, "away_team_id": 2})
        resp = client.get("/api/matches")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["home_team_name"] == "A"

    def test_filter_by_selected(self, client, db):
        from data.evaluator import EvaluationRunner
        _, _, csid = _make_season(db, teams={1: "A", 2: "B", 3: "C"})
        db.store_match({"id": 10, "competition_season_id": csid, "matchday": 1,
                         "status": "SCHEDULED", "utc_date": "2026-08-21T19:00:00Z",
                         "home_team_id": 1, "away_team_id": 2})
        db.store_match({"id": 11, "competition_season_id": csid, "matchday": 1,
                         "status": "SCHEDULED", "utc_date": "2026-08-22T19:00:00Z",
                         "home_team_id": 2, "away_team_id": 3})
        db.store_standings_snapshot(csid, [
            {"team_id": 1, "position": 1, "played": 5, "points": 15, "goal_difference": 20, "ppg": 3.0},
            {"team_id": 2, "position": 10, "played": 5, "points": 5, "goal_difference": -5, "ppg": 1.0},
            {"team_id": 3, "position": 9, "played": 5, "points": 6, "goal_difference": -3, "ppg": 1.2},
        ], "2026-08-15")
        runner = EvaluationRunner(db)
        runner.evaluate_all_pending()

        resp = client.get("/api/matches?selected=true")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == 10


class TestGetMatch:
    def test_not_found(self, client):
        resp = client.get("/api/matches/99999")
        assert resp.status_code == 404

    def test_with_evaluation(self, client, db):
        from data.evaluator import EvaluationRunner
        _, _, csid = _make_season(db, teams={1: "A", 2: "B"})
        db.store_match({"id": 100, "competition_season_id": csid, "matchday": 1,
                         "status": "SCHEDULED", "utc_date": "2026-08-21T19:00:00Z",
                         "home_team_id": 1, "away_team_id": 2})
        db.store_standings_snapshot(csid, [
            {"team_id": 1, "position": 1, "played": 5, "points": 15, "goal_difference": 20, "ppg": 3.0},
            {"team_id": 2, "position": 10, "played": 5, "points": 5, "goal_difference": -5, "ppg": 1.0},
        ], "2026-08-15")
        runner = EvaluationRunner(db)
        runner.evaluate_all_pending()

        resp = client.get("/api/matches/100")
        assert resp.status_code == 200
        data = resp.json()
        assert data["evaluation"] is not None
        assert data["evaluation"]["engine_version"] == "v2.0"
        assert data["evaluation"]["strength_home"]["total"] > 0
