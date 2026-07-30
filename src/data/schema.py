import sqlite3

SCHEMA_SQL = """

CREATE TABLE IF NOT EXISTS engine_versions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    version             TEXT    NOT NULL UNIQUE,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    config_hash         TEXT    NOT NULL,
    structural_weight   REAL    NOT NULL,
    context_weight      REAL    NOT NULL,
    min_difference      INTEGER NOT NULL,
    description         TEXT
);

CREATE TABLE IF NOT EXISTS competitions (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    code     TEXT    NOT NULL UNIQUE,
    name     TEXT    NOT NULL,
    country  TEXT
);

CREATE TABLE IF NOT EXISTS seasons (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    year_start  INTEGER NOT NULL,
    year_end    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS teams (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    short_name  TEXT,
    crest_url   TEXT
);

CREATE TABLE IF NOT EXISTS competition_seasons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id  INTEGER NOT NULL REFERENCES competitions(id),
    season_id       INTEGER NOT NULL REFERENCES seasons(id),
    UNIQUE(competition_id, season_id)
);

CREATE TABLE IF NOT EXISTS standings_snapshots (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_season_id   INTEGER NOT NULL REFERENCES competition_seasons(id),
    team_id                 INTEGER NOT NULL REFERENCES teams(id),
    snapshot_date           TEXT    NOT NULL,
    position                INTEGER,
    played                  INTEGER,
    points                  INTEGER,
    goal_difference         INTEGER,
    ppg                     REAL,
    UNIQUE(competition_season_id, team_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS matches (
    id                      INTEGER PRIMARY KEY,
    competition_season_id   INTEGER NOT NULL REFERENCES competition_seasons(id),
    matchday                INTEGER,
    stage                   TEXT,
    status                  TEXT    DEFAULT 'SCHEDULED',
    utc_date                TEXT    NOT NULL,
    home_team_id            INTEGER NOT NULL REFERENCES teams(id),
    away_team_id            INTEGER NOT NULL REFERENCES teams(id),
    home_score              INTEGER,
    away_score              INTEGER,
    winner                  TEXT,
    created_at              TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at              TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS evaluations (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id                  INTEGER NOT NULL REFERENCES matches(id),
    engine_version_id         INTEGER NOT NULL REFERENCES engine_versions(id),
    evaluated_at              TEXT    NOT NULL DEFAULT (datetime('now')),
    strength_home_total       REAL    NOT NULL,
    strength_home_structural  REAL    NOT NULL,
    strength_home_context     REAL    NOT NULL,
    strength_away_total       REAL    NOT NULL,
    strength_away_structural  REAL    NOT NULL,
    strength_away_context     REAL    NOT NULL,
    difference                REAL    NOT NULL,
    favorite_team_id          INTEGER NOT NULL REFERENCES teams(id),
    selected                  INTEGER NOT NULL,
    UNIQUE(match_id, engine_version_id)
);

CREATE INDEX IF NOT EXISTS idx_standings_cs_date ON standings_snapshots(competition_season_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_matches_cs         ON matches(competition_season_id);
CREATE INDEX IF NOT EXISTS idx_matches_date       ON matches(utc_date);
CREATE INDEX IF NOT EXISTS idx_matches_status     ON matches(status);
CREATE INDEX IF NOT EXISTS idx_evaluations_match  ON evaluations(match_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_engine ON evaluations(engine_version_id);

CREATE TABLE IF NOT EXISTS system_metadata (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def init_db(conn: sqlite3.Connection):
    conn.executescript(SCHEMA_SQL)
    conn.commit()
