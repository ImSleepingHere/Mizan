# Release verification — 5 October 2026

## Delivered result

A clean local hackathon application with the three-plan comparison, imported-timetable correctness/privacy fixes, updated documentation and a GitHub verification workflow. Temporary yellow feature-tour markers are removed. This is a tested local handover; institutional production deployment and the exact presentation laptop are not certified.

| Check | Result | Scope |
|---|---|---|
| Full backend suite in review environment | **129 passed**, 2 dependency deprecation warnings, 73.34 seconds, no skips | Existing domain/API/agent-tool checks, 19 comparison tests and 11 release regression cases |
| Fresh setup from clean delivery folder | **Passed** | Windows PowerShell setup; selected Python 3.12; installed pinned backend packages; pinned pnpm 12.9.1 frozen install and frontend build |
| Full suite in newly installed delivery environment | **129 passed**, 2 dependency deprecation warnings, 74.79 seconds, no skips | Confirms the shipped source with its newly provisioned dependencies |
| Final TypeScript/Vite production build | **Passed** | Includes English/Arabic readiness and validation error text |
| Three-plan browser regression | **Passed** | Real solver, no proposals on search, metrics, EN/AR parity, desktop/mobile, select, approve, publish and outdated comparison protection |
| Main browser smoke | **5/5 passed** plus parity | Placement/approval/publication, rejected conflicts/alternatives, shortage/requisition, optimization/evidence, student access |
| Edugate browser regression | **Passed** | Fictional 4-row PDF read/review/import/optimize/export |
| Local launch and static assets | **Passed** | Delivered environment served health API and rebuilt UI on loopback |
| Git exclusions | **Checked** | Virtual environment, databases, work files, node_modules, frontend/dist, base model and runtime excluded from Git |
| GitHub Actions configuration | **Included** | Hosted run is pending the owner's push; not represented as executed |
| Live AI inference and benchmark | **Not rerun** | Tests use deterministic tools and isolated/mock model paths. Historical deployed evidence is separately dated |
| Actual presentation laptop and real personal documents | **Not tested** | Rehearse on the exact laptop; all release fixtures are fictional |

The two warnings concern upstream Starlette/httpx and AnyIO deprecated interfaces, with no test failures.

## Corrected review findings

- Same imported instructor: sections now link to a common stable ID; overlaps are visible to the independent validator. An explicit ID disambiguates people with identical names.
- Numeric/non-ST student IDs: student overlap and prerequisite records are redacted by their semantics for professor responses; a real API preview regression covers numeric IDs.
- Small rooms: placeholder section capacity is reconciled, actual verified section capacity remains separate, and enrollment overflow is still reported.
- Readiness: verified facts and conflict-free publication eligibility are separate.
- Further imports: preserve existing room/professor availability.
- Ask Mizan preview: an invalid baseline is not marked feasible merely because a move adds no new conflicts.
- Setup ambiguity: chooses Python 3.12 and rejects other versions before environment creation.
- Line endings: canonical benchmark normalization retained; `.gitattributes` added.

## Boundaries

Comparison and ordinary scheduling work without AI assets. Ask Mizan, agents and CV inference require the separately installed base model/runtime. The adapter is shipped; multi-GB runtime/base weights, dependencies, databases and personal records are excluded from the archive. Setup requires network access; installed deterministic operation is local.

Zero student harm is reported when measured, not guaranteed by ordinary optimization. Comparison objectives are bounded to allowed options and can return duplicate or unavailable plans. Unknown means not proved feasible within time, not proved impossible. Imported schedules omit external bookings and unimported students; instructor qualifications, contracts and availability need institutional review. Existing imports verified under the old implementation should have their instructors re-verified with stable IDs.

## Repeat checks

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
powershell -ExecutionPolicy Bypass -File scripts\test.ps1
```

Browser suites create and publish fictional data. Start each on an isolated database and loopback port:

```powershell
$env:MIZAN_DB = (Join-Path (Get-Location) 'work\browser-test.sqlite3')
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

In a second terminal, set `MIZAN_TEST_URL=http://127.0.0.1:8001` and run `node tests/browser-plans.cjs` or `node tests/browser-smoke.cjs`. Use a different fresh database per suite. Both require Chrome (or `MIZAN_BROWSER=msedge`). Edugate additionally requires a fictional PDF/image via `EDUGATE_FILE`. The Windows OCR test may skip on hosts without OCR support; it ran here.

Raw release logs: [release-test-log.txt](release-test-log.txt), [release-browser-log.txt](release-browser-log.txt).
