# MIZAN engineering context — 5 October 2026

Current specification: `docs/MIZAN - Project Documentation v6.md`. Historical v3/v4/v5 context remains in docs. Current release evidence: `docs/release-verification.md`; change log: `CHANGELOG.md`. Do not present historical model results as fresh tests.

## Layout and conventions

- FastAPI `backend.main:app`; SQLite defaults to `data/mizan.sqlite3`. `MIZAN_DB` selects an isolated database.
- OR-Tools objectives: `backend/solver.py`; independent validation/metrics: `analysis.py`; comparison API: `plan_routes.py`.
- React 19/TypeScript/Vite; build via `npx.cmd --yes pnpm@12.9.1 run build` inside frontend. Frozen dependency installation required.
- Python 3.12 and Node 24; `scripts/setup.ps1`, `scripts/start.ps1`, `scripts/test.ps1`.
- All UI wording in English and Arabic; logical CSS properties for RTL. Preserve `DESIGN.md` and `PRODUCT.md`.
- All inference stays on loopback. AI model output never replaces deterministic validation. Approval and publication remain human actions.
- Never commit personal imports, databases, credentials, model runtime, base model or dependencies.
- Browser tests create and publish fictional proposals; use a fresh `MIZAN_DB` and separate port.

## Current features

Three-plan comparison: time saved, fewest changes, balanced impact; same revision, independent validation, persistence, duplicate/stale disclosure, explicit proposal selection. No external AI needed.

Edugate verification: shared instructor IDs (optional explicit ID, normalized-name fallback); preserve availability; reconcile assumed capacity; distinguish facts verified from valid readiness. Names can be ambiguous: explicit IDs are preferred. Institutional qualifications/contracts and other bookings remain incomplete.

Professor redaction strips identity-bearing student conflict records regardless of ID format. Ask Mizan preview accounts for invalid baselines. Frozen benchmark hashes normalize LF/CRLF. No temporary feature-tour CSS is shipped.

## Claims and remaining work

Historical deployed coordinator evidence: base/original prompt 75/120, base/training prompt 96/120, tuned 106/120; attribute only the final increment to tuning. Recorded interpreter score is 7/30 strict, an experimental draft assistant. These were not freshly rerun on this release. Zero harm is a measured run result, not an ordinary optimization constraint.

Exact Zenbook rehearsal, university authentication, department-scoped permissions, calendar/dated sessions, notifications, individual-harm constraints, full accessibility/language review, richer institutional data and live-model regression remain separate work. GitHub workflow is provided but its hosted run is only confirmed after pushing.
