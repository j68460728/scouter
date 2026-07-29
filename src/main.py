import argparse
import os
import sys

from scraper import get_matches, get_standings, get_competition_results
from evaluator_strength import evaluate_matches
from evaluator_ai import evaluate_matches_with_ai
from reporter import generate_report
from config import GSR_MATCHES

def parse_window(value):
    if value is None:
        return None
    value = value.strip()
    if value.endswith('h'):
        return int(value[:-1])
    elif value.endswith('d'):
        return int(value[:-1]) * 24
    else:
        return int(value) * 24

def main():
    parser = argparse.ArgumentParser(description="Scouter Engine")
    parser.add_argument("--mode", choices=["rules", "ai"], required=True, help="Modo: rules (motor de fuerza determinista) o ai")
    parser.add_argument("--window", type=str, default=None, help="Ventana de tiempo. Ej: 7d, 24h. Por defecto: días. Sin el parámetro: todos los partidos.")
    
    args = parser.parse_args()
    window_hours = parse_window(args.window)
    
    print(f"[Scouter] Iniciando Motor de Análisis Competitivo en modo: {args.mode.upper()}...")
    
    # 1. Recolección
    print("[Scouter] Consultando fuentes y obteniendo partidos...")
    matches = get_matches(window_hours=window_hours)
    print(f"[Scouter] Se encontraron {len(matches)} partidos.")
    
    if not matches:
        print("[Scouter] No hay partidos para analizar. Terminando.")
        sys.exit(0)
    
    if args.mode == "ai":
        print("[Scouter] Evaluando con IA...")
        evaluated_matches = evaluate_matches_with_ai(matches)
    else:
        # 2. Obtener standings (posiciones en liga)
        print("[Scouter] Obteniendo standings...")
        league_codes = set(m['competition_code'] for m in matches)
        standings = {}
        for code in league_codes:
            standings.update(get_standings(code))
        
        # 3. Obtener resultados recientes por competición (más eficiente que por equipo)
        print("[Scouter] Obteniendo resultados recientes...")
        team_results = {}
        for code in league_codes:
            results = get_competition_results(code, GSR_MATCHES * 20)
            for m in results:
                hid = m['homeTeam']['id']
                aid = m['awayTeam']['id']
                team_results.setdefault(hid, []).append(m)
                team_results.setdefault(aid, []).append(m)
        
        # 4. Evaluación por fuerza determinista
        print("[Scouter] Evaluando partidos por diferencia de fuerza...")
        evaluated_matches = evaluate_matches(matches, standings, team_results)
    
    # 5. Reporte
    print("[Scouter] Generando reporte y evidencias...")
    generate_report(args.mode, evaluated_matches)
    
    print("[Scouter] Proceso completado exitosamente.")

if __name__ == "__main__":
    main()
