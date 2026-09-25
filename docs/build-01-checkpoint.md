# Build 1 — Working scheduling application

**23 September 2026 · ready for user review**

The user approved consolidating delivery into three phases. This is the first build checkpoint, covering the interface, local data, simulation, scheduling decisions, and staffing analysis. The preliminary product-definition exercise is complete and is not counted as another remaining gate.

## What runs

- English and Arabic RTL interfaces, with locally served fonts and a responsive layout.
- Administrator, scheduling committee, department chair, professor, and student demo accounts with backend role checks.
- Persisted synthetic scenarios with 1,500 students, 80 courses, 100 sections, 40 rooms, and 50 professors.
- Gap hours, long-gap counts, campus days, span, quality score, cohort analysis, faculty load, and room utilization.
- Independent checks for student/faculty/room overlaps, capacity, availability, room type, competency, prerequisites, meeting duration/patterns, blocked periods, and contracted teaching hours.
- CP-SAT optimization with a change limit and time limit, followed by independent result validation.
- Reviewable proposed moves and before/after metrics, including adverse student effects.
- Section placement with compatible student counts, seat limits, resources, and gap/day effects.
- Change requests with conflict detection and feasible alternatives.
- Approval, rejection, and atomic local publication; stale proposals cannot publish.
- Workforce capacity diagnostics, separately examined internal-coverage options, and draft staffing requisitions.
- JSON import/export, inspectable semester records, versioned policy weights, and audit history.
- A student-only timetable and eligible section view.

## Review in five steps

1. Open `http://127.0.0.1:8000` and enter the Administrator demo workspace. The local password is prefilled. Switch between English and Arabic.
2. Inspect the baseline overview, then open Semester lab. Review the timetable, list, and underlying course/student/faculty/room records.
3. Run Optimize semester with at most five changes and a 15-second solver budget. Inspect the verified proposal, before/after metrics, changed meetings, and affected students. Approve and publish only if you want to change the local scenario.
4. Submit a change for S001's Sunday meeting to 10:00 on the original baseline. It conflicts with S002. Review the findings and propose one of the independently validated alternatives. If you have already published an optimization, the original conflict example may change; inspect the current timetable first.
5. Select Staffing shortfall, open Workforce, and prepare the draft requisition. Recruitment shows the saved draft and explicitly identifies the candidate workflow as the next phase.

You can also sign out and use the Student account to inspect the restricted view. The test suite checks server-side restrictions, not only hidden navigation.

## Evidence collected

- **19 domain/API tests pass.** They cover hand-computed metrics, boundary times, prerequisite/availability failures, malformed references and cycles, invalid fixtures, change limits, capacity evidence, placement, approval/publication, stale policies, import/export, role restrictions, and request guards. Two upstream test-client deprecation warnings remain; no test failures remain.
- Browser checks exercise English/Arabic rendering, timetable navigation, placement through publication, conflicting moves and alternatives, requisition creation, full-scale optimization, mobile overflow, and student authorization.
- The browser run recorded no JavaScript page errors and no external runtime requests.
- The production frontend passes TypeScript checking and builds successfully.
- A separate server restart check preserved the published test scenario at revision 2, its 101 sections, and its publication record. The main review workspace remains on its untouched baseline, separate from these tests.

An observed full-scale synthetic run recovered **1,800 student-hours per week**, benefiting **225 students**, with **zero students worsened on gaps or campus days** and **zero hard violations**. This is a measured fixture result, not a university outcome or a promise that every run will return the same moves. Time-limited parallel solver outcomes can vary.

See the test output and screenshots under `work/browser/` for local evidence. Generated test data is separate from the main `data/mizan.sqlite3` workspace.

## Explicit limits at this checkpoint

- The solver searches a bounded neighborhood: approved starts on the existing days/room plus a small selection of alternate room/day patterns. Meeting spacing and faculty assignments are preserved. `OPTIMAL` applies only to that searched neighborhood, not every theoretically possible university timetable.
- Faculty-load balance and total room utilization are constant during the current scheduling search because instructor assignments and instructional minutes are fixed. The UI explains these inactive objective terms. Workforce analysis can separately identify internal coverage options, but does not jointly optimize an institution-wide faculty reassignment plan.
- The representative week uses configured teaching windows and blocked periods. Date-specific holiday recurrence and a calendar editor are not implemented; special windows can be represented in imported scenarios. This is a representative-week scheduling engine, not a date-by-date academic calendar engine.
- Fixtures deliberately simplify enrollment patterns to make results reproducible and inspectable. No public university catalog or actual university records have been imported.
- A staffing capacity bound can prove insufficient qualified contracted hours. Sufficient hours alone do not prove that a conflict-free staffing timetable exists. The application states that distinction.
- New section proposals do not automatically enroll students. Compatibility and seat counts are distinct.
- Demo identities share a configurable local password. This is not a production identity system and the server is bound to loopback.
- AI inference, the five scheduling agents, the Recruitment Assistant, CV extraction, candidate rankings, and external sourcing are not connected yet. Their places in the UI are labeled accordingly. No simulated agent conversations are presented as real execution.

## Review gate

Confirm whether the running workflows and visual direction align with your vision, or request revisions. Build 2 begins after approval and adds the six agents and recruitment workflow. Build 3 handles final integration hardening and delivery.
