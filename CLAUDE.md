# MIZAN — project notes for Claude Code

Local-first university scheduling + workforce + recruitment assistant (Farq hackathon, university-operations track).
Spec: `docs/MIZAN - Project Documentation v3.md` (six agents, deterministic tools, human approval). Everything runs locally; no external AI APIs.

## Layout
- `backend/` FastAPI app (`backend.main:app`), SQLite in `data/mizan.sqlite3`. Agents: `agent_engine.py`; model client: `local_model.py`; solver: `solver.py` (OR-Tools); metrics/validation: `analysis.py`; recruitment: `recruitment.py`.
- `frontend/` React 19 + Vite 7 + TS (pnpm). Built output `frontend/dist/` is what the app serves. Rebuild: `cd frontend; pnpm install; pnpm build`.
- `.models/qwen3-8b.gguf` live model; `.models/mizan-coordinator-lora.gguf` fine-tuned coordinator adapter.
- `.runtime/ollama/lib/ollama/llama-server.exe` — bundled llama.cpp server (Ollama daemon is NOT used; `ollama` CLI is not on PATH).
- `training/coordinator/` — coordinator fine-tuning experiment (see below). `base/`, `checkpoints/`, `cache/` are git-ignored.
- `.venv` = app env (Python 3.12). `.training-venv` = training env (torch 2.8.0+cu128, bitsandbytes, peft, transformers 4.57).

## Run
- `Start Mizan.cmd` → `scripts/start.ps1` → starts model (`scripts/start-model.ps1`, port 11435) + app on http://127.0.0.1:8000. Demo password `Mizan-demo-2026!`; roles admin, registrar, chair, professor, hiring_manager, student.
- `scripts/restart-model.ps1` restarts llama-server (reloads adapter). `Apply Mizan Update.cmd` → `scripts/apply-update.ps1` restarts model, runs deployed eval, restarts app.
- Tests: `scripts/test.ps1` (pytest, 31 tests incl. `tests/test_update_v3.py`). Browser e2e: start a server on port 8001 with `MIZAN_DB` pointing to a fresh file under `work/`, then `node tests/browser-smoke.cjs` (all 5 checks passed on 2026-09-24).
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

## Project status / next steps
- Phase 1 approved; Phase 2 (six agents + recruitment) under user review as of 2026-09-25; Phase 3 (final verification & delivery) not started.
- Next: user's review fixes → hand-written test set → walk the 12 acceptance criteria (spec §13) → Farq demo script (3 scenarios in spec §15) + reset script + deck.
- Housekeeping: today's changes are uncommitted in git; `work/ollama-0.34.3.zip` (1.4 GB) and `training/coordinator/checkpoints/epoch-*` can be deleted.

## Conventions
- Keep everything local; loopback-only model URL is enforced in `local_model.base_url()`.
- Hard constraints are enforced by code, never by the model; no publication/hiring without human approval.
- Arabic + English parity for every UI string (`t(en, ar)` helper); use logical CSS properties for RTL.
