# Change log

## 6.1 — 5 October 2026

- Whole-semester optimization on mixed-roster semesters (e.g. *Faculty week*, real imports) no longer ends `UNKNOWN`: a large-neighbourhood search (`backend/lns.py`) with the same objective reaches the full model's proven optimum in 5 s; the three-plan comparison now produces plans there too.
- Clearer outcome messages (EN/AR): a time-limited search is no longer described as "no feasible improvement" or "no change recommended".
- 11 new tests (`tests/test_lns.py`); 140 passed.

## 6.0 — 5 October 2026

- Three deterministic alternative plans with before/after metrics, class differences, persistence, duplicate disclosure, stale-version guards and normal human approval/publication.
- English/Arabic comparison and mobile-contained scrolling.
- Removed temporary yellow feature-preview annotations.
- Shared imported-instructor identity, explicit optional instructor IDs, and overlap detection.
- Preserved existing room/professor availability on subsequent imports.
- Reconciled assumed section capacity with verified rooms; actual section capacities supported by the verification API.
- Readiness now distinguishes verified facts from conflict-free publication eligibility.
- Numeric/non-ST student conflict and prerequisite identities redacted for professors.
- Ask Mizan preview rejects existing invalid baselines.
- Python 3.12 selection, pinned pnpm bootstrap, line-ending attributes, GitHub verification workflow.
- New v6 documentation; updated v5, README, handover, AI briefing and engineering notes.

Historical v3/v4 specifications and earlier evidence remain archived in docs. Current test results: docs/release-verification.md.
