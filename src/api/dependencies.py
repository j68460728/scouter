import os

from data.store import ScouterDB

DEFAULT_DB_PATH = os.environ.get("SCOUTER_DB_PATH", "data/scouter.sqlite")


def get_db() -> ScouterDB:
    return ScouterDB(DEFAULT_DB_PATH)
