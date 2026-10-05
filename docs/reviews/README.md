# Reviews and their status

Three reviews were done on 4 October 2026. This table maps every finding ID to what changed and the test that pins it. "Partly" and "Open" items are listed honestly.

- [2026-10-04-ux-review.md](2026-10-04-ux-review.md): hands-on usability review (IDs S, I, C, X)
- [2026-10-04-expert-review-1.md](2026-10-04-expert-review-1.md): expert panel, code reading
- [2026-10-04-expert-review-2.md](2026-10-04-expert-review-2.md): expert panel, second pass with runs. It reviewed the last *committed* version, so some findings it repeats (AI-1, DATA-1, DOC-1, DOC-4) were already fixed in the working tree at the time.

Tests: `tests/test_ux_review.py` (UX review), `tests/test_review_v2.py` (expert reviews), `tests/test_edugate.py` (readiness), `tests/browser-smoke.cjs` (flows). Full run: [../test-log-2026-10-04.txt](../test-log-2026-10-04.txt).

## Usability review

| ID | Status | Where |
|---|---|---|
| S01 click opens details | Fixed | `InteractiveTimetable.tsx` (onClick for read-only roles) |
| S02 occupancy | Fixed | `GET /scenarios/{sid}` `enrollment`; `test_occupancy_agrees_across_roles_without_rosters` |
| S03 instructor names | Fixed | student response `professors` (names only); `test_student_isolation_and_server_authorization` |
| S04 student landing | Fixed | `StudentWeek.tsx` (next class, today, published changes; timetable before numbers) |
| S05 metric explanations | Fixed | `StudentWeek.tsx` |
| S06 eligible sections | Partly: grouped, search, comparison, shortlist; no timetable preview | `StudentWeek.tsx` |
| S07 search empty state | Fixed | `InteractiveTimetable.tsx` |
| S08 demo vs official | Partly: labelled "Demo timetable · (current)" | `main.tsx` |
| I01 professor workspace | Fixed | "My teaching week" / "My requests" |
| I02 no-op proposal | Fixed | `/changes` 422; `test_unchanged_meeting_is_not_a_request` |
| I03 preview before submit | Fixed | `ChangeForm.tsx`, preview-change `alternatives` |
| I04 form constraints | Fixed | `ChangeForm.tsx` |
| I05 grouped conflicts | Fixed | `Conflicts.tsx` |
| I06 section picker | Fixed | `FreeSlotFinder.tsx` |
| I07 stale slot results | Fixed | `FreeSlotFinder.tsx` |
| I08 slot next step | Partly: Copy, Request this time; no saved shortlist | `FreeSlotFinder.tsx` |
| I09 all days | Fixed | `FreeSlotFinder.tsx` |
| I10 AI availability | Fixed | `RequestAssistant.tsx`, `/agents/status` for professors |
| I11 handoff keeps destination | Fixed | `ChangeForm` `handoff` |
| I12 action names | Fixed | Preview impact / Prepare request / Send for review |
| I13 own optimization findable | Fixed | `test_professor_sees_own_optimization_in_their_list` |
| I14 drafts kept | Partly: drafts kept; no discard warning | `api.ts` `useDraft` |
| I15 local scope first | Fixed | `Proposals.tsx` |
| C01 approve → publish | Fixed | `ProposalDetail`; browser smoke |
| C02 stale proposals | Fixed | `stale`, `/proposals/{pid}/reevaluate`; `test_stale_proposals_are_flagged_and_can_be_reevaluated` |
| C03 queue narrative | Partly: no affected-cohort filter | `Proposals.tsx` |
| C04 harm vs benefit | Fixed | `Proposals.tsx` |
| C05 dense timetable | Partly: hour overview + drill-down; no zoom/lanes | `InteractiveTimetable.tsx` |
| C06 timetable first | Fixed | `main.tsx` tools tabs |
| C07 section IDs | Fixed | `FreeSlotFinder.tsx` |
| C08 placement comparison | Fixed | `main.tsx` placement modal |
| C09 invalid baseline | Partly: "Fix conflicts first", grouped findings; no progress tracker | `main.tsx` |
| C10 recoverable failures | Partly: plain errors, retry, elapsed time; no cancel | `api.ts`, `main.tsx` |
| C11 permissions explained | Fixed | `main.tsx` read-only notes |
| C12 staffing next step | Fixed | `main.tsx` workforce |
| C13 audit context | Fixed | `/audit` scenario fields; `test_audit_entries_name_their_timetable` |
| X01 scoped errors | Fixed | `main.tsx` |
| X02 stable links | Partly: page, timetable, proposal; filters not in the link | `main.tsx` hash routes |
| X03 exact decision values | Fixed | `ui.tsx` `Metric still` |
| X04 Arabic | Partly: common errors and labels; no full language review | `api.ts`, `main.tsx` |
| X05 account menu | Fixed | `main.tsx` |
| X06 record paging | Fixed | `main.tsx` |

## Expert reviews (1 and 2)

| ID | Status | Where |
|---|---|---|
| COR-1 preview vs proposal | Fixed: preview is "feasible" only if the result could be approved; "adds no conflicts, but N exist" shown | `preview-change` `blocked_by_existing`; `test_preview_and_proposal_agree_when_conflicts_already_exist` |
| COR-2 import raises capacities | Fixed: only placeholder capacities are raised and every raise is reported; verified rooms are never raised | `edugate_routes.build` notes; `test_import_reports_raised_capacities_and_never_raises_verified_rooms` |
| COR-3 rule checker groups | Fixed: full enrollment pattern | `rules._break_groups`; `test_rule_checker_sees_every_student_pattern` |
| COR-4 students at risk | Fixed: 36 without a seat of 112 demanding | `solver._unseated`; `test_students_at_risk_counts_only_unseated` |
| COR-5 optimizer variance | Already deterministic (fixed seed, 4 workers); rehearse on the demo laptop | `solver.py` |
| SEC-1 shared password | Fixed: refused from other computers unless `MIZAN_DEMO_PASSWORD` is set; pre-fill only on localhost | `main.login`; `test_shared_password_refused_from_other_computers` |
| SEC-2 professor redaction | Test added across professor endpoints; allow-list schema still open | `test_professor_responses_never_contain_student_identities` |
| SEC-3 uploaded schedules | Fixed: file not stored (as before); audit keeps a one-way code, not the ID; import screen states what is saved | `test_audit_never_holds_a_raw_student_id` |
| SEC-4 cookie Secure | Fixed: Secure over HTTPS | `main.login` |
| UX-C-1 evening classes | Fixed: visible hours follow the policy and the meetings | `InteractiveTimetable.tsx` |
| UX-C-2 headline vs diagnostics | Fixed: headline changes when the timetable is invalid; bar colour caption clarified | `main.tsx` |
| UX-P-1 hatched band, clipped titles | Fixed: legend entry and full-name tooltips | `InteractiveTimetable.tsx` |
| UX-H-1 requirements editor | Fixed: confirmation before approving; backend already rejects weights below 1 | `RecruitmentWorkspace.tsx`, `recruitment.py` |
| AI-1 coordinator claim | Fixed: three-arm measurement 75 → 96 → 106 | `training/coordinator/deployed_ablation.md` |
| AI-2 weakest case | Disclosed; the final disposition is computed by code | `deployed_ablation.md`, `agent_engine.run_collaboration` |
| AI-3 Ask Mizan wording | Fixed: "Draft interpretation"; acceptance report states 7/30 as below usable | `RequestAssistant.tsx`, `acceptance-report.md` |
| AI-4 shared model lock | Open: do not demo Ask Mizan during an agent run | — |
| DATA-1 generated headline | Fixed: overview note, demo script, evidence (the deck no longer has demo slides; the presenter says it during the live demo) | `main.tsx`, `evidence.md` |
| DATA-2 10% room use | Fixed: no comparison with real figures | `evidence.md` |
| CODE-1 monolithic source | Partly: new modules split out; generated API types still open | `frontend/src/*` |
| PERF-1 agent polling | Fixed: polls only while a run is queued or running | `AgentWorkspace.tsx` |
| PERF-2 solver progress | Partly: elapsed time shown; no best-so-far | `main.tsx` |
| DOC-1 "Met" vs 7/30 | Fixed: AI results table and test log | `acceptance-report.md` |
| DOC-2 review not in repo | Fixed: this folder | — |
| DOC-3 model-off rehearsal | Open: rehearse the demo once with the model stopped | — |
| DOC-4 test count | Fixed: counts come from the dated log | `test-log-2026-10-04.txt` |
