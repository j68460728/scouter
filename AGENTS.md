# Scouter Engine Agent Instructions

## Critical Operational Flow
The system is strictly containerized. All analysis must be executed through the provided CLI wrapper.

### Execution
- **Command:** `./bin/scout analyze --mode [rules|ai] [--window <valor>]`
- **Modes:**
  - `rules`: Deterministic scoring via YAML matrix in `rules/`.
  - `ai`: Uses `src/evaluator_ai.py` (requires `API_BASE_URL` access).
- **Window (opcional):**
  - `--window 7d` → 7 días
  - `--window 48h` → 48 horas
  - `--window 3` → 3 días (por defecto: días)
  - Sin `--window` → todos los partidos disponibles
- **API Key:** Configurada en `docker-compose.yml` como `FOOTBALL_DATA_API_KEY` (football-data.org, no football-data.co.uk).

## Architecture & Conventions
- **Entrypoint:** `bin/scout` (Bash wrapper for `docker compose`).
- **Data Source:** `api.football-data.org/v4` via `src/scraper.py`. Uses REST API, not CSV.
- **Data Persistence:** All outputs (`reports/`, `evidence/`, `logs/`) are mapped to host volumes.
- **Workflow:** Defined in `instructions/workflow.json` (5-step process).

## Developer Quirks
- **Rate Limiting:** Free account allows 10 req/min. The scraper includes a 10s delay between requests and automatic retry on 429 errors. Expect ~70s for a full 6-league run.
- **Determinism:** The `rules` mode is deterministic. Do not modify scoring logic without updating associated test fixtures.
- **Networking:** Container uses `host.docker.internal:host-gateway` for external APIs on host.
