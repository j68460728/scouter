import pytest
from data.store import ScouterDB
from data.evaluator import EvaluationRunner


@pytest.fixture
def db():
    _db = ScouterDB(":memory:")
    yield _db
    _db.close()


class TestMetadata:
    def test_set_and_get(self, db):
        db.set_metadata("last_sync", "2026-07-29T23:01:25Z")
        assert db.get_metadata("last_sync") == "2026-07-29T23:01:25Z"

    def test_get_missing(self, db):
        assert db.get_metadata("nonexistent") is None

    def test_overwrite(self, db):
        db.set_metadata("key", "v1")
        db.set_metadata("key", "v2")
        assert db.get_metadata("key") == "v2"

    def test_multiple_keys(self, db):
        db.set_metadata("a", "1")
        db.set_metadata("b", "2")
        assert db.get_metadata("a") == "1"
        assert db.get_metadata("b") == "2"


class TestSystemStatus:
    def test_empty(self, db):
        status = db.get_system_status()
        assert status["status"] == "no_engine"
        assert status["engine"] is None
        assert status["data"]["matches"] == 0

    def test_with_engine_and_data(self, db):
        EvaluationRunner(db)._ensure_engine_version()
        cid = db.get_or_create_competition("PL")
        sid = db.get_or_create_season("2026/2027", 2026, 2027)
        csid = db.get_or_create_competition_season(cid, sid)
        db.get_or_create_team(1, "A")
        db.get_or_create_team(2, "B")
        db.store_match({"id": 1, "competition_season_id": csid, "matchday": 1,
                         "status": "SCHEDULED", "utc_date": "2026-08-21T19:00:00Z",
                         "home_team_id": 1, "away_team_id": 2})

        status = db.get_system_status()
        assert status["status"] == "ready"
        assert status["engine"]["version"] == "v2.0"
        assert status["data"]["matches"] == 1
        assert status["data"]["teams"] == 2
        assert status["data"]["competitions"] == 1
        assert status["data"]["pending_matches"] == 1
        assert status["data"]["current_season"] == "2026/2027"


class TestBenchmark:
    def _setup(self, db, home_winner=True):
        EvaluationRunner(db)._ensure_engine_version()
        from data.ingest_api import _detect_season_label
        sl = _detect_season_label()
        cid = db.get_or_create_competition("PL")
        sid = db.get_or_create_season(sl, 2026, 2027)
        csid = db.get_or_create_competition_season(cid, sid)
        db.get_or_create_team(1, "A"); db.get_or_create_team(2, "B")
        db.store_match({"id": 1, "competition_season_id": csid, "matchday": 1,
                         "status": "FINISHED", "utc_date": "2026-08-01T19:00:00Z",
                         "home_team_id": 1, "away_team_id": 2,
                         "home_score": 2, "away_score": 0,
                         "winner": "HOME_TEAM" if home_winner else "AWAY_TEAM"})
        db.store_standings_snapshot(csid, [
            {"team_id": 1, "position": 1, "played": 5, "points": 15,
             "goal_difference": 20, "ppg": 3.0},
            {"team_id": 2, "position": 10, "played": 5, "points": 5,
             "goal_difference": -5, "ppg": 1.0},
        ], "2026-07-30")
        runner = EvaluationRunner(db)
        runner.evaluate_all_pending()

    def test_empty(self, db):
        bm = db.get_benchmark()
        assert bm["totals"]["evaluated"] == 0
        assert bm["totals"]["selected"] == 0
        assert bm["totals"]["coverage"] == 0.0
        assert bm["totals"]["accuracy"] == 0.0
        total_range = sum(r["matches"] for r in bm["by_difference_range"])
        assert total_range == 0
        assert bm["by_competition"] == []
        assert bm["by_season"] == []

    def test_correct_prediction(self, db):
        self._setup(db, home_winner=True)
        bm = db.get_benchmark()
        assert bm["totals"]["evaluated"] == 1
        assert bm["totals"]["selected"] == 1
        assert bm["totals"]["correct"] == 1
        assert bm["totals"]["accuracy"] == 1.0

    def test_incorrect_prediction(self, db):
        self._setup(db, home_winner=False)
        bm = db.get_benchmark()
        assert bm["totals"]["correct"] == 0
        assert bm["totals"]["accuracy"] == 0.0

    def test_filter_by_competition(self, db):
        self._setup(db)
        bm = db.get_benchmark(competition_code="PL")
        assert bm["totals"]["selected"] == 1
        bm = db.get_benchmark(competition_code="BL1")
        assert bm["totals"]["selected"] == 0

    def test_filter_by_engine_version(self, db):
        self._setup(db)
        bm = db.get_benchmark(engine_version="v2.0")
        assert bm["totals"]["selected"] == 1
        bm = db.get_benchmark(engine_version="v1.0")
        assert bm["totals"]["selected"] == 0

    def test_by_difference_range(self, db):
        self._setup(db)
        bm = db.get_benchmark()
        ranges = {r["range"]: r for r in bm["by_difference_range"]}
        total = sum(r["matches"] for r in bm["by_difference_range"])
        assert total == bm["totals"]["selected"]

    def test_by_competition(self, db):
        self._setup(db)
        bm = db.get_benchmark()
        assert len(bm["by_competition"]) == 1
        assert bm["by_competition"][0]["competition_code"] == "PL"
