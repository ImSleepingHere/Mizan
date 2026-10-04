# Mizan — Expert Panel Review (read-only)

Reviewed 4 October 2026. Nothing in the repo was modified, and nothing was run.

## Scope and confidence

**Read in full or in the relevant part:** CLAUDE.md, README.md, `docs/` (v4 documentation, acceptance-report, demo-script, evidence, HANDOVER), all of `backend/*.py` (main, models, store, solver, analysis, rules, edugate, edugate_routes, request_routes, interpreter, agent_engine, agent_routes, recruitment, local_model, fixtures), `scripts/*.ps1`, all of `frontend/src/*.tsx|ts`, five test files (`test_ux_review`, `test_api`, `test_acceptance`, `test_scope`, `test_edugate`), `training/coordinator` (report, protocol, manifests, summaries, `deployed_eval.py`, `train.jsonl`/`test.jsonl`), `training/interpreter` (README, scoring, eval), and four screenshots (`work/ux/admin-invalid.png`, `prof-week.png`, plus `student.png` and `admin-detail.png` staged, not examined in detail).

**Not read:** the other tests (`test_agents`, `test_rules`, `test_finder`, `test_interpreter`, `test_recruitment`, `test_domain`, `test_update_v3`, the `.cjs` browser tests), the CSS files, the pptx, the remaining screenshots, `requirements.lock.txt`. The excluded paths were not opened.

**Run:** nothing. This session has no shell on your computer, so no tests, no app, no solver. Every "80 tests passed" and every demo number below is **the repo's own claim**, not something I reproduced. Findings tagged `CODE` come from reading the cited lines (re-checked just before writing). Findings tagged `INFERRED` follow from the code but need the app to confirm. Findings tagged `SCREENSHOT` come from the named image.

**Only running the app can confirm:** solver variance between runs, whether the 4 Oct fixes behave in the browser, Arabic layout at real widths, LLM latency on the demo laptop, the actual behaviour of PDF/OCR on odd inputs, and anything about the live database.

**The 4 Oct usability-review fixes.** `docs/` does not contain `Mizan-UX-Review.md`, which the test file cites by ID. I could therefore only check that the five fixes with tests exist (S02, I02/I03, C02, I13, C13), and the code behind them reads correctly. I cannot say whether the full list is complete (see DOC-2).

---

## COR — correctness

### COR-1 · P2 · Preview says "feasible" by a different test than the proposal's "invalid"
- **Source:** CODE (`backend/main.py:347` vs `:112`)
- **Problem:** `preview-change` reports `feasible = not introduced`, where `introduced` is only the *new* issues versus the baseline. `save_proposal` marks the proposal `invalid` if there are *any* issues in the candidate. If a scenario already carries conflicts (the "Conflict diagnostics" scenario in `admin-invalid.png` shows 159), a move that adds none is previewed as feasible and then saved as `invalid` and cannot be approved.
- **Reproduce or check:** Open the conflict-diagnostics scenario, preview any harmless move, click Propose. Expect a proposal in state `invalid`, even though the preview said feasible.
- **Fix:** Use one definition. Either allow `recommended` when `introduced` is empty (and say "existing N conflicts remain"), or make the preview say "feasible, but the timetable already has N conflicts, so it cannot be approved".
- **Done when:** A test covers a scenario with pre-existing issues, and preview and proposal state agree.

### COR-2 · P2 · Edugate import silently raises capacities, which hides overbooking
- **Source:** CODE (`backend/edugate_routes.py:137-139`)
- **Problem:** `section.capacity = max(section.capacity, roster.get(sid, 0))` and the same for the room. An imported roster larger than the section or room capacity is "fixed" instead of reported. Room-capacity rules and room-use metrics then never flag it for imported data.
- **Reproduce or check:** Import a student set with 40 students in a 35-seat section. Check that no capacity issue appears and the section shows 40/40.
- **Fix:** Keep the stated capacity and report an over-capacity issue, or at minimum add an import warning listing every section that was raised.
- **Done when:** An import that exceeds capacity shows a visible warning or a validation issue.

### COR-3 · P2 · Student-load groups in the rule checker collide on their first section
- **Source:** CODE (`backend/rules.py:325`)
- **Problem:** `groups.setdefault(f"students {key[0]}…", ...)` keys the group on only the first section of a student's sorted section tuple. Two students who share a first section but differ in the rest map to one key, and only the first student's meetings are used (`setdefault`). Break rules (minimum break, day-to-empty) may be checked on the wrong student's week.
- **Reproduce or check:** Build two students with sections (A, B) and (A, C) and a minimum-break rule on C. Check whether the rule sees C's meetings.
- **Fix:** Key on the full tuple (`"|".join(key)`), or de-duplicate by meeting set.
- **Done when:** A test with two students sharing a first section but differing in the rest passes.

### COR-4 · P2 · "Students at risk" counts everyone who wants the course, not those left unserved
- **Source:** CODE (`backend/solver.py:273`, `students_at_risk=len(set(demand.students))`); demo-script step 3 shows "112 students at risk (red)".
- **Problem:** With 3 sections needed and 2 covered, 1 of 3 is uncovered, but all demand students are counted. The figure plausibly overstates the affected students by about 3×. A judge who asks "112 of how many?" gets an unflattering answer.
- **Reproduce or check:** On the Staffing-shortfall scenario compare `students_at_risk` with `uncovered_sections × section capacity`.
- **Fix:** Use the students who cannot be seated given covered capacity (`max(0, demand − covered × capacity)`), or relabel "112 students need this course; 1 of 3 sections is unstaffed".
- **Done when:** The label and the number describe the same quantity.

### COR-5 · P3 · Time-limited optimizer: headline numbers vary between runs
- **Source:** CODE + docs (`docs/demo-script.md`: "1,275–1,350", "about")
- **Problem:** Honest, but a demo that shows one number and then a re-run showing another invites "which is right?".
- **Fix:** Fix the solver seed and worker count for the demo path, or run the optimization once beforehand and say "about 1,800 hours" every time.
- **Done when:** Two consecutive runs on a reset database give identical results, or the script says "about" at every mention.

---

## SEC — security and privacy

### SEC-1 · P2 · One known demo password, pre-filled in the UI and baked into the front-end bundle
- **Source:** CODE (`backend/main.py:126`, `frontend/src/main.tsx:53`; also `docs/demo-script.md`, tests)
- **Problem:** `MIZAN_DEMO_PASSWORD` defaults to `Mizan-demo-2026!`, and the login form pre-fills `admin` and that password. Every role uses the same password. The server binds `127.0.0.1` (`start.ps1`), which limits this to the local machine. But if anyone starts uvicorn with `--host 0.0.0.0` for a judge's phone, the admin account is open.
- **Reproduce or check:** Search the built `frontend/dist` JS for the password string.
- **Fix:** Keep the pre-fill only when `health.mode == "local_demo"` and the host is loopback; refuse to start on a non-loopback host with the default password.
- **Done when:** Starting with a non-loopback host and the default password fails with a clear message.

### SEC-2 · P2 · Professor redaction is a blacklist
- **Source:** CODE (`backend/main.py:76-96`)
- **Problem:** `redact()` only replaces `adverse_students` and filters `records` entries beginning with `ST`. Any new response key that carries student ids or names (a new analysis field, an issue payload, the agent evidence JSON shown in the UI) leaks unless someone remembers to add it. Existing tests (`test_scope`, the professor tests) cover today's shapes only.
- **Reproduce or check:** As professor, fetch every `/api/*` GET and POST response (including `/agents/runs/{id}` evidence and `/proposals/{id}`) and grep for `ST\d{4}` and `Student \d{4}`.
- **Fix:** Add a test that walks all endpoints as professor and asserts no `ST\d+` and no student names appear. Longer term: build professor responses from an allow-list schema.
- **Done when:** A response-wide leak test exists and passes.

### SEC-3 · P2 · Uploaded real student schedules: retention is not evident
- **Source:** INFERRED (`backend/edugate_routes.py`, `edugate.py`; the exclusion of a real student's PDF in the brief suggests this is a real input)
- **Problem:** The Edugate import turns a real PDF (name and student ID) into a student record in the scenario database, and the OCR text passes through the server. I did not find, in what I read, a statement about what is kept (the PDF, the OCR text, the name/ID in audit rows).
- **Reproduce or check:** Import a PDF on a throwaway DB; inspect the DB tables and `work/` for stored name/ID, uploaded bytes, and audit payloads.
- **Fix:** Decide and document: do not keep the uploaded file; keep or hash the student ID; show the policy next to the upload.
- **Done when:** The import screen states what is stored, and a test checks the upload bytes are not persisted.

### SEC-4 · P3 · Session cookie lacks `Secure`; uploads are parsed in-process
- **Source:** CODE (`backend/main.py:133`; `backend/recruitment.py:126` opens DOCX as a zip)
- **Problem:** Cookie flags `httponly` and `samesite=strict` are good; `Secure` is absent (fine on loopback HTTP). DOCX zip handling in recruitment has a 5 MB upload cap on the client; I did not confirm a server-side decompressed-size cap.
- **Fix:** Set `Secure` when not loopback; cap uncompressed size and entry count when reading DOCX.
- **Done when:** A zip-bomb DOCX is rejected quickly.

---

## UX-S / UX-P / UX-C / UX-H — role experiences

### UX-C-1 · P2 · Timetable is hard-coded to 08:00–18:00
- **Source:** CODE (`frontend/src/InteractiveTimetable.tsx:11`: `OPEN=480, CLOSE=1080`)
- **Problem:** Any section starting before 08:00 or ending after 18:00 (evening classes, Edugate-imported real schedules, the 45-minute-grid scenario) is clipped or off-grid, and the drag-to-move ghost cannot target those slots. The solver's own window may differ.
- **Reproduce or check:** Import or create a section at 18:30–19:45 and open Semester lab.
- **Fix:** Derive open/close from the data (min start, max end, padded to the hour) and from the policy window.
- **Done when:** An 18:30 class renders fully and can be dragged.

### UX-C-2 · P2 · Overview headline contradicts its own diagnostics
- **Source:** SCREENSHOT (`work/ux/admin-invalid.png`)
- **Problem:** The page leads "Every hour of the week, in balance." while the same screen shows 15,150 h/week lost, 100% with 2h+ gaps and "159 violations detected. Quality score withheld." A judge reading the invalid scenario sees a tagline that reads as false. The first cohort bar is green at 12 h while the bars at 10 h are red or amber; the caption says "bar colour = department, number colour = how serious", which most viewers will read as severity colouring.
- **Fix:** Make the hero line state-aware (e.g. "Fix conflicts first" when invalid). Use one neutral colour for bars and encode severity only in the number or a marker.
- **Done when:** In the invalid state the hero never claims balance, and bar colour has one meaning.

### UX-P-1 · P3 · Professor week: unexplained hatched band and clipped titles
- **Source:** SCREENSHOT (`work/ux/prof-week.png`)
- **Problem:** A hatched block at 12:00–13:00 on Monday–Wednesday has no legend. Course titles on cards ("Design Studio 48") clip at two lines on short slots.
- **Fix:** Add a legend entry (blocked time / break) and a tooltip. Show full title on hover.
- **Done when:** The band is labelled; hover shows the full title.

### UX-S-1 · P3 · Student view: occupancy is shown but rosters are hidden; consistent with the fix
- **Source:** CODE (`tests/test_ux_review.py::test_occupancy_agrees_across_roles_without_rosters`)
- **Problem:** None found in code for the S02 fix: seat counts agree across roles and students see only themselves.
- **Done when:** (informational) the browser smoke check also asserts this on the Student week screen.

### UX-H-1 · P2 · Recruitment: free-text JSON state and a destructive "edit criteria invalidates assessments"
- **Source:** CODE (`frontend/src/RecruitmentWorkspace.tsx:7,13`)
- **Problem:** Criteria are held as a JSON string and re-parsed in every change handler. A malformed edit is swallowed by `try{...}catch{return null}` and the whole editor silently disappears. Weights are not checked to sum to 100. The "Approve updated requirements" button has no confirmation although it invalidates earlier assessments.
- **Reproduce or check:** Clear a criterion's weight field to empty and watch the editor.
- **Fix:** Hold criteria as an array in state; validate weights; confirm before approving.
- **Done when:** An empty field does not remove the editor, and approving shows the invalidation warning.

---

## AI — claims versus evidence

### AI-1 · P1 · "111/120 vs 75/120" mixes two changes (adapter and prompt) and is on in-distribution data
- **Source:** CODE (`training/coordinator/deployed_eval.py` docstring and `run`), RAN-by-repo (`deployed_eval_summary.json`), `coordinator_report.md`; demo-script closing line
- **Problem:** The deployed evaluation runs "pretrained" with the *original live prompt* and "fine-tuned" with the *training prompt*. The 111 vs 75 difference therefore combines the adapter and a prompt change, so it cannot be credited to fine-tuning alone. The cleaner paired NF4 comparison (same prompt, 116/120 vs 73/120) exists and is stronger. In addition, the test set comes from the same generator as the training data: the repo's own report says it measures "generalization within the implemented coordinator workflow, not real-world ability". My check found 0 exact context overlaps between `train.jsonl` and `test.jsonl`, but the cases are templated, and routing is largely a function of the state, which a small model can learn as a lookup. The demo script puts the 111/120 line in the closing.
- **Reproduce or check:** Run `deployed_eval.py` with the training prompt and adapter off; compare.
- **Fix:** Say "on a synthetic workflow benchmark generated like the training data", use the paired NF4 figures as the headline, and add the third arm (adapter off + training prompt) to the deployed run.
- **Done when:** The pitch figure names the benchmark as synthetic and in-distribution, and the confound is removed or disclosed.

### AI-2 · P2 · Weakest fine-tuned case is hidden by the aggregate
- **Source:** `training/coordinator/coordinator_report.md`
- **Problem:** `final_unchanged` is 4/8 (50%) for the fine-tuned model, the lowest cell. Disposition 96.7% means the model sometimes concludes "changed" when nothing changed. That is exactly the failure a judge would test live ("no improvement possible").
- **Fix:** Disclose it; the code-side validators already stop a false "changed" from publishing. Add a deterministic post-check that disposition matches `comparison.recovered_hours` and changed sections.
- **Done when:** The disposition is computed or verified by code, not only by the model.

### AI-3 · P2 · Ask Mizan: 7/30 strict is shown to the user as a working feature
- **Source:** `training/interpreter/README.md`, `docs/acceptance-report.md`
- **Problem:** Known item. What is worse than stated: the test set was written by the same author as the prompt (the README says so), the dev set has 18/40, and the time-window field is the weakest (22/30). For Arabic, 5/19 strict. The safety argument (confirm before run, code decides) is sound, but the pitch must not use the word "understands".
- **Fix:** In the UI and the pitch, say "drafts an interpretation for you to confirm". Show the "what I understood" panel prominently (already built).
- **Done when:** No slide or UI label claims reliable understanding.

### AI-4 · P3 · Interpreter and coordinator share one local model server with a lock
- **Source:** CODE (`backend/local_model.py:70-76`, global `LOCK`)
- **Problem:** Requests serialize. During an agent run (1–2 min) an Ask Mizan or recruitment call waits or times out. LoRA scales are set explicitly per request (good).
- **Fix:** Show "model busy" in the UI; do not demo Ask Mizan while agents run.
- **Done when:** Ask Mizan during an agent run shows a clear busy message.

---

## DATA — data and claims

### DATA-1 · P1 · The headline numbers are artefacts of the generator and read as results
- **Source:** CODE (`backend/fixtures.py`), `docs/evidence.md` §1, demo-script
- **Problem:** Known (synthetic data, poor baseline), but worse than stated in one way: the optimizer's improvement is also mechanical. Every cohort has identical 1-hour classes at 08/10/13/15/17 on two days, and moving one 17:00 section to 11:00 closes gaps for all 75 students in the group at once ("225 students better off" = 3 groups × 75; "≈1,800 h" = 225 × 8 h). The figure shows the solver finds the obvious move in a hand-built pattern, not how it performs on a real timetable. `evidence.md` does say this honestly; the demo script says it to the audience only as "synthetic".
- **Fix:** Put one sentence in the demo: "the starting timetable is deliberately poor; the point is that every change is checked and approved." Prefer a second scenario with irregular structure (random cohorts) for the optimizer demo if one exists.
- **Done when:** The slide that shows 15,000 h also states how the baseline was built.

### DATA-2 · P2 · "10% room use" is also constructed
- **Source:** `docs/evidence.md` §1 ("20 of 40 rooms used 10 of 50 weekly hours")
- **Problem:** The deck compares it to UK sector figures ("real UK buildings go as low as 10%"). The match is a coincidence by the repo's own words, yet it is framed as validation.
- **Fix:** Drop the comparison on the slide, or label it "illustrative".
- **Done when:** No slide implies the demo campus resembles a real one.

---

## CODE — code quality

### CODE-1 · P2 · Monolithic, minified-style source is hard to defend and to change
- **Source:** CODE (`frontend/src/main.tsx` 67 KB; `RecruitmentWorkspace.tsx` and `AgentWorkspace.tsx` are single-line-per-component, `type R=Record<string,any>` throughout)
- **Problem:** `any`-typed API results everywhere remove the benefit of TypeScript; a renamed backend field fails only at runtime. Dense one-line JSX makes review and accessibility audits hard.
- **Fix:** Generate TS types from the FastAPI OpenAPI schema; run Prettier; split `main.tsx` by route.
- **Done when:** `any` count drops sharply and `tsc` fails on a renamed field.

### CODE-2 · P3 · Duplicate state sources for criteria and chat in Recruitment, effect dependencies incomplete
- **Source:** CODE (`RecruitmentWorkspace.tsx:11-12`)
- **Problem:** `useEffect(..., [jid])` calls `refresh` that closes over stale `jid`/`candidates`; the second effect resets the chat whenever `jobs.length` changes.
- **Fix:** Fetch with an explicit id; do not reset chat on list refresh.
- **Done when:** Adding a candidate does not clear the recruitment chat.

---

## PERF — performance

### PERF-1 · P2 · Agent workspace polls every 3 s and refetches the run list
- **Source:** CODE (`AgentWorkspace.tsx:13`)
- **Problem:** `setInterval(refresh, 3000)` runs forever while the tab is open, fetching status, runs and the current run (with all events). On a 1,500-student scenario the evidence payloads are large. It continues even when no run is active.
- **Fix:** Poll only while a run is `queued|running`; fetch events since the last id.
- **Done when:** An idle page makes no periodic requests.

### PERF-2 · P3 · Single solver run blocks the demo for 15 s with no progress
- **Source:** docs (15 s time-limited search)
- **Fix:** Show elapsed time and the best-so-far objective.
- **Done when:** The dialog shows live progress.

---

## DOC — documents and pitch

### DOC-1 · P1 · The pitch's AI line and the acceptance report overstate "met"
- **Source:** `docs/acceptance-report.md` criteria 13 and 15; `docs/demo-script.md` closing line
- **Problem:** Criterion 13 is marked "Met" with "7/30 strict". The criterion is that the set was frozen and scored once, which is true, but a reader sees "Met" next to 7/30. The 80-test and browser results are self-reported with no CI log or hash in the repo.
- **Fix:** Add a column "result vs target" for the AI rows, and attach the pytest output to `docs/`.
- **Done when:** Each "Met" cites a reproducible log.

### DOC-2 · P2 · The 4 Oct review the code refers to is not in the repo
- **Source:** CODE (`tests/test_ux_review.py` docstring cites `Mizan-UX-Review.md`); `docs/` listing
- **Problem:** Fix IDs (S02, I02, I03, C02, I13, C13) cannot be traced. I cannot tell which review items remain open.
- **Fix:** Commit the review (or a status table of IDs → test/commit).
- **Done when:** Every ID in the tests resolves to a document row.

### DOC-3 · P3 · Demo script depends on several "if it misreads, skip" branches
- **Source:** `docs/demo-script.md`
- **Problem:** Steps 1.7, 2.5 and parts of 3 depend on the model; the script already provides fallbacks, but the main path should be model-free so the story is identical if the GPU fails.
- **Fix:** Rehearse the model-off path end to end once.
- **Done when:** A full 7-minute run succeeds with the model server stopped.

---

# Top 10 to fix first
1. **AI-1** — remove the prompt/adapter confound from the 111 vs 75 claim and name the benchmark as synthetic.
2. **DATA-1** — say on the slide how the baseline and the improvement are built.
3. **DOC-1** — make "Met" rows carry results and logs; stop "Met" next to 7/30.
4. **COR-4** — "students at risk" must match what is actually unserved.
5. **SEC-2** — add a response-wide leak test for the professor role.
6. **COR-1** — one definition of feasible for preview and proposal.
7. **UX-C-2** — hero text and bar colours must not contradict the invalid state.
8. **COR-2** — Edugate import must not silently raise capacities.
9. **SEC-1** — refuse the default password on a non-loopback host.
10. **UX-C-1** — derive timetable hours from the data.

# Judge questions we would struggle with
1. *"Is 15,000 gap hours a real measurement?"* — No. It is built by the generator (10 h × 1,500 students).
2. *"What does the optimizer do on a realistic timetable?"* — Untested; the demo improvement is one mechanical move repeated across identical cohorts.
3. *"Did fine-tuning cause 111 vs 75?"* — Partly. The deployed comparison also changes the prompt; the paired 116 vs 73 is cleaner but synthetic and from the training generator.
4. *"What happens when the model says nothing changed?"* — The fine-tuned model scores 4/8 on that case type; code safeguards stop a bad publish, but the narrative can be wrong.
5. *"7/30 — why ship Ask Mizan?"* — Because it only drafts and a person confirms; we cannot claim it understands requests.
6. *"112 students at risk — of what?"* — It counts everyone who wants the course, not those without a seat.
7. *"Could a professor see a student's identity?"* — Today no leak is known, but redaction is a blacklist and untested across all endpoints.
8. *"Who else could log in?"* — One shared demo password, pre-filled; safe only because of the loopback binding.
9. *"What happens to the real student schedule PDF you imported?"* — No stated retention policy.
10. *"Why does the same demo give different numbers twice?"* — Time-limited solver; results are "about".

# What is genuinely strong
- **Safety by construction:** the model only extracts or routes; code decides support, permissions and publication, with an independent validator re-checking every candidate and revision-based stale detection.
- **Honest evaluation hygiene:** a frozen, hashed handwritten test set scored once, with the weak 7/30 published, plus a paired statistical comparison for the coordinator.
- **Evidence discipline in the docs:** `evidence.md` separates measured demo numbers from cited research and lists claims not to use.
- **Recruitment grounding:** only verbatim quotes count as evidence, instruction-like quotes are rejected, and unknown stays unknown.
- **Local-first design with bilingual RTL UI** and a tested EN/AR parity check.
