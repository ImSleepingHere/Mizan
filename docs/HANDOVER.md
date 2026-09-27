# Mizan: handover for the demo presenter

This guide is everything you need to install Mizan on your own PC and give the Farq demo.
Setup takes about 30–60 minutes, mostly downloading. Do it the day before, not an hour before.

## What you're presenting

Mizan checks a university timetable before it's published. It measures what the timetable costs students (for example, hours lost to gaps between classes), recommends changes, shows the evidence, and a person approves every change. It runs entirely on one PC: a local AI model, no cloud services. All data is synthetic.

- Demo script, 7 minutes, word for word: [`docs/demo-script.md`](demo-script.md)
- Slide deck: https://claude.ai/artifact/7HQp54eBHaf9ka8Qk975uW (the project owner must share it with you; it downloads as PowerPoint or PDF)
- Proof that it works, if a judge asks: [`docs/acceptance-report.md`](acceptance-report.md)

## 1. What your PC needs

| Need | Why |
|---|---|
| Windows 10 or 11 | The launch scripts are Windows scripts |
| **NVIDIA GPU with 8 GB+ memory** (recommended) | Runs the local AI model. Without it the model falls back to the CPU and Ask Mizan, the agents and CV analysis become very slow |
| About 15 GB free disk | 5.2 GB model, 1.8 GB runtime, dependencies |
| Python 3.12 — https://www.python.org/downloads/ | Tick "Add python.exe to PATH" in the installer |
| Node.js 24 LTS — https://nodejs.org | Builds the website (includes `npx`; pnpm doesn't need installing) |
| Git — https://git-scm.com | To get the code |
| Google Chrome or Microsoft Edge | To show the app |

Without an NVIDIA GPU you can still demo everything except Ask Mizan, "Start collaboration" and "Analyze evidence". The demo script marks those steps as optional.

## 2. Install (once)

Open **PowerShell** and run these one at a time:

```powershell
git clone https://github.com/ImSleepingHere/Mizan.git
cd Mizan
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
.\.venv\Scripts\python.exe scripts\install_model_runtime.py
```

- `setup.ps1` installs Python and website dependencies and builds the site, in about 5–10 minutes.
- `install_model_runtime.py` downloads the local model runtime (about 1.5 GB) and the Qwen3-8B model (about 5.2 GB), and verifies their checksums. The fine-tuned coordinator adapter already comes with the code.

**Faster alternative:** if the project owner can give you a USB drive, copy their `.models\qwen3-8b.gguf` file and whole `.runtime` folder into your `Mizan` folder, and skip the download.

You need a GitHub invitation to the repository if it's private. Ask the project owner.

## 3. Check it's ready

Double-click **`Check Mizan Setup.cmd`** in the Mizan folder. Every line should say `[OK]` and end with "Ready". A `[MISS]` line tells you exactly what to run.

## 4. Before the demo (10 minutes)

1. Double-click **`Reset Mizan Demo.cmd`**. It gives you clean demo data and keeps a backup of the old data.
2. Double-click **`Start Mizan.cmd`** and keep that window open. Wait about 1 minute for the AI model to load.
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
