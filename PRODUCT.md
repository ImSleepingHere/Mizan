# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- **Primary audience for the current design pass: Farq hackathon judges** (university-operations track) watching a short live demo on a laptop or projector. They must grasp in seconds what Mizan measures, what it recommends, and that humans approve every change.
- Product users behind the demo: scheduling committee / registrar (run optimizations, approve and publish), department chair (review, workforce evidence), administrator (policy weights, data import), professors (ask for changes to their own sections, find common free slots), hiring managers (recruitment after a proven capacity shortfall), students (read-only personal week).

## Product Purpose
Mizan evaluates a university semester before publication. A timetable can satisfy every hard rule and still waste student hours in gaps, add campus days, and load faculty unevenly. Mizan measures those costs, searches for better valid timetables, checks proposed changes, separates scheduling problems from real staffing shortfalls, and prepares recruitment only when the shortfall is proven. Success: a reviewer sees the cost, a concrete recommended change, the evidence behind it, and approves or rejects it.

## Positioning
Deterministic tools decide feasibility (OR-Tools solver, independent validators); six local AI agents only coordinate and explain. Everything runs on one PC with a local Qwen3-8B model and a fine-tuned coordinator adapter, with no external AI APIs. Every change is a reviewable proposal with before/after metrics and an audit trail; nothing is published or hired without human approval.

## Operating Context
- Riyadh week: Sunday–Thursday, 08:00–18:00, Asia/Riyadh timezone.
- Roles: admin, registrar, chair, professor, hiring_manager, student. Demo password is shared and local.
- Scenarios: baseline, diagnostic (conflicts), shortfall (staffing), faculty (professor's own sections S087–S091).
- Core workflows: overview metrics → semester lab (interactive drag-and-drop timetable with live preview, Ask Mizan request interpreter, My classes, common free-slot finder) → recommendations (proposal review, approve, publish) → change requests → workforce evidence → recruitment → activity/audit and agent runs → settings (policy weights, import/export, model status).

## Capabilities and Constraints
- Hard constraints are enforced by code, never by the model. The quality score is withheld when a scenario is invalid.
- "Optimal" means optimal within the searched neighborhood; the UI must not overclaim.
- Professors never see student IDs (server-side redaction).
- React 19 + Vite 7 + TypeScript, served as a static build by FastAPI; fonts self-hosted via @fontsource (no CDN).
- Browser smoke test (`tests/browser-smoke.cjs`) relies on accessible names of buttons, headings, labels and a few class names (`.placement-option`, `.proposal-card`).

## Brand Commitments
- Name: MIZAN / ميزان ("balance, scale"). Arabic letter mark م.
- Full English and Arabic parity for every UI string (`t(en, ar)`), with correct RTL layout using logical CSS properties.
- Voice: calm, precise, evidence first. "Scheduling intelligence. Human decisions."

## Evidence on Hand
- Synthetic data only; must always be labelled as synthetic.
- Real measured results: fine-tuned coordinator 111/120 vs 75/120 pretrained on the deployed eval (`training/coordinator/deployed_eval_summary.json`); interpreter handwritten test 7/30 strict. Do not invent other benchmarks, customers or institutional adoption.

## Product Principles
1. Show the cost before the cure: metrics first, then recommendations.
2. Evidence beside every claim: before/after, validation status, rule checks.
3. The human decides: approve, reject, publish are always explicit actions.
4. Honest limits: synthetic data, bounded optimality, local prototype.
5. Bilingual by default: Arabic is a first-class reading direction, not a translation layer.

## Accessibility & Inclusion
- Keyboard-operable timetable (move form in the drawer), visible focus, reduced-motion respected, WCAG AA contrast for text.
