import hashlib
import json
import sqlite3
from datetime import datetime, timezone

import yaml

from .schema import init_db


def compute_config_hash(yaml_dict: dict) -> str:
    canonical = json.dumps(yaml_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


class ScouterDB:

    def __init__(self, db_path: str = ":memory:"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        init_db(self._conn)

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def close(self):
        self._conn.close()

    # ------------------------------------------------------------------
    # engine_versions
    # ------------------------------------------------------------------
    def register_engine_version(self, config: dict) -> int:
        config_hash = config.get("config_hash") or compute_config_hash(config)
        cur = self._conn.execute(
            """INSERT OR IGNORE INTO engine_versions
               (version, config_hash, structural_weight, context_weight, min_difference, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                config.get("version", "unknown"),
                config_hash,
                config.get("structural_weight", 0.0),
                config.get("context_weight", 0.0),
                config.get("min_difference", 20),
                config.get("description"),
            ),
        )
        if cur.rowcount == 0:
            row = self._conn.execute(
                "SELECT id FROM engine_versions WHERE version = ?", (config.get("version", "unknown"),)
            ).fetchone()
            return row["id"]
        self._conn.commit()
        return cur.lastrowid

    def get_engine_version(self, engine_version_id: int) -> dict:
        row = self._conn.execute(
            "SELECT * FROM engine_versions WHERE id = ?", (engine_version_id,)
        ).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # competitions
    # ------------------------------------------------------------------
    def get_or_create_competition(self, code: str, name: str = None,
                                  country: str = None) -> int:
        row = self._conn.execute(
            "SELECT id FROM competitions WHERE code = ?", (code,)
        ).fetchone()
        if row:
            return row["id"]
        cur = self._conn.execute(
            "INSERT INTO competitions (code, name, country) VALUES (?, ?, ?)",
            (code, name or code, country),
        )
        self._conn.commit()
        return cur.lastrowid

    # ------------------------------------------------------------------
    # seasons
    # ------------------------------------------------------------------
    def get_or_create_season(self, name: str, year_start: int,
                             year_end: int) -> int:
        row = self._conn.execute(
            "SELECT id FROM seasons WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return row["id"]
        cur = self._conn.execute(
            "INSERT INTO seasons (name, year_start, year_end) VALUES (?, ?, ?)",
            (name, year_start, year_end),
        )
        self._conn.commit()
        return cur.lastrowid

    # ------------------------------------------------------------------
    # competition_seasons
    # ------------------------------------------------------------------
    def get_or_create_competition_season(self, competition_id: int,
                                         season_id: int) -> int:
        row = self._conn.execute(
            "SELECT id FROM competition_seasons WHERE competition_id = ? AND season_id = ?",
            (competition_id, season_id),
        ).fetchone()
        if row:
            return row["id"]
        cur = self._conn.execute(
            "INSERT INTO competition_seasons (competition_id, season_id) VALUES (?, ?)",
            (competition_id, season_id),
        )
        self._conn.commit()
        return cur.lastrowid

    # ------------------------------------------------------------------
    # teams
    # ------------------------------------------------------------------
    def get_or_create_team(self, team_id: int, name: str,
                           short_name: str = None,
                           crest_url: str = None) -> int:
        row = self._conn.execute(
            "SELECT id FROM teams WHERE id = ?", (team_id,)
        ).fetchone()
        if row:
            existing = self._conn.execute(
                "SELECT * FROM teams WHERE id = ?", (team_id,)
            ).fetchone()
            if (existing["name"] != name
                    or existing["short_name"] != short_name
                    or existing["crest_url"] != crest_url):
                self._conn.execute(
                    "UPDATE teams SET name = ?, short_name = ?, crest_url = ? WHERE id = ?",
                    (name, short_name, crest_url, team_id),
                )
                self._conn.commit()
            return team_id
        self._conn.execute(
            "INSERT INTO teams (id, name, short_name, crest_url) VALUES (?, ?, ?, ?)",
            (team_id, name, short_name, crest_url),
        )
        self._conn.commit()
        return team_id

    # ------------------------------------------------------------------
    # standings_snapshots
    # ------------------------------------------------------------------
    def store_standings_snapshot(self, competition_season_id: int,
                                 standings_list: list,
                                 snapshot_date: str):
        for entry in standings_list:
            self._conn.execute(
                """INSERT OR REPLACE INTO standings_snapshots
                   (competition_season_id, team_id, snapshot_date,
                    position, played, points, goal_difference, ppg)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    competition_season_id,
                    entry["team_id"],
                    snapshot_date,
                    entry.get("position"),
                    entry.get("played"),
                    entry.get("points"),
                    entry.get("goal_difference"),
                    entry.get("ppg"),
                ),
            )
        self._conn.commit()

    def get_standings_as_of(self, competition_code: str, season_name: str,
                            as_of_date: str) -> dict:
        cursor = self._conn.execute(
            """WITH target AS (
                   SELECT MAX(ss.snapshot_date) AS snapshot_date
                   FROM standings_snapshots ss
                   JOIN competition_seasons cs ON ss.competition_season_id = cs.id
                   JOIN competitions c ON cs.competition_id = c.id
                   JOIN seasons s ON cs.season_id = s.id
                   WHERE c.code = ? AND s.name = ? AND ss.snapshot_date <= ?
               )
               SELECT ss.*, t.name AS team_name
               FROM standings_snapshots ss
               JOIN target ON ss.snapshot_date = target.snapshot_date
               JOIN teams t ON ss.team_id = t.id
               JOIN competition_seasons cs ON ss.competition_season_id = cs.id
               JOIN competitions c ON cs.competition_id = c.id
               JOIN seasons s ON cs.season_id = s.id
               WHERE c.code = ? AND s.name = ?""",
            (competition_code, season_name, as_of_date,
             competition_code, season_name),
        )
        rows = cursor.fetchall()
        return {r["team_id"]: dict(r) for r in rows}

    # ------------------------------------------------------------------
    # matches
    # ------------------------------------------------------------------
    def store_match(self, match_data: dict) -> int:
        existing = self._conn.execute(
            "SELECT * FROM matches WHERE id = ?", (match_data["id"],)
        ).fetchone()
        if existing:
            changed = False
            for key in ("status", "home_score", "away_score", "winner",
                         "matchday", "stage"):
                if existing[key] != match_data.get(key):
                    changed = True
                    break
            if not changed:
                return existing["id"]
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            self._conn.execute(
                """UPDATE matches SET
                     status = ?, home_score = ?, away_score = ?,
                     winner = ?, matchday = ?, stage = ?, updated_at = ?
                   WHERE id = ?""",
                (
                    match_data.get("status", existing["status"]),
                    match_data.get("home_score"),
                    match_data.get("away_score"),
                    match_data.get("winner"),
                    match_data.get("matchday", existing["matchday"]),
                    match_data.get("stage", existing["stage"]),
                    now,
                    match_data["id"],
                ),
            )
            self._conn.commit()
            return existing["id"]

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._conn.execute(
            """INSERT INTO matches
               (id, competition_season_id, matchday, stage, status,
                utc_date, home_team_id, away_team_id,
                home_score, away_score, winner, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                match_data["id"],
                match_data["competition_season_id"],
                match_data.get("matchday"),
                match_data.get("stage"),
                match_data.get("status", "SCHEDULED"),
                match_data["utc_date"],
                match_data["home_team_id"],
                match_data["away_team_id"],
                match_data.get("home_score"),
                match_data.get("away_score"),
                match_data.get("winner"),
                now,
                now,
            ),
        )
        self._conn.commit()
        return match_data["id"]

    def store_matches(self, matches_list: list) -> list:
        return [self.store_match(m) for m in matches_list]

    def get_match(self, match_id: int) -> dict:
        row = self._conn.execute(
            """SELECT m.*, ht.name AS home_team_name, at.name AS away_team_name,
                      c.code AS competition_code, s.name AS season_name
               FROM matches m
               JOIN competition_seasons cs ON m.competition_season_id = cs.id
               JOIN competitions c ON cs.competition_id = c.id
               JOIN seasons s ON cs.season_id = s.id
               JOIN teams ht ON m.home_team_id = ht.id
               JOIN teams at ON m.away_team_id = at.id
               WHERE m.id = ?""",
            (match_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_matches(self, competition_code: str = None, season_name: str = None,
                    status: str = None, from_date: str = None,
                    to_date: str = None, limit: int = None,
                    offset: int = 0) -> list:
        clauses = []
        params = []
        if competition_code:
            clauses.append("c.code = ?")
            params.append(competition_code)
        if season_name:
            clauses.append("s.name = ?")
            params.append(season_name)
        if status:
            clauses.append("m.status = ?")
            params.append(status)
        if from_date:
            clauses.append("m.utc_date >= ?")
            params.append(from_date)
        if to_date:
            clauses.append("m.utc_date <= ?")
            params.append(to_date)

        where = " AND ".join(clauses) if clauses else "1"
        sql = (
            "SELECT m.*, c.code AS competition_code, s.name AS season_name, "
            "ht.name AS home_team_name, at.name AS away_team_name "
            "FROM matches m "
            "JOIN competition_seasons cs ON m.competition_season_id = cs.id "
            "JOIN competitions c ON cs.competition_id = c.id "
            "JOIN seasons s ON cs.season_id = s.id "
            "JOIN teams ht ON m.home_team_id = ht.id "
            "JOIN teams at ON m.away_team_id = at.id "
            f"WHERE {where} ORDER BY m.utc_date"
        )
        if limit:
            sql += f" LIMIT {limit} OFFSET {offset}"
        return [dict(r) for r in self._conn.execute(sql, params)]

    # ------------------------------------------------------------------
    # evaluations
    # ------------------------------------------------------------------
    def store_evaluation(self, match_id: int, engine_version_id: int,
                         eval_data: dict) -> int:
        cur = self._conn.execute(
            """INSERT OR IGNORE INTO evaluations
               (match_id, engine_version_id,
                strength_home_total, strength_home_structural,
                strength_home_context, strength_away_total,
                strength_away_structural, strength_away_context,
                difference, favorite_team_id, selected)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                match_id,
                engine_version_id,
                eval_data["strength_home_total"],
                eval_data["strength_home_structural"],
                eval_data["strength_home_context"],
                eval_data["strength_away_total"],
                eval_data["strength_away_structural"],
                eval_data["strength_away_context"],
                eval_data["difference"],
                eval_data["favorite_team_id"],
                1 if eval_data["selected"] else 0,
            ),
        )
        if cur.rowcount == 0:
            row = self._conn.execute(
                "SELECT id FROM evaluations WHERE match_id = ? AND engine_version_id = ?",
                (match_id, engine_version_id),
            ).fetchone()
            return row["id"]
        self._conn.commit()
        return cur.lastrowid

    def get_evaluations(self, engine_version_id: int = None,
                        competition_code: str = None,
                        season_name: str = None,
                        match_id: int = None,
                        selected_only: bool = False,
                        from_date: str = None,
                        to_date: str = None,
                        limit: int = None,
                        offset: int = 0) -> list:
        clauses = []
        params = []
        if engine_version_id is not None:
            clauses.append("e.engine_version_id = ?")
            params.append(engine_version_id)
        if match_id is not None:
            clauses.append("e.match_id = ?")
            params.append(match_id)
        if competition_code:
            clauses.append("c.code = ?")
            params.append(competition_code)
        if season_name:
            clauses.append("s.name = ?")
            params.append(season_name)
        if selected_only:
            clauses.append("e.selected = 1")
        if from_date:
            clauses.append("m.utc_date >= ?")
            params.append(from_date)
        if to_date:
            clauses.append("m.utc_date <= ?")
            params.append(to_date)

        where = " AND ".join(clauses) if clauses else "1"
        sql = (
            "SELECT e.*, "
            "m.utc_date AS match_date, m.status AS match_status, "
            "m.home_team_id, m.away_team_id, "
            "m.home_score, m.away_score, m.winner AS actual_winner, "
            "ht.name AS home_team_name, at.name AS away_team_name, "
            "ft.name AS favorite_team_name, "
            "ev.version AS engine_version "
            "FROM evaluations e "
            "JOIN matches m ON e.match_id = m.id "
            "JOIN teams ht ON m.home_team_id = ht.id "
            "JOIN teams at ON m.away_team_id = at.id "
            "JOIN teams ft ON e.favorite_team_id = ft.id "
            "JOIN engine_versions ev ON e.engine_version_id = ev.id "
            "JOIN competition_seasons cs ON m.competition_season_id = cs.id "
            "JOIN competitions c ON cs.competition_id = c.id "
            "JOIN seasons s ON cs.season_id = s.id "
            f"WHERE {where} ORDER BY m.utc_date"
        )
        if limit:
            sql += f" LIMIT {limit} OFFSET {offset}"

        results = []
        for r in self._conn.execute(sql, params):
            d = dict(r)
            if d["actual_winner"] == "HOME_TEAM":
                d["actual_winner_name"] = d["home_team_name"]
            elif d["actual_winner"] == "AWAY_TEAM":
                d["actual_winner_name"] = d["away_team_name"]
            elif d["actual_winner"] == "DRAW":
                d["actual_winner_name"] = "DRAW"
            else:
                d["actual_winner_name"] = None

            if d["selected"] and d["actual_winner"] and d["actual_winner"] != "":
                if d["actual_winner"] == "HOME_TEAM":
                    winner_id = d["home_team_id"]
                elif d["actual_winner"] == "AWAY_TEAM":
                    winner_id = d["away_team_id"]
                else:
                    winner_id = None
                d["correct"] = 1 if winner_id and winner_id == d["favorite_team_id"] else 0
            else:
                d["correct"] = None
            results.append(d)
        return results

    # ------------------------------------------------------------------
    # teams
    # ------------------------------------------------------------------
    def get_team(self, team_id: int) -> dict:
        row = self._conn.execute(
            "SELECT * FROM teams WHERE id = ?", (team_id,)
        ).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # system_metadata
    # ------------------------------------------------------------------
    def set_metadata(self, key: str, value: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO system_metadata (key, value) VALUES (?, ?)",
            (key, value),
        )
        self._conn.commit()

    def get_metadata(self, key: str) -> str:
        row = self._conn.execute(
            "SELECT value FROM system_metadata WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    # ------------------------------------------------------------------
    # system status
    # ------------------------------------------------------------------
    def get_system_status(self) -> dict:
        ev = self._conn.execute(
            "SELECT * FROM engine_versions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        engine = dict(ev) if ev else None

        last_sync = self.get_metadata("last_sync")
        engine_id = engine["id"] if engine else -1

        counts = self._conn.execute(
            """SELECT
                   (SELECT COUNT(*) FROM matches) AS matches,
                   (SELECT COUNT(*) FROM teams) AS teams,
                   (SELECT COUNT(*) FROM competitions) AS competitions,
                   (SELECT COUNT(*) FROM matches WHERE id NOT IN (SELECT match_id FROM evaluations WHERE engine_version_id = ?)) AS pending""",
            (engine_id,)
        ).fetchone()

        current_season = self._conn.execute(
            """SELECT s.name FROM seasons s
               JOIN competition_seasons cs ON cs.season_id = s.id
               ORDER BY s.year_start DESC LIMIT 1"""
        ).fetchone()
        season_name = current_season["name"] if current_season else None

        return {
            "engine": {
                "version": engine["version"] if engine else None,
                "structural_weight": engine["structural_weight"] if engine else None,
                "context_weight": engine["context_weight"] if engine else None,
                "min_difference": engine["min_difference"] if engine else None,
            } if engine else None,
            "data": {
                "last_sync": last_sync,
                "matches": counts["matches"],
                "teams": counts["teams"],
                "competitions": counts["competitions"],
                "pending_matches": counts["pending"],
                "current_season": season_name,
            },
            "status": "ready" if engine else "no_engine",
        }

    # ------------------------------------------------------------------
    # benchmark
    # ------------------------------------------------------------------
    def get_benchmark(self, competition_code: str = None,
                      season_name: str = None,
                      engine_version: str = None) -> dict:
        clauses = ["e.selected = 1"]
        params = []
        if competition_code:
            clauses.append("c.code = ?")
            params.append(competition_code)
        if season_name:
            clauses.append("s.name = ?")
            params.append(season_name)
        if engine_version:
            clauses.append("ev.version = ?")
            params.append(engine_version)

        where = " AND ".join(clauses)

        correct_expr = (
            "CASE WHEN m.winner = 'HOME_TEAM' AND e.favorite_team_id = m.home_team_id THEN 1 "
            "     WHEN m.winner = 'AWAY_TEAM' AND e.favorite_team_id = m.away_team_id THEN 1 "
            "     ELSE 0 END"
        )

        base = (
            "FROM evaluations e "
            "JOIN matches m ON e.match_id = m.id "
            "JOIN engine_versions ev ON e.engine_version_id = ev.id "
            "JOIN competition_seasons cs ON m.competition_season_id = cs.id "
            "JOIN competitions c ON cs.competition_id = c.id "
            "JOIN seasons s ON cs.season_id = s.id "
            f"WHERE {where}"
        )

        total_row = self._conn.execute(
            f"SELECT COUNT(*) AS total, SUM({correct_expr}) AS correct {base}", params
        ).fetchone()
        total = total_row["total"] or 0
        correct = total_row["correct"] or 0

        all_matches = self._conn.execute(
            "SELECT COUNT(*) AS total FROM matches"
        ).fetchone()["total"] or 0

        home_wins = self._conn.execute(
            "SELECT COUNT(*) AS cnt FROM matches WHERE winner = 'HOME_TEAM'"
        ).fetchone()["cnt"] or 0

        baseline = round(home_wins / all_matches, 4) if all_matches else 0.0
        accuracy = round(correct / total, 4) if total else 0.0

        diff_ranges = [
            ("20-29", 20, 29),
            ("30-39", 30, 39),
            ("40-49", 40, 49),
            ("50+", 50, 999),
        ]
        by_range = []
        for label, lo, hi in diff_ranges:
            row = self._conn.execute(
                f"SELECT COUNT(*) AS cnt, SUM({correct_expr}) AS ok {base} AND e.difference >= ? AND e.difference <= ?",
                params + [lo, hi],
            ).fetchone()
            cnt = row["cnt"] or 0
            by_range.append({
                "range": label,
                "matches": cnt,
                "correct": row["ok"] or 0,
                "accuracy": round(row["ok"] / cnt, 4) if cnt else 0.0,
            })

        by_comp = []
        comp_rows = self._conn.execute(
            f"SELECT c.code, COUNT(*) AS cnt, SUM({correct_expr}) AS ok {base} GROUP BY c.code ORDER BY cnt DESC",
            params,
        )
        for r in comp_rows:
            cnt = r["cnt"] or 0
            by_comp.append({
                "competition_code": r["code"],
                "matches": cnt,
                "correct": r["ok"] or 0,
                "accuracy": round(r["ok"] / cnt, 4) if cnt else 0.0,
            })

        by_season = []
        seas_rows = self._conn.execute(
            f"SELECT s.name, COUNT(*) AS cnt, SUM({correct_expr}) AS ok {base} GROUP BY s.name ORDER BY COUNT(*) DESC",
            params,
        )
        for r in seas_rows:
            cnt = r["cnt"] or 0
            by_season.append({
                "season_name": r["name"],
                "matches": cnt,
                "correct": r["ok"] or 0,
                "accuracy": round(r["ok"] / cnt, 4) if cnt else 0.0,
            })

        evaluated = self._conn.execute(
            f"SELECT COUNT(*) AS cnt {base.replace('e.selected = 1', '1')}", params
        ).fetchone()["cnt"] or 0

        return {
            "totals": {
                "evaluated": evaluated,
                "selected": total,
                "coverage": round(total / evaluated, 4) if evaluated else 0.0,
                "correct": correct,
                "accuracy": accuracy,
                "baseline_home": baseline,
                "vs_baseline": round(accuracy - baseline, 4) if accuracy else 0.0,
            },
            "by_difference_range": by_range,
            "by_competition": by_comp,
            "by_season": by_season,
        }

    def get_team_history(self, team_id: int) -> list:
        rows = self._conn.execute(
            """SELECT s.name AS season_name, c.code AS competition_code,
                      ss.position, ss.played, ss.points,
                      ss.goal_difference, ss.ppg, ss.snapshot_date
               FROM standings_snapshots ss
               JOIN competition_seasons cs ON ss.competition_season_id = cs.id
               JOIN competitions c ON cs.competition_id = c.id
               JOIN seasons s ON cs.season_id = s.id
               WHERE ss.team_id = ?
                 AND ss.snapshot_date = (
                     SELECT MAX(ss2.snapshot_date)
                     FROM standings_snapshots ss2
                     WHERE ss2.competition_season_id = ss.competition_season_id
                       AND ss2.team_id = ss.team_id
                 )
               ORDER BY s.year_start""",
            (team_id,),
        )
        return [dict(r) for r in rows]
