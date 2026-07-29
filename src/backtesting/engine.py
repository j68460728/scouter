import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from strength_profile import build_match, _load_matrix
from backtesting.historical_data import load_csv_data, compute_standings, get_recent_for_team

LEAGUES = ["PL", "BL1", "PD", "SA", "FL1"]
SEASONS = ["2023", "2024"]

_RESULT_CACHE = {}

def _load_season(league_code, season_year):
    key = (league_code, season_year)
    if key not in _RESULT_CACHE:
        _RESULT_CACHE[key] = load_csv_data(league_code, season_year)
    return _RESULT_CACHE[key]

def run_backtest(min_diff=None):
    matrix = _load_matrix()
    if min_diff is None:
        min_diff = matrix.get('confidence', {}).get('min_difference', 15)
    rows = []

    for league_code in LEAGUES:
        for season_year in SEASONS:
            all_matches = _load_season(league_code, season_year)
            if not all_matches:
                continue

            print(f"[Backtest] Processing {league_code} {season_year}/{int(season_year)+1} — {len(all_matches)} matches")

            for i, match in enumerate(all_matches):
                before = all_matches[:i]
                standings = compute_standings(before)

                team_results = {}
                for tid in [match['homeTeam']['id'], match['awayTeam']['id']]:
                    team_results[tid] = []

                match_eval = {
                    "home_team": match['homeTeam']['name'],
                    "home_id": match['homeTeam']['id'],
                    "away_team": match['awayTeam']['name'],
                    "away_id": match['awayTeam']['id'],
                    "competition_code": league_code,
                    "date": match['utcDate'],
                    "stage": match.get('stage', 'REGULAR_SEASON'),
                }

                home, away = build_match(match_eval, standings, team_results, matrix)
                diff = round(abs(home['total'] - away['total']), 1)
                favorite = match['homeTeam']['name'] if home['total'] >= away['total'] else match['awayTeam']['name']
                selected = diff >= min_diff

                ft = match.get('score', {}).get('fullTime', {})
                hg = ft.get('home', 0) or 0
                ag = ft.get('away', 0) or 0
                if hg > ag:
                    actual_winner = match['homeTeam']['name']
                    actual_code = "home"
                elif ag > hg:
                    actual_winner = match['awayTeam']['name']
                    actual_code = "away"
                else:
                    actual_winner = "draw"
                    actual_code = "draw"

                correct = None
                if selected:
                    correct = 1 if favorite == actual_winner else 0

                rows.append({
                    "match_id": match['id'],
                    "league": league_code,
                    "season": season_year,
                    "date": match['utcDate'],
                    "matchday": match.get('matchday', 0),
                    "home_team": match['homeTeam']['name'],
                    "away_team": match['awayTeam']['name'],
                    "home_strength": home['total'],
                    "away_strength": away['total'],
                    "difference": diff,
                    "favorite": favorite,
                    "selected": selected,
                    "actual_winner": actual_winner,
                    "actual_code": actual_code,
                    "correct": correct,
                })

    return rows

def save_results(rows, path=None):
    if path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"backtest_results_{ts}.json"
    with open(path, "w") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"[Backtest] {len(rows)} results saved to {path}")
    return path
