# MIZAN — ميزان

A local-first university scheduling, workforce and recruitment assistant. MIZAN measures student waiting time, compares feasible improvements, shows the trade-offs, and requires human approval before timetable publication. English and Arabic interfaces are included.

## Documentation

- [Project documentation v6](docs/MIZAN%20-%20Project%20Documentation%20v6.md): complete system, architecture, roles, APIs and limitations.
- [Handover and setup](docs/HANDOVER.md).
- [Three-plan comparison](docs/three-plan-comparison.md).
- [Release verification](docs/release-verification.md) and [change log](CHANGELOG.md).
- [Push to GitHub](docs/GITHUB-PUSH.md).
- [AI briefing](docs/AI-BRIEFING.md) and [evidence](docs/evidence.md).

## New in this release

Compare **Most time saved**, **Fewest changes**, and **Balanced impact** against the current timetable. Inspect student benefits and harms, changed sections, campus days and conflict counts. Select a plan to prepare a proposal, then approve and publish through the normal review process. Outdated, duplicate and unsuccessful searches are disclosed. The comparison uses deterministic optimization and works without an AI model.

This release also corrects shared imported-instructor identity, numeric student-ID redaction, small-room readiness, availability preservation and interpretation-preview consistency. Temporary yellow demo highlights are removed.

## Install and run (Windows)

Install **Python 3.12** and **Node.js 24**. From the project folder:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

Open http://127.0.0.1:8000. Sign in as Administrator using the pre-filled demo password `Mizan-demo-2026!`. Other demo roles: registrar, chair, professor, student, hiring_manager. This is local demonstration authentication.

For optional Ask Mizan, agent collaboration and CV inference, install the pinned local model/runtime:

```powershell
.\.venv\Scripts\python.exe scripts\install_model_runtime.py
```

The multi-GB base model and runtime are downloaded separately; the coordinator adapter and its upstream licence are included. AI startup checks and reported benchmark results do not establish model accuracy on real institutional data.

## Verify

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test.ps1
```

The GitHub workflow runs the Python suite and a frozen frontend build. Browser tests must use isolated databases: see [release verification](docs/release-verification.md). They create and publish fictional proposals.

## Repository contents

`backend/`: FastAPI, SQLite, OR-Tools and validation. `frontend/`: React/TypeScript/Vite with local fonts. `tests/`: domain/API/browser regression suites. `scripts/`: setup, launch, model installation and test tools. `docs/`: project specification, handover and recorded evidence. `training/`: synthetic training/evaluation evidence.

Initial scenarios are fictional. User-reviewed Edugate imports may contain real records and remain in local `data/`. Databases, work files, dependencies, secrets, runtime binaries and the base model are Git-ignored. The delivery ZIP includes a rebuilt website for convenience; Git excludes `frontend/dist/`, which setup recreates.

## Practical limits

Time-limited bounded searches may return no plan; zero student harm is measured, not guaranteed. Imported schedules omit external bookings and unimported students. Actual instructor qualifications, availability and contracts require institutional verification. Windows OCR needs installed English/Arabic language support. AI calls need a separately installed local model, can be slow on CPU, and were not freshly rerun for this handover. Exact demo laptop rehearsal and institutional deployment are separate checks.
