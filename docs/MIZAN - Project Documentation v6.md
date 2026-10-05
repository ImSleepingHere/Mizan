# MIZAN — ميزان
## Project documentation v6.0 — GitHub handover release

**5 October 2026 · Farq hackathon, university-operations track · Al Yamamah University**

Mizan checks a university timetable before it's published. It measures what the timetable costs students and staff, recommends valid improvements, checks proposed changes before they happen, separates scheduling problems from real staffing shortages, and prepares recruitment only when a shortage is proven. It can read a real Al Yamamah student schedule (Edugate PDF or phone-app screenshot), improve it, and print it back in the Edugate layout. A person approves every publication and every hiring step. Everything runs locally on one PC.

This document describes the system **as built with the 5 October release updates; historical model evidence remains dated 4 October**. It supersedes v5; v3/v4 and dated logs remain historical records. The design specification, [`MIZAN - Project Documentation v3.md`](MIZAN%20-%20Project%20Documentation%20v3.md), remains the record of what was planned and why; where they differ, this document describes the software.

| | |
|---|---|
| Status | Prepared for local hackathon demonstration; full release checks and limits are listed in [release-verification.md](release-verification.md). Exact presentation laptop rehearsal remains required. |
| Tests | Current release verification: [release-verification.md](release-verification.md). Historical AI results: [test-log-2026-10-04.txt](test-log-2026-10-04.txt) |
| Acceptance | All 15 criteria of spec §13 and §18.7 mapped to passing tests, with AI results stated next to them ([acceptance report](acceptance-report.md)) |
| Data | Synthetic demo scenarios (1,500 fictional students each) plus Edugate imports of real schedules |
| Claims | Every figure used in the pitch is either measured by the app or cited: [evidence.md](evidence.md) |
| Presenting it | [HANDOVER.md](HANDOVER.md) (install and run) · [demo-script.md](demo-script.md) · [Mizan-Farq-2026.pptx](Mizan-Farq-2026.pptx) |

---

## 1. The problem

A timetable can satisfy every hard rule and still be expensive. Students lose hours in gaps between classes, come to campus on extra days, and some cohorts carry more of the burden than others. Rooms sit idle. Registrars rarely see these costs before publication, because conventional tools only check that nothing clashes. Changes during the semester (a professor's request, a room problem) are handled by email, and each one ripples through rooms, instructors and every enrolled student.

Research supports the cost (details and sources in [evidence.md](evidence.md)):
- Prince Sultan University, Riyadh (4,325 students, PLoS ONE 2021): three timetable factors, one of them free time between classes, predicted absences with 87% accuracy; absences correlated with GPA at −0.71.
- A UK study with quasi-random timetables (IZA DP 17979, 2025): back-to-back classes raised attendance by 1.5 points; single-class days lowered it by 0.9. Effects on grades were small, so Mizan claims attendance and student time, not grades.
- Teaching rooms are used about 20% of the time on average across 30+ UK universities.

Mizan makes the cost visible and actionable: **measure → recommend → prove (independent validation) → a person decides**.

The demo semester is synthetic and **deliberately poor**: identical cohorts with built-in gaps cost 15,000 student-hours a week (10 h each). A recorded 15-second optimization recovered about 1,800 hours with zero students worse off in that run. Ordinary optimization does not guarantee zero individual harm. These numbers show the method, not real-world performance; the app and deck say so.

## 2. Principles

- **Tools decide, models explain.** Feasibility comes only from deterministic code: the validator, the OR-Tools solver, the rule checker. A language model's statement is never evidence, and the final outcome of an agent run is computed by code.
- **The human decides.** No publication, candidate rejection, hiring or outreach without an explicit human action.
- **Local first.** No external AI API. The model runs on a loopback-only server; code enforces the loopback address.
- **Honest numbers.** Every figure is computed from the data or cited. Synthetic data is labelled. "Optimal" is only claimed within the searched options. AI results are reported with their weaknesses.
- **Bilingual by default.** Arabic and English have equal status; right-to-left layout uses logical CSS properties; a test checks both languages show identical figures.

## 3. Users and permissions

Local demo identities share the password `Mizan-demo-2026!` (override with `MIZAN_DEMO_PASSWORD`). With the default password, **sign-in is refused from any other computer**; the login form pre-fills the password only on localhost. This is not institutional authentication.

| Role (username) | Lands on | Can |
|---|---|---|
| Administrator (`admin`) | Overview | Everything, including policy weights |
| Scheduling committee (`registrar`) | Overview | Optimize, change requests, placements, approve/reject/publish, imports (JSON and Edugate), verification, agent runs |
| Department chair (`chair`) | Overview | Read metrics, proposals and workforce; prepare requisitions; recruitment; Ask Mizan results only; read-only change form |
| Professor (`professor`, P001) | My teaching week | Own sections only: preview and request changes, improve own classes, common-time finder, Ask Mizan. Never sees student IDs |
| Hiring manager (`hiring_manager`) | Recruitment | Requirements, candidates, evidence, recruitment chat. No student records |
| Student (`student`, ST0001) | My timetable | Own week, next class, published changes, explained metrics, sections that fit, own Edugate-layout PDF. Read-only |

Every permission is enforced on the server (§13); the interface only hides what a role can't use and says why on read-only screens.

## 4. What the application does (screen by screen)

**Overview (staff).** Weekly student time lost to gaps (graded red→green), schedule quality, students with 2h+ gaps, room use, sections analysed; average gap by cohort; room-capacity ring; validation status; next decisions; quick actions. For synthetic scenarios a note says the starting timetable is deliberately poor. When the timetable has hard violations the headline changes to "Fix the conflicts before improving this timetable", and **Fix conflicts first** replaces Optimize.

**Semester lab (staff) / My teaching week (professor).**
- **Weekly timetable first.** Sunday–Thursday, Riyadh time; visible hours follow the timetable's teaching window and its meetings (evening classes from imports included). Filters (cohort, room, instructor, department), one search box with an empty state and "x of y sections". Click, tap or Enter opens a class's details: instructor name, room, real occupancy, meetings, and (for editors) a move form with live end time, **Preview impact** and **Prepare request**. Dragging a class shows a live preview (no database write). With "All sections" (100+ classes) an hour-by-hour overview replaces unreadable cards; a cell drills down. A "Midday break" legend explains the hatched band.
- **Planning tools in tabs:** *Edugate import & export* (staff), *Find a meeting time*, *Ask Mizan*.
- **Validation findings** (invalid timetables): grouped plain-language conflicts with **Show on timetable**.
- **Semester records:** courses, students, faculty, rooms; pages of 50, sort, search.
- **My classes** (professor): aggregates for own sections and **Improve my classes**, with a link to the saved request.

**Recommendations (staff).** A request queue with tabs **Needs a decision / Outdated / Conflicting / History**, search and sort. Each card reads like "Dr. X asks to move Course (S087): Sunday 10:00 → Tuesday 11:15", with submitted time, version, hours saved and students worse off. Opening one shows the decision view (§6.4).

**Change requests (staff) / My requests (professor).** Choose a class and meeting → new day and start (only times that end within teaching hours) → before/after summary with end time → **Preview impact** (saves nothing): conflicts grouped in plain language, hours saved, students better or worse off, and feasible alternatives. A reason is required. **Send for review** creates the request; **Propose this** sends an alternative. Professors see everything they submitted, of every kind. Chairs see a read-only note.

**Workforce.** Per unmet teaching demand: status (verified shortfall / internal coverage review / capacity available), sections needed and covered, minimum uncovered, **students without a seat** (of those who need the course), the evidence, qualified instructors with spare hours, possible internal moves, and who makes the next decision. Faculty workload with search and filters (all, over contract, qualified for the shortfall); only overload is red.

**Recruitment.** Requisitions from proven shortfalls; job-related criteria with weights (approving new requirements asks for confirmation because earlier assessments become outdated); CVs from PDF/DOCX/TXT or pasted text; evidence comparison (supported with a verbatim quote, or unknown); candidate brief; recruitment chat.

**Activity & evidence.** Agent collaboration panel (polls only while a run is active) and an audit trail labelled by timetable, filterable by timetable and action, linking to proposals.

**Settings.** Optimization weights (admin only; others see a read-only note; load and room-use weights are marked "fixed today"), JSON import/export, environment status.

**Student — My timetable.** Next class and today's classes first; a notice if the latest published version changed their classes; the timetable; "Your week in numbers" with plain explanations and their own biggest break; sections they could add, grouped by course, with search, a shortlist and the effect on campus days and waiting time (suggestions only; registration is in Edugate); **Download my schedule (Edugate PDF)**.

**Across the app.** Stable links (`#/page?sid=…&proposal=…`) with Back/Forward; errors in plain language with **Try again**, cleared when you leave the task; elapsed time during optimization; an account menu with an explicit **Sign out**; drafts (change form, common-time search, Ask Mizan text) kept within the session.

## 5. System architecture

```
Browser (React 19 + TypeScript, static files from frontend/dist)
   │  same-origin loopback HTTP, session cookie + X-Mizan-Action guard
   ▼
FastAPI app  backend.main:app  (127.0.0.1:8000)
   ├── analysis.py        metrics, independent validation, comparisons, eligibility
   ├── solver.py          OR-Tools CP-SAT optimization, placement, workforce, common slots
   ├── rules.py           request-scoped rules, independent rule checker, diagnosis
   ├── agent_engine.py    six-agent collaboration loop with budgets (1 worker thread)
   ├── interpreter.py     request interpretation (model extracts fields; code decides)
   ├── recruitment.py     requirements, CV ingestion, evidence assessment, chat
   ├── edugate.py         Windows OCR reading of Edugate PDFs/screenshots; Edugate-layout PDF
   ├── edugate_routes.py  read → review → import; readiness and verification; export
   ├── store.py           SQLite (data/mizan.sqlite3), versions, audit
   └── local_model.py     client for the local model (loopback only)
          │
          ▼
llama-server (llama.cpp, bundled in .runtime/)  127.0.0.1:11435
   Qwen3-8B GGUF + LoRA coordinator adapter (applied per request, coordinator only)
   NVIDIA GPU → CUDA; no NVIDIA GPU → CPU engines (scripts/start-model.ps1 detects it)
```

- **Backend:** Python 3.12, FastAPI, strict Pydantic models, OR-Tools, SQLite, PyMuPDF, Pillow, Windows OCR (`winrt-*`). About 4,000 lines.
- **Frontend:** React 19, Vite 7, TypeScript, lucide icons, self-hosted fonts. Modules: `main.tsx` (shell and pages), `Proposals.tsx`, `ChangeForm.tsx`, `Conflicts.tsx`, `InteractiveTimetable.tsx`, `StudentWeek.tsx`, `FreeSlotFinder.tsx`, `RequestAssistant.tsx`, `MyClasses.tsx`, `EdugateExchange.tsx`, `Readiness.tsx`, `AgentWorkspace.tsx`, `RecruitmentWorkspace.tsx`, `ui.tsx`, `api.ts`, `grade.ts`; styles `style.css`, `campus.css`, `review.css`.
- **Model:** Qwen3-8B (Q4 GGUF, 5.2 GB). On an NVIDIA GPU replies take about a second; on a laptop processor tens of seconds (§16).

## 6. Scheduling model

### 6.1 Hard constraints (independent validator, `analysis.validate`)

| Code | Meaning |
|---|---|
| `STUDENT_OVERLAP` · `PROFESSOR_OVERLAP` · `ROOM_OVERLAP` | Simultaneous meetings for the same person or room (adjacent meetings don't overlap) |
| `CAPACITY` | Enrolment exceeds section or room capacity |
| `ROOM_TYPE` · `COMPETENCY` · `PREREQUISITE` | Wrong room type; instructor not qualified; missing prerequisite |
| `DURATION` · `MEETING_PATTERN` | Wrong instructional minutes or meeting pattern |
| `BLOCKED_TIME` | Outside opening hours or inside a blocked window |
| `CONTRACTED_HOURS` | Instructor over contracted teaching time |
| `PROFESSOR_AVAILABILITY` · `ROOM_AVAILABILITY` | Not available at that time |

An invalid scenario still gets metrics, but its quality score is withheld, optimization is blocked (`INVALID_BASELINE`), and no change can be approved until the conflicts are fixed. In the interface, findings are grouped into plain sentences ("S001 and S087 meet at the same time. 12 students are enrolled in both"), with the codes in a details section.

### 6.2 Metrics (`analysis.metrics`, version 1.0)

Weekly student gap hours, students with 2h+/4h+ gaps, campus days, daily span, worst-decile gap hours, faculty-load Gini, room utilization, per-cohort averages, and a quality score: 40% gaps (per 1,200 min) · 20% longest gap (per 240) · 15% campus days (per 5) · 15% daily span (per 600) · 5% fragments (per 10) · 5% irregular starts (per 10), each capped at 1. Occupancy (`enrollment`) is returned as counts to every role, never as rosters.

### 6.3 Optimization (`solver.optimize`)

- **Search space:** per section, all approved start times on its current days and room plus three alternatives; meeting spacing preserved; instructor assignments fixed (so load balance and total room use don't change in this search).
- **Objective:** policy weights summing to 100 (gaps 30, days 18, fairness 14, load 12, simplicity 8, rooms 10, changes 8); split meeting times cost twice an irregular start.
- **Limits:** maximum changed sections (0–30), time budget (1–60 s; 15 s in the UI). Fixed random seed and 4 workers, so a run repeats on the same machine.
- **Outcomes:** `OPTIMAL` (best within the search space), `FEASIBLE`, `INFEASIBLE`, `UNKNOWN` (no proposal; timetable kept), `INVALID_BASELINE`.
- Every candidate is re-validated and, under request rules, re-checked by the rule checker.

### 6.3a Three-plan comparison (4 October update)

**Recommendations → Compare three plans** runs three independently validated priorities against one immutable timetable version: most time saved, fewest changes with at least 1% aggregate gap reduction, and balanced impact (worst-decile gaps first, then spreading waiting-time relief). Compare hours recovered, changed sections, benefits and harms, campus days, worst-decile gaps, and conflicts in Arabic or English. Generation saves a comparison, not a proposal. Explicitly selecting a stored plan prepares a proposal for the existing approval/publication flow. Outdated comparisons cannot be selected; identical timetables and unsuccessful searches are disclosed. No AI model is required. Policy weights are unchanged.

Fresh verification for this update: **118 automated tests passed**, plus the new end-to-end comparison flow. See [three-plan-comparison.md](three-plan-comparison.md) for objectives, API, measured examples, constraints and demo instructions. The historical 99-test results elsewhere in this document describe the original build.

### 6.4 Changes, proposals, approval and publication

- **Preview** (`preview-change`) saves nothing. It reports new conflicts, hours saved, students better/worse off, optional feasible alternatives, and whether the result could be approved: `feasible` means no new conflicts **and** no existing ones; `blocked_by_existing` flags "adds no conflicts, but the timetable already has N". Moving a meeting to its current slot is reported as `unchanged`.
- **A change request** (`/changes`) is created only on an explicit **Send for review**; a move to the current slot is refused (422). It stores what was asked (`analysis.request`).
- **Statuses:** `recommended` → `approved` → `published`, or `rejected`, `invalid` (conflicts), `superseded` (replaced by a re-evaluation).
- **Outdated (stale):** a proposal made for an older timetable version is marked **Outdated** in the list and can't be approved. Single-meeting changes can be **re-evaluated** against the current version in one click (the old one becomes `superseded`); optimizations are re-run.
- **Decision view:** Preview → Propose → Approve → Publish strip; requester, time and version; **benefit** (hours saved, students better off) and **harm and risk** (students worse off, conflicts) shown separately with exact values; for local requests, affected classes first and whole-timetable figures in a collapsible "context" section with definitions (worst-off 10%, load spread, quality score); students worse off listed as "+120 gap minutes / week · no extra campus days" (committee only).
- **Approve** keeps the decision open with "Approved · not yet published" and **Publish**, naming the version change (v2 → v3). **Publishing** re-validates against the current version; published timetables become a new version and nothing is overwritten.

## 7. The six agents

| Agent | Tool it must call before reporting | Job |
|---|---|---|
| Coordinator (fine-tuned) | — | Chooses the next specialist from the evidence; finalizes only when all reviews are current |
| Student Experience | `analyze_student_experience` | Burdened cohorts and priorities from computed metrics |
| Workforce Planning | `analyze_workforce` | Coverage and shortfall signals; never proposes hires on its own |
| Scheduling & Optimization | `optimize_schedule` | Runs the solver within the user's limits; may re-run to revise |
| Change Impact | `evaluate_change` | Validates the latest candidate (conflicts, rules, students worse off, change limit); can demand a revision |
| Recruitment Assistant | recruitment tools | Works with the hiring manager (§9) |

- **Loop (`agent_engine.run_collaboration`):** the coordinator delegates to pending specialists; a specialist must call its tool before reporting; if Change Impact rejects a candidate, scheduling and impact run again (the evidence-driven revision, covered by a test); a validation gate refuses to finalize while a review is missing or stale.
- **The final outcome is computed by code** from the validated comparison (`recommend` saves a proposal and never publishes; `no_change`; `needs_review`), not taken from the model.
- **Budgets:** 24 model decisions, 12 tool calls, 10 coordinator rounds, wall-clock limit (360 s default). Cancellation is honoured before every step; an exhausted budget ends the run as `failed` with no conclusion.
- **What the model sees:** the request, limits, summarised evidence and recent messages, with source data treated as untrusted.

## 8. Professor requests

### 8.1 Ask Mizan (request interpreter)

- **The model drafts; code decides.** The model extracts fields only (goal, sections, meetings, days, times, windows, rules), using the base model with no view of the professor's sections. Code normalizes, applies conventions, decides support (bilingual reasons), asks clarifying questions, resolves scope and permissions, and runs a date lexicon that can only make the scope more cautious.
- **Nothing runs silently.** The user sees the drafted interpretation (button: **Draft interpretation**), corrects it, and confirms. Dated changes, duration changes, online delivery and undefined goals never run.
- **Availability first:** the panel checks the local model before you type and keeps your text if it's offline, with a link to the request form.
- **Measured accuracy (frozen handwritten set, scored once):** 7/30 fully correct (Arabic 5/19), per field 22–30/30, time windows weakest. This is below a usable level for unattended use; it is kept only because of confirmation and code-side checks, and is described as drafting, never understanding.

### 8.2 "My classes" scope

Aggregates for the professor's own sections and **Improve my classes** (other sections fixed, change count capped, result is a committee request). `main.redact()` removes student identities from every professor response; a test scans the professor's endpoints for student IDs.

### 8.3 Request-scoped rules (`rules.py`)

Time windows, protected sections/meetings, locked days, keep day/time/room, breaks (professor or students), emptying a day, must change (room), maximum changes, scope. Split times only when a day-limited rule needs them ("times split by rule X"). Candidates pass an independent rule checker that groups students by their full enrolment pattern, exactly as the solver does. Infeasible rule sets are diagnosed by removing one rule at a time; `UNKNOWN` is reported as "not proven".

### 8.4 Common time finder

Ranks weekly slots (15-minute grid) for the students of chosen sections: students who can't attend, instructor free, free rooms with capacity, extra campus days, added gaps. Sections are picked by course name with search; results are cleared or marked out of date when the criteria change and state the criteria used; "All days" is explicit. Each slot can be copied or used to pre-fill a change request. It books nothing.

### 8.5 Edugate schedules: import, readiness, export

- **Reading** (`POST /api/edugate/read`, no write): Windows OCR on this PC (Arabic + English). Edugate's "Microsoft Print to PDF" output has no text layer, so the page is rendered (PyMuPDF), turned upright and read. Arabic ↔ English codes (عرب ARB, مال FIN, نما MIS, تسق MKT, ادا MGT), dot-confusion and `A-OI → A-01` corrections. Screenshots are read per day column; a missing start is filled from the same course on another day or the usual class length and flagged; a missing end (cut off) is never guessed. The uploaded file is not stored.
- **Review before import:** every row editable, warnings shown, student ID and name entered by the user. **Add to Mizan and optimize** creates an *Edugate timetable* (kind `edugate`) or adds the student to an existing one; shared course+section are shared sections. Placeholders: one instructor per section, rooms seat 40. If imported students exceed an assumed capacity, the seats are raised **and each raise is reported**; verified rooms are never raised (an overbooked verified room shows a `CAPACITY` conflict).
- **Data readiness** (`GET /api/edugate/{sid}/readiness`): Verified (student clashes checked for N imported students; verified rooms and instructors), Assumed (room capacities, instructors, availability), Not visible (other room bookings, students not imported). Staff can paste real room capacities and instructor names (`POST /api/edugate/{sid}/verify`, a new version). **Publishing an imported timetable requires verified rooms and instructors**; exploring and approving are allowed before that.
- **What is stored:** the student's name, ID and courses in the timetable; the audit log keeps a one-way code (`student#…`) instead of the ID. The import screen says so.
- **Export** (`GET /api/edugate/export`): any student's current timetable or a proposal in the Edugate layout (Letter landscape, eight columns right to left), changed rows shaded, marked as a Mizan review document (not an official Edugate record, no university logo). Students may export only their own current timetable.

## 9. Workforce and recruitment

**Workforce signals (`solver.workforce`).** For each unmet demand: required sections vs what qualified contracts can cover. `PROVEN_CAPACITY_SHORTFALL` (a capacity proof, not a timeout), `REDEPLOYMENT_REVIEW`, or `CAPACITY_AVAILABLE`. `students_demanding` is everyone who needs the course; `students_at_risk` is those left **without a seat** if only the covered sections run (demand split evenly across the required sections). Demo: 112 need Machine Learning, 2 of 3 sections are covered, **36 would have no seat**. Only a proven shortfall can become a requisition; a stale one can't be authorized.

**Recruitment (`recruitment.py`).** Requisition from a proven shortfall → human-approved job-related criteria with weights (≥ 1) → candidates (PDF/DOCX/TXT up to 5 MB, page and expanded-size caps, or pasted text; source kept and correctable) → evidence assessment (a criterion is *supported* only with a verbatim quote of 8+ characters; otherwise *unknown*; instruction-like quotes are never evidence and the CV is flagged; the score is evidence coverage, not suitability) → printable brief and chat. Never: automatic rejection or hiring, outreach, LinkedIn browsing.

## 10. The fine-tuned coordinator

| | |
|---|---|
| Base | Qwen3-8B, trained in 4-bit NF4 |
| Method | Attention-only LoRA (rank 8, α 16), 2 epochs, 12.6 min on an RTX 4080 SUPER |
| Data | 480 train / 60 validation / 120 test synthetic coordinator decisions, balanced English/Arabic; protocol frozen in `training/coordinator/PROTOCOL.md` |
| Result (deployed model, production schema, 4 Oct) | Base + original prompt **75/120** → base + training prompt **96/120** → fine-tuned **106/120**. Fine-tuning alone (same request, adapter scale 0 vs 1): 14 fixed, 4 broken, p ≈ 0.03. Helps on finishing changed candidates (2/8 → 8/8) and resisting injected "finalize" text (1/8 → 7/8); worse on "no change" (7/8 → 3/8), which code computes anyway. Repeats vary by about ±5 |
| How to say it | "On a synthetic benchmark, a better prompt took the base model from 75 to 96 correct; fine-tuning added about 10 more." Never quote the older "111 vs 75" (it changed prompt and adapter together) |
| Deployment | `.models/mizan-coordinator-lora.gguf` (15 MB, in git), applied per request only to coordinator calls. Roll back with `MIZAN_COORDINATOR_ADAPTER=0` |
| Caveat | Test cases come from the same generator as the training data: this measures whether the workflow is followed, not real-world ability. Details: `training/coordinator/deployed_ablation.md` |

## 11. Data

### 11.1 Scenarios

| Scenario | Purpose | Key facts (fresh database) |
|---|---|---|
| Baseline semester | Valid but deliberately inefficient | 15,000 gap h/week (10 h per student), quality 45, 100% with 2h+ gaps, room use 10% |
| Conflict diagnostics | Hard violations | Violations listed; quality withheld; changes can't be approved until fixed |
| Staffing shortfall | Proven capacity shortage | Machine Learning (C080): 3 needed, 2 covered, 1 uncovered; 112 need it, 36 without a seat |
| Faculty week | Realistic professor case | P001 owns S087–S091 (mixed rosters, 75/90-min courses); R040 seats 200 |
| Edugate imports | Real schedules (created by users) | Kind `edugate`; placeholders until verified; readiness report |

Demo scenarios: 1,500 fictional students (20 cohorts × 75), 80 courses in four departments with English and Arabic names, 100 sections, 40 rooms, 50 professors; seeded and reproducible (`backend/fixtures.py`). The optimizer's first moves are obvious by construction (identical cohorts): one moved section helps all 75 students of a group.

### 11.2 Data model (`backend/models.py`)

`Semester` = courses (optional registrar `code`/`code_ar`/`credits`), students, professors, rooms, sections (optional printed `label`/`activity`), demands, `Policy` (timezone, opening hours, blocked windows, allowed starts, weights), optional `term`, and `verified` (verified rooms and section instructors of imported timetables). Strict: unknown fields, duplicate IDs, broken references and prerequisite cycles are rejected.

### 11.3 Storage (`data/mizan.sqlite3`)

`scenarios` and `versions` (every version kept), `proposals`, `audit`, `requisitions`, `sessions`, `agent_runs`/`agent_events`, `request_interpretations`, `hiring_jobs`/`candidates`/`assessments`/`hiring_messages`. JSON import up to 15 MB; export as JSON.

## 12. Interface and design system

"Information System" design ([`DESIGN.md`](../DESIGN.md), tokens in `.impeccable/design.json`) with a campus overview: paper background, ink sidebar, four flat signal colours, light Archivo numerals, Noto Kufi Arabic, square corners. Colour carries two meanings: **department** (bars and timetable blocks; the overview caption says the bar colour is the department only) and **how good a number is** (continuous red → amber → green from each metric's anchors, plus a word). Harm figures (students worse off, conflicts) use a cautionary tone, never "Strong". Decision dialogs show exact values (no count-up). Reduced motion respected, focus visible, keyboard-operable timetable, AA contrast. Every string exists in English and Arabic (`t(en, ar)`); common backend errors are translated in `api.ts`.

## 13. Security, privacy and approval

- **Sessions:** random token in an HttpOnly, SameSite=Strict cookie (8 h), `Secure` over HTTPS. Role checks on every endpoint.
- **Shared demo password:** refused from non-local clients unless `MIZAN_DEMO_PASSWORD` is set; pre-filled only on localhost.
- **Cross-site protection:** state-changing calls need `X-Mizan-Action: 1` and a same-origin `Origin`; `nosniff`, same-origin referrer policy, `no-store` for API data.
- **Loopback only:** app on 127.0.0.1; the model client refuses non-loopback URLs.
- **Privacy:** professors never receive student IDs (redaction plus an endpoint-scanning test); hiring managers can't read student records; students see only their own data, their instructors' names and aggregate seat counts; free-slot results are counts. Edugate uploads are not stored; audit rows hold a one-way student code.
- **Untrusted content:** CV text is data only (instruction-like quotes never count); imports strictly validated; rendered text escaped; agent prompts treat source data as untrusted.
- **Approval:** agents and optimization only create proposals; publishing needs a registrar or admin, re-validates, and (for imports) verified data; policy changes version the scenario and make earlier proposals outdated; every action is audited.

## 14. API reference

All under `/api`, JSON, session required unless noted; state-changing calls need `X-Mizan-Action: 1`. "Staff" = admin, registrar, chair.

| Endpoint | Roles | Purpose |
|---|---|---|
| `POST /login` · `POST /logout` · `GET /me` | public / any | Session (default password: local clients only) |
| `GET /health` | public | Version and mode |
| `GET /scenarios` · `GET /scenarios/{sid}` | any | List; data scoped by role, with `enrollment` counts (students also get own instructors and `recent_changes`) |
| `GET /scenarios/{sid}/metrics` · `/export` | staff | Metrics and validation; JSON export |
| `POST /import` | admin, registrar | Import a semester JSON |
| `POST /scenarios/{sid}/optimize` | admin, registrar, professor (own) | Optimization → proposal |
| `POST /scenarios/{sid}/preview-change` | admin, registrar, professor (own) | Read-only preview; `alternatives:true` adds feasible alternatives; `unchanged`, `blocked_by_existing` |
| `POST /scenarios/{sid}/changes` | admin, registrar, professor (own) | Change request → proposal (422 for the current slot) |
| `POST /scenarios/{sid}/alternative` | admin, registrar, professor | Propose a feasible alternative |
| `GET /proposals` · `POST /proposals/{pid}/{approve\|reject\|publish}` | staff, professor (own) · admin, registrar | List (with `stale`, `actor_name`, `current_revision`) and decisions |
| `POST /proposals/{pid}/reevaluate` | admin, registrar, professor (own) | Re-run an outdated meeting change; old → `superseded` |
| `GET /scenarios/{sid}/my-classes` | professor | Own-section aggregates |
| `POST /scenarios/{sid}/free-slots` | admin, registrar, chair, professor (own) | Common free slots |
| `GET /scenarios/{sid}/placement/{course}` · `POST …/placement` | staff · admin, registrar | Rank and propose an extra section |
| `GET /scenarios/{sid}/eligible` | student | Sections that fit (with instructor and room) |
| `GET /scenarios/{sid}/workforce` | staff | Signals (`students_at_risk`, `students_demanding`) and workloads |
| `POST /scenarios/{sid}/requisitions` · `GET /requisitions` | admin, chair · staff, hiring manager | Requisitions |
| `GET /audit` | staff | Audit trail with scenario and actor names |
| `POST /scenarios/{sid}/policy` | admin | New policy version |
| `POST /edugate/read` · `POST /edugate/import` · `GET /edugate/timetables` | admin, registrar | Read (no write) · import reviewed rows (returns `notes`) · list Edugate timetables |
| `GET /edugate/{sid}/readiness` · `POST /edugate/{sid}/verify` | staff · admin, registrar | Data readiness · record verified rooms and instructors |
| `GET /edugate/export` | staff; student (own, current) | Edugate-layout PDF |
| `GET /agents/status` · `POST /agents/runs` · `GET /agents/runs[/{id}]` · `POST …/cancel` | status: staff, hiring manager, professor · runs: admin, registrar | Model status; agent runs |
| `POST /requests/interpret` · `/{id}/revise` · `/{id}/confirm` · `/{id}/cancel` · `GET /requests` | admin, registrar, chair, professor | Ask Mizan |
| `/recruitment/…` | admin, chair, hiring manager | Recruitment |

## 15. Repository layout

```
backend/        FastAPI app and domain modules (see §5)
frontend/       React app (src/); built site in dist/ (not in git; built by scripts/setup.ps1)
tests/          pytest suites; browser-smoke.cjs, browser-phase2.cjs, browser-edugate.cjs
training/       coordinator fine-tuning and evaluation (coordinator/), interpreter evaluation (interpreter/)
scripts/        setup, start, start/restart model, reset-demo, check-setup, test, apply-update, demo/record-demo.cjs
docs/           this document, v4 (history), v3 spec, acceptance report, demo script, handover, evidence, reviews/, test log, deck, AI-BRIEFING.md
.models/        fine-tuned adapter (in git); base model downloaded here (not in git)
.runtime/       bundled llama.cpp runtime (downloaded, not in git)
data/, work/    local database, backups, logs, screenshots (not in git)
DESIGN.md, PRODUCT.md, AGENTS.md, CLAUDE.md, .impeccable/   design system, product brief, notes for coding assistants
*.cmd           Start Mizan · Reset Mizan Demo · Check Mizan Setup · Apply Mizan Update
```

## 16. Installing and running

Step by step for a new PC: [HANDOVER.md](HANDOVER.md). In short:

1. Windows 10/11, Python 3.12, Node.js 24+ (setup only), about 10 GB free.
2. `scripts\setup.ps1`: Python packages from `requirements.lock.txt` (incl. PyMuPDF, Pillow, Windows OCR bindings) and the web build.
3. `.venv\Scripts\python.exe scripts\install_model_runtime.py`: optional local AI runtime and Qwen3-8B (~7 GB, checksum-verified); deterministic comparison and scheduling work without them.
4. **Check Mizan Setup.cmd** → **Reset Mizan Demo.cmd** → **Start Mizan.cmd** (http://127.0.0.1:8000).

**Hardware.**
- **NVIDIA GPU (8 GB+):** the model runs on CUDA; AI replies in about a second.
- **No NVIDIA GPU** (e.g. AMD Ryzen laptop with Radeon graphics): `start-model.ps1` runs the model on the processor and `start.ps1` raises the AI request timeout to 10 minutes (`MIZAN_MODEL_TIMEOUT`). Measured on a desktop Ryzen 7 9800X3D: about 52 prompt tokens/s, 10–16 output tokens/s, 4–11 s per coordinator decision; a laptop is slower. Timetable features are unaffected; Ask Mizan, CV analysis and agent runs take from tens of seconds to minutes. Override the device with `MIZAN_MODEL_DEVICE=cpu|cuda`. (A Vulkan path for Radeon graphics was tried and didn't engage; it is not offered.)
- **Edugate import** needs the Windows OCR languages Arabic and English (Settings → Time & language → Language).

Without the model, everything works except Ask Mizan, agent collaboration and CV analysis.

## 17. Testing and quality

| Suite | What it covers | Result (4 Oct) |
|---|---|---|
| `scripts/test.ps1` (pytest, 99 tests) | Metrics, validation, solver statuses, rules, scope and redaction, interpreter safety, agents (revision, budgets, cancellation), recruitment evidence and injection, API authorization, CSRF, staleness, import/export, Edugate (incl. OCR round trip and readiness), UX-review and expert-review behaviour | 99 passed |
| `tests/browser-smoke.cjs` | Placement → approve → publish; conflicting change → preview → alternative; shortage → requisition; full optimization → evidence; student access; EN/AR figures identical; mobile | 5/5 + parity |
| `tests/browser-phase2.cjs` | Live model: agent run, recruitment assessment and chat, Arabic mobile | Passed |
| `tests/browser-edugate.cjs` | Edugate PDF and app screenshot → review → import → optimize → export (`EDUGATE_FILE`, not committed) | Both passed |
| `training/coordinator/deployed_eval.py` | 120 synthetic coordinator decisions, three arms | 75 → 96 → 106 |
| `training/interpreter/eval_interpreter.py` | Frozen 30-case handwritten set (scored once) | 7/30 strict |

The table above records historical 4 October evidence, not a fresh live-model run. Current release checks are in [release-verification.md](release-verification.md). Historical log: [test-log-2026-10-04.txt](test-log-2026-10-04.txt).

## 18. Known limitations

- **Synthetic demo data** with a deliberately poor start; no institutional deployment is claimed. The optimizer has not been measured on a real department's full timetable.
- **Time-limited search:** results are optimal only within the searched options; whole-semester optimization on *Faculty week* hits its limit (`UNKNOWN`), own-section runs finish in about 1 s.
- **Instructor assignments are fixed** during optimization.
- **Ask Mizan** drafts at 7/30 strict accuracy; it waits while an agent run uses the model (one model server, one request at a time).
- **Coordinator evaluation** is on generator-made cases.
- **Edugate import** knows two layouts and five course prefixes, needs Windows OCR, and can miss single-digit section numbers (the review step shows every row). Imported data is incomplete until verified.
- **Slow AI without an NVIDIA GPU** (§16).
- **Professor redaction** removes known student fields (guarded by a test) rather than building responses from an allow-list.
- **Interface:** filters aren't in links; optimization can't be cancelled; no best-so-far progress; full Arabic language and screen-reader reviews not done.

## 19. Deferred work (after Farq)

From the strategic review ([reviews](reviews/README.md)) and the v3.1 plan:
- Semester calendar: dated one-off changes, holidays, Ramadan schedules, exams, makeup and online sessions, different session lengths.
- Bulk import of real faculty assignments, room capacities, full rosters and existing bookings; joint staffing + timetable optimization.
- Approval stages, comments, notifications, calendar export, effective dates, version comparison and restore.
- Extend the implemented three-plan comparison with configurable individual-harm safeguards and additional institutional objectives.
- Travel time between buildings, accessibility, equipment.
- Pilot foundations: university identities, department-scoped access, background jobs with progress and cancel, migrations and backups, performance on large anonymized data.
- A more reliable Ask Mizan with a new independent test set; varied coordinator training data.

## 20. Reviews and project history

**Reviews (4 Oct 2026, in [docs/reviews](reviews/README.md)):** a hands-on usability review (42 findings; all fixed or partly fixed), and two expert-panel reviews (code reading, then runs). The status table maps every finding ID to its fix and test.

| Date (2026) | Milestone |
|---|---|
| Build 1 | Scheduling application: metrics, validation, optimization, change requests, bilingual UI |
| Build 2 | Agents and recruitment assistant with local Qwen3-8B |
| 23 Sep | Spec v3.0: six-agent architecture |
| 24 Sep | Interactive timetable; fine-tuned coordinator live |
| 27 Sep | Spec v3.1 professor requests (interpreter, My classes, rules, free-slot finder); interface v4 "Information System" |
| 27–28 Sep | Phase 3: acceptance tests, CV-injection guard, reset and setup tools, demo script, handover, v4 documentation |
| 28 Sep | Campus overview front end; scripted demo recorder |
| 4 Oct | Edugate import/export; research evidence for the pitch; pitch deck (PowerPoint) |
| 4 Oct | Usability review implemented (role workspaces, preview-before-submit, request queue, decision view, outdated/re-evaluate, plain conflicts) |
| 4 Oct | Expert reviews: coordinator re-measured with three arms; claims corrected; data readiness and publish guard; students without a seat; rule-checker grouping; password and audit privacy; evening hours; CPU mode for laptops; this document |

## 21. Glossary

- **Gap:** idle time between a student's classes on the same day.
- **Search space / neighbourhood:** the alternative times and rooms the solver may choose from.
- **Preview:** a read-only check of a change; nothing is saved.
- **Proposal / request:** a candidate change awaiting a human decision.
- **Outdated (stale):** made for an older timetable version; can't be approved; can be re-evaluated.
- **Superseded:** replaced by a re-evaluated request.
- **Publish:** make an approved proposal the official local timetable, after re-validation.
- **Proven capacity shortfall:** qualified contracts can't cover the required sections, whatever the timetable.
- **Students without a seat:** demand minus the seats of the covered sections.
- **Data readiness:** what an imported timetable has verified, assumes, or can't see.
- **LoRA adapter:** a small set of fine-tuned weights applied on top of the base model.
- **Graded number:** a value coloured continuously from red (bad) to green (good) by its metric's anchors.


## 22. Release update — 5 October 2026

### Three alternative plans

Recommendations and the optimization dialog offer **Compare three plans**. Each search uses the same timetable revision and independent validation:

| Plan | Priority |
|---|---|
| Most time saved | Total student gap time, then campus days and changes |
| Fewest changes | Minimum changed sections while recovering at least 1% of current gap time |
| Balanced impact | Worst-off 10% gap burden first, then distribute relief across long waits |

Compare current vs all plans using weekly gaps, hours recovered, sections changed, students helped/harmed, campus days, worst-decile gaps, largest gap increase and hard conflicts. Expand the class changes; explicitly select a plan to create a proposal. Staff then approve and revalidate before local publication. Searching creates no proposal and does not alter the current timetable. Comparisons persist and become outdated when the revision changes. Duplicate plans, time-limited valid solutions and unproven searches are disclosed. There is no guarantee that three distinct plans exist or that every student improves. Search uses a bounded neighbourhood.

API: `POST /api/scenarios/{sid}/plan-comparisons`, `GET /api/scenarios/{sid}/plan-comparisons`, `POST /api/plan-comparisons/{cid}/{key}/select`. Generation/selection require admin or registrar; readable results require staff authorization. See [three-plan-comparison.md](three-plan-comparison.md).

### Imported timetable and privacy fixes

- Instructor verification links sections to a stable shared ID. Use `section, instructor name, instructor ID` in the verification form. The optional ID distinguishes people with the same name. Without it, equal normalized names conservatively share one identity. Shared instructor overlaps now appear in validation. Names alone are not sufficient institutional identity evidence.
- Existing resource availability survives further student imports. New placeholders still assume broad availability; actual availability, contracts, qualifications and external bookings require institutional review.
- Verified smaller rooms replace unverified placeholder section capacity without hiding enrollment overflow. The verification API also accepts `sections:[{id,capacity}]` to record a separate actual section capacity; future room edits preserve it.
- Readiness separates `facts_verified` from `ready_to_publish` and includes `conflict_count`. All resource facts may be verified while conflicts still prevent publication. The UI states that distinction.
- Professor conflict responses remove student identifiers by issue meaning, including numeric and non-ST IDs and prerequisite issues.
- Ask Mizan read-only preview reports existing invalid baseline constraints and unchanged moves consistently with ordinary preview.

### Reproducibility and delivery

Setup selects Python 3.12 and fails early on other versions. pnpm bootstrap is pinned to 12.9.1; dependencies use the frozen lockfile. GitHub Actions checks backend tests and frontend build on Windows/Python 3.12/Node 24. `.gitattributes` defines text line endings; interpreter benchmark hashing normalizes LF/CRLF without altering cases or recorded results. Temporary yellow feature-tour styling is removed; ordinary product status colours remain.

See [GITHUB-PUSH.md](GITHUB-PUSH.md), [HANDOVER.md](HANDOVER.md), [CHANGELOG.md](../CHANGELOG.md), and [release-verification.md](release-verification.md). v3/v4 and earlier dated test logs are retained as history.
