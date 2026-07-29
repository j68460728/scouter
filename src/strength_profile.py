import yaml
import os
from config import GSR_MATCHES
from utils import normalize, gsr_from_matches, ppg_from_matches, goals_avg_from_matches

def _load_matrix():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rules', 'strength_matrix.yaml')
    with open(path) as f:
        return yaml.safe_load(f)

def _team_strength(team_id, is_home, competition_code, stage, standings, team_results, matrix):
    w = matrix['weights']
    norm = matrix['normalization']

    comp_coeff = matrix.get('competition_coefficients', {}).get(competition_code, 10)
    st = standings.get(team_id, {})
    results = team_results.get(team_id, [])

    # Structural (60%)
    c_comp = normalize(comp_coeff, 25) * w['structural']['competition_coefficient']
    c_ppg = normalize(st.get('ppg', 0), norm['max_ppg']) * w['structural']['points_per_game']
    c_gd = normalize(st.get('goal_difference', 0), norm['max_season_gd']) * w['structural']['season_goal_difference']
    structural = c_comp + c_ppg + c_gd

    # Recent Form (30%)
    r_gsr = 0.0
    r_ppg = 0.0
    r_ga = 0.0
    min_matches = matrix['gsr']['min_matches']
    if len(results) >= min_matches:
        gsr = gsr_from_matches(results, team_id) / matrix['gsr']['matches']
        r_gsr = normalize(gsr, norm['max_gsr']) * w['recent_form']['gsr']
        r_ppg = normalize(ppg_from_matches(results, team_id), norm['max_ppg']) * w['recent_form']['points_per_game']
        r_ga = normalize(goals_avg_from_matches(results, team_id), norm['max_goals_per_game']) * w['recent_form']['goal_average']
    recent_form = r_gsr + r_ppg + r_ga

    # Context (10%)
    ctx_home = (w['context']['home_advantage'] if is_home else 0)
    stage_val = norm.get('stage_knockout', 5) if stage in ('KNOCKOUT', 'QUARTER_FINALS', 'SEMI_FINALS', 'FINAL') else norm.get('stage_group', 3) if stage in ('GROUP_STAGE', 'group') else norm.get('stage_regular', 1)
    ctx_stage = normalize(stage_val, 5) * w['context']['competition_stage']
    context = ctx_home + ctx_stage

    total = round(min(100.0, structural + recent_form + context), 1)

    return {
        'name': st.get('name', team_id),
        'structural': round(structural, 1),
        'recent_form': round(recent_form, 1),
        'context': round(context, 1),
        'total': total
    }

def build_match(match, standings, team_results, matrix=None):
    if matrix is None:
        matrix = _load_matrix()
    stage = match.get('stage', 'REGULAR_SEASON')
    home = _team_strength(match['home_id'], True, match['competition_code'], stage, standings, team_results, matrix)
    away = _team_strength(match['away_id'], False, match['competition_code'], stage, standings, team_results, matrix)
    home['name'] = match['home_team']
    away['name'] = match['away_team']
    return home, away
