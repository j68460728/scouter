import requests
import json
import yaml
import os

def evaluate_matches_with_ai(matches):
    rules_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rules', 'scoring_matrix.yaml')
    with open(rules_path, 'r') as f:
        rules = yaml.safe_load(f)
        
    prompt = f"""
    Eres un experto analista deportivo. Evalúa los siguientes partidos usando estrictamente esta matriz de puntuación:
    {json.dumps(rules['scoring_matrix']['criteria'], indent=2)}
    
    Partidos:
    {json.dumps(matches, indent=2)}
    
    El umbral para seleccionar un partido es {rules['scoring_matrix']['threshold']}.
    Tu objetivo es aplicar tu conocimiento general sobre el prestigio, plantillas actuales y rachas para asignar los puntos.
    Devuelve un JSON válido (sin backticks de markdown ni texto extra) estrictamente con este formato:
    [
      {{
        "match_id": "id del partido",
        "score": 8,
        "justification": ["razon 1", "razon 2"],
        "selected": true
      }}
    ]
    """
    
    # URL al OmniRoute local. 
    # Al correr en Docker de Linux, host.docker.internal puede requerir config especial,
    # probaremos con el default de Docker en Linux (172.17.0.1) si host.docker.internal falla.
    api_base = os.getenv("API_BASE_URL", "http://host.docker.internal:20128/v1")
    ai_model = os.getenv("AI_MODEL", "google/gemini-pro")
    
    print(f"[Scouter-AI] Consultando modelo {ai_model} via {api_base} ...")
    try:
        response = requests.post(
            f"{api_base}/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": "Bearer sk-dummy"},
            json={
                "model": ai_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        content = data['choices'][0]['message']['content']
        # Limpiar posible envoltura markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        ai_results = json.loads(content)
        
        evaluated = []
        for ai_res in ai_results:
            match_data = next(m for m in matches if m['id'] == ai_res['match_id'])
            evaluated.append({
                "match": match_data,
                "score": ai_res['score'],
                "justification": ai_res['justification'],
                "selected": ai_res['selected']
            })
        return evaluated
        
    except Exception as e:
        print(f"[Error en IA] No se pudo obtener la evaluación: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Detalle: {e.response.text}")
        return []
