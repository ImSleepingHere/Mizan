# Mizan: handover for the demo presenter

This guide is everything you need to install Mizan on your own PC and give the Farq demo.
Setup takes about 30–60 minutes, mostly downloading. Do it the day before, not an hour before.

## What you're presenting

Mizan checks a university timetable before it's published. It measures what the timetable costs students (for example, hours lost to gaps between classes), recommends changes, shows the evidence, and a person approves every change. It runs entirely on one PC: a local AI model, no cloud services. Initial demo data is synthetic. Edugate imports may contain real records and stay in the local database, outside Git.

- Demo script, 7 minutes, word for word: [`docs/demo-script.md`](demo-script.md)
- Proof that it works, if a judge asks: [`docs/acceptance-report.md`](acceptance-report.md)

## 1. What your PC needs

| Need | Why |
|---|---|
| Windows 10 or 11 | The launch scripts are Windows scripts |
| **NVIDIA GPU with 8 GB+ memory** (recommended) | Runs the local AI model. Without it the model falls back to the CPU and Ask Mizan, the agents and CV analysis become very slow |
| About 15 GB free disk | 5.2 GB model, 1.8 GB runtime, dependencies |
| Python 3.12 — https://www.python.org/downloads/ | Tick "Add python.exe to PATH" in the installer |
| Node.js 24 LTS — https://nodejs.org | Builds the website (includes `npx`; pnpm doesn't need installing) |
| Git (optional) — https://git-scm.com | Only if you clone instead of downloading the ZIP |
| Google Chrome or Microsoft Edge | To show the app |

Without an NVIDIA GPU you can still demo everything except Ask Mizan, "Start collaboration" and "Analyze evidence". The demo script marks those steps as optional.

## 2. Install (once)

**Get the code (ZIP):** on GitHub click **Code → Download ZIP**. Before extracting, right-click the ZIP → **Properties** → tick **Unblock** → OK, so Windows doesn't block the scripts. Extract it to a short path such as `C:\Mizan`, not a OneDrive or Desktop folder. Check that the folder contains `Check Mizan Setup.cmd` and `docs\HANDOVER.md`; if not, the ZIP is outdated, so download it again. (With Git you can use `git clone https://github.com/ImSleepingHere/Mizan.git` instead.)

Then open **PowerShell** in that folder (Shift + right-click inside the folder → *Open PowerShell window here*) and run these one at a time:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
.\.venv\Scripts\python.exe scripts\install_model_runtime.py
```

- `setup.ps1` installs Python and website dependencies and builds the site, in about 5–10 minutes.
- `install_model_runtime.py` downloads the local model runtime (about 1.5 GB) and the Qwen3-8B model (about 5.2 GB), and verifies their checksums. The fine-tuned coordinator adapter already comes with the code.

**Faster alternative:** if the project owner can give you a USB drive, copy their `.models\qwen3-8b.gguf` file and whole `.runtime` folder into your `Mizan` folder, and skip the download.

**Updating later:** a ZIP can't pull fixes. Download the new ZIP, extract it, and copy your old `.venv`, `.models`, `.runtime` and `data` folders into it (or run setup again).

## 3. Check it's ready

Double-click **`Check Mizan Setup.cmd`** in the Mizan folder. Required environment and website checks should say `[OK]`. Missing optional AI assets appear as warnings: deterministic scheduling and comparison still work. A `[MISS]` line tells you exactly what to run.

## 4. Before the demo (10 minutes)

1. Double-click **`Reset Mizan Demo.cmd`**. It gives you clean demo data and keeps a backup of the old data.
2. Double-click **`Start Mizan.cmd`** and keep that window open. If AI assets are installed, wait for the local model to load. Otherwise proceed with deterministic scheduling.
3. Open **http://127.0.0.1:8000** in Chrome at 100% zoom.
4. Log in: role **Administrator**; the password `Mizan-demo-2026!` is pre-filled.
5. In **Settings → Environment**, check that "Model service" shows *qwen3-8b · local* and "Coordinator agent" shows *Fine-tuned (LoRA)*.
6. Run through [`docs/demo-script.md`](demo-script.md) once. Then run **Reset** again so the real demo starts clean. Close the app window first, because Reset refuses to run while the app is open.

## 5. During the demo

Follow [`docs/demo-script.md`](demo-script.md). The essentials:

- The opening screen is meant to be **red**. The demo semester is deliberately inefficient: 15,000 student-hours a week lost to gaps.
- **Optimize semester** takes about 15 seconds; explain what it does while it runs. Results vary slightly between runs, so say "about 1,800 hours".
- Say "optimal **within the searched options**", never just "optimal". Always say "synthetic data".
- **Ask Mizan** is the weakest feature. Rehearse your exact sentence, or skip it. If it misreads, point out that it asked for confirmation and ran nothing.
- The **العربية** button (top right) switches everything to Arabic, right-to-left, with the same numbers.

## 6. If something goes wrong

| Problem | Fix |
|---|---|
| Page shows old or odd numbers | Switch the scenario in the top bar and back, or reload the page |
| "Model not running" / agents don't start | Skip the AI steps and continue, since everything else works. After the demo, run `Check Mizan Setup.cmd` |
| Start says Mizan is already running | It's fine. Open http://127.0.0.1:8000 |
| Reset says Mizan is still running | Close the Start Mizan window, then Reset |
| Anything else mid-demo | Close the app window → `Reset Mizan Demo.cmd` → `Start Mizan.cmd` (about 1 minute) |

## Accounts (all use `Mizan-demo-2026!`)

| Role | Shows |
|---|---|
| Administrator | Everything; use this for the demo |
| Scheduling committee (registrar) | Approve and publish |
| Department chair | Review and workforce evidence |
| Professor | "My classes", own-section requests (faculty-week scenario) |
| Hiring manager | Recruitment only |
| Student | Personal read-only timetable |

These are local demo accounts, not real university logins.


## Current release: comparison and setup

Use Python 3.12; setup chooses it with the Windows `py` launcher and pins pnpm 12.9.1. Go to Recommendations → Compare three plans. Generate at 5 seconds per plan, compare the priorities, expand class changes, choose a plan and follow the normal approval/publication flow. These steps work without a model. For the three-person five-minute pitch use [demo-five-minutes.md](demo-five-minutes.md), not the longer historical demo script. Current verification and limits: [release-verification.md](release-verification.md). Full documentation: [v6](MIZAN%20-%20Project%20Documentation%20v6.md).
