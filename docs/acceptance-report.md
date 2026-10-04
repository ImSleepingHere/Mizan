# MIZAN — acceptance report (spec §13 and §18.7)

Checked on 27 September 2026 against branch `redesign/v4`; re-checked on 4 October 2026 (evening) on `main` plus the Edugate exchange and the UX-review fixes. Every result below comes from one run recorded in [test-log-2026-10-04.txt](test-log-2026-10-04.txt).

"Met" means the criterion's condition holds and a test or log shows it. Where a criterion is about how something is measured rather than how good it is (13), the measured result is stated next to it so "Met" is never read as "good enough".

| Suite | Result (4 Oct, see log) |
|---|---|
| Python (`scripts/test.ps1`, 99 tests) | 99 passed |
| Browser smoke (`tests/browser-smoke.cjs`, fresh database) | 5/5 checks passed, plus the EN/AR parity check |
| Browser phase 2 (`tests/browser-phase2.cjs`, live Qwen3-8B + fine-tuned coordinator) | Passed: agent run completed, recruitment assessed and chatted, Arabic mobile without overflow |
| Browser Edugate (`tests/browser-edugate.cjs`, an app screenshot and an Edugate PDF, not in the repository) | Both passed: 6 rows read, imported, optimized, exported |

## AI results against what they are for

| Component | Measured result | Target / what it means | Assessment |
|---|---|---|---|
| Fine-tuned coordinator (`training/coordinator/deployed_ablation.md`) | 75 → 96 (better prompt) → 106 of 120 (fine-tuned); fine-tuning alone 14 fixed / 4 broken, p ≈ 0.03 | Route the six agents correctly; synthetic benchmark generated like the training data | Useful but modest; workflow-level only, not real-world ability. Code decides hard rules and the final outcome |
| Ask Mizan request interpreter (`training/interpreter/results_test.json`) | 7/30 fully correct (Arabic 5/19); per field 22–30/30, time windows weakest | Draft an interpretation a person confirms | **Below a usable level for unattended use.** Kept only because nothing runs without the user's confirmation and code-side checks; described as "drafts an interpretation", never "understands" |

## Criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Reproducible local dataset can be generated/imported and explored | Met | `fixtures.generate*` (fixed seeds); `test_import_export_roundtrip_and_invalid_references`; Semester records and timetable in the UI |
| 2 | Metrics match hand-checked fixtures, incl. repeated meetings and boundary times | Met | `test_valid_baseline_and_hand_computed_metrics`, `test_adjacent_meetings_do_not_overlap`, `test_hand_checked_ranking_and_counts`, `test_forty_five_minute_grid` |
| 3 | Every recommended schedule passes independent validation | Met | `solver.optimize` re-validates every candidate; `test_agents_validate_before_proposal_and_do_not_publish`, `test_invalid_change_blocked_and_alternatives_validated`, `test_checker_catches_each_violation_independently` |
| 4 | Solver distinguishes feasible, optimal, infeasible, unknown/time-limited | Met (new tests) | `test_time_limited_search_is_unknown_and_keeps_the_timetable`, `test_unknown_result_never_becomes_a_proposal`, `test_small_search_is_optimal_only_within_its_neighbourhood`, `test_infeasible_rules_are_diagnosed_and_timetable_kept` |
| 5 | Comparisons use the same population and versioned settings | Met (new tests) | `test_comparison_refuses_a_different_population`, `test_proposals_record_the_versioned_settings_they_used`, `test_policy_invalidates_approval` |
| 6 | Agents show at least one evidence-driven revision | Met (new test) | `test_impact_review_drives_a_scheduling_revision`: first search yields no candidate → Change Impact requires revision → Scheduling reruns → Impact re-checks → recommendation |
| 7 | Workflow stops within budgets and fails without unsupported conclusions | Met (new test) | `test_budgets_stop_the_run_without_a_conclusion` (wall-clock budget and a coordinator that never finalizes), `test_cancelled_run_never_calls_model`, `test_model_unavailable_or_unparseable` |
| 8 | Workforce separates proven shortage from an inconclusive solver run | Met | `test_shortage_is_a_capacity_proof_not_a_timeout`, `test_requisition_requires_proven_shortage`, `test_stale_shortage_cannot_authorize` |
| 9 | Recruitment assessments trace to approved criteria and evidence; unknowns visible | Met | `test_source_checks_staleness_and_html_escape` (verbatim quotes only, unknowns kept), candidate brief shows source CV unchanged |
| 10 | No publication, rejection, hiring or outreach without human authorization | Met | `test_approval_publication_and_stale_rejection`, `test_cv_upload_and_rejection`, agents never publish; no outreach channel exists (LinkedIn/email not connected) |
| 11 | Arabic and English show identical verified facts with correct RTL | Met (new check) | Browser smoke compares every overview figure in EN and AR (incl. the room-use ring and legend added with the campus overview) and asserts `dir=rtl`; phase-2 checks Arabic mobile layout |
| 12 | Stale approvals, unauthorized access, malicious imported instructions are checked | Met (strengthened) | Stale: `test_policy_invalidates_approval`; access: `test_student_isolation_and_server_authorization`, `test_hiring_role_cannot_access_student_records`, `test_csrf_guard_and_logout`; injection: new `test_cv_instructions_are_ignored_even_if_the_model_obeys_them` — instruction-like CV text is never counted as evidence and the CV is flagged |
| 13 | Handwritten request set frozen and scored once | Met (process). **Result: 7/30 strict, below a usable level** | `test_frozen_test_set_is_unchanged`; scored once, `results_test.json` blocks rescoring. See "AI results" above |
| 14 | Each rule has a solver test; candidates pass the independent rule checker | Met | `tests/test_rules.py` (one test per rule family) |
| 15 | Professor scope enforced by code; no student identities exposed | Met | `test_optimizer_moves_only_movable_sections`, `test_professor_cannot_move_others_sections`, `test_professor_previews_and_changes_are_redacted`, `test_professor_improves_own_classes_without_student_identities` |

## Changes made during this check

- Recruitment (`backend/recruitment.py`): a quote that reads as an instruction to the reviewer or model (English or Arabic) is never accepted as evidence, even if it appears verbatim in the CV; such CVs carry a visible flag. Previously a compromised model could quote an injected line as "evidence".
- New tests: `tests/test_acceptance.py` (7) and two agent tests in `tests/test_agents.py`.
- Browser smoke now asserts that Arabic and English overview figures are identical.
- `tests/browser-phase2.cjs` updated for the redesigned overview heading.
- 4 Oct re-check: the local `frontend/dist` build (git-ignored) predated the last `main.tsx` edit, so the frontend was rebuilt before the browser runs; the parity check now also reads `.campus-ring` and `.campus-room-legend` figures.

## Known limitations (honest, not blockers)

- Semester-wide optimization is time-limited (15 s in the demo): results are `FEASIBLE` within the searched neighbourhood and can differ slightly between runs. The UI never calls them globally optimal.
- Request interpretation (Ask Mizan) scored 7/30 strict on the frozen handwritten set; no misread request can change the timetable without the user's confirmation and code-side checks.
- Deferred features (spec §18.8): dated changes/term calendar, session length, online sessions, merged dated sessions, room locations, approval levels, notices.
- Data is synthetic; no institutional deployment is claimed.
