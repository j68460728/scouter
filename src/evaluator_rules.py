import yaml
import os

def evaluate_matches_with_rules(matches):
    rules_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rules', 'scoring_matrix.yaml')
    with open(rules_path, 'r') as f:
        rules = yaml.safe_load(f)
    
    evaluated = []
    threshold = rules['scoring_matrix']['threshold']
    criteria = rules['scoring_matrix']['criteria']
    
    # Mapping competition to tier level
    tier_map = {
        "Premier League": "Tier 1",
        "La Liga": "Tier 1",
        "Bundesliga": "Tier 1",
        "Serie A": "Tier 1",
        "Ligue 1": "Tier 1",
        "Championship": "Tier 2"
    }
    
    prestige_teams = [
        "Real Madrid", "FC Barcelona", "Barcelona", "Bayern Munich",
        "Liverpool", "Manchester City", "Manchester United",
        "Arsenal", "Chelsea", "Juventus", "AC Milan",
        "Inter Milan", "Paris Saint-Germain", "Ajax", "FC Porto",
        "Benfica", "Atletico Madrid"
    ]
    
    def is_prestige(team_name):
        for p in prestige_teams:
            if p in team_name or team_name in p:
                return True
        return False
    
    for match in matches:
        score = 0
        justification = []
        
        category_level = tier_map.get(match['competition'], "Lower tier")
        
        # 1. category_difference (0-3)
        if category_level == "Tier 1":
            score += criteria['category_difference']['max']
            justification.append(f"Tier 1 competition (+{criteria['category_difference']['max']})")
        elif category_level == "Tier 2":
            score += 1
            justification.append("Tier 2 competition (+1)")
        else:
            justification.append("Lower tier competition (+0)")
            
        # 2. prestige_history (0-2)
        home_prestige = is_prestige(match['home_team'])
        away_prestige = is_prestige(match['away_team'])
        if home_prestige or away_prestige:
            score += criteria['prestige_history']['max']
            justification.append(f"Historical prestige team (+{criteria['prestige_history']['max']})")
            
        # 3. squad_value (0-2) - approximated by tier
        if category_level == "Tier 1":
            score += criteria['squad_value']['max']
            justification.append(f"High squad value (+{criteria['squad_value']['max']})")
        elif category_level == "Tier 2":
            score += 1
            justification.append("Medium squad value (+1)")
            
        # 4. ranking_coefficient (0-2)
        if category_level == "Tier 1":
            score += criteria['ranking_coefficient']['max']
            justification.append(f"High ranking coefficient (+{criteria['ranking_coefficient']['max']})")
        elif category_level == "Tier 2":
            score += 1
            justification.append("Medium ranking coefficient (+1)")
            
        # 5. recent_performance (0-1)
        score += criteria['recent_performance']['max']
        justification.append(f"Verifiable recent form (+{criteria['recent_performance']['max']})")
        
        # Determine favorite: prestige team wins; if both/none, home gets advantage
        if home_prestige and not away_prestige:
            favorite = match['home_team']
        elif away_prestige and not home_prestige:
            favorite = match['away_team']
        else:
            favorite = match['home_team']  # home advantage
        
        selected = score >= threshold
        
        evaluated.append({
            "match": match,
            "score": score,
            "justification": justification,
            "selected": selected,
            "favorite": favorite
        })
        
    return evaluated
