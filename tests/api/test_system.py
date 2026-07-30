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


def _make_season(db, code="PL", sname="2026/2027", syear=2026, teams=None):
    cid = db.get_or_create_competition(code)
    sid = db.get_or_create_season(sname, syear, syear + 1)
    csid = db.get_or_create_competition_season(cid, sid)
    if teams:
        for tid, nm in teams.items():
            db.get_or_create_team(tid, nm)
    return cid, sid, csid


class TestSystemStatus:
    def test_no_engine(self, client):
        resp = client.get("/api/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "no_engine"
        assert data["engine"] is None

    def test_with_data(self, client, db):
        from data.evaluator import EvaluationRunner
        EvaluationRunner(db)._ensure_engine_version()
        _make_season(db, teams={1: "A", 2: "B"})
        _, _, csid = _make_season(db)
        db.store_match({"id": 1, "competition_season_id": csid, "matchday": 1,
                         "status": "SCHEDULED", "utc_date": "2026-08-21T19:00:00Z",
                         "home_team_id": 1, "away_team_id": 2})

        resp = client.get("/api/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["engine"]["version"] == "v2.0"
        assert data["data"]["matches"] == 1
        assert data["data"]["teams"] == 2
        assert data["data"]["competitions"] == 1
        assert data["data"]["pending_matches"] == 1
        assert data["data"]["current_season"] == "2026/2027"

    def test_last_sync_tracked(self, client, db):
        db.set_metadata("last_sync", "2026-07-29T23:01:25Z")
        resp = client.get("/api/system/status")
        data = resp.json()
        assert data["data"]["last_sync"] == "2026-07-29T23:01:25Z"


class TestBenchmark:
    def _setup_data(self, db):
        from data.evaluator import EvaluationRunner
        from data.ingest_api import _detect_season_label
        sl = _detect_season_label()
        _, _, csid = _make_season(db, sname=sl, syear=2026, teams={1: "A", 2: "B"})
        db.store_match({"id": 10, "competition_season_id": csid, "matchday": 1,
                         "status": "FINISHED", "utc_date": "2026-08-01T19:00:00Z",
                         "home_team_id": 1, "away_team_id": 2,
                         "home_score": 2, "away_score": 0, "winner": "HOME_TEAM"})
        db.store_match({"id": 11, "competition_season_id": csid, "matchday": 2,
                         "status": "FINISHED", "utc_date": "2026-08-08T19:00:00Z",
                         "home_team_id": 2, "away_team_id": 1,
                         "home_score": 0, "away_score": 1, "winner": "AWAY_TEAM"})
        db.store_standings_snapshot(csid, [
            {"team_id": 1, "position": 1, "played": 5, "points": 15,
             "goal_difference": 20, "ppg": 3.0},
            {"team_id": 2, "position": 10, "played": 5, "points": 5,
             "goal_difference": -5, "ppg": 1.0},
        ], "2026-07-30")

        runner = EvaluationRunner(db)
        runner.evaluate_all_pending()

    def test_benchmark_empty(self, client):
        resp = client.get("/api/system/benchmark")
        assert resp.status_code == 200
        data = resp.json()
        assert data["totals"]["evaluated"] == 0
        assert data["totals"]["selected"] == 0

    def test_benchmark_with_data(self, client, db):
        self._setup_data(db)
        resp = client.get("/api/system/benchmark")
        assert resp.status_code == 200
        data = resp.json()
        assert data["totals"]["evaluated"] == 2
        assert data["totals"]["selected"] == 2  # both have large diff
        assert data["totals"]["coverage"] == 1.0
        assert data["totals"]["correct"] == 2  # both correct
        assert data["totals"]["accuracy"] == 1.0

    def test_benchmark_filter_by_competition(self, client, db):
        self._setup_data(db)
        resp = client.get("/api/system/benchmark?competition_code=PL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["totals"]["evaluated"] == 2
        assert len(data["by_competition"]) == 1
        assert data["by_competition"][0]["competition_code"] == "PL"

    def test_benchmark_by_difference_range(self, client, db):
        self._setup_data(db)
        resp = client.get("/api/system/benchmark")
        data = resp.json()
        ranges = {r["range"]: r for r in data["by_difference_range"]}
        assert "20-29" in ranges or "50+" in ranges
        total_in_ranges = sum(r["matches"] for r in data["by_difference_range"])
        assert total_in_ranges == data["totals"]["selected"]
