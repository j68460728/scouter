import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

import pytest
from data.store import ScouterDB
from data.ingest_csv import ingest_csv_season, _csv_team_id


CSV_CONTENT = """Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR
E0,16/08/24,Arsenal,Wolves,2,0,H
E0,16/08/24,Man City,Chelsea,3,1,H
E0,17/08/24,Liverpool,Newcastle,1,1,D
E0,17/08/24,Arsenal,Man City,0,2,A
E0,18/08/24,Man City,Newcastle,4,0,H
"""


@pytest.fixture
def csv_path():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv",
                                      delete=False, encoding="utf-8-sig") as f:
        f.write(CSV_CONTENT)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def db():
    _db = ScouterDB(":memory:")
    yield _db
    _db.close()


class TestIngestCSV:
    def test_ingest_creates_teams(self, db, csv_path):
        result = ingest_csv_season(db, csv_path, "PL", "2024")
        assert result["teams"] >= 4  # Arsenal, Wolves, Man City, Chelsea, ...
        assert db.get_team(_csv_team_id("Arsenal")) is not None
        assert db.get_team(_csv_team_id("Man City")) is not None

    def test_ingest_creates_matches(self, db, csv_path):
        result = ingest_csv_season(db, csv_path, "PL", "2024")
        assert result["matches"] == 5

    def test_ingest_creates_snapshots(self, db, csv_path):
        result = ingest_csv_season(db, csv_path, "PL", "2024")
        assert result["snapshots"] >= 2  # 3 distinct dates
        arsenal_id = _csv_team_id("Arsenal")
        as_of = db.get_standings_as_of("PL", "2024/2025", "2024-08-17")
        assert arsenal_id in as_of
        assert as_of[arsenal_id]["points"] >= 3  # won first match

    def test_idempotent_reingest(self, db, csv_path):
        r1 = ingest_csv_season(db, csv_path, "PL", "2024")
        r2 = ingest_csv_season(db, csv_path, "PL", "2024")
        assert r2["matches"] == 5  # no duplicate matches created
        ms = db.get_matches(competition_code="PL")
        assert len(ms) == 5  # still 5

    def test_time_travel_with_csv_data(self, db, csv_path):
        ingest_csv_season(db, csv_path, "PL", "2024")
        arsenal_id = _csv_team_id("Arsenal")
        as_of_16 = db.get_standings_as_of("PL", "2024/2025", "2024-08-16")
        as_of_17 = db.get_standings_as_of("PL", "2024/2025", "2024-08-17")
        as_of_18 = db.get_standings_as_of("PL", "2024/2025", "2024-08-18")

        assert arsenal_id in as_of_16
        assert arsenal_id in as_of_17
        assert arsenal_id in as_of_18

        points_16 = as_of_16[arsenal_id]["points"]
        points_18 = as_of_18[arsenal_id]["points"]

        # Arsenal won 2-0 on 16th, lost 0-2 on 17th
        # So points should be 3 after 16th, 3 after 18th (loss)
        st = as_of_18[arsenal_id]
        assert st["points"] == 3
        assert st["goal_difference"] == 0

    def test_unknown_competition(self, db):
        with pytest.raises(ValueError):
            ingest_csv_season(db, "dummy.csv", "XX", "2024")

    def test_unknown_season(self, db, csv_path):
        with pytest.raises(ValueError):
            ingest_csv_season(db, csv_path, "PL", "9999")


class TestCSVHelpers:
    def test_team_id_deterministic(self):
        assert _csv_team_id("Arsenal") == _csv_team_id("Arsenal")
        assert _csv_team_id("Arsenal") != _csv_team_id("Man City")

    def test_team_id_negative(self):
        assert _csv_team_id("Arsenal") < 0
        assert _csv_team_id("Chelsea") < 0
