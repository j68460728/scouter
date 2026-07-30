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
| `--mode` | Sí | Modo de ejecución: `rules` (evaluación por fuerza determinista) o `ai` (IA, experimental) |
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
- Equipos local y visitante con **favorito** indicado (⭐)
- Competición
- **Fecha/Hora en Colombia** (UTC-5)
- **Fuerza de cada equipo** (0–100) con desglose estructural / forma reciente / contexto
- **Diferencia de fuerza** (umbral mínimo: 15 pts)

```
### ⭐ Arsenal FC (Favorito) vs Coventry City FC — Diferencia: 29.9 pts
- **Competición:** Premier League
- **Fecha/Hora (Colombia):** 2026-08-21 14:00
- **Fuerza local (Arsenal FC):** 55.9/100
  - Estructural: 49.9/60
  - Forma reciente: 0.0/30
  - Contexto: 6.0/10
- **Fuerza visitante (Coventry City FC):** 26.0/100
  - Estructural: 25.0/60
  - Forma reciente: 0.0/30
  - Contexto: 1.0/10
```

### Evidencia (`evidence/evidence_rules_YYYYMMDD_HHMMSS.json`)
Datos crudos en JSON de todos los partidos evaluados con fuerza, diferencia y desglose.

### Logs (`logs/execution_rules_YYYYMMDD_HHMMSS.log`)
Registro de auditoría de la ejecución.

## Arquitectura

- `bin/scout` → Entrypoint (Bash wrapper para Docker)
- `src/config.py` → Configuración de ligas y API
- `src/scraper.py` → Consume API REST de football-data.org (matches + standings + resultados)
- `src/strength_profile.py` → Construye perfil de fuerza del equipo (0–100) desde datos objetivos
- `src/evaluator_strength.py` → Calcula diferencia de fuerza y selecciona candidatos
- `src/reporter.py` → Genera reportes Markdown + JSON
- `rules/strength_matrix.yaml` → Pesos, coeficientes, límites de normalización y umbral de selección

## Personalización

Ajuste la sensibilidad del análisis editando `rules/strength_matrix.yaml`:
- `confidence.min_difference`: Diferencia de fuerza mínima para seleccionar un partido (default: 15)
- `weights`: Distribución entre estructural (60%), forma reciente (30%) y contexto (10%)
- `gsr.matches`: Número de partidos para calcular Goal Superiority Rating (default: 6)

## Guía de Usuario

Consulte `docs/USER_GUIDE.md` para una guía detallada de uso e interpretación de resultados.
