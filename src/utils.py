def clamp(value, lo, hi):
    return max(lo, min(hi, value))

def normalize(value, max_val, invert=False):
    if max_val <= 0:
        return 0.0
    raw = value / max_val
    if invert:
        raw = 1.0 - raw
    return clamp(raw, 0.0, 1.0)

def gsr_from_matches(matches, team_id):
    total = 0
    for m in matches:
        ft = m.get('score', {}).get('fullTime', {})
        home = ft.get('home', 0) or 0
        away = ft.get('away', 0) or 0
        if m.get('homeTeam', {}).get('id') == team_id:
            total += home - away
        else:
            total += away - home
    return total

def ppg_from_matches(matches, team_id):
    points = 0
    for m in matches:
        ft = m.get('score', {}).get('fullTime', {})
        home = ft.get('home', 0) or 0
        away = ft.get('away', 0) or 0
        is_home = m.get('homeTeam', {}).get('id') == team_id
        scored = home if is_home else away
        conceded = away if is_home else home
        if scored > conceded:
            points += 3
        elif scored == conceded:
            points += 1
    return points / len(matches) if matches else 0.0

def goals_avg_from_matches(matches, team_id):
    total = 0
    for m in matches:
        ft = m.get('score', {}).get('fullTime', {})
        home = ft.get('home', 0) or 0
        away = ft.get('away', 0) or 0
        if m.get('homeTeam', {}).get('id') == team_id:
            total += home
        else:
            total += away
    return total / len(matches) if matches else 0.0
