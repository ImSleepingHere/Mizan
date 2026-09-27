# MIZAN — project notes for Claude Code

Local-first university scheduling + workforce + recruitment assistant (Farq hackathon, university-operations track).
Spec: `docs/MIZAN - Project Documentation v3.md` (six agents, deterministic tools, human approval). Everything runs locally; no external AI APIs.

## Layout
- `backend/` FastAPI app (`backend.main:app`), SQLite in `data/mizan.sqlite3`. Agents: `agent_engine.py`; model client: `local_model.py`; solver: `solver.py` (OR-Tools); metrics/validation: `analysis.py`; recruitment: `recruitment.py`.
- `frontend/` React 19 + Vite 7 + TS (pnpm). Built output `frontend/dist/` is what the app serves. Rebuild: `cd frontend; pnpm install; pnpm build`. node/pnpm are NOT on PATH: use `C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe` with `..\node_modules\pnpm\bin\pnpm.cjs`, and set `CI=true` (pnpm aborts without a TTY otherwise).
- `.models/qwen3-8b.gguf` live model; `.models/mizan-coordinator-lora.gguf` fine-tuned coordinator adapter.
- `.runtime/ollama/lib/ollama/llama-server.exe` — bundled llama.cpp server (Ollama daemon is NOT used; `ollama` CLI is not on PATH).
- `training/coordinator/` — coordinator fine-tuning experiment (see below). `base/`, `checkpoints/`, `cache/` are git-ignored.
- `.venv` = app env (Python 3.12). `.training-venv` = training env (torch 2.8.0+cu128, bitsandbytes, peft, transformers 4.57).

## Run
- `Start Mizan.cmd` → `scripts/start.ps1` → starts model (`scripts/start-model.ps1`, port 11435) + app on http://127.0.0.1:8000. Demo password `Mizan-demo-2026!`; roles admin, registrar, chair, professor, hiring_manager, student.
- `scripts/restart-model.ps1` restarts llama-server (reloads adapter). `Apply Mizan Update.cmd` → `scripts/apply-update.ps1` restarts model, runs deployed eval, restarts app.
- Tests: `scripts/test.ps1` (pytest on `tests/`, 64 tests incl. `tests/test_update_v3.py`, `tests/test_interpreter.py`, `tests/test_scope.py`, `tests/test_rules.py`; the script passes `tests` so pytest no longer crawls unreadable `work/` folders). Browser e2e: start a server on port 8001 with `MIZAN_DB` pointing to a fresh file under `work/`, then `node tests/browser-smoke.cjs` (all 5 checks passed on 2026-09-24).
- GPU: RTX 4080 SUPER 16 GB. llama-server holds ~5 GB RAM + VRAM; stop it before training.

## Fine-tuned coordinator (done, live since 2026-09-24)
- Protocol frozen in `training/coordinator/PROTOCOL.md`: Qwen3-8B NF4, attention-only LoRA r8/α16, 2 epochs, 480 train / 60 val / 120 test synthetic cases (balanced EN/AR). Runner: `run_experiment.ps1`; report: `coordinator_report.md`.
- Paired NF4 test: pretrained 73/120 pass → fine-tuned 116/120 (44 fixed / 1 broken). Epoch 2 selected (val loss 0.0258). Training took 12.6 min.
- Deployed (live GGUF + production JSON schema, `deployed_eval.py`): pretrained 75/120 → fine-tuned 111/120 (42 fixed / 6 broken, p≈1e-7). `deployed_eval_summary.json`.
- Remaining errors: says "recommend" for unchanged final candidates (harmless in app — `run_collaboration` computes disposition itself) and sometimes ignores "start with teaching capacity".
- Adapter applies ONLY to coordinator calls: `local_model.structured()` always sends per-request `lora` scales (1.0 for coordinator, 0.0 otherwise); coordinator uses `COORDINATOR_TUNED_PROMPT` (exact training prompt) + compact JSON. Rollback: env `MIZAN_COORDINATOR_ADAPTER=0`.
- Caveat: test set comes from the same generator as training data → measures in-workflow generalization only. More epochs NOT recommended; next is varied data + a hand-written messy EN/AR test set.
- Fixes made along the way: training venv torch had been overwritten with 2.14.0+cpu (repaired to 2.8.0+cu128); `train.py` lm_head dtype mismatch fixed with a forward pre-hook; `benchmark.grade` catches AttributeError.

## Frontend v3 (done 2026-09-24)
- New "Najd Night" theme (indigo sidebar, violet→saffron gradient, Sora headings), motion (page/card entrance, count-ups, animated bars, reduced-motion respected), overview hero.
- `frontend/src/InteractiveTimetable.tsx`: drag-and-drop meetings with live `POST /api/scenarios/{sid}/preview-change` (no DB write, ~70 ms), dock to submit as change request (`/changes`), detail drawer with keyboard move form, filters (cohort/room/faculty/department/search), lane layout for overlaps, Riyadh now-line. Professors edit only own sections; students read-only.
- Agent panel shows roster, LoRA-tagged coordinator events, fine-tuned badge; Settings shows real model/coordinator status.

## Spec v3.1: professor requests (plan approved 2026-09-27; spec §18)
- Why: 30 real professor requests; ~5/30 supported before. Items 1→4 in order, commit after each: 1 request interpreter, 2 "my classes" scope, 3 optimizer rules, 4 common free-slot finder. Later (after Farq): term calendar/dated changes, session length, online, merged dated sessions, room locations, approval levels, notices.
- User decisions: §18 lives inside the v3 spec file. Per-meeting different start times ONLY when a rule requires it; same-time default + soft penalty for split times + proposal shows "times split by rule X". New realistic demo scenario (NEW; existing scenarios/tests untouched): professor account owning S087–S091, mixed rosters, some Mon/Wed meetings, a few 75/90-min courses. No EXAM_SCOPE: finding a slot for a quiz/revision is the weekly free-slot finder; booking on a date is EXTRA_SESSION or DATED_CHANGE; finding with any date wording is in scope with `date_note`.
- Item 1 (done 2026-09-27): `backend/interpreter.py` — the model extracts fields only; code normalizes, applies conventions, decides support (bilingual reasons), asks questions, runs a date lexicon backstop that can only make scope more cautious, and resolves scope/permissions. `backend/request_routes.py` — `/api/requests/interpret`, `/{id}/revise`, `/{id}/confirm`, `/{id}/cancel`; table `request_interpretations`; audited; confirm runs only a read-only preview for exact single moves. Base model only (adapter scale 0; own_sections are not shown to the model). UI: `frontend/src/RequestAssistant.tsx` ("Ask Mizan" on Semester lab for admin/registrar/chair/professor).
- Item 2 (done 2026-09-27): new scenario `faculty` ("Faculty week · mixed rosters", `fixtures.generate_faculty`, seed 2027, valid by construction; seeded by `init_db` next to the other three). The `professor` account (P001) owns S087–S091 there (35 students each, capacity 35) (Sun/Tue, Tue/Thu, Mon/Wed, Sun/Thu; C047 75 min in S087+S089 = two sections of one course; C050 90 min); R040 hall seats 200 for merges. `solver.optimize(..., movable=)` fixes all other sections. Professors may call `/optimize` (own sections only, max_changes capped, proposal kind `own_optimization`, still needs committee approval) and `GET /scenarios/{sid}/my-classes` (aggregates). `main.redact()` strips student IDs from every professor response (preview, changes, proposals, optimize, request confirm) — this also fixed an existing leak of `adverse_students` to professors. UI: `frontend/src/MyClasses.tsx` on Semester lab. Whole-semester optimize on `faculty` hits the 10 s limit (UNKNOWN); own-scope runs OPTIMAL in ~1 s.
- Item 3 (done 2026-09-27): `backend/rules.py` — `RuleSet` (windows global/per-day, protected sections/meetings, locked days, keep day/time/room, breaks between_each|one_block for professor/students (one_block students not supported), day_to_empty, must_change, must_change_room, max_changes, scope), `from_interpretation`, option filter, per-meeting split options only when a rule is day-limited (`needs_split`), CP-SAT break constraints, independent `check_rules`, `split_reasons` ("times split by rule X"), and `optimize_with_rules` (on INFEASIBLE removes one rule at a time → `diagnosis.blocking_rules`; UNKNOWN is reported as not proven). `solver.optimize(rules=)` filters options, adds a split penalty (2× irregular weight) and re-checks candidates. Confirm of reschedule/room/inexact moves runs it and saves a `rule_change` proposal (chair: result only). Any request with DATED_CHANGE/DURATION/ONLINE/UNDEFINED never runs (`BLOCKING_CODES`); the user must correct "When" explicitly. Agent runs accept `limits['rules']` (tools only; Change Impact rejects rule violations). Realism note: in `faculty` many rules are genuinely INFEASIBLE because every alternative slot clashes with some students; the diagnosis says which rule. Protected/locked meetings also block room changes (bug caught by tests).
- Interpreter eval: `training/interpreter/` — frozen 30-case `handwritten_test.jsonl` (sha 74f8…e868; score ONCE after items 1–4 with `eval_interpreter.py --set test --final`), dev set of 40 (`dev_set.py`). Dev after prompt work: 18/40 strict, per-field 35–40/40, 0 silent guesses, 4 false flags (base Qwen3-8B). Prompt tuning stopped there on purpose.

## Project status / next steps
- Phase 1 approved; Phase 2 (six agents + recruitment) under user review; Phase 3 (final verification & delivery) not started.
- Next: v3.1 items 2 → 3 → 4 (then score the 30 once) → walk the acceptance criteria (spec §13 + §18.7) → Farq demo script (3 scenarios in spec §15) + reset script + deck.
- Housekeeping: ask the user before deleting `work/ollama-0.34.3.zip` (1.4 GB) or `training/coordinator/checkpoints/epoch-*`.

## Conventions
- Keep everything local; loopback-only model URL is enforced in `local_model.base_url()`.
- Hard constraints are enforced by code, never by the model; no publication/hiring without human approval.
- Arabic + English parity for every UI string (`t(en, ar)` helper); use logical CSS properties for RTL.
