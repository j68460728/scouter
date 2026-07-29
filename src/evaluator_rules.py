import yaml
import os

def evaluate_matches_with_rules(matches):
    rules_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rules', 'scoring_matrix.yaml')
    with open(rules_path, 'r') as f:
        rules = yaml.safe_load(f)
    
    evaluated = []
    threshold = rules['scoring_matrix']['threshold']
    
    for match in matches:
        score = 0
        justification = []
        
        # Lógica dura simulada para el ejemplo basado en el JSON de entrada
        if match['category_level'] == "Tier 1":
            score += 3
            justification.append("Tier 1 competition (+3)")
        elif match['category_level'] == "Tier 2":
            score += 2
            justification.append("Tier 2 competition (+2)")
        else:
            score += 1
            justification.append("Lower tier competition (+1)")
            
        # Simular prestigio historico
        if match['home_team'] in ["Real Madrid", "Bayern Munich", "Barcelona"]:
            score += 2
            justification.append("Historical prestige team (+2)")
        elif match['category_level'] in ["Tier 1", "Tier 2"]:
            score += 1
            justification.append("Standard professional prestige (+1)")
            
        # Simular squad value
        if match['category_level'] == "Tier 1":
            score += 2
            justification.append("High squad value estimated for Tier 1 (+2)")
        else:
            score += 1
            justification.append("Average squad value (+1)")
            
        # Simular ranking coef
        score += 1
        justification.append("Average ranking coeff (+1)")
        
        # Simular forma reciente
        score += 1
        justification.append("Recent verifiable form (+1)")
        
        selected = score >= threshold
        
        evaluated.append({
            "match": match,
            "score": score,
            "justification": justification,
            "selected": selected
        })
        
    return evaluated
