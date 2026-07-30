# Scouter Engine Agent Instructions

## Critical Operational Flow
The system is strictly containerized. All analysis must be executed through the provided CLI wrapper.

### Execution
- **Command:** `./bin/scout analyze --mode [rules|ai] [--window <valor>]`
- **Modes:**
  - `rules`: **Strength-based evaluation** (Team Strength 0–100, difference comparison, configurable via `rules/strength_matrix.yaml`)
  - `ai`: Uses `src/evaluator_ai.py` (requires `API_BASE_URL` access)
- **Window (opcional):**
  - `--window 7d` → 7 días
  - `--window 48h` → 48 horas
  - `--window 3` → 3 días (por defecto: días)
  - Sin `--window` → todos los partidos disponibles
- **API Key:** Configurada en `docker-compose.yml` como `FOOTBALL_DATA_API_KEY` (football-data.org).
- **Imagen Docker:** Reconstruir con `docker compose build scouter` tras cambios en `src/`.

## Architecture & Conventions
- **Entrypoint:** `bin/scout` (Bash wrapper for `docker compose`).
- **Data Source:** `api.football-data.org/v4` via `src/scraper.py`. Uses REST API.
- **Scouter Engine v2 (frozen):** `src/strength_profile.py` builds Team Strength (0–100) from structural (85.7%) and context (14.3%). `src/evaluator_strength.py` computes `abs(home - away)` and selects matches where `difference >= 20`.
- **Model Configuration (congelada):**
  - Structural: 85.7% (competition_coefficient 35.7, points_per_game 35.7, season_goal_difference 14.3)
  - Context: 14.3% (home_advantage 7.1, competition_stage 7.2)
  - Recent Form: eliminado (0%)
  - GSR: eliminado
  - min_difference: 20
  - Sealed in `rules/strength_matrix.yaml`. No modificar.
- **OOS Benchmark (Scouter Engine v2):** 2024/25, 5 leagues (PL/BL1/PD/SA/FL1), 1752 matches: coverage 12.5%, accuracy 68.9%, baseline home 42.0%.
  - Cualquier modificación futura debe superar este benchmark con cobertura comparable.
  - Histórico en `bin/oos` (script de evaluación) y `backtest_results_*.json` (resultados completos 2 temporadas).
- **New files:** `src/evaluator_strength.py`, `src/strength_profile.py`, `src/utils.py`, `src/backtesting/`
- **Removed:** `src/evaluator_rules.py`, recent form and GSR from strength_profile
- **Data Persistence:** Outputs (`reports/`, `evidence/`, `logs/`) mapped to host volumes.
- **Workflow:** Defined in `instructions/workflow.json` (5-step process).

## Developer Quirks
- **Rate Limiting:** Free account allows 10 req/min. The scraper includes a 10s delay between requests and automatic retry on 429 errors. Expect ~70s for a full 6-league run.
- **Determinism:** The `rules` mode is deterministic (strength-based). Do not modify scoring logic without updating associated test fixtures.
- **Normalization:** All limits (max_ppg, max_season_gd, etc.) are defined in `strength_matrix.yaml`. Never hardcode limits in Python.
- **Networking:** Container uses `host.docker.internal:host-gateway` for external APIs on host.
- **Data Leakage:** Current standings are fetched via `get_standings()` which always returns the **current** league table. When analyzing past matches (no `--window`), this introduces data leakage — standings include results from after the match date. For upcoming matches (with `--window`), there is no leakage. **Do not use current pipeline for backtesting without implementing time-traveled standings.**
- **Backtesting:** Pipeline in `src/backtesting/` (engine.py, historical_data.py, metrics.py) uses football-data.co.uk CSVs (free historical data). Entrypoints: `bin/backtest`, `bin/calibrate`, `bin/audit`, `bin/oos`.
- **No recent form/GSR:** Model v2 uses Structural+Context only. GSR experiment confirmed signal (r=0.33) but ablation proved zero incremental value over SC-only. Removed permanently.
