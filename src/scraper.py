import requests
import os
import time
import re
from datetime import datetime, timedelta
from config import BASE_URL, API_KEY, LEAGUES, RATE_LIMIT_DELAY

_cache = {}
_cache_time = {}

def _request(url, headers=None, cache_ttl=60):
    if headers is None:
        headers = {'X-Auth-Token': API_KEY}
    cache_key = url
    now = time.time()
    if cache_key in _cache and now - _cache_time.get(cache_key, 0) < cache_ttl:
        return _cache[cache_key]
    time.sleep(RATE_LIMIT_DELAY)
    response = requests.get(url, headers=headers)
    if response.status_code == 429:
        match = re.search(r'Wait (\d+) seconds', response.text)
        wait = int(match.group(1)) + 2 if match else 60
        print(f"[Scouter] Límite alcanzado. Esperando {wait}s...")
        time.sleep(wait)
        response = requests.get(url, headers=headers)
    if response.status_code == 200:
        _cache[cache_key] = response
        _cache_time[cache_key] = now
    return response

def get_matches(window_hours=None):
    all_matches = []
    
    now = datetime.utcnow()
    window_end = None
    if window_hours is not None:
        window_end = now + timedelta(hours=window_hours)
        print(f"[Scouter] Filtro activo: ventana de {window_hours} horas desde ahora")
    else:
        print("[Scouter] Sin filtro de ventana: se traerán todos los partidos disponibles")
    
    for league_code, league_name in LEAGUES.items():
        url = f"{BASE_URL}/competitions/{league_code}/matches"
        print(f"[Scouter] Consultando {league_name}...")
        
        try:
            response = _request(url)
            
            if response.status_code != 200:
                print(f"[Scouter] Error {response.status_code} para {league_name}: {response.text}")
                continue
                
            data = response.json()
            matches = data.get('matches', [])
            
            for match in matches:
                match_date = datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ')
                
                if window_end is None or (now <= match_date <= window_end):
                    all_matches.append({
                        "id": str(match['id']),
                        "home_team": match['homeTeam']['name'],
                        "home_id": match['homeTeam']['id'],
                        "away_team": match['awayTeam']['name'],
                        "away_id": match['awayTeam']['id'],
                        "competition": league_name,
                        "competition_code": league_code,
                        "date": match['utcDate'],
                        "matchday": match.get('matchday', 0),
                        "stage": match.get('stage', 'REGULAR_SEASON')
                    })
                    
        except Exception as e:
            print(f"[Scouter] Error procesando {league_name}: {e}")
            
    return all_matches

def get_standings(league_code):
    url = f"{BASE_URL}/competitions/{league_code}/standings"
    response = _request(url)
    if response.status_code != 200:
        return {}
    data = response.json()
    standings = {}
    for group in data.get('standings', []):
        for entry in group.get('table', []):
            team_id = entry['team']['id']
            standings[team_id] = {
                'id': team_id,
                'name': entry['team']['name'],
                'position': entry['position'],
                'played': entry['playedGames'],
                'points': entry['points'],
                'goal_difference': entry.get('goalDifference', 0),
                'goals_for': entry.get('goalsFor', 0),
                'goals_against': entry.get('goalsAgainst', 0),
                'ppg': entry['points'] / entry['playedGames'] if entry['playedGames'] > 0 else 0.0
            }
    return standings

def get_recent_results(team_id, limit=6):
    url = f"{BASE_URL}/teams/{team_id}/matches?status=FINISHED&limit={limit}"
    response = _request(url)
    if response.status_code != 200:
        return []
    data = response.json()
    return data.get('matches', [])[:limit]

def get_competition_results(league_code, limit=200):
    url = f"{BASE_URL}/competitions/{league_code}/matches?status=FINISHED&limit={limit}"
    response = _request(url)
    if response.status_code != 200:
        return []
    data = response.json()
    return data.get('matches', [])
