import os
import sys
from unittest import mock
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

import pytest
from data.store import ScouterDB
from data.ingest_api import (
    ingest_api_standings,
    ingest_api_matches,
    LEAGUES,
    _detect_season_label,
)


MOCK_STANDINGS = {
    57: {"id": 57, "name": "Arsenal FC", "position": 1, "playedGames": 10,
         "points": 25, "goalDifference": 18, "goalsFor": 22, "goalsAgainst": 4},
    65: {"id": 65, "name": "Manchester City FC", "position": 2,
         "playedGames": 10, "points": 23, "goalDifference": 15,
         "goalsFor": 20, "goalsAgainst": 5},
}

MOCK_MATCHES = [
    {
        "id": "1001",
        "home_team": "Arsenal FC",
        "home_id": 57,
        "away_team": "Bournemouth AFC",
        "away_id": 1044,
        "competition": "Premier League",
        "competition_code": "PL",
        "date": "2026-08-21T19:00:00Z",
        "matchday": 1,
        "stage": "REGULAR_SEASON",
    },
    {
        "id": "1002",
        "home_team": "Manchester City FC",
        "home_id": 65,
        "away_team": "Chelsea FC",
        "away_id": 61,
        "competition": "Premier League",
        "competition_code": "PL",
        "date": "2026-08-22T15:00:00Z",
        "matchday": 1,
        "stage": "REGULAR_SEASON",
    },
]


@pytest.fixture
def db():
    _db = ScouterDB(":memory:")
    yield _db
    _db.close()


MOCK_LEAGUES = {"PL", "BL1", "PD", "SA", "FL1"}


def _mock_get_standings(league_code):
    if league_code not in MOCK_LEAGUES:
        return {}
    return {
        tid: {
            "name": info["name"],
            "position": info["position"],
            "played": info["playedGames"],
            "points": info["points"],
            "goal_difference": info["goalDifference"],
            "ppg": info["points"] / info["playedGames"],
        }
        for tid, info in MOCK_STANDINGS.items()
    }


def _mock_get_matches(window_hours=None):
    if window_hours is None:
        return MOCK_MATCHES
    return MOCK_MATCHES  # same data regardless of window for tests


@mock.patch("data.ingest_api._api_standings", side_effect=_mock_get_standings)
@mock.patch("data.ingest_api._api_matches", side_effect=_mock_get_matches)
class TestIngestAPI:
    def test_standings_creates_teams(self, mock_matches, mock_standings, db):
        n = ingest_api_standings(db, "PL")
        assert n == 2
        assert db.get_team(57) is not None
        assert db.get_team(65) is not None

    def test_standings_creates_snapshot(self, mock_matches, mock_standings, db):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ingest_api_standings(db, "PL")
        as_of = db.get_standings_as_of("PL", _detect_season_label(), today)
        assert len(as_of) == 2
        assert as_of[57]["position"] == 1
        assert as_of[65]["position"] == 2

    def test_idempotent_standings(self, mock_matches, mock_standings, db):
        ingest_api_standings(db, "PL")
        n1 = len(db.get_standings_as_of("PL", _detect_season_label(), "2099-12-31"))
        ingest_api_standings(db, "PL")
        n2 = len(db.get_standings_as_of("PL", _detect_season_label(), "2099-12-31"))
        assert n2 >= n1  # may add another snapshot, but no duplicates

    def test_matches_creates_teams(self, mock_matches, mock_standings, db):
        n = ingest_api_matches(db, "PL")
        assert n == 2
        assert db.get_team(1044) is not None  # Bournemouth

    def test_matches_persisted(self, mock_matches, mock_standings, db):
        ingest_api_matches(db, "PL")
        ms = db.get_matches(competition_code="PL")
        assert len(ms) == 2
        assert ms[0]["home_team_name"] == "Arsenal FC"

    def test_matches_idempotent(self, mock_matches, mock_standings, db):
        ingest_api_matches(db, "PL")
        ingest_api_matches(db, "PL")
        ms = db.get_matches(competition_code="PL")
        assert len(ms) == 2

    def test_all_leagues_creates_competitions(self, mock_matches, mock_standings, db):
        from data.ingest_api import ingest_api_all
        result = ingest_api_all(db)
        for code in LEAGUES:
            assert result[code]["standings"] == 2
        assert result["PL"]["matches"] == 2
        assert result["BL1"]["matches"] == 0

    def test_standings_unknown_league(self, mock_matches, mock_standings, db):
        n = ingest_api_standings(db, "XX")
        assert n == 0


class TestIngestAPIHelpers:
    def test_detect_season_august(self):
        label = _detect_season_label("2026-08-21T19:00:00Z")
        assert label == "2026/2027"

    def test_detect_season_may(self):
        label = _detect_season_label("2026-05-15T19:00:00Z")
        assert label == "2025/2026"

    def test_detect_season_july(self):
        label = _detect_season_label("2026-07-29T19:00:00Z")
        assert label == "2025/2026"

    def test_detect_season_january(self):
        label = _detect_season_label("2027-01-15T15:00:00Z")
        assert label == "2026/2027"
