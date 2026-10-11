# Change log

## 6.2 — 5 October 2026 (audit fixes)

- Break rules bind only what the request can move: a short break between two sections outside the request's scope no longer makes a student or professor break rule infeasible (solver and independent checker). A one-free-block rule applies only on days where a section in scope meets.
- A rule request the official timetable already meets returns "no change is needed" instead of an unrelated optimization proposal (`already_satisfied`). Explicit move/room requests still run.
- The agent run's "max students worse off" limit is now a solver constraint (`solver.optimize(max_worsened=)`, full model and LNS), so Change Impact no longer rejects every revision on mixed-roster semesters. Faculty week, 0 worse off: 686 h saved with 5 changes.
- Hiring-criteria filter matches whole words: "Embraces …" is no longer rejected; "Racial …" and "Religious …" are now caught.
- Edugate import/verify refuse (409) when the timetable changed between reading and writing, instead of a 500.
- Common time finder: one session for several sections needs a room for every distinct student, not just the largest section.
- Conflict lists count every student: per-student conflicts collapse to one line per class pair with an exact `student_count` before any truncation (`analysis.condense_issues`). The change preview showed "18 students are enrolled in both" for a 75-student clash because only the first 20 conflict rows were sent.
- Normal optimization: presolve probing is off in the full model (as in LNS). It used ~7 of 10 s on the baseline, so "Optimize semester" with 2 changes ended `UNKNOWN`; it now proves the 2-change optimum (750 h, 0 worse off) in ~6 s. Other limits and the three plans give the same results.
- Semester lab shows what the latest publish moved: it opens on a changed cohort, marks moved classes "Moved" (previous time in the tooltip), and offers "Show only moved classes". Staff and professors now receive `recent_changes`.
- 25 new tests (`tests/test_audit_fixes.py`); 165 passed; browser smoke and plan suites pass.

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
