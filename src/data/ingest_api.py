import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from .store import ScouterDB
from scraper import get_standings as _api_standings, get_matches as _api_matches


LEAGUES = ["PL", "BL1", "PD", "SA", "FL1"]


def _detect_season_label(utc_date: str = None) -> str:
    if utc_date:
        dt = datetime.strptime(utc_date[:10], "%Y-%m-%d")
    else:
        dt = datetime.now(timezone.utc)
    if dt.month >= 8:
        start = dt.year
    else:
        start = dt.year - 1
    return f"{start}/{start + 1}"


def _extract_season_year(season_label: str) -> int:
    return int(season_label.split("/")[0])


def ingest_api_standings(db: ScouterDB, competition_code: str,
                         season_label: str = None) -> int:
    if season_label is None:
        season_label = _detect_season_label()
    season_year = _extract_season_year(season_label)

    cid = db.get_or_create_competition(competition_code)
    sid = db.get_or_create_season(season_label, season_year, season_year + 1)
    csid = db.get_or_create_competition_season(cid, sid)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    standings_data = _api_standings(competition_code)
    if not standings_data:
        return 0

    standings_list = []
    for team_id, entry in standings_data.items():
        db.get_or_create_team(team_id, entry["name"])
        standings_list.append({
            "team_id": team_id,
            "position": entry["position"],
            "played": entry["played"],
            "points": entry["points"],
            "goal_difference": entry["goal_difference"],
            "ppg": entry["ppg"],
        })

    db.store_standings_snapshot(csid, standings_list, today_str)
    return len(standings_list)


def ingest_api_matches(db: ScouterDB, competition_code: str,
                       window_hours: int = None) -> int:
    matches = _api_matches(window_hours=window_hours)
    comp_matches = [m for m in matches
                    if m["competition_code"] == competition_code]
    if not comp_matches:
        return 0

    cid = db.get_or_create_competition(competition_code)
    processed = 0
    for m in comp_matches:
        season_label = _detect_season_label(m["date"])
        season_year = _extract_season_year(season_label)
        sid = db.get_or_create_season(season_label, season_year,
                                       season_year + 1)
        csid = db.get_or_create_competition_season(cid, sid)
        db.get_or_create_team(m["home_id"], m["home_team"])
        db.get_or_create_team(m["away_id"], m["away_team"])
        db.store_match({
            "id": int(m["id"]),
            "competition_season_id": csid,
            "matchday": m.get("matchday"),
            "stage": m.get("stage", "REGULAR_SEASON"),
            "status": "SCHEDULED",
            "utc_date": m["date"],
            "home_team_id": m["home_id"],
            "away_team_id": m["away_id"],
        })
        processed += 1
    return processed


def _next_season_label() -> str:
    """Return the season label for upcoming matches (1 month offset)."""
    from datetime import timedelta
    return _detect_season_label((datetime.now(timezone.utc) + timedelta(days=30)).isoformat())


def ingest_api_all(db: ScouterDB) -> dict:
    results = {}
    season_label = _next_season_label()
    for code in LEAGUES:
        st = ingest_api_standings(db, code, season_label)
        mt = ingest_api_matches(db, code, window_hours=8760)
        results[code] = {"standings": st, "matches": mt}
    return results
