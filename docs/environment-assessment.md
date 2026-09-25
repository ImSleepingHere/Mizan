# Phase 1 environment assessment

Inspected 23 September 2026. Read-only inspection; no packages installed, models downloaded, or global configuration changed.

## Confirmed hardware

- CPU: AMD Ryzen 7 9800X3D; 16 logical processors reported.
- RAM: 31.11 GiB usable physical memory; approximately 19 GiB available during inspection.
- GPU: NVIDIA GeForce RTX 4080 SUPER.
- GPU memory: 16,376 MiB reported by nvidia-smi.
- NVIDIA driver: 596.49.
- C: free space: approximately 49.5 GiB at inspection.

Memory availability and disk space change during normal use. These are observations, not capacity reservations.

## Development environment

- Git is available at C:\Program Files\Git\cmd\git.exe.
- Bundled Python 3.12.14 and Node.js 24.19.0 execute successfully through the Codex runtime.
- Python, Node, npm, Ollama, and Docker were not found on the current process PATH. This does not prove that none are installed elsewhere.
- FastAPI, OR-Tools, pytest, and SQLAlchemy are absent from the inspected bundled Python environment. pypdf is present.
- Existing repository contains Git metadata, ignore/attribute configuration, and the v3 specification. Preserve these.
- Git's sandbox user differs from the repository owner. A command-scoped safe.directory setting allows inspection without changing global Git settings.
- Windows CIM hardware queries were denied. CPU registry data, the Windows memory API, and nvidia-smi supplied the hardware findings instead; the CPU registry query also emitted a conversion warning while returning the processor name.

## Implementation decisions

Use React with TypeScript for the frontend, FastAPI for the backend, SQLite for local persistence, and OR-Tools CP-SAT for optimization. Keep runtime files and model artifacts out of version control. Install project dependencies in isolated project environments, not into Codex's bundled Python.

Use one local inference service for all six logical agent roles, with sequential inference initially. The observed GPU is a promising candidate for a quantized model, but no model has been downloaded or benchmarked. Arabic quality, structured tool calls, context size, and latency remain unverified.

Select the actual model and serving runtime during Phase 5 after checking current official model/runtime documentation, licensing, download size, and a local benchmark. Do not claim six working AI agents until model-driven tool use and revision tests pass.

Reserve disk capacity for dependencies, datasets, and one candidate model before downloading. Do not download multiple large models speculatively. No hardware purchase is indicated by this initial assessment.

## Reproducibility target

The finished project must have pinned dependencies, documented runtime prerequisites, a repeatable setup script, and a Windows start command. Final operation must not depend on hard-coded private Codex runtime paths. Docker is optional, not a prerequisite.

## Remaining evidence needed

1. Frontend and backend dependency installation/build checks in their phases.
2. Solver correctness and runtime on the target synthetic dataset in Phases 3–4.
3. Local-model Arabic/tool-use evaluation and memory measurement in Phase 5.
4. Full cold-start and recovery testing in Phase 7.
