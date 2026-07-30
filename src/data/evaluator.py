import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from .store import ScouterDB, compute_config_hash
from strength_profile import build_match, _load_matrix


def _compute_standings(match_rows):
    """Reconstruct standings from match rows ordered chronologically.
    Each row must have: home_team_id, away_team_id, home_score, away_score.
    Returns dict[team_id → {name, played, points, goal_difference, ppg}]."""
    standings = {}
    for m in match_rows:
        hid, aid = m["home_team_id"], m["away_team_id"]
        hg, ag = (m["home_score"] or 0), (m["away_score"] or 0)
        for team_id, gf, ga, name in [
            (hid, hg, ag, m.get("home_team_name", str(hid))),
            (aid, ag, hg, m.get("away_team_name", str(aid))),
        ]:
            if team_id not in standings:
                standings[team_id] = {
                    "name": name,
                    "played": 0,
                    "points": 0,
                    "goal_difference": 0,
                    "ppg": 0.0,
                }
            s = standings[team_id]
            s["played"] += 1
            s["goal_difference"] += gf - ga
            if gf > ga:
                s["points"] += 3
            elif gf == ga:
                s["points"] += 1
    for s in standings.values():
        s["ppg"] = round(s["points"] / s["played"], 4) if s["played"] else 0.0
    return standings


def _match_to_engine_dict(match_row):
    return {
        "home_team": match_row.get("home_team_name", ""),
        "home_id": match_row["home_team_id"],
        "away_team": match_row.get("away_team_name", ""),
        "away_id": match_row["away_team_id"],
        "competition_code": match_row.get("competition_code", ""),
        "date": match_row["utc_date"],
        "stage": match_row.get("stage", "REGULAR_SEASON"),
    }


class EvaluationRunner:
    def __init__(self, db: ScouterDB, matrix: dict = None):
        self.db = db
        self.matrix = matrix if matrix is not None else _load_matrix()
        self._ev_id = None

    def _ensure_engine_version(self) -> int:
        if self._ev_id is not None:
            return self._ev_id
        config_hash = compute_config_hash(self.matrix)
        w = self.matrix["weights"]
        cfg = {
            "version": "v2.0",
            "config_hash": config_hash,
            "structural_weight": w["structural"]["weight"],
            "context_weight": w["context"]["weight"],
            "min_difference": self.matrix["confidence"]["min_difference"],
            "description": "Scouter Engine v2 — Structural + Context only",
        }
        self._ev_id = self.db.register_engine_version(cfg)
        return self._ev_id

    def _store_eval(self, match_id, home, away, diff, fav_id, selected):
        self.db.store_evaluation(match_id, self._ev_id, {
            "strength_home_total": home["total"],
            "strength_home_structural": home["structural"],
            "strength_home_context": home["context"],
            "strength_away_total": away["total"],
            "strength_away_structural": away["structural"],
            "strength_away_context": away["context"],
            "difference": diff,
            "favorite_team_id": fav_id,
            "selected": selected,
        })

    def evaluate_all_pending(self) -> int:
        ev_id = self._ensure_engine_version()
        rows = self.db.conn.execute("""
            SELECT m.id, m.home_team_id, m.away_team_id,
                   m.utc_date, m.stage,
                   ht.name AS home_team_name,
                   at.name AS away_team_name,
                   c.code AS competition_code,
                   s.name AS season_name
            FROM matches m
            JOIN competition_seasons cs ON m.competition_season_id = cs.id
            JOIN competitions c ON cs.competition_id = c.id
            JOIN seasons s ON cs.season_id = s.id
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE m.id NOT IN (
                SELECT match_id FROM evaluations
                WHERE engine_version_id = ?
            )
            ORDER BY m.utc_date
        """, (ev_id,))
        count = 0
        for r in rows:
            m = dict(r)
            standings = self.db.get_standings_as_of(
                m["competition_code"], m["season_name"], m["utc_date"][:10]
            )
            home, away = build_match(
                _match_to_engine_dict(m), standings, {}, self.matrix
            )
            min_diff = self.matrix["confidence"]["min_difference"]
            diff = round(abs(home["total"] - away["total"]), 1)
            fav_id = m["home_team_id"] if home["total"] >= away["total"] else m["away_team_id"]
            selected = diff >= min_diff
            self._store_eval(m["id"], home, away, diff, fav_id, selected)
            count += 1
        return count

    def evaluate_season(self, competition_code: str,
                        season_name: str) -> int:
        rows = self.db.conn.execute("""
            SELECT m.id, m.home_team_id, m.away_team_id,
                   m.utc_date, m.stage,
                   m.home_score, m.away_score, m.winner,
                   ht.name AS home_team_name,
                   at.name AS away_team_name
            FROM matches m
            JOIN competition_seasons cs ON m.competition_season_id = cs.id
            JOIN competitions c ON cs.competition_id = c.id
            JOIN seasons s ON cs.season_id = s.id
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE c.code = ? AND s.name = ?
            ORDER BY m.utc_date
        """, (competition_code, season_name))

        all_matches = [dict(r) for r in rows]
        self._ensure_engine_version()
        count = 0

        for i, m in enumerate(all_matches):
            before = all_matches[:i]
            standings = _compute_standings(before)
            em = _match_to_engine_dict(m)
            em["competition_code"] = competition_code
            home, away = build_match(em, standings, {}, self.matrix)
            min_diff = self.matrix["confidence"]["min_difference"]
            diff = round(abs(home["total"] - away["total"]), 1)
            fav_id = m["home_team_id"] if home["total"] >= away["total"] else m["away_team_id"]
            selected = diff >= min_diff
            self._store_eval(m["id"], home, away, diff, fav_id, selected)
            count += 1
        return count

    def evaluate_match(self, match_id: int) -> dict:
        row = self.db.conn.execute("""
            SELECT m.id, m.home_team_id, m.away_team_id,
                   m.utc_date, m.stage,
                   ht.name AS home_team_name,
                   at.name AS away_team_name,
                   c.code AS competition_code,
                   s.name AS season_name
            FROM matches m
            JOIN competition_seasons cs ON m.competition_season_id = cs.id
            JOIN competitions c ON cs.competition_id = c.id
            JOIN seasons s ON cs.season_id = s.id
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE m.id = ?
        """, (match_id,))
        m = row.fetchone()
        if not m:
            return None
        m = dict(m)
        self._ensure_engine_version()
        standings = self.db.get_standings_as_of(
            m["competition_code"], m["season_name"], m["utc_date"][:10]
        )
        home, away = build_match(
            _match_to_engine_dict(m), standings, {}, self.matrix
        )
        min_diff = self.matrix["confidence"]["min_difference"]
        diff = round(abs(home["total"] - away["total"]), 1)
        fav_id = m["home_team_id"] if home["total"] >= away["total"] else m["away_team_id"]
        selected = diff >= min_diff
        self._store_eval(m["id"], home, away, diff, fav_id, selected)
        return {
            "match_id": match_id,
            "home_strength": home,
            "away_strength": away,
            "difference": diff,
            "favorite_team_id": fav_id,
            "selected": selected,
        }
