import os
import json
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader

COLOMBIA_OFFSET = -5  # UTC-5

def utc_to_colombia(utc_str):
    if not utc_str:
        return ""
    dt = datetime.strptime(utc_str, '%Y-%m-%dT%H:%M:%SZ')
    col_dt = dt + timedelta(hours=COLOMBIA_OFFSET)
    return col_dt.strftime('%Y-%m-%d %H:%M')

def generate_report(mode, evaluated_matches):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    reports_dir = os.path.join(base_dir, 'reports')
    evidence_dir = os.path.join(base_dir, 'evidence')
    logs_dir = os.path.join(base_dir, 'logs')
    templates_dir = os.path.join(base_dir, 'templates')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Guardar Evidencia
    evidence_path = os.path.join(evidence_dir, f'evidence_{mode}_{timestamp}.json')
    with open(evidence_path, 'w') as f:
        json.dump(evaluated_matches, f, indent=2)
        
    # 2. Generar Reporte con Jinja2
    template_path = os.path.join(templates_dir, 'report_template.md')
    if not os.path.exists(template_path):
        os.makedirs(templates_dir, exist_ok=True)
        with open(template_path, 'w') as f:
            f.write("""# Reporte de Análisis Competitivo (Modo: {{ mode | upper }})

Fecha: {{ date }}

## Partidos Evaluados: {{ evaluated | length }}
## Partidos Seleccionados (Umbral >= 8): {{ selected | length }}

{% for match in selected %}
### ⭐ {{ match.favorite_label }} (Favorito) vs {{ match.rival_label }}
- **Competición:** {{ match.match.competition }}
- **Fecha/Hora (Colombia):** {{ match.colombia_date }}
- **Puntuación:** {{ match.score }}
- **Justificación:**
{% for j in match.justification %}  - {{ j }}
{% endfor %}
{% endfor %}

---
*Evidencia guardada en `evidence/evidence_{{ mode }}_{{ timestamp }}.json`*
""")
            
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template('report_template.md')
    
    selected_matches = [m for m in evaluated_matches if m['selected']]
    
    # Pre-process selected matches: convert dates, determine favorite/rival
    for m in selected_matches:
        m['colombia_date'] = utc_to_colombia(m['match'].get('date', ''))
        if m['match']['home_team'] == m['favorite']:
            m['favorite_label'] = m['match']['home_team']
            m['rival_label'] = m['match']['away_team']
        else:
            m['favorite_label'] = m['match']['away_team']
            m['rival_label'] = m['match']['home_team']
    
    markdown_output = template.render(
        mode=mode,
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        timestamp=timestamp,
        evaluated=evaluated_matches,
        selected=selected_matches
    )
    
    report_path = os.path.join(reports_dir, f'report_{mode}_{timestamp}.md')
    with open(report_path, 'w') as f:
        f.write(markdown_output)
        
    # 3. Simple audit log
    log_path = os.path.join(logs_dir, f'execution_{mode}_{timestamp}.log')
    with open(log_path, 'w') as f:
        f.write(f"[{datetime.now().isoformat()}] Ejecucion completada. Seleccionados: {len(selected_matches)} de {len(evaluated_matches)}.\n")

    print(f"[Scouter] Reporte generado: {report_path}")
