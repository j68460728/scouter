# Reporte de Análisis Competitivo (Modo: {{ mode | upper }})

Fecha: {{ date }}

## Partidos Evaluados: {{ evaluated | length }}
## Partidos Seleccionados (Umbral >= 8): {{ selected | length }}

{% for match in selected %}
### {{ match.match.home_team }} vs {{ match.match.away_team }}
- **Competición:** {{ match.match.competition }}
- **Puntuación:** {{ match.score }}
- **Justificación:**
{% for j in match.justification %}  - {{ j }}
{% endfor %}
{% endfor %}

---
*Evidencia guardada en `evidence/evidence_{{ mode }}_{{ timestamp }}.json`*
