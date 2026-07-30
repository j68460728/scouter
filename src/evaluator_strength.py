import yaml
import os
from strength_profile import build_match
from config import CONFIDENCE_THRESHOLD

def _load_matrix():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rules', 'strength_matrix.yaml')
    with open(path) as f:
        return yaml.safe_load(f)

def evaluate_matches(matches, standings, team_results):
    matrix = _load_matrix()
    min_diff = matrix.get('confidence', {}).get('min_difference', CONFIDENCE_THRESHOLD)
    evaluated = []

    for match in matches:
        home, away = build_match(match, standings, team_results, matrix)
        diff = round(abs(home['total'] - away['total']), 1)
        favorite = match['home_team'] if home['total'] >= away['total'] else match['away_team']
        selected = diff >= min_diff

        evaluated.append({
            "match": match,
            "home_strength": home,
            "away_strength": away,
            "difference": diff,
            "favorite": favorite,
            "selected": selected,
            "score": round(home['total'] + away['total'], 1),
            "justification": [
                f"Fuerza estructural: Local {home['structural']} vs Visita {away['structural']}",
                f"Contexto: Local {home['context']} vs Visita {away['context']}",
                f"Diferencia total: {diff} pts (umbral: {min_diff})"
            ]
        })

    return evaluated