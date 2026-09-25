# Build 2 checkpoint — agents, recruitment, and visual refresh

Date: 23 September 2026. Status: ready for user review; final delivery phase has not started.

## What changed

The website now uses white and light-gray surfaces, charcoal typography, blue actions, and restrained status colors. English and Arabic layouts remain available.

Six logical agents share one local Qwen3 8B model. They are separately prompted roles, not six trained models. No model training or paid API account was needed. The Coordinator chooses among pending specialist reviews. Student Experience, Scheduling & Optimization, Change Impact, and Workforce Planning exchange calculated evidence through the coordinator. Their allowed tools are constrained by the workflow; algorithms compute schedules, capacity, and impacts. Required reviews and publication rules are enforced in code. This is bounded agent collaboration, not unrestricted autonomous agents.

The sixth role, Recruitment Assistant, analyzes supplied CVs and speaks with the hiring manager. It chooses available read tools during conversations and can draft interview questions or messages. Manager approval opens a hiring workspace from a current, proven staffing requisition. Requirements have explicit weights and versions. PDF, DOCX, and TXT sources can be uploaded, viewed, and corrected. Changes invalidate earlier comparisons. A quoted qualification must exist verbatim in the supplied text or it becomes unknown. Human review is still required to establish whether a quote actually satisfies a criterion. Candidate ordering represents weighted evidence coverage, not a probability of suitability or an automated hiring decision.

Candidate briefs include current evidence and a formatted CV preserving source wording. They open as printable HTML; the browser can save them as PDF. Candidate claims remain unverified. No messages are sent externally.

## Review this phase

1. Refresh http://127.0.0.1:8000 and inspect the new palette.
2. Sign in as admin and open Activity & evidence. Enter a scheduling request and start collaboration. Inspect agent actions, tool evidence, and the resulting recommendation. Publication remains a separate human action.
3. Choose the staffing-shortfall scenario, open Workforce, and prepare a requisition.
4. Open Recruitment, review the role and job-related requirements, then authorize recruitment.
5. Add a fictional demo CV or upload an authorized source. Analyze evidence, inspect the quotes, open the brief, and ask the recruiter a question in English or Arabic.
6. Sign in as hiring_manager to inspect the restricted recruitment workspace. This role cannot access student records or publish schedules.

The common demo password remains Mizan-demo-2026!.

## Verified

- 26 domain/API tests passed, including role isolation, stale criteria, stale staffing evidence, source-quote rejection, DOCX upload, file limits, HTML escaping, cancellation, and no automatic timetable publication.
- Frontend production build passed.
- Real local-model English collaboration completed in about 15 seconds in one measured run, with nine model calls and four tool calls. Its eight-second solver search recovered 1,800 aggregate student-hours per week in the fictional baseline, benefiting 225 students with zero worsened and zero hard violations. This is one measured result, not a guarantee or a global optimum.
- Real Arabic scheduling collaboration also completed in 15.34 seconds. GPU memory in use after testing was 10,872 MiB out of 16,376 MiB, including other processes.
- Real CV evidence analysis and Arabic recruiter conversation passed.
- Browser workflow completed an agent run, authorized recruitment, assessed a sample CV, and held recruiter chat with no browser errors. Arabic mobile layout had no horizontal overflow.
- UI screenshots and isolated test databases remain under work/. Tests did not publish into the user's main database.

## Operating boundaries

- Agents share local Qwen3 8B Q4_K_M inference via a loopback llama.cpp server, bundled with pinned Ollama 0.34.3. Runtime and model are installed within this repository. The daemon is not used and no global model directory is needed.
- Scheduling allows up to 24 model calls, 12 tool calls, 10 coordinator rounds, and a six-minute elapsed budget checked between actions. Individual model calls time out after 90 seconds; cancellation takes effect between actions. Only one scheduling run executes at a time. Interrupted runs are marked as such after restart.
- Solver limits and revision checks remain authoritative. A failed or rejected agent result cannot silently publish a timetable.
- CV size is limited to 5 MB, 30 PDF pages, and 24,000 extracted characters. Scanned-image OCR is not enabled. Paste verified text when extraction is unavailable.
- LinkedIn live browsing and external candidate search remain unavailable. Authorized exports or pasted profiles with source attribution are supported. No university database is required.
- AI interpretation and recruiter prose can be wrong. Exact quote matching proves source presence, not truth or job fit. Final review, interviews, identity verification, and hiring decisions remain human tasks.
- This is a single-PC demonstration using shared demo credentials. Institutional authentication, production deployment, and full operational hardening remain outside this checkpoint.

## Reproducibility

The runtime archive and GGUF have pinned SHA-256 digests in scripts/install_model_runtime.py. Fresh installation needs network access and roughly 6.7 GB of downloads plus extraction space. Start Mizan.cmd launches the application and installed model; scripts/start-model.ps1 can start the model separately. The current startup profile uses NVIDIA CUDA 12 and this PC's GPU.

Primary runtime/model references: https://github.com/ollama/ollama/releases/tag/v0.34.3 ; https://github.com/ggml-org/llama.cpp/tree/master/tools/server ; https://ollama.com/library/qwen3:8b .

After this review, the final phase covers integrated regression, recovery and backup instructions, startup/persistence verification, and handover polish.
