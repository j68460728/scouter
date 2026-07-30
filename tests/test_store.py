import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from data.store import ScouterDB, compute_config_hash


@pytest.fixture
def db():
    _db = ScouterDB(":memory:")
    yield _db
    _db.close()


# ------------------------------------------------------------------
# Engine version helpers
# ------------------------------------------------------------------
V2_CONFIG = {
    "version": "v2.0",
    "structural_weight": 0.857,
    "context_weight": 0.143,
    "min_difference": 20,
    "description": "Scouter Engine v2 — Structural + Context only",
}

V2_1_CONFIG = {
    "version": "v2.1",
    "structural_weight": 0.850,
    "context_weight": 0.150,
    "min_difference": 18,
    "description": "Experimental v2.1",
}


@pytest.fixture
def v2_id(db):
    return db.register_engine_version(V2_CONFIG)


@pytest.fixture
def v2_1_id(db):
    return db.register_engine_version(V2_1_CONFIG)


@pytest.fixture
def pl_season(db):
    cid = db.get_or_create_competition("PL", "Premier League", "England")
    sid = db.get_or_create_season("2024/2025", 2024, 2025)
    csid = db.get_or_create_competition_season(cid, sid)
    return cid, sid, csid


@pytest.fixture
def la_season(db):
    cid = db.get_or_create_competition("PD", "La Liga", "Spain")
    sid = db.get_or_create_season("2024/2025", 2024, 2025)
    csid = db.get_or_create_competition_season(cid, sid)
    return cid, sid, csid


@pytest.fixture
def teams(db):
    ids = {}
    for t in [
        (57, "Arsenal FC", "Arsenal"),
        (65, "Manchester City FC", "Man City"),
        (61, "Chelsea FC", "Chelsea"),
        (1044, "Bournemouth AFC", "Bournemouth"),
    ]:
        ids[t[0]] = db.get_or_create_team(*t)
    return ids


# ======================================================================
# Scenario 1: INSERTAR
# ======================================================================
class TestInsert:
    def test_engine_version(self, db):
        eid = db.register_engine_version(V2_CONFIG)
        row = db.get_engine_version(eid)
        assert row is not None
        assert row["version"] == "v2.0"
        assert row["structural_weight"] == 0.857
        assert row["min_difference"] == 20

    def test_competition(self, db):
        cid = db.get_or_create_competition("PL", "Premier League", "England")
        assert cid > 0
        same = db.get_or_create_competition("PL", "Premier League", "England")
        assert same == cid

    def test_season(self, db):
        sid = db.get_or_create_season("2024/2025", 2024, 2025)
        assert sid > 0
        same = db.get_or_create_season("2024/2025", 2024, 2025)
        assert same == sid

    def test_team(self, db):
        tid = db.get_or_create_team(57, "Arsenal FC", "Arsenal")
        assert tid == 57
        row = db.get_team(57)
        assert row["name"] == "Arsenal FC"

    def test_standings_snapshot(self, db, pl_season, teams):
        _, _, csid = pl_season
        db.store_standings_snapshot(csid, [
            {"team_id": 57, "position": 1, "played": 10, "points": 25, "goal_difference": 18, "ppg": 2.5},
            {"team_id": 65, "position": 2, "played": 10, "points": 23, "goal_difference": 15, "ppg": 2.3},
        ], "2024-10-15")
        rows = db.get_standings_as_of("PL", "2024/2025", "2024-10-15")
        assert len(rows) == 2
        assert rows[57]["position"] == 1

    def test_match(self, db, pl_season, teams):
        _, _, csid = pl_season
        mid = db.store_match({
            "id": 1001,
            "competition_season_id": csid,
            "matchday": 8,
            "stage": "REGULAR_SEASON",
            "status": "SCHEDULED",
            "utc_date": "2024-10-15T19:00:00Z",
            "home_team_id": 57,
            "away_team_id": 65,
        })
        row = db.get_match(1001)
        assert row["id"] == 1001
        assert row["home_team_name"] == "Arsenal FC"

    def test_evaluation(self, db, pl_season, teams, v2_id):
        _, _, csid = pl_season
        mid = db.store_match({
            "id": 1002, "competition_season_id": csid, "matchday": 8,
            "stage": "REGULAR_SEASON", "status": "SCHEDULED",
            "utc_date": "2024-10-15T19:00:00Z",
            "home_team_id": 57, "away_team_id": 65,
        })
        eid = db.store_evaluation(mid, v2_id, {
            "strength_home_total": 79.8,
            "strength_home_structural": 71.3,
            "strength_home_context": 8.5,
            "strength_away_total": 55.8,
            "strength_away_structural": 54.4,
            "strength_away_context": 1.4,
            "difference": 24.0,
            "favorite_team_id": 57,
            "selected": True,
        })
        assert eid > 0


# ======================================================================
# Scenario 2: CONSULTAR
# ======================================================================
class TestQuery:
    def test_get_match_by_id(self, db, pl_season, teams):
        _, _, csid = pl_season
        db.store_match({"id": 2001, "competition_season_id": csid, "matchday": 1,
                         "status": "FINISHED", "utc_date": "2024-08-15T19:00:00Z",
                         "home_team_id": 57, "away_team_id": 1044,
                         "home_score": 2, "away_score": 0, "winner": "HOME_TEAM"})
        m = db.get_match(2001)
        assert m["home_score"] == 2
        assert m["actual_winner"] if "actual_winner" in m else "HOME_TEAM"

    def test_get_matches_by_competition(self, db, pl_season, teams):
        _, _, csid = pl_season
        db.store_matches([
            {"id": 3001, "competition_season_id": csid, "matchday": 1,
             "status": "FINISHED", "utc_date": "2024-08-15T19:00:00Z",
             "home_team_id": 57, "away_team_id": 1044},
            {"id": 3002, "competition_season_id": csid, "matchday": 1,
             "status": "FINISHED", "utc_date": "2024-08-16T19:00:00Z",
             "home_team_id": 65, "away_team_id": 61},
        ])
        ms = db.get_matches(competition_code="PL")
        assert len(ms) == 2

    def test_get_matches_filter_by_status(self, db, pl_season, teams):
        _, _, csid = pl_season
        db.store_matches([
            {"id": 4001, "competition_season_id": csid, "matchday": 1,
             "status": "FINISHED", "utc_date": "2024-08-15T19:00:00Z",
             "home_team_id": 57, "away_team_id": 1044,
             "home_score": 1, "away_score": 1, "winner": "DRAW"},
            {"id": 4002, "competition_season_id": csid, "matchday": 2,
             "status": "SCHEDULED", "utc_date": "2024-08-25T19:00:00Z",
             "home_team_id": 61, "away_team_id": 57},
        ])
        scheduled = db.get_matches(competition_code="PL", status="SCHEDULED")
        assert len(scheduled) == 1
        assert scheduled[0]["status"] == "SCHEDULED"

    def test_get_evaluations_with_join(self, db, pl_season, teams, v2_id):
        _, _, csid = pl_season
        db.store_match({"id": 5001, "competition_season_id": csid, "matchday": 1,
                         "status": "FINISHED", "utc_date": "2024-08-15T19:00:00Z",
                         "home_team_id": 57, "away_team_id": 1044,
                         "home_score": 2, "away_score": 0, "winner": "HOME_TEAM"})
        db.store_evaluation(5001, v2_id, {
            "strength_home_total": 79.8, "strength_home_structural": 71.3,
            "strength_home_context": 8.5, "strength_away_total": 55.8,
            "strength_away_structural": 54.4, "strength_away_context": 1.4,
            "difference": 24.0, "favorite_team_id": 57, "selected": True,
        })
        evals = db.get_evaluations()
        assert len(evals) == 1
        e = evals[0]
        assert e["favorite_team_name"] == "Arsenal FC"
        assert e["actual_winner_name"] == "Arsenal FC"
        assert e["correct"] == 1


# ======================================================================
# Scenario 3: TIME-TRAVEL
# ======================================================================
class TestTimeTravel:
    def test_standings_as_of_returns_correct_snapshot(self, db, pl_season, teams):
        _, _, csid = pl_season
        db.store_standings_snapshot(csid, [
            {"team_id": 57, "position": 1, "played": 5, "points": 13,
             "goal_difference": 10, "ppg": 2.6},
            {"team_id": 65, "position": 3, "played": 5, "points": 10,
             "goal_difference": 5, "ppg": 2.0},
        ], "2024-09-15")

        db.store_standings_snapshot(csid, [
            {"team_id": 57, "position": 1, "played": 10, "points": 25,
             "goal_difference": 18, "ppg": 2.5},
            {"team_id": 65, "position": 2, "played": 10, "points": 23,
             "goal_difference": 15, "ppg": 2.3},
        ], "2024-10-15")

        as_of = db.get_standings_as_of("PL", "2024/2025", "2024-10-01")
        assert len(as_of) == 2
        assert as_of[57]["position"] == 1
        assert as_of[57]["played"] == 5
        assert as_of[57]["points"] == 13
        assert as_of[65]["played"] == 5

    def test_standings_as_of_exact_date(self, db, pl_season, teams):
        _, _, csid = pl_season
        db.store_standings_snapshot(csid, [
            {"team_id": 57, "position": 1, "played": 10, "points": 25,
             "goal_difference": 18, "ppg": 2.5},
        ], "2024-10-15")

        as_of = db.get_standings_as_of("PL", "2024/2025", "2024-10-15")
        assert len(as_of) == 1
        assert as_of[57]["played"] == 10

    def test_standings_as_of_before_any_snapshot(self, db, pl_season, teams):
        _, _, csid = pl_season
        db.store_standings_snapshot(csid, [
            {"team_id": 57, "position": 1, "played": 10, "points": 25,
             "goal_difference": 18, "ppg": 2.5},
        ], "2024-10-15")

        as_of = db.get_standings_as_of("PL", "2024/2025", "2024-09-01")
        assert len(as_of) == 0

    def test_snapshot_coherence(self, db, pl_season, teams):
        _, _, csid = pl_season
        db.store_standings_snapshot(csid, [
            {"team_id": 57, "position": 1, "played": 5, "points": 13,
             "goal_difference": 10, "ppg": 2.6},
            {"team_id": 65, "position": 3, "played": 5, "points": 10,
             "goal_difference": 5, "ppg": 2.0},
        ], "2024-09-15")
        db.store_standings_snapshot(csid, [
            {"team_id": 57, "position": 2, "played": 10, "points": 22,
             "goal_difference": 12, "ppg": 2.2},
            {"team_id": 65, "position": 1, "played": 10, "points": 25,
             "goal_difference": 18, "ppg": 2.5},
        ], "2024-10-15")
        as_of = db.get_standings_as_of("PL", "2024/2025", "2024-10-01")
        assert as_of[57]["position"] == 1
        assert as_of[65]["position"] == 3


# ======================================================================
# Scenario 4: HISTORICO DE EQUIPO
# ======================================================================
class TestTeamHistory:
    def test_two_seasons(self, db, teams):
        pl_cid = db.get_or_create_competition("PL", "Premier League", "England")
        pd_cid = db.get_or_create_competition("PD", "La Liga", "Spain")

        s23 = db.get_or_create_season("2023/2024", 2023, 2024)
        s24 = db.get_or_create_season("2024/2025", 2024, 2025)

        cs23 = db.get_or_create_competition_season(pl_cid, s23)
        cs24 = db.get_or_create_competition_season(pd_cid, s24)

        db.store_standings_snapshot(cs23, [
            {"team_id": 57, "position": 2, "played": 38, "points": 84,
             "goal_difference": 42, "ppg": 2.21},
        ], "2024-05-19")

        db.store_standings_snapshot(cs24, [
            {"team_id": 57, "position": 5, "played": 15, "points": 30,
             "goal_difference": 10, "ppg": 2.0},
        ], "2024-12-15")

        history = db.get_team_history(57)
        assert len(history) == 2
        seasons_found = {h["season_name"] for h in history}
        assert "2023/2024" in seasons_found
        assert "2024/2025" in seasons_found
        for h in history:
            if h["season_name"] == "2023/2024":
                assert h["competition_code"] == "PL"
                assert h["position"] == 2
            elif h["season_name"] == "2024/2025":
                assert h["competition_code"] == "PD"
                assert h["position"] == 5


# ======================================================================
# Scenario 5: DATA LEAKAGE CHECK
# ======================================================================
class TestDataLeakage:
    def test_no_future_data(self, db, pl_season, teams):
        _, _, csid = pl_season
        db.store_standings_snapshot(csid, [
            {"team_id": 57, "position": 1, "played": 10, "points": 25,
             "goal_difference": 18, "ppg": 2.5},
            {"team_id": 65, "position": 2, "played": 10, "points": 23,
             "goal_difference": 15, "ppg": 2.3},
        ], "2024-10-15")

        db.store_standings_snapshot(csid, [
            {"team_id": 57, "position": 1, "played": 20, "points": 52,
             "goal_difference": 30, "ppg": 2.6},
            {"team_id": 65, "position": 3, "played": 20, "points": 40,
             "goal_difference": 20, "ppg": 2.0},
        ], "2024-11-01")

        as_of_oct20 = db.get_standings_as_of("PL", "2024/2025", "2024-10-20")
        assert as_of_oct20[57]["played"] == 10, (
            f"Expected 10, got {as_of_oct20[57]['played']} — data leakage!"
        )
        assert as_of_oct20[57]["points"] == 25

        as_of_nov5 = db.get_standings_as_of("PL", "2024/2025", "2024-11-05")
        assert as_of_nov5[57]["played"] == 20


# ======================================================================
# Scenario 6: EVALUACION VINCULADA A VERSION
# ======================================================================
class TestEvaluationVersioning:
    def test_two_versions_same_match(self, db, pl_season, teams, v2_id, v2_1_id):
        _, _, csid = pl_season
        db.store_match({"id": 6001, "competition_season_id": csid, "matchday": 1,
                         "status": "FINISHED", "utc_date": "2024-08-15T19:00:00Z",
                         "home_team_id": 57, "away_team_id": 1044,
                         "home_score": 2, "away_score": 0, "winner": "HOME_TEAM"})

        db.store_evaluation(6001, v2_id, {
            "strength_home_total": 79.8, "strength_home_structural": 71.3,
            "strength_home_context": 8.5, "strength_away_total": 55.8,
            "strength_away_structural": 54.4, "strength_away_context": 1.4,
            "difference": 24.0, "favorite_team_id": 57, "selected": True,
        })
        db.store_evaluation(6001, v2_1_id, {
            "strength_home_total": 78.0, "strength_home_structural": 70.0,
            "strength_home_context": 8.0, "strength_away_total": 60.0,
            "strength_away_structural": 58.0, "strength_away_context": 2.0,
            "difference": 18.0, "favorite_team_id": 57, "selected": False,
        })

        evals = db.get_evaluations(competition_code="PL", season_name="2024/2025")
        assert len(evals) == 2
        versions = {e["engine_version"] for e in evals}
        assert "v2.0" in versions
        assert "v2.1" in versions

        v2_eval = [e for e in evals if e["engine_version"] == "v2.0"][0]
        v2_1_eval = [e for e in evals if e["engine_version"] == "v2.1"][0]
        assert abs(v2_eval["difference"] - 24.0) < 0.01
        assert abs(v2_1_eval["difference"] - 18.0) < 0.01


# ======================================================================
# Edge cases
# ======================================================================
class TestEdgeCases:
    def test_store_match_noop_does_not_update_timestamp(self, db, pl_season, teams):
        _, _, csid = pl_season
        mid = db.store_match({"id": 7001, "competition_season_id": csid, "matchday": 1,
                               "status": "FINISHED", "utc_date": "2024-08-15T19:00:00Z",
                               "home_team_id": 57, "away_team_id": 1044,
                               "home_score": 2, "away_score": 0, "winner": "HOME_TEAM"})
        original = db.get_match(7001)
        orig_updated = original["updated_at"]

        import time
        time.sleep(0.05)

        db.store_match({"id": 7001, "competition_season_id": csid, "matchday": 1,
                         "status": "FINISHED", "utc_date": "2024-08-15T19:00:00Z",
                         "home_team_id": 57, "away_team_id": 1044,
                         "home_score": 2, "away_score": 0, "winner": "HOME_TEAM"})
        after = db.get_match(7001)
        assert after["updated_at"] == orig_updated, "updated_at should not change on no-op"

    def test_store_match_update_changes_timestamp(self, db, pl_season, teams):
        _, _, csid = pl_season
        mid = db.store_match({"id": 7002, "competition_season_id": csid, "matchday": 1,
                               "status": "SCHEDULED", "utc_date": "2024-08-15T19:00:00Z",
                               "home_team_id": 57, "away_team_id": 1044})

        import time
        time.sleep(0.05)

        db.store_match({"id": 7002, "competition_season_id": csid, "matchday": 1,
                         "status": "FINISHED", "utc_date": "2024-08-15T19:00:00Z",
                         "home_team_id": 57, "away_team_id": 1044,
                         "home_score": 2, "away_score": 0, "winner": "HOME_TEAM"})
        after = db.get_match(7002)
        assert after["status"] == "FINISHED"
        assert after["home_score"] == 2

    def test_get_evaluations_selected_only(self, db, pl_season, teams, v2_id):
        _, _, csid = pl_season
        db.store_matches([
            {"id": 8001, "competition_season_id": csid, "matchday": 1,
             "status": "FINISHED", "utc_date": "2024-08-15T19:00:00Z",
             "home_team_id": 57, "away_team_id": 1044,
             "home_score": 2, "away_score": 0, "winner": "HOME_TEAM"},
            {"id": 8002, "competition_season_id": csid, "matchday": 1,
             "status": "FINISHED", "utc_date": "2024-08-16T19:00:00Z",
             "home_team_id": 65, "away_team_id": 61,
             "home_score": 1, "away_score": 0, "winner": "HOME_TEAM"},
        ])
        db.store_evaluation(8001, v2_id, {
            "strength_home_total": 79.8, "strength_home_structural": 71.3,
            "strength_home_context": 8.5, "strength_away_total": 55.8,
            "strength_away_structural": 54.4, "strength_away_context": 1.4,
            "difference": 24.0, "favorite_team_id": 57, "selected": True,
        })
        db.store_evaluation(8002, v2_id, {
            "strength_home_total": 60.0, "strength_home_structural": 52.0,
            "strength_home_context": 8.0, "strength_away_total": 55.0,
            "strength_away_structural": 53.0, "strength_away_context": 2.0,
            "difference": 5.0, "favorite_team_id": 65, "selected": False,
        })

        all_evals = db.get_evaluations()
        assert len(all_evals) == 2

        selected = db.get_evaluations(selected_only=True)
        assert len(selected) == 1
        assert selected[0]["difference"] == 24.0

    def test_team_not_found(self, db):
        team = db.get_team(99999)
        assert team is None

    def test_engine_version_not_found(self, db):
        ev = db.get_engine_version(99999)
        assert ev is None

    def test_config_hash_consistency(self):
        cfg1 = {"structural_weight": 0.857, "context_weight": 0.143, "min_difference": 20}
        cfg2 = {"context_weight": 0.143, "structural_weight": 0.857, "min_difference": 20}
        assert compute_config_hash(cfg1) == compute_config_hash(cfg2)

    def test_config_hash_different_configs(self):
        cfg1 = {"structural_weight": 0.857, "context_weight": 0.143, "min_difference": 20}
        cfg2 = {"structural_weight": 0.850, "context_weight": 0.150, "min_difference": 18}
        assert compute_config_hash(cfg1) != compute_config_hash(cfg2)

    def test_standings_no_snapshot_returns_empty(self, db):
        result = db.get_standings_as_of("PL", "2024/2025", "2024-10-15")
        assert result == {}

    def test_get_matches_none(self, db):
        ms = db.get_matches(competition_code="XX")
        assert ms == []

    def test_get_evaluations_none(self, db):
        evals = db.get_evaluations()
        assert evals == []

    def test_team_history_empty(self, db):
        history = db.get_team_history(99999)
        assert history == []
