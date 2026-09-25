# MIZAN — ميزان

Local-first university scheduling, workforce planning, and recruitment assistance.

## Current status

The second consolidated build phase is ready for review: Apple-inspired colors, five collaborating scheduling agents, and a Recruitment Assistant using local Qwen3 8B inference. Recruitment includes manager-approved criteria, PDF/DOCX/TXT CV ingestion, source correction, evidence comparisons, printable briefs and source CV drafts, and bilingual hiring-manager chat. No live LinkedIn connection is configured.

- [Build 2 checkpoint and review guide](docs/build-02-checkpoint.md)
- [Build 1 checkpoint and review guide](docs/build-01-checkpoint.md)
- [Approved scope, journeys, and acceptance criteria](docs/phase-01-product-contract.md)
- [Environment assessment](docs/environment-assessment.md)
- [Revised project specification](docs/MIZAN%20-%20Project%20Documentation%20v3.md)

## Architecture

Six logical AI agents: Coordinator, Student Experience, Scheduling & Optimization, Change Impact, Workforce Planning, and Recruitment Assistant. Shared deterministic tools calculate results and enforce rules. Staff approve publication and hiring decisions.

The initial release uses a local database and reproducible synthetic data. Live LinkedIn access and university-system integration depend on separately available access; they are not simulated as working integrations.

## Phase gates

1. Working scheduling application — approved.
2. Six agents and recruitment — ready for review.
3. Final verification and delivery — not started.

## Run on this PC

Double-click **Start Mizan.cmd**, then open **http://127.0.0.1:8000**. The prepared environment and built frontend are already present locally. The server binds to loopback only.

Demo accounts: `admin`, `registrar`, `chair`, `professor`, `student`, `hiring_manager`. The default demonstration password is `Mizan-demo-2026!`. These are intentionally local demo identities, not institutional authentication. Set `MIZAN_DEMO_PASSWORD` before starting to override the shared demo password.

The initial fixtures contain 1,500 fictional students, 80 courses, 100 sections, 40 rooms, and 50 professors. The baseline, diagnostic, and staffing-shortfall scenarios are separate. Your changes are saved in `data/mizan.sqlite3`; restarting does not reset them.

## Fresh setup

Prerequisites: Python 3.12+, Node.js 24+, and pnpm 11+. The setup script accepts explicit `-Python` and `-Pnpm` paths when these are not on PATH.

```powershell
./scripts/setup.ps1
# Optional on a fresh machine: download ~6.7 GB of pinned runtime/model assets.
./.venv/Scripts/python.exe scripts/install_model_runtime.py
./scripts/start.ps1
```

Backend packages are pinned in `requirements.lock.txt`. Frontend versions are pinned by `frontend/pnpm-lock.yaml`. Fonts are served locally; the running application does not need an external font service. Dependency installation requires network access.

## Verification

```powershell
./scripts/test.ps1
```

This runs domain and API checks in isolated SQLite databases under `work/`. For browser checks, start a separate server with `MIZAN_DB` pointing to a fresh file under `work/` and port 8001, then run `node tests/browser-smoke.cjs`. The script uses the installed Chrome browser in a new temporary profile. Set `MIZAN_BROWSER=msedge` to use Edge. Do not point the browser test at your main workspace: it creates and publishes test proposals.

## Structure

- `backend/`: data contracts, fixtures, analysis, optimization, storage, HTTP API.
- `frontend/`: React/TypeScript application and local fonts.
- `tests/`: domain, API, and browser checks.
- `scripts/`: Windows setup, startup, and testing.
- `docs/`: specifications, environment findings, and phase checkpoints.
- `data/`: generated local database; excluded from Git.
- `work/`: screenshots, logs, and test databases; excluded from Git.

The local `.venv` was provisioned from the available Python runtime on this PC. A fresh setup uses your explicitly supplied Python installation. No credentials, runtime dependencies, or generated personal records should be committed.

## Local model

Start Mizan also starts the installed model on loopback port 11435. It uses the llama.cpp server bundled in pinned Ollama 0.34.3; the Ollama daemon is not started. Model and runtime files stay in `.models/` and `.runtime/`. This PC uses CUDA on the RTX 4080 SUPER. The download installer verifies SHA-256 digests. Ordinary inference sends no records to an external provider.

See the second checkpoint for model limits and review steps. `tests/browser-phase2.cjs` exercises agents and recruitment against the isolated server on port 8001 and requires the local model. It creates fictional records and must not be pointed at your main database.
