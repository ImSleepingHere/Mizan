# MIZAN — ميزان
## Project documentation v4.0 (as built)

**28 September 2026 · Farq hackathon, university-operations track**

Mizan checks a university timetable before it's published. It measures what the timetable costs students and staff, recommends valid improvements, checks proposed changes, separates scheduling problems from real staffing shortages, and prepares recruitment only when a shortage is proven. A person approves every publication and every hiring step. Everything runs locally on one PC.

This document describes the system **as it is built and tested today**. The earlier design specification, [`MIZAN - Project Documentation v3.md`](MIZAN%20-%20Project%20Documentation%20v3.md) (v3.0 and the v3.1 addendum), remains the record of what was planned and why. Where the two differ, this document describes the software.

| | |
|---|---|
| Status | Ready for the Farq demo. Phases 1 and 3 complete; Phase 2 (agents and recruitment) awaiting final sign-off |
| Tests | 80 automated tests, a 5-check browser smoke test with an English/Arabic parity check, and a browser test of the agents and recruitment with the live model |
| Acceptance | All 15 criteria in spec §13 and §18.7 map to passing tests ([acceptance report](acceptance-report.md)) |
| Data | Synthetic only: 1,500 fictional students, 80 courses, 100 sections, 40 rooms, 50 professors per scenario |
| Presenting it | [HANDOVER.md](HANDOVER.md) (install and run) · [demo-script.md](demo-script.md) (7-minute demo) |

---

## 1. The problem

A timetable can satisfy every hard rule and still be expensive. Students lose hours in gaps between classes, come to campus on extra days, and some cohorts carry far more of the burden than others. Rooms sit idle, and faculty loads are uneven. Registrars rarely see these costs before publication, because conventional tools only check that nothing clashes.

Mizan makes the cost visible and actionable:

1. **Measure:** compute student, room and faculty metrics from the actual timetable.
2. **Recommend:** search for valid alternatives within limits a person sets.
3. **Prove:** re-check every candidate with an independent validator, and show before and after figures.
4. **Decide:** a person approves, and publishing re-validates first.

The demo semester shows why this matters. It's fully valid, yet it costs students **15,000 hours a week** in gaps (10 hours each), every student has at least one gap of two hours or more, quality scores 45/100, and rooms are used 10% of the available time. A 15-second optimization moving five sections recovers about 1,800 student-hours a week with nobody worse off.

## 2. Principles

- **Tools decide, models explain.** Feasibility comes only from deterministic code: the validator, the OR-Tools solver and the rule checker. A language model's statement is never evidence.
- **The human decides.** No publication, candidate rejection, hiring decision or outreach happens without an explicit human action.
- **Local first.** No external AI API. The model runs on a loopback-only server, and code enforces the loopback address.
- **Honest numbers.** Every figure is computed from the dataset. Synthetic data is labelled on screen. "Optimal" is only claimed within the searched options, and time-limited results say so.
- **Bilingual by default.** Arabic and English have equal status; right-to-left layout uses logical CSS properties, and a test checks the two languages show identical figures.

## 3. Users and permissions

All accounts are local demo identities sharing the password `Mizan-demo-2026!`, which can be overridden with `MIZAN_DEMO_PASSWORD`. They are not institutional authentication.

| Role (username) | Main use | Can |
|---|---|---|
| Administrator (`admin`) | Everything | Every staff action, plus policy weights (the only role that can change them) |
| Scheduling committee (`registrar`) | Runs the timetable | Optimize, change requests, placements, approve, reject and publish, import data, start agent runs |
| Department chair (`chair`) | Reviews | Read metrics, proposals and workforce; prepare requisitions; recruitment; Ask Mizan results only |
| Professor (`professor`, P001) | Own classes | Ask Mizan, My classes, optimize **own sections only**, change own meetings, free-slot finder for own sections. Never sees student IDs |
| Hiring manager (`hiring_manager`) | Recruitment | Approve requirements, add and assess candidates, chat with the recruitment agent. No student records |
| Student (`student`, ST0001) | Own week | Personal timetable, personal metrics, eligible conflict-free sections. Read-only |

Permissions are enforced on the server for every endpoint (§13). The interface only hides what a role can't use.

## 4. What the application does (screen by screen)

**Overview.** The weekly student time lost to gaps, as a large number graded red to green. Three graded tiles: quality score, students with 2h+ gaps, and room use. A waiting-proposals line, and average gap by cohort on a fixed 0–12 hour axis with a 0.75-hour target marker. Semester facts and validation status, then the next decisions.

**Semester lab.**
- **Weekly timetable:** Sunday–Thursday, 08:00–18:00, Riyadh time. Filters by cohort, room, faculty, department and search. Drag a meeting to a new slot and a live preview (no database write, about 70 ms) turns the drop target green or red with conflicts, recovered hours and students worse off. The staged move goes to a dock to submit as a change request. There's a keyboard move form in the details drawer, and a list view.
- **Ask Mizan:** a natural-language request in Arabic or English (§8.1).
- **My classes:** professors only (§8.2).
- **Find a common time:** the free-slot finder (§8.4).
- **Place a section:** ranks slots for an extra section of a course by compatible eligible students, seats and gap change.
- **Semester records:** courses, students, faculty and rooms behind every calculation. Export to JSON.

**Recommendations.** All proposals with status and recovered hours. Opening one shows the evidence:
- a Preview → Propose → Approve → Publish strip, with Publish marked as changing the official timetable
- graded tiles: recovered hours, students benefiting, students worse off, conflicts
- solver status and search scope
- a before/after metrics table where each changed value is coloured by whether it improved
- every changed section, rules applied, adverse students (hidden from professors) and feasible alternatives

**Change requests.** Propose moving one meeting to a day and 24-hour start time, with a reason. It's evaluated immediately; if blocked, each conflict is listed and validated alternatives are offered.

**Workforce.** Per unmet teaching demand, one of three statuses:
- a **verified capacity shortfall**: sections needed, currently covered, minimum uncovered and students at risk, with the evidence
- an **internal coverage review**
- **contracted capacity available**

Faculty workload against contract appears as neutral bars; only overload is red, because this is capacity planning, not performance evaluation.

**Recruitment.** Requisitions from proven shortfalls. Job-related criteria with weights, approved by a person. CVs from PDF, DOCX, TXT or pasted text, with source correction. An evidence comparison where each criterion is *supported* (with a verbatim quote) or *unknown*. A printable candidate brief with the unchanged source CV, and a bilingual chat with the recruitment agent.

**Activity & evidence.** The agent collaboration panel: request, change limit, roster, a timeline of every model decision and tool result with the fine-tuned coordinator marked, and the final decision packet. The audit trail of every action.

**Settings.** Optimization weights (they must sum to 100; saving creates a new policy version and makes earlier approvals stale), JSON import and export, and environment status (storage, timezone, model service, coordinator adapter).

**Student view.** My timetable, personal gap hours, campus days, longest gap and quality (all graded), and eligible conflict-free sections.

## 5. System architecture

```
Browser (React 19 + TypeScript, served as static files)
   │  same-origin loopback HTTP, session cookie + X-Mizan-Action guard
   ▼
FastAPI app  backend.main:app  (127.0.0.1:8000)
   ├── analysis.py      metrics, independent validation, comparisons, eligibility
   ├── solver.py        OR-Tools CP-SAT optimization, placement, workforce, common slots
   ├── rules.py         request-scoped rules, independent rule checker, diagnosis
   ├── agent_engine.py  six-agent collaboration loop with budgets (1 worker thread)
   ├── interpreter.py   request interpretation (model extracts fields; code decides)
   ├── recruitment.py   requirements, CV ingestion, evidence assessment, chat
   ├── store.py         SQLite (data/mizan.sqlite3), versions, audit
   └── local_model.py   client for the local model (loopback only)
          │
          ▼
llama-server (llama.cpp, bundled in .runtime/)  127.0.0.1:11435
   Qwen3-8B GGUF + LoRA coordinator adapter (applied per request, coordinator only)
```

- **Backend:** Python 3.12, FastAPI, Pydantic strict models, OR-Tools, SQLite. About 3,100 lines in `backend/`.
- **Frontend:** React 19, Vite 7, TypeScript, lucide icons, self-hosted fonts (Archivo, Noto Kufi Arabic). The build output `frontend/dist/` is served by FastAPI; no external requests at runtime.
- **Model:** Qwen3-8B (Q4 GGUF, 5.2 GB) on a bundled llama.cpp server with CUDA. A GPU with 8 GB+ is recommended.
- **Concurrency:** agent runs execute on a single background worker and can be cancelled. Other requests are synchronous.

## 6. Scheduling model

### 6.1 Hard constraints (independent validator, `analysis.validate`)

A timetable is valid only if none of these occur. Each finding carries a code and the records involved:

| Code | Meaning |
|---|---|
| `STUDENT_OVERLAP` · `PROFESSOR_OVERLAP` · `ROOM_OVERLAP` | Simultaneous meetings for the same person or room (adjacent meetings don't overlap) |
| `CAPACITY` | Enrolment exceeds section or room capacity |
| `ROOM_TYPE` | Room type doesn't match the course |
| `COMPETENCY` | Professor not qualified for the course |
| `PREREQUISITE` | Student lacks a prerequisite |
| `DURATION` · `MEETING_PATTERN` | Wrong instructional minutes or meeting pattern |
| `BLOCKED_TIME` | Outside opening hours or inside a blocked window |
| `CONTRACTED_HOURS` | Professor over contracted teaching time |
| Availability | Professor or room not available at that time |

An invalid scenario still gets its metrics computed, but **its quality score is withheld**. The *Conflict diagnostics* scenario demonstrates this.

### 6.2 Metrics (`analysis.metrics`, metric version 1.0)

Weekly student gap hours, students with gaps of 2h+ and 4h+, average campus days, average daily span, worst-decile gap hours, faculty-load Gini, room utilization, per-cohort averages, and a quality score:

> 40% gaps (per 1,200 min) · 20% longest gap (per 240 min) · 15% campus days (per 5) · 15% daily span (per 600 min) · 5% fragments (per 10) · 5% irregular starts (per 10). Each ratio capped at 1.

### 6.3 Optimization (`solver.optimize`)

- **Search space (the "neighbourhood"):** for each section, all approved start times on its current days and room, plus three alternatives. Meeting spacing is preserved and faculty assignments stay fixed. That's why teaching-load balance and total room use can't change in this search, and the result says so.
- **Objective:** a weighted sum, using policy weights that must sum to 100 (defaults: gaps 30, days 18, fairness 14, load 12, simplicity 8, rooms 10, changes 8). An exact integer scale preserves the configured ratios. Split meeting times are penalised at twice an irregular start.
- **Limits:** a maximum number of changed sections (0–30) and a time budget (1–60 s; 15 s in the UI).
- **Outcomes:**

  | Status | Meaning |
  |---|---|
  | `OPTIMAL` | Best within the neighbourhood |
  | `FEASIBLE` | Improvement found, not proven best in the time |
  | `INFEASIBLE` | Nothing valid in the neighbourhood |
  | `UNKNOWN` | Time ran out before a solution; the official timetable is kept and no proposal is created |
  | `INVALID_BASELINE` | The scenario must be fixed first |

- **Every candidate is re-validated** (§6.1) and, under request rules, re-checked by the rule checker before it can become a proposal.

### 6.4 Proposals, approval and publication

A proposal stores the candidate, its analysis and the scenario revision it was computed on. Statuses: `recommended` → `approved` → `published`, or `rejected` / `invalid`.

Publishing re-validates against the **current** revision, so a proposal whose base has changed (another publication, a policy change) is refused as stale. Published timetables become a new version; nothing is overwritten.

## 7. The six agents

| Agent | Tool it must call before reporting | Job |
|---|---|---|
| Coordinator (fine-tuned) | — | Chooses the next specialist from the evidence; finalizes only when all reviews are current |
| Student Experience | `analyze_student_experience` | Burdened cohorts and priorities from computed metrics |
| Workforce Planning | `analyze_workforce` | Teaching coverage and shortfall signals; never proposes new hires on its own |
| Scheduling & Optimization | `optimize_schedule` | Runs the solver within the user's limits; may re-run to revise |
| Change Impact | `evaluate_change` | Validates the latest candidate against conflicts, rules, students worse off and the change limit; can demand a revision |
| Recruitment Assistant | (recruitment tools) | Works with the hiring manager (§9) |

**Collaboration loop (`agent_engine.run_collaboration`).**
- The coordinator delegates to the specialists still pending. A specialist must call its tool before it may report.
- If Change Impact rejects a candidate, scheduling becomes pending again, and impact must re-check the new candidate. This is the evidence-driven revision the spec requires (§13.6), and a test covers it.
- A validation gate refuses to finalize while any review is missing or stale.
- The final decision packet is `recommend` (saves a proposal, never publishes), `no_change`, or `needs_review`.

**Budgets:** at most 24 model decisions, 12 tool calls, 10 coordinator rounds and a wall-clock limit (360 s by default). Cancellation is honoured before every step. When a budget runs out, the run ends as `failed` with no conclusion and no proposal.

**What the model sees:** the request, limits, summarised evidence and recent messages. Request rules (§8.3) go to the tools only, never into the coordinator's context. The system prompt tells the model to treat source data as untrusted and never to invent numbers, override policy or publish.

## 8. Professor requests (v3.1)

Built from 30 real professor requests, of which only about 5 were supported before.

### 8.1 Ask Mizan: the request interpreter

- **The model extracts fields only** (goal, sections, meetings, days, times, windows, rules). It uses the base model, with no adapter and no view of the professor's sections.
- **Code does the rest:** normalizes values, applies conventions, decides whether the request is supported (with bilingual reasons), asks clarifying questions (`WHICH_SECTION`, `WHICH_MEETING`, `MISSING_TIME`, `AMBIGUOUS_TIME`…), and resolves scope and permissions (`NOT_OWN`, `ROLE_SCOPE`, `READ_ONLY`…).
- **A date lexicon backstop** can only make the scope more cautious.
- **Requests never run silently.** The user sees what Mizan understood, can correct it, and must confirm. Dated changes, duration changes, online delivery and undefined goals (`BLOCKING_CODES`) never run; the user must correct them explicitly.
- **Confirming** runs a read-only preview for an exact single move, the rule-based optimizer for reschedules, or the free-slot finder for "find a time" requests.
- **Measured accuracy (frozen handwritten test, scored once):** 7/30 fully correct, per-field 22–30/30. Three cases counted as silent guesses by the metric, but none could change the timetable. The weakest field is time windows.

### 8.2 "My classes" scope

A professor sees aggregate figures for their own sections (students, average gap, campus days, 2h+ gaps, teaching load) and can **improve their own classes**: every other section is fixed in the search, the change count is capped, and the result is a proposal for committee approval. Student identities are removed from every professor response by `main.redact()`.

### 8.3 Request-scoped rules (`rules.py`)

- **Rules:** time windows (global or per day), protected sections or meetings, locked days, keep day/time/room, breaks for the professor or students, emptying a day, must change, must change room, maximum changes, and scope.
- **Split times:** meeting times are split across days only when a day-limited rule requires it, and the proposal says "times split by rule X".
- **Checking:** candidates pass an independent rule checker.
- **Infeasible rules:** Mizan removes one rule at a time and reports which rule blocks the request. `UNKNOWN` is reported as "not proven", never as infeasible.

### 8.4 Common free-slot finder

`solver.common_slots` ranks non-overlapping weekly slots on a 15-minute grid for the students of the chosen sections. For each slot it reports:
- how many students can't attend
- whether the professor is free
- free rooms with enough capacity (one room for a merged class, one per section for "same time")
- extra campus days and added gaps

It books nothing.

### 8.5 Edugate schedules: import and export (4 Oct)

Al Yamamah students get their timetable as an Edugate "جدول الطالب" PDF or as a week grid in the phone app. Mizan reads both and prints back in the Edugate layout (`backend/edugate.py`, `backend/edugate_routes.py`, `frontend/src/EdugateExchange.tsx`, on Semester lab).

- **Reading** uses the Windows OCR engine on this PC (Arabic + English); the file is not stored. Edugate's "Microsoft Print to PDF" output has no text layer, so the PDF page is rendered (PyMuPDF), turned upright, and read. Codes map Arabic ↔ English (عرب ARB, مال FIN, نما MIS, تسق MKT, ادا MGT); OCR slips such as dot confusions (نسف → تسق) and `A-OI` → `A-01` are corrected. Screenshots are read per day column; a missing start is filled from the same course on another day or from the usual class length and flagged; a missing end (block cut off at the bottom) is never guessed.
- **Review before import:** every row is editable; warnings are shown; nothing is written until **Add to Mizan and optimize** (admin, registrar). The schedule becomes an *Edugate timetable* scenario (kind `edugate`) or is added to an existing one; students in the same course and section share it. Instructors, room sizes and other bookings are not in the source, so placeholders are used (one instructor per section, rooms seat 40); the optimizer then runs as usual (start times on the imported 90-minute rhythm).
- **Export** (`GET /api/edugate/export`) prints any student's current timetable or a proposal in the Edugate layout (Letter landscape, same eight columns right to left). Rows that differ from the imported schedule are shaded. The page says it is a Mizan document for review, not an official Edugate record, and carries no university logo. Students may export only their own current timetable.

## 9. Workforce and recruitment

**Workforce signals (`solver.workforce`).** For each unmet demand, Mizan compares required sections with what qualified professors' contracts can cover:
- `PROVEN_CAPACITY_SHORTFALL`: even all qualified contracts can't cover it. This is a capacity proof, not a solver timeout.
- `REDEPLOYMENT_REVIEW`: internal moves may cover it.
- `CAPACITY_AVAILABLE`

Only a proven shortfall can become a requisition, and a stale one can't be authorized.

**Recruitment (`recruitment.py`).**

1. **Requisition** prepared by an admin or chair from a proven shortfall.
2. **Requirements** approved by a person: job-related criteria with weights. Editing them invalidates earlier assessments.
3. **Candidates** from PDF, DOCX or TXT uploads (up to 5 MB) or pasted text. The source is kept unchanged and can be corrected.
4. **Evidence assessment:**
   - Each criterion is *supported* only with a verbatim quote of 8+ characters found in the CV. Everything else is *unknown*, never "unqualified".
   - Quotes that read as instructions to the reviewer or model (English or Arabic) are never evidence, and such CVs are flagged.
   - The score is evidence coverage, not suitability.
5. **Brief and chat:** a printable brief shows the evidence and the source CV (HTML-escaped). The recruitment agent drafts interview questions or requirement suggestions for human approval.
6. **Never:** automatic rejection or hiring, outreach, or LinkedIn browsing. No external connection is configured.

## 10. The fine-tuned coordinator

| | |
|---|---|
| Base | Qwen3-8B, trained in 4-bit NF4 |
| Method | Attention-only LoRA (rank 8, α 16), 2 epochs, 12.6 minutes on an RTX 4080 SUPER |
| Data | 480 train / 60 validation / 120 test synthetic coordinator decisions, balanced English/Arabic (`training/coordinator/`, protocol frozen in `PROTOCOL.md`) |
| Result (deployed GGUF, production schema) | **111/120** vs 75/120 for the base model (42 fixed, 6 broken, p ≈ 1e-7) |
| Deployment | `.models/mizan-coordinator-lora.gguf` (15 MB, in the repository). Applied per request **only** to coordinator calls (scale 1.0; 0.0 for everything else). Roll back with `MIZAN_COORDINATOR_ADAPTER=0` |
| Caveat | The test set comes from the same generator as the training data, so it measures in-workflow generalisation only |

## 11. Data

### 11.1 Scenarios (seeded on first start)

| Scenario | Purpose | Key facts (fresh database) |
|---|---|---|
| Baseline semester | Valid but inefficient timetable | 15,000 gap h/week, quality 45, 100% with 2h+ gaps, room use 10% |
| Conflict diagnostics | Real hard violations | Violations listed; quality score withheld |
| Staffing shortfall | Proven capacity shortage | Machine Learning (C080): 3 sections needed, 2 covered, 1 uncovered, 112 students at risk |
| Faculty week | Realistic professor case | P001 owns S087–S091 (mixed rosters, 75- and 90-minute courses); R040 seats 200 for merges |

Each scenario has 1,500 fictional students (20 cohorts × 75), 80 courses in four departments (Computing, Business, Engineering, Design) with English and Arabic names, 100 sections, 40 rooms and 50 professors. Generation is seeded and reproducible (`backend/fixtures.py`).

### 11.2 Data model (`backend/models.py`)

`Semester` = courses, students (cohort, sections, completed courses), professors (competencies, availability, contracted minutes), rooms (type, capacity, availability), sections (course, professor, room, capacity, meetings), demands, and a `Policy` (timezone, opening hours 08:00–18:00, blocked windows, allowed start times, objective weights). All models are strict; unknown fields, duplicate IDs, broken references and prerequisite cycles are rejected on import.

### 11.3 Storage (`data/mizan.sqlite3`)

| Tables | Holds |
|---|---|
| `scenarios`, `versions` | Current data and every published version |
| `proposals` | Candidates with analysis and base revision |
| `audit` | Every action with actor, subject and detail |
| `requisitions` | Requisitions from proven shortfalls |
| `sessions` | Login sessions (8-hour, HttpOnly, SameSite=Strict cookie) |
| `agent_runs`, `agent_events` | Agent runs and every decision and tool result |
| `request_interpretations` | Ask Mizan requests, corrections and results |
| `hiring_jobs`, `candidates`, `assessments`, `hiring_messages` | Recruitment |

Import accepts a Mizan JSON semester (up to 15 MB); schema and references are checked before saving, and scheduling violations are reported separately. Export downloads the current scenario as JSON.

## 12. Interface and design system

The interface uses an "Information System" design, recorded in [`DESIGN.md`](../DESIGN.md) (tokens in `.impeccable/design.json`):
- a paper background (#f6f6f3) and an ink-black sidebar
- four flat signal colours: blue for actions, green, orange and red
- light Archivo numerals, with Noto Kufi Arabic for Arabic
- square corners and 1-px rules; shadows only on floating layers

**Colour carries exactly two meanings:**
- **Which department.** Blue, green, orange and red are assigned in alphabetical order, so the timetable, overview bars and legend always match.
- **How good a number is.** `frontend/src/grade.ts` gives each metric a "bad" and a "good" anchor and colours values on a continuous OKLCH scale from red through amber to green, with no hard thresholds. Every graded value also carries a word: Critical, Weak, Fair, Good or Strong (حرج، ضعيف، متوسط، جيد، ممتاز).

**Motion and accessibility.** Numbers count up, bars grow in and the live preview reacts. Reduced-motion preferences are respected. Focus is visible; the timetable can be operated from the keyboard; text meets AA contrast.

**Language.** Every string exists in English and Arabic (`t(en, ar)`), and the layout mirrors right-to-left.

The design direction was chosen with the product owner from six candidate styles, then refined: calmer type, but "colourful and alive" with graded numbers. The Figma file holds foundations, an editable overview and all page screenshots: https://www.figma.com/design/AqHJqn2UaIKJ9iyFb1UeOZ

## 13. Security, privacy and approval

- **Sessions:** random token in an HttpOnly, SameSite=Strict cookie, expiring after 8 hours. Every endpoint checks the role on the server.
- **Cross-site protection:** every state-changing API call needs the `X-Mizan-Action: 1` header and a same-origin `Origin`. Responses set `nosniff`, `same-origin` referrer policy and `no-store` for API data.
- **Loopback only:** the app binds to 127.0.0.1, and the model client refuses any non-loopback URL.
- **Privacy:**
  - Professors never receive student IDs, which are redacted from previews, changes, proposals, optimizations and request results.
  - Hiring managers can't read student records.
  - Students see only their own data.
  - Free-slot results are counts only.
- **Untrusted content:**
  - CV text goes to the model only as data (`untrusted_cv`), and instruction-like quotes are never evidence.
  - Imported semesters are strictly validated, and all rendered text is escaped.
  - Agent prompts treat source data as untrusted.
- **Approval:** agents and optimization only create proposals. Publishing needs a registrar or admin and re-validates. Policy changes version the scenario and make earlier approvals stale. Every action is audited.

## 14. API reference

All endpoints are under `/api`, return JSON, and require a session unless noted. State-changing calls need the `X-Mizan-Action: 1` header.

| Endpoint | Roles | Purpose |
|---|---|---|
| `POST /login` · `POST /logout` · `GET /me` | public / any | Session |
| `GET /health` | public | Version and mode |
| `GET /scenarios` · `GET /scenarios/{sid}` | any | Scenario list; scenario data (scoped by role) |
| `GET /scenarios/{sid}/metrics` · `/export` | staff | Metrics and validation; JSON export |
| `POST /import` | admin, registrar | Import a semester |
| `POST /scenarios/{sid}/optimize` | admin, registrar, professor (own) | Optimization → proposal |
| `POST /edugate/read` · `POST /edugate/import` · `GET /edugate/timetables` | admin, registrar | Read an Edugate PDF / app screenshot (no write); import reviewed rows; list Edugate timetables |
| `GET /edugate/export` | staff; student (own, current) | Student timetable or proposal as an Edugate-layout PDF |
| `POST /scenarios/{sid}/changes` | admin, registrar, professor (own) | Change request → proposal with alternatives |
| `POST /scenarios/{sid}/preview-change` | admin, registrar, professor (own) | Read-only live preview |
| `POST /scenarios/{sid}/alternative` | admin, registrar, professor | Propose a feasible alternative |
| `GET /scenarios/{sid}/my-classes` | professor | Own-section aggregates |
| `POST /scenarios/{sid}/free-slots` | admin, registrar, chair, professor (own) | Common free slots |
| `GET /scenarios/{sid}/placement/{course}` · `POST …/placement` | staff · admin, registrar | Rank and propose an extra section |
| `GET /scenarios/{sid}/eligible` | student | Eligible conflict-free sections |
| `GET /proposals` · `POST /proposals/{pid}/{approve\|reject\|publish}` | staff, professor · admin, registrar | Proposals and decisions |
| `GET /scenarios/{sid}/workforce` | staff | Workforce signals and workloads |
| `POST /scenarios/{sid}/requisitions` · `GET /requisitions` | admin, chair · staff, hiring manager | Requisitions |
| `GET /audit` | staff | Audit trail |
| `POST /scenarios/{sid}/policy` | admin | Save a policy version |
| `GET /agents/status` · `POST /agents/runs` · `GET /agents/runs[/{id}]` · `POST …/cancel` | varies (runs: admin, registrar) | Model status; agent runs |
| `POST /requests/interpret` · `/{id}/revise` · `/{id}/confirm` · `/{id}/cancel` · `GET /requests` | admin, registrar, chair, professor | Ask Mizan |
| `/recruitment/…` (requisition approval, jobs, candidates, upload, assess, brief, chat) | admin, chair, hiring manager | Recruitment |

"Staff" means admin, registrar and chair.

## 15. Repository layout

```
backend/        FastAPI app, analysis, solver, rules, agents, interpreter, recruitment, storage
frontend/       React app (src/), built site (dist/, not in git)
tests/          pytest suites, browser-smoke.cjs, browser-phase2.cjs
training/       coordinator fine-tuning (coordinator/) and interpreter evaluation (interpreter/)
scripts/        setup, start, start/restart model, reset-demo, check-setup, test, apply-update
docs/           this document, v3 spec, acceptance report, demo script, handover, build checkpoints
.models/        fine-tuned adapter (in git); base model downloaded here (not in git)
.runtime/       bundled llama.cpp runtime (downloaded, not in git)
data/           local database and backups (not in git)
DESIGN.md, PRODUCT.md, .impeccable/   design system and product brief
*.cmd           Start Mizan · Reset Mizan Demo · Check Mizan Setup · Apply Mizan Update
```

## 16. Installing and running

Full, step-by-step instructions for a new PC are in [HANDOVER.md](HANDOVER.md). In short:

1. Install Python 3.12 and Node.js 24.
2. Run `scripts\setup.ps1`: backend dependencies and the website build. pnpm is fetched through npx if missing.
3. Run `.venv\Scripts\python.exe scripts\install_model_runtime.py`: the runtime and Qwen3-8B, about 7 GB, checksum-verified.
4. **Check Mizan Setup.cmd** shows what's missing, **Reset Mizan Demo.cmd** gives clean data (with a backup), and **Start Mizan.cmd** starts the model and app on http://127.0.0.1:8000.

Without the model, everything works except Ask Mizan, agent collaboration and CV analysis.

## 17. Testing and quality

| Suite | What it covers | Latest result |
|---|---|---|
| `scripts/test.ps1` (pytest, 86 tests) | Hand-checked metrics, validation, solver statuses, rules, scope and redaction, interpreter safety, agents (validation, revision, budgets, cancellation), recruitment evidence and injection, API authorization, CSRF, staleness, import/export, Edugate import/export incl. an OCR round trip | 86 passed |
| `tests/browser-smoke.cjs` | Placement → approval → publication; conflict → alternative; shortage → requisition; full optimization → evidence; student access; English/Arabic figures identical; mobile layout | 5/5 + parity passed |
| `tests/browser-edugate.cjs` | Upload an Edugate PDF or app screenshot (`EDUGATE_FILE`, not committed) → review → import → optimize → export PDF | Passed with both formats (4 Oct) |
| `tests/browser-phase2.cjs` | Live model: agent run completes, recruitment assessment and chat, Arabic mobile | Passed |
| `training/interpreter/eval_interpreter.py` | Frozen 30-case handwritten request set (scored once) | 7/30 strict; no misread can change the timetable |
| `training/coordinator/deployed_eval.py` | 120 coordinator decisions | 111/120 fine-tuned vs 75/120 base |

The full mapping of acceptance criteria to tests is in [acceptance-report.md](acceptance-report.md).

## 18. Known limitations

- **Synthetic data only;** no institutional deployment is claimed.
- **Time-limited search:** semester-wide optimization is `FEASIBLE` in 15 s and varies slightly between runs. Optimal only within the searched neighbourhood. Whole-semester optimization on *Faculty week* hits its limit (`UNKNOWN`); own-section runs finish `OPTIMAL` in about 1 s.
- **Faculty assignments are fixed** during optimization, so load balance and total room use can't improve there.
- **Request understanding is modest** (7/30 strict). Confirmation and code-side checks keep it safe.
- **The coordinator evaluation** uses generator-made test cases.
- **Edugate import** reads the two layouts seen so far (Edugate PDF, app "My Courses" screenshot) and needs Windows OCR; the course-code map covers ARB, FIN, MIS, MKT, MGT (other codes import as printed). Single-digit section numbers can be missed; the review step shows every row.
- **Minor UI:** after an agent run, the Activity page's audit trail updates only on reload.

## 19. Deferred work (after Farq)

- A term calendar with dated changes (one-off moves, extra dated sessions, merged dated sessions)
- Session-length changes and online delivery
- Room locations and walking distance
- Approval levels and notices to students
- Ghost slots on the timetable
- More varied coordinator training data and a hand-written messy test set
- Live university-system and LinkedIn integrations, which need real access

## 20. Project history

| Date (2026) | Milestone |
|---|---|
| Build 1 | Working scheduling application: metrics, validation, optimization, change requests, bilingual UI (approved) |
| Build 2 | Agents and recruitment assistant with local Qwen3-8B inference |
| 23 Sep | Spec v3.0: revised six-agent architecture |
| 24 Sep | "Najd Night" interface, interactive drag-and-drop timetable, fine-tuned coordinator live |
| 27 Sep | Spec v3.1 professor requests: interpreter, My classes, rules, free-slot finder; interpreter test scored once |
| 27 Sep | Interface v4 "Information System" with graded numbers; independent design review; DESIGN.md |
| 4 Oct | Edugate schedule import (PDF + app screenshot, local OCR) and Edugate-layout PDF export |
| 27–28 Sep | Phase 3: acceptance gaps closed with tests, CV-injection guard, reset and setup-check tools, demo script, handover guide, this document |

## 21. Glossary

- **Gap:** idle time between a student's classes on the same day.
- **Neighbourhood:** the set of alternative times and rooms the solver may choose from.
- **Proposal:** a candidate timetable change awaiting human decision. It never changes the official timetable by itself.
- **Publish:** make an approved proposal the official local timetable, after re-validation.
- **Stale:** a proposal or requisition whose base data has changed since it was made.
- **Proven capacity shortfall:** qualified contracts can't cover required sections, whatever the timetable.
- **LoRA adapter:** a small set of fine-tuned weights applied on top of the base model.
- **Graded number:** a value coloured continuously from red (bad) to green (good) by its metric's own anchors.
