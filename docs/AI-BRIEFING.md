# Briefing for an AI assistant joining the Mizan project

You can see this GitHub repository and nothing else. This file tells you what the repository can't: the situation, the decisions already made, what lives only on the owner's computers, the rules for claims, and what is still open. Updated 5 October 2026 for the GitHub handover; original event and machine context follows.

## 1. Read these first, in this order

1. `docs/MIZAN - Project Documentation v6.md`: what the system is and does today (authoritative; v4 and v3 are history).
2. `CLAUDE.md`: the running engineering notes (paths, commands, gotchas, decisions). `AGENTS.md` repeats conventions for other coding assistants.
3. `docs/reviews/README.md`: every review finding (IDs like S01, I03, C02, COR-4, AI-1) with its status, fix and test.
4. `docs/evidence.md`: which numbers may be used in the pitch, where each comes from, and which must not be used.
5. `docs/demo-script.md`, `docs/HANDOVER.md`, `docs/acceptance-report.md`, `docs/test-log-2026-10-04.txt`.
6. `training/coordinator/deployed_ablation.md`: the corrected AI result.

## 2. The situation

- **Event:** Farq Hackathon 2026, university-operations track, final on **5 October 2026** at Al Yamamah University. Mizan is branded for that university.
- **Organisers' rules (from their email, not in the repo):**
  - It must be a working solution, not just a prototype, and demonstrable live; judges may ask to try it.
  - The pitch is a **PowerPoint** (not a video), sized "1600 × 3096 px": the deck assumes **3096 wide × 1600 tall**, which is not yet confirmed with the mentor.
  - **5 minutes** of pitch plus 2 minutes of questions; every team member presents; start with a short team and idea introduction. The four judges have never seen the idea.
  - Judging criteria: understanding of the problem, innovation, user need, fit of solution to problem, potential and value, technical aspects, presentation and role split.
- **The deck:** `docs/Mizan-Farq-2026.pptx`, 8 slides, English, speaker notes on every slide. An Arabic version may be wanted later. Slide 1 holds the team names (edited by the owner).

## 3. What is NOT in the repository

| Missing from git | Where it is / why | What it means for you |
|---|---|---|
| `frontend/dist/` | Built locally by `scripts/setup.ps1` | Build before running: `cd frontend; CI=true npx pnpm install; CI=true npx pnpm build` |
| Base model `.models/qwen3-8b.gguf` (5.2 GB) and `.runtime/` (llama.cpp) | Downloaded by `scripts/install_model_runtime.py` | Without them, Ask Mizan, agents and CV analysis are off; everything else works |
| `data/` (live database), `work/` (logs, screenshots, test databases) | Local only | Screenshots referenced in reviews (e.g. `work/ux/*.png`) are not visible to you |
| The owner's real Edugate schedule PDF and phone screenshot | On the owner's desktop; the PDF contains a real student name and ID | **Never** ask for it to be committed or used as a fixture. Tests use invented rows and an OCR round trip |
| Original review files, the organisers' email, demo videos | Owner's desktop | Reviews are copied into `docs/reviews/`; email facts are in §2 above |
| Training checkpoints and base weights | Git-ignored | Results and predictions are in `training/coordinator/*.json` |

GitHub may lag the owner's working copy. If something in a review or chat doesn't match the code you see, the owner may not have pushed yet.

## 4. The machines

- **Development PC:** Windows 11, AMD Ryzen 7 9800X3D, **NVIDIA RTX 4080 SUPER 16 GB**. The model runs on CUDA (about a second per AI reply). All tests and the three-arm coordinator evaluation were run here.
- **Demo laptop:** ASUS Zenbook 14, Windows 11 Home, **AMD Ryzen with Radeon 840M graphics, no NVIDIA GPU**, 31 GB RAM, 772 GB free, Windows OCR languages Arabic and English installed.
  - `scripts/start-model.ps1` detects the missing NVIDIA GPU and runs the model on the processor; `scripts/start.ps1` raises the AI request timeout to 10 minutes.
  - Expect slow AI (tens of seconds per step; minutes for an agent run). Timetable features and the Edugate import run at full speed.
  - A Vulkan path for the Radeon graphics was tried and did not engage; it is deliberately not offered.
  - **Not yet tested on the laptop itself.**
- **Demo plan:** run the non-AI story live on the laptop (Edugate import → optimize → evidence → approve → publish; change request with 77 conflicts and 3 alternatives; staffing shortfall). Show the agent collaboration from a video recorded on the development PC (`scripts/demo/record-demo.cjs`). Don't run Ask Mizan while an agent run is using the model.

## 5. Rules for claims (non-negotiable)

These come from two expert reviews and were checked against the code and fresh measurements.

| Say | Never say |
|---|---|
| "In our demo semester of 1,500 synthetic students, the starting timetable is deliberately poor: 10 hours of gaps each per week. Mizan recovered about 1,800 hours in 15 seconds and nobody's week got worse." | That 15,000 hours is a real measurement, or that the optimizer's improvement shows real-world performance (cohorts are identical by construction) |
| "On a synthetic benchmark of 120 coordinator decisions, a better prompt took the base model from 75 to 96 correct; fine-tuning added about 10 more (106)." | **"111 vs 75"** (it mixed a prompt change with the adapter) or "116 vs 73" as a deployed result |
| Ask Mizan "drafts an interpretation for you to check and confirm"; 7/30 fully correct on a handwritten test | That Mizan "understands" requests |
| "36 of the 112 students who need Machine Learning would have no seat" | "112 students at risk" |
| Research figures from `docs/evidence.md` with their sources (Prince Sultan University study, IZA UK study, room-use data) | That fewer gaps raise grades; vendor figures ("4–8 weeks per timetable", "12–18% conflicts"); that the demo's 10% room use resembles a real campus |
| "Optimal within the searched options" | "Optimal" on its own |
| The Edugate export is "a Mizan document for review" | That it is an official Edugate record (it carries no university logo on purpose) |

## 6. Decisions the owner has made

- **Design:** calm, small type, but colourful and alive; numbers graded continuously red → amber → green per metric (`frontend/src/grade.ts`), no hard thresholds; faculty workload is not graded (only overload is red). Show design sketches before big visual changes. `DESIGN.md` is the design source of truth.
- **Bilingual parity:** every UI string through `t(en, ar)`; logical CSS properties for right-to-left.
- **Safety model:** hard constraints are enforced by code, never by the model; no publication or hiring without a person; everything local (the model client refuses non-loopback URLs).
- **Edugate:** imports create a separate "Edugate timetable", not mixed into the synthetic semester; placeholders until verified; publishing an import needs verified rooms and instructors.
- **Scope tonight:** all usability-review items and all expert-review findings that could be fixed were fixed. The remaining strategic items (semester calendar, approval stages and notifications, joint staffing optimization, travel time, pilot foundations) are **after the final**.
- **Git:** the owner commits and pushes. Don't commit, push, or open pull requests unless asked. GitHub CLI (`gh`) is not installed.
- **Housekeeping:** ask before deleting large local files (`work/ollama-0.34.3.zip`, training checkpoints).

## 7. Still open (as of 4 Oct, evening)

- Confirm the slide size with the mentor; possibly an Arabic deck.
- Set up and rehearse on the Zenbook; run `Check Mizan Setup.cmd`; run Optimize once to confirm the figures; time one Ask Mizan request there.
- Rehearse the whole demo once with the model stopped (review item DOC-3).
- Re-record the demo video (the screens changed on 4 Oct).
- Waiting on the owner: whether to change the timetable details drawer to slide in with a transform instead of animating its width (a design-tool warning on `frontend/src/style.css`, line ~329; it predates this work).
- Known open findings with no fix yet: AI-4 (one model request at a time), CODE-1 (typed API models, splitting long files), optimization cancel and best-so-far progress, filters in links, a full Arabic language and screen-reader review. See `docs/reviews/README.md`.

## 8. How to verify things yourself

- **Tests:** `scripts/test.ps1` (or `python -m pytest tests -q`), See docs/release-verification.md for the fresh release count. Windows OCR may skip when unavailable.
- **Browser tests:** start the app on port 8001 with `MIZAN_DB` pointing to a fresh file under `work/`, then `node tests/browser-smoke.cjs` (5 checks + English/Arabic parity), `node tests/browser-phase2.cjs` (needs the model), `EDUGATE_FILE=<schedule> node tests/browser-edugate.cjs`.
- **Demo figures** on a fresh database: baseline 15,000 gap h/week, quality 45, 100% with 2h+ gaps, room use 10%; 15 s optimize ≈ +1,800 h, 225 better off, 0 worse; S001 → Sunday 10:00 = 77 conflicts and 3 alternatives; shortfall C080: 3 needed, 2 covered, 1 uncovered, 36 without a seat of 112.
- **Recorded results:** `docs/test-log-2026-10-04.txt`.

## 9. Technical gotchas learned the hard way

- `frontend/src/main.tsx` uses long one-line JSX; edit with exact unique string matches. Sibling panels must not share `key={sid}` (it left a stale duplicate on language switch).
- The browser smoke test depends on visible labels: "Preview impact", "Send for review", "Approve proposal", "Revalidate & publish locally", "Account menu", "Sign out", "Reason", "New start time". Renaming them breaks it.
- pnpm isn't installed globally: use `npx pnpm` with `CI=true`.
- PyMuPDF and Arabic: put logical text ("04:30 م - 06:20 م") in a right-to-left box and check glyph order with `get_text('rawdict')`, not by eye; call `doc.subset_fonts()` or PDFs grow to megabytes.
- Saving the deck with python-pptx drops the `jpg` content-type entry; restore `<Default Extension="jpg" ContentType="image/jpeg"/>` in `[Content_Types].xml` and validate.
- The coordinator evaluation's middle arm sends the fine-tuned request with every adapter at scale 0 (`training/coordinator/deployed_eval.py`); fine-tuning should only be credited for arm 2 → arm 3.


## Three-plan comparison update (4 October 2026)

Implemented deterministic **Compare three plans** on Recommendations and the optimization dialog. Fixed priorities: most time saved, fewest changes (minimum 1% gap improvement), balanced student waiting burden. Latest comparisons persist; no proposal until explicit selection; existing human approval/publication and imported-data guards remain active. Duplicate results and failed searches are disclosed. Details: `docs/three-plan-comparison.md`. API: `backend/plan_routes.py`; objective variants: `backend/solver.py`; UI: `frontend/src/PlanComparison.tsx` and `plans.css`.

Fresh verification: **118 pytest tests passed**, including 19 new comparison checks. `tests/browser-plans.cjs` covers real solver comparison, English/Arabic parity, mobile, selection, approval, publication and staleness. This update's count supersedes historical 99/80-test counts above; existing AI logs were not rerun. Interpreter benchmark integrity now normalizes LF/CRLF before hashing; cases and saved results are unchanged. The 5 October release additionally resolves the reproduced import, redaction and preview defects; see the current release report.

**Solver on mixed rosters (5 Oct 2026).** Whole-semester optimization on *Faculty week* (1,499 distinct student timetables vs 20 in the baseline) used to end `UNKNOWN`: the full CP-SAT model spent 25–45 s in presolve. Such runs (no rules, no scope, >200 patterns) now use a large-neighbourhood search (`backend/lns.py`) with the identical objective: 5 s reaches the plan the full model proves optimal in 85 s (663 h saved, 5 changes), and all three plans succeed in 15 s. Results are reported as `FEASIBLE` (not proven optimal). Baseline-sized, rule and own-section runs are unchanged. pytest: 140 passed (`tests/test_lns.py` checks the objective equals the full model's for all four objectives).


## 10. Current handover authority

Read v6, CHANGELOG and release-verification first for the current delivered system. The three-plan comparison is implemented, not deferred. Instructor identities, resource availability, small-room reconciliation, readiness and non-ST redaction were corrected on 5 October. Yellow preview annotations are removed. Tests of real AI inference and the exact presentation laptop remain unverified for this release. The owner pushes the prepared folder; do not infer that it is already on GitHub.
