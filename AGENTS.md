# Scouter Engine Agent Instructions

## Critical Operational Flow
The system is strictly containerized. All analysis must be executed through the provided CLI wrapper.

### Execution
- **Command:** `./bin/scout analyze --mode [rules|ai]`
- **Modes:**
  - `rules`: Executes logic using predefined YAML matrices in `rules/`.
  - `ai`: Executes logic using `src/evaluator_ai.py` (requires `API_BASE_URL` access).

## Architecture & Conventions
- **Entrypoint:** `bin/scout` (Bash wrapper for `docker compose`).
- **Data Persistence:** All outputs (`reports/`, `evidence/`, `logs/`) are mapped to host volumes in `docker-compose.yml`.
- **Workflow:** Defined in `instructions/workflow.json`. Agents must adhere to the 5-step process described there (Initialization, Discovery, Evaluation, Audit, Reporting).

## Developer Quirks
- **Networking:** The container relies on `host.docker.internal:host-gateway` to communicate with external APIs on the host machine. If API calls fail, verify the `API_BASE_URL` in `docker-compose.yml`.
- **Determinism:** The `rules` mode is intended to be deterministic. Do not modify scoring logic without updating associated test fixtures.
