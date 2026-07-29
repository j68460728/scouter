# Scouter Engine

Sistema de análisis deportivo autónomo, reproducible y auditable, diseñado para identificar enfrentamientos con diferencia competitiva significativa en el fútbol profesional utilizando datos reales de la API de football-data.org.

## Requisitos
- Docker y Docker Compose
- Conexión a internet
- API Key de football-data.org (ya configurada en `docker-compose.yml`)

## Uso

```bash
./bin/scout analyze --mode rules [--window <valor>]
```

### Parámetros

| Parámetro | Obligatorio | Descripción |
|---|---|---|
| `--mode` | Sí | Modo de ejecución: `rules` (matriz de reglas) o `ai` (IA, en desarrollo) |
| `--window` | No | Ventana de tiempo. Ej: `7d` (7 días), `24h` (24 horas). Sin unidad = días. Si se omite, se traen **todos** los partidos disponibles. |

### Ejemplos

```bash
# Todos los partidos disponibles (sin filtro)
./bin/scout analyze --mode rules

# Partidos en las próximas 48 horas
./bin/scout analyze --mode rules --window 48h

# Partidos en los próximos 7 días
./bin/scout analyze --mode rules --window 7d

# Partidos en los próximos 3 días (por defecto: días)
./bin/scout analyze --mode rules --window 3
```

## Salida esperada

### Reporte (`reports/report_rules_YYYYMMDD_HHMMSS.md`)
Lista los partidos seleccionados con:
- Equipos local y visitante
- Competición
- **Fecha/Hora del encuentro** (formato ISO UTC)
- Puntuación total (umbral >= 8)
- Justificación desglosada por criterio

```
### Arsenal FC vs Coventry City FC
- **Competición:** Premier League
- **Fecha/Hora:** 2026-08-21T19:00:00Z
- **Puntuación:** 10
- **Justificación:**
  - Tier 1 competition (+3)
  - Historical prestige team (+2)
  ...
```

### Evidencia (`evidence/evidence_rules_YYYYMMDD_HHMMSS.json`)
Datos crudos en JSON de todos los partidos evaluados con su puntuación y justificación.

### Logs (`logs/execution_rules_YYYYMMDD_HHMMSS.log`)
Registro de auditoría de la ejecución.

## Arquitectura

- `bin/scout` → Entrypoint (Bash wrapper para Docker)
- `src/config.py` → Configuración de ligas y API
- `src/scraper.py` → Consume API REST de football-data.org
- `src/evaluator_rules.py` → Aplica matriz de puntuación (`rules/scoring_matrix.yaml`)
- `src/reporter.py` → Genera reportes Markdown + JSON
- `rules/scoring_matrix.yaml` → Define criterios y umbral de selección

## Personalización

Ajuste el umbral de selección editando `rules/scoring_matrix.yaml`:
```yaml
threshold: 8  # Valor mínimo para seleccionar un partido
```

## Guía de Usuario

Consulte `docs/USER_GUIDE.md` para una guía detallada de uso e interpretación de resultados.
