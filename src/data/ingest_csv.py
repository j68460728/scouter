import csv
import hashlib
import os
from datetime import datetime

import requests

from .store import ScouterDB

CSV_BASE = "https://www.football-data.co.uk/mmz4281"
CSV_LEAGUE_MAP = {
    "PL": "E0", "BL1": "D1", "PD": "SP1", "SA": "I1", "FL1": "F1",
}
SEASON_CODES = {}
for year in range(2020, 2030):
    code = f"{str(year)[2:]}{str(year+1)[2:]}"
    SEASON_CODES[str(year)] = code


def _csv_team_id(name: str) -> int:
    raw = hashlib.md5(name.encode()).hexdigest()[:12]
    return -(int(raw, 16) % (2**31 - 1))


def _csv_match_id(season_code: str, home: str, away: str,
                  date_str: str) -> int:
    raw = f"{season_code}|{home}|{away}|{date_str}"
    digest = hashlib.md5(raw.encode()).hexdigest()[:12]
    return -(int(digest, 16) % (2**31 - 1))


def _detect_season_name(season_year: str) -> str:
    y = int(season_year)
    return f"{y}/{y + 1}"


def _parse_date(date_str: str, time_str: str = "") -> str:
    dt_str = f"{date_str.strip()} {time_str.strip()}" if time_str.strip() else date_str.strip()
    for fmt in ["%d/%m/%y %H:%M", "%d/%m/%Y %H:%M", "%d/%m/%y", "%d/%m/%Y"]:
        try:
            dt = datetime.strptime(dt_str, fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return None


def ingest_csv_season(db: ScouterDB, csv_source: str,
                      competition_code: str, season_year: str) -> dict:
    csv_code = CSV_LEAGUE_MAP.get(competition_code)
    if not csv_code:
        raise ValueError(f"Unknown competition code: {competition_code}")
    season_code = SEASON_CODES.get(season_year)
    if not season_code:
        raise ValueError(f"Unknown season year: {season_year}")
    season_name = _detect_season_name(season_year)

    if csv_source.startswith("http://") or csv_source.startswith("https://"):
        resp = requests.get(csv_source, timeout=30)
        if resp.status_code != 200:
            raise IOError(f"Failed to download CSV: {resp.status_code}")
        raw = resp.content.decode("utf-8-sig").strip().splitlines()
    elif os.path.isfile(csv_source):
        with open(csv_source, encoding="utf-8-sig") as f:
            raw = f.read().strip().splitlines()
    else:
        url = f"{CSV_BASE}/{season_code}/{csv_code}.csv"
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            raise IOError(f"Failed to download CSV from {url}: {resp.status_code}")
        raw = resp.content.decode("utf-8-sig").strip().splitlines()

    reader = csv.DictReader(raw)
    cid = db.get_or_create_competition(competition_code)
    sid = db.get_or_create_season(season_name, int(season_year),
                                   int(season_year) + 1)
    csid = db.get_or_create_competition_season(cid, sid)

    matches = []
    teams_created = set()
    for row in reader:
        try:
            date_str = row.get("Date", "").strip()
            time_str = row.get("Time", "").strip()
            utc_date = _parse_date(date_str, time_str)
            if not utc_date:
                continue
            home = row["HomeTeam"].strip()
            away = row["AwayTeam"].strip()
            hg = int(row.get("FTHG", 0) or 0)
            ag = int(row.get("FTAG", 0) or 0)
        except (ValueError, KeyError):
            continue

        home_id = _csv_team_id(home)
        away_id = _csv_team_id(away)
        match_id = _csv_match_id(season_code, home, away, utc_date)

        db.get_or_create_team(home_id, home)
        db.get_or_create_team(away_id, away)
        teams_created.add(home_id)
        teams_created.add(away_id)

        winner = None
        if hg > ag:
            winner = "HOME_TEAM"
        elif ag > hg:
            winner = "AWAY_TEAM"
        elif hg == ag:
            winner = "DRAW"

        db.store_match({
            "id": match_id,
            "competition_season_id": csid,
            "matchday": None,
            "stage": "REGULAR_SEASON",
            "status": "FINISHED",
            "utc_date": utc_date,
            "home_team_id": home_id,
            "away_team_id": away_id,
            "home_score": hg,
            "away_score": ag,
            "winner": winner,
        })
        matches.append({
            "match_id": match_id,
            "utc_date": utc_date,
        })

    matches.sort(key=lambda m: m["utc_date"])
    dates = sorted(set(m["utc_date"][:10] for m in matches))

    snapshots_created = 0
    for date_prefix in dates:
        last_match_date = max(m["utc_date"] for m in matches
                              if m["utc_date"].startswith(date_prefix))
        matches_up_to = [m for m in matches
                         if m["utc_date"] <= last_match_date]
        standings = _compute_standings_from_matches(db, csid, matches_up_to)
        if standings:
            db.store_standings_snapshot(csid, standings, date_prefix)
            snapshots_created += 1

    return {
        "teams": len(teams_created),
        "matches": len(matches),
        "snapshots": snapshots_created,
    }


def _compute_standings_from_matches(db: ScouterDB, csid: int,
                                    match_list: list) -> list:
    standings = {}
    for m in match_list:
        row = db.get_match(m["match_id"])
        if not row:
            continue
        hid, aid = row["home_team_id"], row["away_team_id"]
        hg, ag = row["home_score"] or 0, row["away_score"] or 0

        for team_id, gf, ga in [(hid, hg, ag), (aid, ag, hg)]:
            if team_id not in standings:
                t = db.get_team(team_id)
                standings[team_id] = {
                    "team_id": team_id,
                    "name": t["name"] if t else str(team_id),
                    "position": 0,
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

    sorted_teams = sorted(
        standings.values(),
        key=lambda x: (-x["points"], -x["goal_difference"])
    )
    for idx, s in enumerate(sorted_teams, 1):
        s["position"] = idx
        s["ppg"] = round(s["points"] / s["played"], 4) if s["played"] else 0.0

    return sorted_teams
