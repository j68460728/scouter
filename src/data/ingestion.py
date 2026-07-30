from data.store import ScouterDB
from data.ingest_api import ingest_api_all
from data.ingest_csv import ingest_csv_season


def sync_all(db_path: str = "data/scouter.sqlite") -> dict:
    db = ScouterDB(db_path)
    try:
        result = ingest_api_all(db)
        return result
    finally:
        db.close()


def backfill_season(db_path: str, csv_source: str,
                    competition_code: str, season_year: str) -> dict:
    db = ScouterDB(db_path)
    try:
        result = ingest_csv_season(db, csv_source,
                                    competition_code, season_year)
        return result
    finally:
        db.close()
