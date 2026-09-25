# MIZAN — ميزان
## Project documentation v3.0

**Revised six-agent architecture · 23 September 2026**

Operational scheduling intelligence and evidence-based workforce planning for university administration.

**Status:** Proposed implementation specification. This document describes the system to be built, not features already implemented or results already measured. It supersedes the eight-agent architecture in v2.0.

## 1. Product vision

MIZAN helps university staff evaluate a semester before publication, improve valid timetables, assess changes, identify teaching-capacity shortages, and prepare recruitment decisions when additional staff are needed.

A timetable can satisfy every scheduling rule and still impose long student gaps, excessive campus days, uneven teaching loads, and poor room utilization. MIZAN measures those costs and recommends specific, reviewable changes.

The revised design uses six AI agents that collaborate through a controlled workflow. They use shared software tools to calculate metrics, validate rules, simulate scenarios, and search for improved schedules. An agent's explanation is never evidence that a schedule is feasible: feasibility must come from the validation tools.

University staff approve schedule publication. Hiring managers retain responsibility for recruitment decisions.

## 2. Starting conditions and scope

The initial build assumes one personal computer, no access to a university database, and possible access to public datasets or course catalogs.

MIZAN will create its own local database. It will initially contain synthetic students, faculty, enrollments, rooms, availability, and timetables. Public course information may supply realistic course names and prerequisite structures when its reuse is permitted.

The standalone application can demonstrate all current workflows without a university connection. In this mode, publishing changes updates MIZAN's own official timetable. Updating a university registration system is a later integration.

Candidate evaluation will initially use fictional candidate records or CVs supplied with authorization. Live sourcing, messaging, university integrations, and external service accounts are separate capabilities that require the relevant access.

### Product lifecycle

1. **Simulate:** Evaluate the proposed semester and expose scheduling burdens.
2. **Optimize:** Find feasible changes that improve defined objectives.
3. **Place:** Rank meeting times for additional sections.
4. **Adapt:** Evaluate proposed changes to an existing timetable.
5. **Staff:** Identify capacity shortages and assess internal coverage options.
6. **Recruit:** Help a hiring manager evaluate candidates for an approved staffing need.

## 3. Users and authority

- **Scheduling committee:** Compare scenarios, inspect changes, and approve recommendations.
- **Registrar:** Review section placement and publish approved timetable changes.
- **Department chair:** Review teaching coverage, competencies, and staffing requisitions.
- **Hiring manager:** Define job requirements, review candidate evidence, and make hiring decisions.
- **Professor:** Submit proposed meeting changes and view their consequences.
- **Student:** View their own timetable, quality metrics, eligible sections, and approved changes.
- **System administrator:** Manage configuration, data imports, access, and local deployment.

Roles restrict both actions and visible data. Student views must not expose other students' records. Recruitment records must be restricted to authorized recruitment users.

## 4. What counts as an agent

An agent has a bounded objective, access to approved tools, shared task context, and the ability to choose a next action based on results. It may request additional analysis, challenge another agent's proposal, or revise its own recommendation.

A function that calculates gaps or checks prerequisites remains a tool. Calling a deterministic function an agent does not make the system agentic.

MIZAN contains **six logical AI agents**, not six separately trained models. Initially, all six can share one locally hosted, pretrained language model while using different instructions, permissions, tools, and task state. Sequential execution is acceptable on a single PC; collaboration does not require simultaneous inference.

No custom model training or fine-tuning is required for the initial release. Hardware suitability and model quality must be measured before selecting the local model.

## 5. The six agents

### 5.1 Coordinator Agent

**Objective:** Translate a user request into bounded work, direct collaboration, and produce one consolidated recommendation.

The coordinator identifies the requested outcome, records constraints, assigns tasks, requests revisions, and resolves the workflow when agents disagree. It distinguishes validated facts from assumptions and unanswered questions.

**Tools:** Task dispatch, scenario retrieval, result aggregation, report assembly, and approval-workflow services.

**Output:** A decision packet containing the recommendation, alternatives, evidence, trade-offs, solver status, unresolved issues, and required approval.

**Boundary:** Cannot override hard constraints, invent facts, approve hiring, or publish a schedule by itself.

### 5.2 Student Experience Agent

**Objective:** Identify which student groups face the greatest scheduling burden and recommend analysis priorities.

It examines gaps, daily spans, campus days, fragmentation, and cohort differences. It can request deeper analysis of the worst-affected students and challenge recommendations whose average improvement hides substantial regressions.

**Tools:** Student metrics, cohort aggregation, fairness analysis, schedule-quality scoring, and eligibility queries.

**Output:** Ranked improvement targets, affected cohorts, and evidence-backed student-impact findings.

**Boundary:** All metrics come from tools; the agent does not estimate missing values as facts.

### 5.3 Scheduling & Optimization Agent

**Objective:** Find improved scheduling alternatives within approved academic and operational constraints.

It selects supported optimization configurations, invokes the solver, examines results, and requests bounded reruns when appropriate. It also evaluates candidate slots for additional sections.

**Tools:** OR-Tools CP-SAT, candidate generation, constraint validation, section placement, and scenario comparison.

**Output:** Versioned candidate schedules, exact proposed moves, validated metrics, solver status, runtime, and objective values.

**Boundary:** The language model does not generate and execute arbitrary solver code. It selects validated tool inputs. It cannot represent a feasible solution as a proven optimum.

### 5.4 Change Impact Agent

**Objective:** Examine disruption and consequences before any proposed change is approved.

It checks affected students, faculty, rooms, conflicts, gap changes, extra campus days, and the number of modified meetings. It can request alternatives when a proposal is infeasible or its disruption exceeds configured limits.

**Tools:** Change-impact evaluation, constraint validation, scenario differences, and alternative-slot analysis.

**Output:** An impact assessment identifying beneficiaries, adversely affected groups, conflicts, and feasible alternatives.

**Boundary:** Does not approve or publish changes.

### 5.5 Workforce Planning Agent

**Objective:** Determine whether teaching capacity can cover the required sections and distinguish staffing problems from scheduling problems.

It evaluates instructor competencies, availability, contracted hours, and potential redeployment. It requests targeted diagnostic runs before attributing an infeasible schedule to staffing.

**Tools:** Capacity analysis, competency matching, workload metrics, diagnostic solver scenarios, and requisition generation.

**Output:** Internal coverage options or an evidenced staffing requisition specifying competency, uncovered sections, affected students, teaching hours, and the constraint responsible.

**Boundary:** A solver timeout does not prove a staffing shortage. Any attributed cause must have diagnostic support. Overload may be shown as a separately labeled policy exception, never silently treated as valid.

### 5.6 Recruitment Assistant Agent

**Objective:** Help a human hiring manager assess candidates against an approved staffing need.

It receives the workforce requisition, asks the hiring manager to confirm job requirements and evaluation criteria, and searches authorized candidate sources when connected. It can inspect supplied CVs, assemble evidence, compare qualifications, and suggest interview questions.

**Tools:** Requisition retrieval, CV extraction, authorized candidate-source adapters, criteria-based scoring, candidate-brief generation, and draft communications.

**Output:** A reviewable shortlist, criterion-level evidence, missing-information flags, candidate briefs, and draft communications when requested.

**Boundary:** No autonomous hiring or rejection. No invented qualifications. No scoring based on protected characteristics, inferred sensitive traits, or unrelated personal information. Missing information remains unknown rather than being automatically scored as failure.

## 6. Collaboration and a single conclusion

Agents communicate through structured task records managed by the coordinator. Each record includes a task identifier, scenario version, request, assumptions, tool-result references, findings, issues, proposed next step, and completion status.

All agents evaluating a proposal use the same immutable data snapshot. A changed snapshot creates a new analysis version.

### Example workflow

**Request:** Reduce student waiting time without hiring additional faculty or changing more than five sections.

1. The coordinator records the two limits and requests baseline analysis.
2. Student Experience identifies the most burdened cohorts.
3. Scheduling runs the optimizer with the limits enforced.
4. Workforce verifies existing instructor coverage and contracted hours.
5. Change Impact examines regressions and disruption.
6. If a reviewer finds an issue, the coordinator requests a bounded revision.
7. The coordinator returns a consolidated recommendation with verified results and explicit trade-offs.

The system does not decide correctness by agent majority vote. Hard constraints are enforced by code. Soft trade-offs follow documented weights and approved limits. If no acceptable alternative is found, the conclusion reports that outcome and preserves the existing valid timetable.

### Execution controls

- Configure a maximum number of revision rounds, tool calls, and elapsed runtime per task.
- Prevent duplicate work by caching results against scenario and configuration versions.
- Reject invalid tool parameters and malformed outputs.
- Record tool failures and partial results without presenting them as completed analysis.
- Stop on unresolved contradictions and return a clear issue for human review.
- Store concise decision summaries and tool evidence for auditing.

## 7. Shared deterministic tools

The following remain software tools rather than additional agents:

- **Constraint validator:** Student, professor, and room overlaps; capacity; availability; duration; room suitability; blocked periods; contracted hours.
- **Eligibility checker:** Completed prerequisites, co-requisites where applicable, and approved registration rules.
- **Semester simulator:** Per-student and institution-level evaluation of a fixed scenario.
- **Student metrics engine:** Weekly gap hours, long gaps, campus days, daily span, fragmentation, and fairness comparisons.
- **Optimization engine:** Valid assignment search using OR-Tools CP-SAT.
- **Section-placement evaluator:** Eligible student compatibility, available seats, room suitability, extra days, and added gaps.
- **Change-impact evaluator:** Before/after differences and affected populations.
- **Workforce analyzer:** Competency coverage, contracted capacity, diagnostic shortages, and load distribution.
- **Recruitment evidence tools:** Document extraction, source tracking, explicit scoring rules, and document generation.

The interface injects validated numerical results into reports. Generated prose must reference those facts and must not introduce unsupported numerical or feasibility claims.

## 8. Scheduling decision model

### Hard constraints

Preserve required instructional duration and meeting patterns. Prevent student, faculty, and room overlaps. Respect capacities, room types, approved availability, prerequisites where assignment is involved, and contracted teaching hours unless a separately authorized policy exception applies.

Support configured prayer-time blocks, holidays, and Ramadan-adjusted windows. Institutional rules and calendars are input configuration, not assumptions made by the model.

### Soft objectives

Initial configurable weights carried forward from v2.0 are: student gap reduction 30%; campus-day reduction 18%; student fairness 14%; teaching-load balance 12%; schedule simplicity 8%; room utilization 10%; minimum modifications 8%.

These are starting values, not validated university policy. Normalize objective terms, document their definitions, avoid double-counting, and version all settings.

### Metrics

Weekly student-hours recovered equals baseline weekly gap hours minus candidate weekly gap hours, using the same population and definitions.

Report long-gap counts at two and four hours, campus days, daily span, teaching-load Gini, room utilization, changed sections, and solver runtime. Show the most burdened student decile and the number and magnitude of adverse student outcomes.

A 0–100 quality score may summarize these measures using documented reference ranges and weights. It must always appear alongside component metrics and must never conceal a hard violation.

## 9. Recruitment workflow and candidate documents

1. **Establish need:** Workforce produces a requisition supported by current capacity evidence.
2. **Authorize recruitment:** The hiring manager approves recruitment and confirms the job requirements. A staffing signal alone does not start outreach.
3. **Define evaluation:** Record essential requirements, preferred qualifications, weights, evidence standards, and review ownership before ranking candidates.
4. **Collect candidates:** Import authorized CVs or use an approved connected source. The initial offline version uses sample or supplied records.
5. **Evaluate:** Separate eligibility requirements from comparative scoring. Show source evidence for each scored criterion, unknown information, and any extraction uncertainty.
6. **Review shortlist:** Present candidates for human assessment. Preserve the criteria version and allow correction of inaccurate candidate information.
7. **Prepare follow-up:** Draft questions and messages. External sending requires explicit authorization and an available connection; drafts remain local otherwise.

### LinkedIn and external access

LinkedIn is a possible source, not a guaranteed dependency. Implement a source adapter only when an authorized access method is available and its terms permit the intended use. Do not assume unrestricted scraping or access to private profiles. User-supplied profile information can be reviewed with source and date recorded.

### CV versus candidate brief

A **candidate brief** is MIZAN's internal evidence summary for a hiring manager. It clearly distinguishes verified information, source claims, and unknowns.

A **formatted CV** is a document prepared from information supplied or confirmed by the candidate. It requires candidate verification before being treated as their résumé. The system must not invent employment history, degrees, certifications, or skills, or present a research summary as candidate-authored material.

## 10. Data design and prototype datasets

Core records include Student, Course, Prerequisite, Section, Meeting, Professor, Competency, Room, Enrollment, Availability, Scenario, Assignment, Change Request, Approval, Staffing Signal, and Staffing Requisition.

Recruitment adds Job Requirement, Evaluation Criterion, Candidate, Candidate Document, Source Evidence, Candidate Assessment, Shortlist, and Communication Draft.

Agent execution adds Agent Task, Tool Run, Decision Packet, and Audit Event.

Repeated section meetings are stored separately. Scenario assignments, objective settings, criteria, tool results, and approvals are versioned. Professor competency and contracted-hour fields are required for workforce analysis.

### Dataset strategy

Start with a small fixture for correctness, then scale toward approximately 1,500 students, 80 courses, 100 sections, 40 rooms, and 50 professors. Final dimensions depend on hardware and solver performance.

Maintain three separate scheduling datasets:

- A valid baseline with inefficient gaps and opportunities for improvement.
- Invalid diagnostic cases containing capacity mismatches or scheduling conflicts.
- A staffing-shortfall case where required demand cannot be covered under the stated faculty constraints.

This corrects v2.0's inconsistent request for a valid baseline containing a room-capacity violation. Use fixed generation seeds and record source provenance. Label all synthetic results clearly.

Use fictional recruitment candidates with varied strengths, incomplete information, and at least one document-parsing edge case. Do not use real personal records merely to make the demo look realistic.

## 11. Application and deployment

### Suggested implementation

- **Frontend:** React or Next.js with Arabic RTL and English LTR support from the first components.
- **Backend:** Python and FastAPI.
- **Database:** SQLite for initial local development; PostgreSQL when concurrency or deployment requirements justify it.
- **Optimization:** OR-Tools CP-SAT.
- **Agent workflow:** An explicit state machine or LangGraph with bounded transitions and typed tool inputs.
- **Model:** One locally served, Arabic-capable pretrained model shared by the six logical agents, selected after a hardware and quality check.
- **Documents:** Local CV extraction and candidate-brief export, with OCR support added if needed.

No external AI API is required by this design. Internal application APIs and optional external candidate-source connections are distinct from AI-provider APIs.

If the PC cannot run a suitable model, deterministic workflows and bilingual templates can still support development and demonstrations. That fallback must be described as a workflow-based version, not as six operating AI agents. Hosted model use would be a separate architecture decision requiring an explicit decision about data handling.

### Essential screens

- Administration dashboard with semester metrics and scenario comparison.
- Virtual Semester view with timetable exploration and cohort analysis.
- Recommendation detail with exact moves, evidence, adverse impacts, and approval state.
- Change-request workspace with alternatives and publication status.
- Workforce workspace with coverage, shortages, and requisitions.
- Recruitment workspace with requirements, candidate evidence, shortlist, and drafts.
- Student read-only timetable and eligible-section view.
- Agent activity view showing task progress, tool results, and concise decision summaries.

## 12. Approval, privacy, and reliability

Immediately before publication, revalidate the approved candidate against the current timetable. If the data has changed, invalidate stale approval or request a fresh review. Publish changes atomically and preserve the prior version for recovery.

Keep institutional scheduling records and recruitment records local by default, restrict access by role, and configure retention and deletion. Before real institutional use, establish the university's data-handling and legal requirements through its responsible staff; this document does not establish compliance.

Treat imported catalogs, webpages, profiles, and CVs as untrusted data. Instructions embedded in them must not alter agent behavior or trigger tool calls. External content cannot authorize messages, access expansion, or publication.

## 13. Validation and acceptance criteria

The current release is complete when:

1. A reproducible local dataset can be imported or generated and explored.
2. Metrics match hand-checked fixtures, including repeated meetings and boundary times.
3. Every recommended schedule passes independent constraint validation.
4. Solver results distinguish feasible, optimal, infeasible, and unknown/time-limited outcomes correctly.
5. Scenario comparisons use the same population and versioned settings.
6. Agents demonstrate at least one evidence-driven revision, rather than only a fixed sequence of calls.
7. The workflow stops within configured budgets and handles failures without unsupported conclusions.
8. Workforce findings distinguish a demonstrated capacity shortage from an inconclusive solver run.
9. Recruitment assessments trace to approved job-related criteria and candidate evidence, with unknowns visible.
10. No schedule publication, candidate rejection, hiring decision, or external outreach occurs without the required human authorization.
11. Arabic and English screens display identical verified facts, including correct RTL layout.
12. Stale approvals, unauthorized access, and malicious instructions in imported documents are covered by meaningful checks.

Agent evaluation should test tool selection, adherence to constraints, unsupported claims, revision behavior, and reliable termination. Scheduling correctness is tested independently of language-model quality.

## 14. Build sequence and provisional effort

Build the mathematical and data foundation before adding agent reasoning. Agent collaboration is useful only when its tools return trustworthy results.

1. **Foundation:** Local database, fixtures, imports, scenario versioning, bilingual application shell.
2. **Scheduling core:** Metrics, validation, simulation, optimization, and before/after comparison.
3. **Operational workflows:** Section placement, change impact, workforce diagnostics, and approvals.
4. **Agent layer:** Six role definitions, tool permissions, coordinator state, bounded revision, and evidence tracking.
5. **Recruitment:** Approved requisitions, sample CV ingestion, criterion-based comparison, shortlist, and document outputs.
6. **Hardening:** End-to-end evaluation, permissions, stale-data handling, performance tuning, and demonstration preparation.

For one developer working consistently with AI assistance, a provisional planning range is **2–3 weeks for a focused scheduling demo** and **12–18 weeks total for a tested standalone six-agent release including offline recruitment**. These are estimates, not commitments. Experience, available hours, local-model hardware, and feature depth may materially change them.

Live candidate sourcing, external messaging, university-system integration, and institutional deployment are excluded from that range until access and requirements are known. Start with a hardware inspection and a small end-to-end prototype before fixing a delivery date.

## 15. Demonstration scenarios

### Semester improvement

Open a valid but inefficient timetable. Show measured student burden, run optimization, inspect one concrete move, and demonstrate the agents evaluating its consequences before human approval.

### Capacity shortage and recruitment

Open a separate staffing-shortfall scenario. Show the diagnostic evidence, consider internal coverage, prepare a requisition, obtain simulated hiring-manager approval, and compare fictional candidates against declared criteria.

### Mid-semester adaptation

Submit an infeasible change, show the conflicts, generate a feasible alternative, and revalidate before publication to MIZAN's local official timetable.

All displayed quantities must be computed from the demonstration dataset. No illustrative improvement is presented as a measured outcome, and synthetic results are labeled on screen.

## 16. Deferred capabilities

Demand forecasting, predictive hiring need, exam scheduling, graduation progression planning, full disruption recovery, and campus-wide simulations remain future scope. Demand forecasting requires suitable historical data and separate model evaluation; it is not part of the six-agent release.

## 17. Architecture summary

**Six AI agents collaborate through a coordinator. Shared deterministic tools compute facts and enforce scheduling rules. One pretrained local model may power all six roles. Human staff approve operational changes and recruitment decisions.**

The initial product is a complete standalone application on the available PC, backed by synthetic and permitted public data. Real-world integrations are added when access exists, without overstating what the local prototype has demonstrated.
