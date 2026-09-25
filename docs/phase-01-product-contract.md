# Phase 1 — Product contract and review checkpoint

**Status: approved as the scope reference. Delivery gates consolidated into three build phases by the user.**

This contract translates v3 into reviewable deliverables. Its original seven-part breakdown below is retained as implementation detail. The approved delivery gates are now: (1) working scheduling application, (2) six agents and recruitment, and (3) final verification and delivery. See the current README and build checkpoint for implementation status. The feature scope is unchanged.

## 1. The finish line

MIZAN is a locally runnable, Arabic/English application that evaluates a semester, proposes valid improvements, explains their effects, identifies staffing shortages, and helps a hiring manager review candidates. Six agents collaborate using verified tools, with one consolidated decision packet for each task.

The user can complete the end-to-end journeys below on this PC using supplied synthetic fixtures. The software persists work across restart, exposes failures honestly, and provides repeatable setup and demo instructions.

University access is not needed for this release. A local official timetable is the publication destination. Candidate research initially uses fictional or authorized supplied information. Live source connections remain visibly unavailable until real access is configured.

## 2. Scope checklist

### Scheduling and simulation

- Import or generate a semester; inspect courses, sections, repeated meetings, rooms, enrollments, faculty availability, and prerequisites.
- Calculate weekly gaps, long-gap counts, campus days, daily spans, score components, cohort fairness, room utilization, and teaching-load distribution.
- Generate improved schedules with configurable objectives and limits on changed sections.
- Show exact moves, before/after metrics, affected students, regressions, constraint results, and solver status.
- Rank feasible times for new sections using eligible students, conflict compatibility, gaps, campus days, and available capacity.
- Evaluate professor change requests and feasible alternatives.
- Approve, reject, and publish changes with current-data revalidation and audit history.

### Workforce and recruitment

- Diagnose competency and contracted-hour shortages; distinguish them from unrelated infeasibility or solver timeout.
- Evaluate internal coverage before preparing an evidenced requisition.
- Let the hiring manager confirm job requirements and scoring criteria through a guided conversational workspace.
- Import text-based PDF and DOCX CVs, with clear unsupported/scanned-document feedback until OCR is implemented. Preserve extracted evidence for human correction.
- Compare candidates against approved job-related criteria, identifying supported qualifications and unknown information.
- Produce a ranked shortlist with criterion-level evidence, candidate briefs, interview questions, and communication drafts.
- Format a CV from candidate-supplied or confirmed information, explicitly marking it as pending candidate verification when applicable.
- Do not send external messages or make hiring/rejection decisions autonomously.

### Agent system and application

- Six separate agent roles with bounded objectives, permitted tools, structured messages, and shared scenario identifiers.
- Coordinator dispatch, specialist challenges, revisions based on tool evidence, and a single decision packet.
- Arabic RTL and English LTR screens sharing the same factual records.
- Role-based server-side access, local persistence, approval history, and evidence-linked agent activity.
- Read-only student view with own timetable, quality indicators, eligible sections, and approved changes.

## 3. Explicit boundaries

Included: all standalone v3 workflows, synthetic datasets, local model integration, local approvals, candidate documents, meaningful tests, and packaging.

Access-dependent: live LinkedIn sourcing, external messaging, real university import adapters, and publishing into university systems. Provide honest connection states; do not substitute fake successful integrations. Drafting and supplied-CV review remain functional without them.

Deferred as in v3: forecasting demand and hiring, exam scheduling, graduation progression planning, full disruption recovery, and campus-wide simulation beyond the defined semester workflow.

No model training is required. A template-only fallback can support development but does not satisfy final agent acceptance.

## 4. Screens and navigation

The main navigation contains Overview, Semester Lab, Recommendations, Change Requests, Workforce, Recruitment, Agent Activity, and Settings. Students receive a restricted My Timetable view. Faculty receive a restricted timetable/change-request experience.

Overview shows the selected scenario, data provenance, computed indicators, and pending decisions. Semester Lab combines a timetable, cohort filters, simulation, and comparisons. Recommendation details connect every proposed move to consequences and approval state.

Workforce connects shortage evidence to a requisition. Recruitment connects that requisition to requirements, candidate evidence, shortlist, and exports. Agent Activity shows concise task messages and actual tool events, not fabricated dialogue or private chain-of-thought.

Phase 2 uses a professional institutional visual direction with readable timetables, clear comparison views, and Arabic support from the start. Its purpose is to get visual approval before substantial backend integration. Sample values are visibly labeled.

## 5. Reviewable user journeys

### Journey A — Improve a semester

Select the valid but inefficient fixture, inspect baseline indicators, request improvement with at most five changed sections and no additional hires, review the agent-supported result, inspect one move, approve, and publish locally.

**Accept when:** reported metrics reproduce from stored assignments; independent validation passes; limits hold; adverse outcomes remain visible; restarting retains the publication and audit record. Finding no acceptable improvement is a valid outcome when reported honestly.

### Journey B — Add a section

Choose a course, inspect eligible students, compare candidate slots, and create a proposed section placement.

**Accept when:** prerequisite failures, occupied rooms, unavailable faculty, capacity limits, and conflicting enrollments are handled correctly. Counts must not imply all eligible students are guaranteed a seat.

### Journey C — Evaluate a requested move

A professor requests a conflicting move. Staff see why it fails, inspect a feasible alternative, and approve it. Change the timetable before publication to test stale approval handling.

**Accept when:** conflicts name the relevant records; the infeasible move cannot publish; stale approval requires reevaluation; the publication is atomic.

### Journey D — Resolve a shortage

Select the staffing-shortfall fixture, examine competency coverage and contracted hours, test internal reassignment, and prepare a requisition if the shortage remains.

**Accept when:** evidence identifies the limiting resource and uncovered demand. A timeout or unrelated room conflict does not become a claim that hiring is necessary.

### Journey E — Assist a hiring manager

Approve the requisition for recruitment, confirm requirements in the hiring workspace, import sample CVs, inspect and correct extraction, compare candidates, review the shortlist, and export a candidate brief or supported CV draft.

**Accept when:** rankings expose criteria and evidence, unknowns are visible, unsupported credentials are absent, criteria changes create a new assessment version, and no external communication is sent implicitly.

### Journey F — Inspect agent collaboration

Submit a scheduling goal and observe specialists requesting analysis, reviewing solver evidence, raising a concrete issue, and causing a bounded revision. Receive one final decision packet.

**Accept when:** logs demonstrate model-selected tool actions and evidence-driven revision; all agents use the correct scenario version; errors and budget exhaustion terminate clearly. Not every task must invoke every agent; recruitment runs only for a relevant authorized workflow.

### Journey G — Switch language and role

View the same scenario in Arabic and English, then sign in as a student and as a hiring manager.

**Accept when:** numerical facts remain identical, RTL is usable, and direct backend requests cannot expose another student's records or restricted recruitment documents.

## 6. Definition of reliable results

- Store time as integer minutes with explicit dates/day patterns and a configurable institution timezone.
- A meeting ending when another starts is not an overlap. Travel requirements, if configured, are checked separately.
- Calculate gaps only between consecutive meetings on the same teaching day. Invalid overlapping schedules receive diagnostics rather than misleading quality claims.
- Use identical populations and metric versions for comparisons.
- A changed-section limit counts unique sections, not individual meeting records.
- Validate results independently of the solver and agent explanations.
- Report solver status accurately; unknown is not infeasible, feasible is not necessarily optimal.
- Version scenario data, policy weights, approvals, candidate evidence, and scoring criteria.
- Default to no external data transmission for model inference.

## 7. Data and architecture decisions

Use React/TypeScript, FastAPI, SQLite, and OR-Tools. Use an explicit coordinator state machine with structured model tool calls and one shared local inference service. Choose exact package versions during installation against current official documentation.

Keep three independent scheduling fixtures: valid/inefficient, invalid/diagnostic, and staffing-shortfall. Start with hand-checkable small cases, then generate the larger target semester with fixed seeds. Approximate v3 counts must be internally consistent: total seats must support the generated enrollment load. Increase section counts or adjust loads if necessary rather than generating impossible data solely to match illustrative counts.

Public catalogs are optional enrichment, not a blocker. Record source and reuse conditions if used. Candidate examples are fictional and visibly labeled.

## 8. Phase gates and evidence

### Phase 1 — Product contract

Deliver scope, user journeys, hardware assessment, architectural direction, and acceptance criteria. **Current evidence:** these documents and read-only environment checks. User approval required before Phase 2.

### Phase 2 — Interface prototype

Deliver navigable bilingual screens, representative empty/error/loading states, and the primary journeys with labeled sample data. Check navigation and layouts. Do not claim functioning optimization or agents.

### Phase 3 — Data and simulation

Deliver persisted records, deterministic fixture generation, imports, metrics, prerequisite checking, and independent validation. Verify with hand-calculated cases and invalid-input tests.

### Phase 4 — Operational decisions

Deliver solver integration, placement, impacts, workforce diagnostics, approvals, and publication. Verify constraints, limits, statuses, rollback/atomicity, and stale-data handling.

### Phase 5 — Scheduling agents

Deliver the five scheduling roles, local inference, structured tools, bounded revision, and audit-visible outcomes. Test Arabic requests, tool selection, unsupported claims, malformed output, timeout, and injected instructions in source data. Benchmark actual memory and latency.

### Phase 6 — Recruitment

Deliver the sixth role, hiring-manager interaction, CV extraction/correction, criteria, candidate comparison, briefs, CV drafts, and interview/message drafts. Verify evidence tracking and missing-information handling. Show unavailable live sources honestly.

### Phase 7 — Complete application

Deliver connected role-aware journeys, meaningful regression tests, repeatable setup/start scripts, backups/recovery instructions, demo fixtures, and final documentation. Verify a clean local startup and persistence through restart. Record outstanding limitations rather than claiming untested integrations work.

## 9. Review process

At each phase, present the concrete artifact or running application, what was verified, and any remaining limits. Stop before the next phase until the user approves or provides corrections. User review time is outside implementation estimates.

The earlier 53–106 active-hour estimate is provisional and unmeasured. It is not a deadline or a requirement to consume that time. Report actual deliverables and revise remaining estimates from evidence; hardware/model testing and integration remain the main uncertainties.

## 10. Phase 1 approval question

Does this contract match the intended standalone MIZAN: all six agent roles, bilingual scheduling and workforce workflows, human-reviewed recruitment using sample/supplied CVs, and live integrations added when access exists?

Approval authorizes Phase 2 interface implementation. It does not imply approval of a visual design that has not yet been presented.
