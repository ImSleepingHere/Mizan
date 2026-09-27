# MIZAN — ميزان

Local-first university scheduling, workforce planning, and recruitment assistance.

## Presenting the demo?

Start with **[docs/HANDOVER.md](docs/HANDOVER.md)**: install on a new PC, check readiness, run, reset, and the demo itself.

- [Demo script (7 minutes)](docs/demo-script.md)
- [Acceptance report: all spec criteria mapped to passing tests](docs/acceptance-report.md)
- [Revised project specification](docs/MIZAN%20-%20Project%20Documentation%20v3.md)
- Design system: [DESIGN.md](DESIGN.md) · product brief: [PRODUCT.md](PRODUCT.md)

## Current status

Ready for the Farq demo (27 September 2026). Six collaborating agents with a fine-tuned local coordinator, OR-Tools optimization with independent validation, change requests, professor requests (Ask Mizan, My classes, request rules, common free-slot finder), workforce evidence and recruitment assistance, in a bilingual "Information System" interface with graded metrics. 80 automated tests and two browser suites pass.

## Architecture

Six logical AI agents: Coordinator, Student Experience, Scheduling & Optimization, Change Impact, Workforce Planning, and Recruitment Assistant. Shared deterministic tools calculate results and enforce rules. Staff approve publication and hiring decisions.

The initial release uses a local database and reproducible synthetic data. Live LinkedIn access and university-system integration depend on separately available access; they are not simulated as working integrations.

## Phase gates

1. Working scheduling application: approved.
2. Six agents and recruitment: ready for review.
3. Final verification and delivery: done (acceptance report, demo script, reset script, deck).

## Run on this PC

Double-click **Start Mizan.cmd**, then open **http://127.0.0.1:8000**. The server binds to loopback only. **Check Mizan Setup.cmd** reports anything missing; **Reset Mizan Demo.cmd** restores clean demo data (the old database is kept in `data/backups/`).

Demo accounts: `admin`, `registrar`, `chair`, `professor`, `student`, `hiring_manager`. The default demonstration password is `Mizan-demo-2026!`. These are intentionally local demo identities, not institutional authentication. Set `MIZAN_DEMO_PASSWORD` before starting to override the shared demo password.

The initial fixtures contain 1,500 fictional students, 80 courses, 100 sections, 40 rooms, and 50 professors. The baseline, diagnostic, staffing-shortfall and faculty-week scenarios are separate. Your changes are saved in `data/mizan.sqlite3`; restarting does not reset them (use Reset Mizan Demo.cmd).

## Fresh setup

Prerequisites: Python 3.12+ and Node.js 24+ (pnpm is fetched through npx when it is not installed). The setup script accepts explicit `-Python` and `-Pnpm` paths. The fine-tuned coordinator adapter ships in `.models/`; the base model and runtime are downloaded and checksum-verified by `install_model_runtime.py`.

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
