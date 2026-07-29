import os
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

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
    # Check if template exists, if not create a fallback template inline
    template_path = os.path.join(templates_dir, 'report_template.md')
    if not os.path.exists(template_path):
        os.makedirs(templates_dir, exist_ok=True)
        with open(template_path, 'w') as f:
            f.write("""# Reporte de Análisis Competitivo (Modo: {{ mode | upper }})

Fecha: {{ date }}

## Partidos Evaluados: {{ evaluated | length }}
## Partidos Seleccionados (Umbral >= 8): {{ selected | length }}

{% for match in selected %}
### {{ match.match.home_team }} vs {{ match.match.away_team }}
- **Competición:** {{ match.match.competition }}
- **Fecha/Hora:** {{ match.match.date }}
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
