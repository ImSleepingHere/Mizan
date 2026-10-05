# Compare three timetable plans

Added 4 October 2026. This feature uses deterministic scheduling tools and works without the local AI model.

## Use it

1. Sign in as **Administrator** or **Scheduling committee**.
2. Open **Recommendations → Compare three plans**. You can also reach it through **Optimize semester → Compare three plans**.
3. Set maximum changed sections and the search budget **per plan**, then choose **Generate three plans**. Defaults: five changed sections and 15 seconds per plan (up to 45 seconds of solver time plus model construction and validation).
4. Compare the current timetable with all three plans. Scroll inside the table on a phone.
5. Choose **Review this plan**. This creates a normal proposal; the timetable has not changed.
6. Review benefits, harms and classes moved, then **Approve proposal → Revalidate & publish locally**.

Chairs can read saved comparisons. Students, professors and hiring managers cannot access whole-semester comparisons. The latest comparison survives reload and language switching. Publishing or updating policy makes comparisons from an earlier timetable version outdated; they cannot be selected.

## What the three priorities actually do

| Plan | Objective |
|---|---|
| Most time saved | Minimize all students' weekly gap minutes, then campus days, then changed sections. |
| Fewest changes | Minimize changed sections while recovering at least 1% of the starting timetable's gap minutes (rounded up, minimum one minute); total gaps break ties. |
| Balanced impact | Minimize the worst-off 10%'s total gap minutes first. Secondary cost is the sum of squared individual gap minutes, plus a smaller total-gap cost and disruption cost. Squared gaps favor spreading relief among students with long waits. |

The profiles use fixed comparison priorities; they do not change saved policy weights. All use the existing bounded candidate neighborhood, instructor assignments, hard constraints, maximum change count, and independent validator.

Every alternative must be a genuine aggregate gap reduction. The baseline is not presented as an improvement. A zero-gap timetable or zero-change budget may have no alternative. The balanced strategy optimizes student waiting burden; it is not a guarantee of demographic fairness or zero individual harm.

**Honest outcomes:** OPTIMAL means best within searched options. FEASIBLE is a valid time-limited result, with no optimality promise. UNKNOWN/INFEASIBLE do not produce a selectable plan. Two priorities may produce the same timetable: the screen states this and selection shares one proposal. It never fabricates three distinct alternatives.

**Imported timetables:** comparison checks the available data and assumptions. The existing verified-room/instructor publication guard remains active. The separate review's existing imported-instructor identity and other pre-existing defects are not fixed by this feature.

## A short hackathon demonstration

Start from a freshly reset synthetic baseline. Choose five changed sections and five search seconds per plan. Fresh browser execution on this review PC produced:

| Plan | Weekly hours recovered | Sections moved | Students benefiting | Students worse off |
|---|---:|---:|---:|---:|
| Most time saved | 1,800 | 5 | 225 | 0 |
| Fewest changes | 300 | 1 | 75 | 0 |
| Balanced impact | 1,500 | 5 | 375 | 0 |

These are measurements on the deliberately poor synthetic semester, not guaranteed results on another machine or real campus. The worst-decile average stayed at ten hours in all three because the five-change budget cannot improve every burdened group. The balanced plan still spreads relief more widely. Do not claim that it reduced that displayed worst-decile figure in this run.

Suggested line: “Which matters more to your committee: the most hours recovered, the fewest classes moved, or helping more students? Mizan shows the trade-offs; you choose.” Select Fewest changes to demonstrate one small, validated change and its approval flow.

## Storage and API

- `POST /api/scenarios/{sid}/plan-comparisons`: `{revision, max_changes, seconds}`. Admin/registrar only. Stores comparison snapshots; creates no proposal.
- `GET /api/scenarios/{sid}/plan-comparisons`: latest saved comparison, with staleness, metrics and changes. Staff only; candidate payloads are withheld.
- `POST /api/plan-comparisons/{id}/{key}/select`: keys `time_saved`, `fewest_changes`, `balanced`. Admin/registrar only. Rechecks version and validation inside an SQLite write transaction; repeated selection is idempotent while its proposal is recommended/approved.
- New `plan_comparisons` table is created automatically on normal application startup. Existing databases are preserved; no reset is required to install this feature.

## Verification

Fresh suite: **118 tests passed**, including 19 new comparison cases. The frozen interpreter-checksum test and evaluator now hash canonical LF newlines; the benchmark cases and saved AI evaluations are unchanged.

`tests/browser-plans.cjs` checks real solver strategies, read-only generation, displayed figures, English/Arabic parity, desktop fit, mobile internal scrolling, selection, approval/publication, and outdated comparisons. It creates/publishes fictional proposals: run only against a separate test database.

The original core browser suite and fictional Edugate PDF suite are rerun for regression. Live AI tests require the omitted base model/runtime and were not rerun for this deterministic feature.
