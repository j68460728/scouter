# Scouter Engine Agent Instructions

## Critical Operational Flow
The system is strictly containerized. All analysis must be executed through the provided CLI wrapper.

### Execution
- **Command:** `./bin/scout analyze --mode [rules|ai] [--window <valor>]`
- **Modes:**
  - `rules`: **Strength-based evaluation** (Team Strength 0–100, difference comparison, GSR component, configurable via `rules/strength_matrix.yaml`)
  - `ai`: Uses `src/evaluator_ai.py` (requires `API_BASE_URL` access)
- **Window (opcional):**
  - `--window 7d` → 7 días
  - `--window 48h` → 48 horas
  - `--window 3` → 3 días (por defecto: días)
  - Sin `--window` → todos los partidos disponibles
- **API Key:** Configurada en `docker-compose.yml` como `FOOTBALL_DATA_API_KEY` (football-data.org).

## Architecture & Conventions
- **Entrypoint:** `bin/scout` (Bash wrapper for `docker compose`).
- **Data Source:** `api.football-data.org/v4` via `src/scraper.py`. Uses REST API.
- **Strength Engine:** `src/strength_profile.py` builds Team Strength (0–100) from structural (60%), recent form/GSR (30%), and context (10%). `src/evaluator_strength.py` computes `abs(home - away)` and selects matches where difference >= 15.
- **New files:** `src/evaluator_strength.py`, `src/strength_profile.py`, `src/utils.py`, `rules/strength_matrix.yaml`
- **Removed:** `src/evaluator_rules.py` (replaced by evaluator_strength)
- **Data Persistence:** All outputs (`reports/`, `evidence/`, `logs/`) are mapped to host volumes.
- **Workflow:** Defined in `instructions/workflow.json` (5-step process).

## Developer Quirks
- **Rate Limiting:** Free account allows 10 req/min. The scraper includes a 10s delay between requests and automatic retry on 429 errors. Expect ~70s for a full 6-league run.
- **Determinism:** The `rules` mode is deterministic (strength-based). Do not modify scoring logic without updating associated test fixtures.
- **GSR:** Goal Superiority Rating uses last N matches (default 6, configurable in `strength_matrix.yaml`). Requires `min_matches: 5` to produce a non-zero value.
- **Normalization:** All limits (max_ppg, max_season_gd, max_gsr, etc.) are defined in `strength_matrix.yaml`. Never hardcode limits in Python.
- **Networking:** Container uses `host.docker.internal:host-gateway` for external APIs on host.
