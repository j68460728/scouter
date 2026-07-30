import os
import sys
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

import pytest
from data.store import ScouterDB, compute_config_hash
from data.evaluator import EvaluationRunner, _compute_standings
from strength_profile import _load_matrix


MATRIX = _load_matrix()
V2_HASH = compute_config_hash(MATRIX)


@pytest.fixture
def db():
    _db = ScouterDB(":memory:")
    yield _db
    _db.close()


@pytest.fixture
def runner(db):
    return EvaluationRunner(db)


def _make_season(db, competition_code="PL", season_name="2024/2025",
                 season_year=2024, teams_data=None):
    cid = db.get_or_create_competition(competition_code)
    sid = db.get_or_create_season(season_name, season_year, season_year + 1)
    csid = db.get_or_create_competition_season(cid, sid)
    if teams_data:
        for tid, name in teams_data.items():
            db.get_or_create_team(tid, name)
    return cid, sid, csid


def _insert_standings(db, csid, date_str, standings_data):
    entries = []
    for tid, data in standings_data.items():
        db.get_or_create_team(tid, data["name"])
        entries.append({
            "team_id": tid, "position": data["pos"],
            "played": data["pl"], "points": data["pts"],
            "goal_difference": data["gd"], "ppg": data["pts"] / data["pl"],
        })
    db.store_standings_snapshot(csid, entries, date_str)


def _insert_match(db, csid, match_id, home_id, away_id, date_str,
                  status="SCHEDULED", hg=None, ag=None, winner=None):
    db.store_match({
        "id": match_id, "competition_season_id": csid, "matchday": 1,
        "stage": "REGULAR_SEASON", "status": status,
        "utc_date": date_str,
        "home_team_id": home_id, "away_team_id": away_id,
        "home_score": hg, "away_score": ag, "winner": winner,
    })


# ======================================================================
# _compute_standings
# ======================================================================
class TestComputeStandings:
    def test_empty_list(self):
        assert _compute_standings([]) == {}

    def test_single_match(self):
        rows = [
            {"home_team_id": 1, "away_team_id": 2,
             "home_score": 2, "away_score": 0,
             "home_team_name": "A", "away_team_name": "B"},
        ]
        st = _compute_standings(rows)
        assert st[1]["points"] == 3
        assert st[2]["points"] == 0
        assert st[1]["goal_difference"] == 2

    def test_two_matches(self):
        rows = [
            {"home_team_id": 1, "away_team_id": 2,
             "home_score": 2, "away_score": 0,
             "home_team_name": "A", "away_team_name": "B"},
            {"home_team_id": 1, "away_team_id": 3,
             "home_score": 1, "away_score": 0,
             "home_team_name": "A", "away_team_name": "C"},
        ]
        st = _compute_standings(rows)
        assert st[1]["points"] == 6
        assert st[1]["played"] == 2
        assert st[2]["played"] == 1


# ======================================================================
# evaluate_all_pending
# ======================================================================
class TestEvaluatePending:
    def test_evaluates_scheduled_match(self, db, runner):
        _, _, csid = _make_season(db, teams_data={57: "Arsenal", 65: "Man City"})
        _insert_standings(db, csid, "2026-08-15", {
            57: {"name": "Arsenal", "pos": 1, "pl": 5, "pts": 13, "gd": 10},
            65: {"name": "Man City", "pos": 3, "pl": 5, "pts": 10, "gd": 5},
        })
        _insert_match(db, csid, 1001, 57, 65, "2026-08-21T19:00:00Z")

        n = runner.evaluate_all_pending()
        assert n == 1

        evals = db.get_evaluations()
        assert len(evals) == 1
        assert evals[0]["favorite_team_name"] == "Arsenal"
        assert evals[0]["engine_version"] == "v2.0"

    def test_idempotent(self, db, runner):
        _, _, csid = _make_season(db, teams_data={57: "Arsenal", 65: "Man City"})
        _insert_standings(db, csid, "2026-08-15", {
            57: {"name": "Arsenal", "pos": 1, "pl": 5, "pts": 13, "gd": 10},
            65: {"name": "Man City", "pos": 3, "pl": 5, "pts": 10, "gd": 5},
        })
        _insert_match(db, csid, 1001, 57, 65, "2026-08-21T19:00:00Z")

        runner.evaluate_all_pending()
        n2 = runner.evaluate_all_pending()
        assert n2 == 0
        evals = db.get_evaluations()
        assert len(evals) == 1

    def test_skips_already_evaluated(self, db, runner):
        _, _, csid = _make_season(db, teams_data={57: "Arsenal", 65: "Man City", 61: "Chelsea"})
        _insert_standings(db, csid, "2026-08-15", {
            57: {"name": "Arsenal", "pos": 1, "pl": 5, "pts": 13, "gd": 10},
            65: {"name": "Man City", "pos": 3, "pl": 5, "pts": 10, "gd": 5},
            61: {"name": "Chelsea", "pos": 5, "pl": 5, "pts": 8, "gd": 2},
        })
        _insert_match(db, csid, 1001, 57, 65, "2026-08-21T19:00:00Z")
        _insert_match(db, csid, 1002, 61, 57, "2026-08-28T19:00:00Z")

        runner.evaluate_all_pending()
        assert runner.evaluate_all_pending() == 0


# ======================================================================
# evaluate_season
# ======================================================================
class TestEvaluateSeason:
    def test_evaluates_historical_chronologically(self, db, runner):
        _, _, csid = _make_season(db, teams_data={1: "A", 2: "B", 3: "C"})
        _insert_match(db, csid, 1, 1, 2, "2024-08-15T19:00:00Z",
                      status="FINISHED", hg=2, ag=0, winner="HOME_TEAM")
        _insert_match(db, csid, 2, 1, 3, "2024-08-22T19:00:00Z",
                      status="FINISHED", hg=1, ag=1, winner="DRAW")
        _insert_match(db, csid, 3, 2, 3, "2024-08-29T19:00:00Z",
                      status="FINISHED", hg=0, ag=0, winner="DRAW")

        n = runner.evaluate_season("PL", "2024/2025")
        assert n == 3

        evals = db.get_evaluations()
        assert len(evals) == 3

    def test_time_travel_no_leakage(self, db, runner):
        _, _, csid = _make_season(db, teams_data={1: "A", 2: "B", 3: "C", 4: "D"})
        _insert_match(db, csid, 1, 1, 2, "2024-08-15T19:00:00Z",
                      status="FINISHED", hg=3, ag=0, winner="HOME_TEAM")
        _insert_match(db, csid, 2, 3, 4, "2024-08-15T19:05:00Z",
                      status="FINISHED", hg=1, ag=1, winner="DRAW")
        _insert_match(db, csid, 3, 1, 3, "2024-08-22T19:00:00Z",
                      status="FINISHED", hg=2, ag=0, winner="HOME_TEAM")

        runner.evaluate_season("PL", "2024/2025")
        ft = [e for e in db.get_evaluations() if e["match_id"] == 3]
        assert len(ft) == 1
        assert ft[0]["strength_home_total"] > 0

    def test_standings_strictly_before(self, db, runner):
        _, _, csid = _make_season(db, teams_data={1: "A", 2: "B", 3: "C"})
        _insert_match(db, csid, 1, 1, 2, "2024-08-15T19:00:00Z",
                      status="FINISHED", hg=3, ag=0, winner="HOME_TEAM")
        _insert_match(db, csid, 2, 3, 2, "2024-08-15T19:05:00Z",
                      status="FINISHED", hg=2, ag=0, winner="HOME_TEAM")
        _insert_match(db, csid, 3, 1, 3, "2024-08-22T19:00:00Z",
                      status="FINISHED", hg=0, ag=1, winner="AWAY_TEAM")

        runner.evaluate_season("PL", "2024/2025")
        evals = {e["match_id"]: e for e in db.get_evaluations()}
        e3 = evals[3]
        assert e3["favorite_team_id"] == 1


# ======================================================================
# evaluate_match
# ======================================================================
class TestEvaluateMatch:
    def test_evaluate_single_match(self, db, runner):
        _, _, csid = _make_season(db, teams_data={57: "Arsenal", 65: "Man City"})
        _insert_standings(db, csid, "2026-08-15", {
            57: {"name": "Arsenal", "pos": 1, "pl": 5, "pts": 13, "gd": 10},
            65: {"name": "Man City", "pos": 3, "pl": 5, "pts": 10, "gd": 5},
        })
        _insert_match(db, csid, 1001, 57, 65, "2026-08-21T19:00:00Z")

        result = runner.evaluate_match(1001)
        assert result is not None
        assert result["match_id"] == 1001
        assert "home_strength" in result
        assert "difference" in result

    def test_unknown_match(self, db, runner):
        result = runner.evaluate_match(99999)
        assert result is None

    def test_match_already_evaluated(self, db, runner):
        _, _, csid = _make_season(db, teams_data={57: "Arsenal", 65: "Man City"})
        _insert_standings(db, csid, "2026-08-15", {
            57: {"name": "Arsenal", "pos": 1, "pl": 5, "pts": 13, "gd": 10},
            65: {"name": "Man City", "pos": 3, "pl": 5, "pts": 10, "gd": 5},
        })
        _insert_match(db, csid, 1001, 57, 65, "2026-08-21T19:00:00Z")

        runner.evaluate_match(1001)
        evals = db.get_evaluations()
        assert len(evals) == 1


# ======================================================================
# Engine version from YAML
# ======================================================================
class TestEngineVersion:
    def test_config_hash_from_yaml(self, db):
        runner = EvaluationRunner(db)
        ev_id = runner._ensure_engine_version()
        ev = db.get_engine_version(ev_id)
        assert ev["config_hash"] == V2_HASH
        assert ev["structural_weight"] == 0.857
        assert ev["min_difference"] == 20

    def test_different_runner_same_config(self, db):
        r1 = EvaluationRunner(db)
        r2 = EvaluationRunner(db)
        id1 = r1._ensure_engine_version()
        id2 = r2._ensure_engine_version()
        assert id1 == id2

    def test_selection_threshold_from_yaml(self, db, runner):
        _, _, csid = _make_season(db, teams_data={57: "A", 65: "B", 61: "C"})
        _insert_standings(db, csid, "2026-08-15", {
            57: {"name": "A", "pos": 1, "pl": 5, "pts": 15, "gd": 20},
            65: {"name": "B", "pos": 10, "pl": 5, "pts": 5, "gd": -5},
            61: {"name": "C", "pos": 9, "pl": 5, "pts": 6, "gd": -3},
        })
        _insert_match(db, csid, 1, 57, 65, "2026-08-21T19:00:00Z")
        _insert_match(db, csid, 2, 57, 61, "2026-08-28T19:00:00Z")

        runner.evaluate_all_pending()
        evals = db.get_evaluations(selected_only=True)
        assert len(evals) == 2


# ======================================================================
# Engine purity
# ======================================================================
class TestEnginePurity:
    def test_strength_profile_not_modified(self, db, runner):
        import inspect
        from strength_profile import build_match as bm
        source = inspect.getsource(bm)
        assert "SQLite" not in source
        assert "ScouterDB" not in source
        assert "store" not in source

    def test_no_new_files_outside_data(self):
        excluded = {"evaluator.py"}
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'src', 'data'
        )
        files = set(os.listdir(data_dir)) - {"__pycache__"}
        unwanted = files - {"__init__.py", "schema.py", "store.py",
                           "ingest_csv.py", "ingest_api.py",
                           "ingestion.py", "evaluator.py"}
        assert not unwanted, f"Unexpected files: {unwanted}"
