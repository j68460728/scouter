import argparse
import os
import sys

from scraper import get_matches
from evaluator_rules import evaluate_matches_with_rules
from evaluator_ai import evaluate_matches_with_ai
from reporter import generate_report

def parse_window(value):
    if value is None:
        return None
    value = value.strip()
    if value.endswith('h'):
        return int(value[:-1])
    elif value.endswith('d'):
        return int(value[:-1]) * 24
    else:
        return int(value) * 24  # default unit: days

def main():
    parser = argparse.ArgumentParser(description="Scouter Engine - Modo Dual")
    parser.add_argument("--mode", choices=["rules", "ai"], required=True, help="Modo de ejecución: rules o ai")
    parser.add_argument("--window", type=str, default=None, help="Ventana de tiempo (opcional). Ej: 7d (7 días), 24h (24 horas). Por defecto: días. Sin el parámetro se traen todos los partidos.")
    
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
        
    # 2. Evaluación
    print("[Scouter] Evaluando partidos...")
    if args.mode == "rules":
        evaluated_matches = evaluate_matches_with_rules(matches)
    else:
        evaluated_matches = evaluate_matches_with_ai(matches)
        
    # 3. Reporte
    print("[Scouter] Generando reporte y evidencias...")
    generate_report(args.mode, evaluated_matches)
    
    print("[Scouter] Proceso completado exitosamente.")

if __name__ == "__main__":
    main()
