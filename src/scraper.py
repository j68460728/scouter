import requests
import os
import time
from datetime import datetime, timedelta
from config import BASE_URL, API_KEY, LEAGUES

def get_matches(window_hours=None):
    all_matches = []
    
    # Define optional window
    now = datetime.utcnow()
    window_end = None
    if window_hours is not None:
        window_end = now + timedelta(hours=window_hours)
        print(f"[Scouter] Filtro activo: ventana de {window_hours} horas desde ahora")
    else:
        print("[Scouter] Sin filtro de ventana: se traerán todos los partidos disponibles")
    
    headers = {'X-Auth-Token': API_KEY}
    
    for league_code, league_name in LEAGUES.items():
        url = f"{BASE_URL}/competitions/{league_code}/matches"
        print(f"[Scouter] Consultando {league_name}...")
        
        # Respetar rate limit de 10 req/min
        time.sleep(10)

        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 429:
                # Rate limit excedido: esperar según lo indicado por la API
                import re
                match = re.search(r'Wait (\d+) seconds', response.text)
                wait = int(match.group(1)) + 2 if match else 60
                print(f"[Scouter] Límite alcanzado. Esperando {wait}s...")
                time.sleep(wait)
                response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"[Scouter] Error {response.status_code} para {league_name}: {response.text}")
                continue
                
            data = response.json()
            matches = data.get('matches', [])
            
            for match in matches:
                match_date = datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ')
                
                # Si hay ventana definida, filtrar; si no, incluir todos
                if window_end is None or (now <= match_date <= window_end):
                    all_matches.append({
                        "id": str(match['id']),
                        "home_team": match['homeTeam']['name'],
                        "away_team": match['awayTeam']['name'],
                        "competition": league_name,
                        "date": match['utcDate']
                    })
                    
        except Exception as e:
            print(f"[Scouter] Error procesando {league_name}: {e}")
            
    return all_matches
