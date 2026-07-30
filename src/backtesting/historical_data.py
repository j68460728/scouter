import csv
import os
import sys
from datetime import datetime

import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

CSV_BASE = "https://www.football-data.co.uk/mmz4281"

CSV_LEAGUE_MAP = {
    "PL": "E0",
    "BL1": "D1",
    "PD": "SP1",
    "SA": "I1",
    "FL1": "F1",
}

SEASON_CODES = {
    "2023": "2324",
    "2024": "2425",
}

def _season_label(season_year):
    return f"{season_year}/{int(season_year) + 1}"

def load_csv_data(league_code, season_year):
    csv_code = CSV_LEAGUE_MAP[league_code]
    season_code = SEASON_CODES[season_year]
    url = f"{CSV_BASE}/{season_code}/{csv_code}.csv"

    print(f"[Backtest] Loading {league_code} {_season_label(season_year)} from CSV...", file=sys.stderr)
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        print(f"[Backtest]   Error {resp.status_code} for {url}", file=sys.stderr)
        return []

    raw = resp.content.decode("utf-8-sig").strip().splitlines()
    reader = csv.DictReader(raw)

    matches = []
    for row in reader:
        try:
            date_str = row["Date"].strip()
            time_str = row.get("Time", "").strip()
            dt_str = f"{date_str} {time_str}" if time_str else date_str

            for fmt in ["%d/%m/%y %H:%M", "%d/%m/%Y %H:%M", "%d/%m/%y", "%d/%m/%Y"]:
                try:
                    dt = datetime.strptime(dt_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                continue

            hg = int(row["FTHG"])
            ag = int(row["FTAG"])
            home = row["HomeTeam"].strip()
            away = row["AwayTeam"].strip()

            matches.append({
                "id": f"{csv_code}_{season_code}_{len(matches)}",
                "utcDate": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "homeTeam": {"id": home, "name": home},
                "awayTeam": {"id": away, "name": away},
                "score": {"fullTime": {"home": hg, "away": ag}},
                "stage": "REGULAR_SEASON",
                "competition_code": league_code,
                "matchday": len(matches) // 10 + 1,
            })
        except (ValueError, KeyError):
            continue

    matches.sort(key=lambda m: m["utcDate"])
    print(f"[Backtest]   {len(matches)} matches loaded", file=sys.stderr)
    return matches


def compute_standings(matches_before):
    standings = {}
    for m in matches_before:
        hid = m["homeTeam"]["id"]
        aid = m["awayTeam"]["id"]
        ft = m.get("score", {}).get("fullTime", {})
        hg = ft.get("home", 0) or 0
        ag = ft.get("away", 0) or 0

        for team_id, name, gf, ga in [
            (hid, m["homeTeam"]["name"], hg, ag),
            (aid, m["awayTeam"]["name"], ag, hg),
        ]:
            if team_id not in standings:
                standings[team_id] = {
                    "id": team_id,
                    "name": name,
                    "points": 0,
                    "played": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "goal_difference": 0,
                }
            s = standings[team_id]
            s["played"] += 1
            s["goals_for"] += gf
            s["goals_against"] += ga
            s["goal_difference"] = s["goals_for"] - s["goals_against"]
            if gf > ga:
                s["points"] += 3
            elif gf == ga:
                s["points"] += 1

    for s in standings.values():
        s["ppg"] = s["points"] / s["played"] if s["played"] > 0 else 0.0

    return standings


def get_recent_for_team(matches_before, team_id, window=6):
    team_matches = [
        m
        for m in matches_before
        if m["homeTeam"]["id"] == team_id or m["awayTeam"]["id"] == team_id
    ]
    return team_matches[-window:]
