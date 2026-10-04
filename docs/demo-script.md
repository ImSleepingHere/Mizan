# MIZAN — Farq demo script (about 7 minutes)

Three scenarios from spec §15. Every number below was measured on a freshly reset database on 27 September 2026. Optimizer figures come from a 15-second, time-limited search and can differ slightly between runs, so say "about".

## Before you start (10 minutes)

1. Close Mizan if it is running, then double-click **`Reset Mizan Demo.cmd`**. It backs up the current database to `data\backups\` and creates a clean one: four scenarios, no proposals, and an empty audit trail.
2. Double-click **`Start Mizan.cmd`** and wait about a minute for the local model.
3. Open http://127.0.0.1:8000 at 100% zoom and about 1440 px wide.
4. Check **Settings → Environment**: "Model service: qwen3-8b · local" and "Coordinator agent: Fine-tuned (LoRA)".
5. Rehearse the Ask Mizan sentence once (step 2c). If it misreads, skip that step in the live demo.

Demo password: `Mizan-demo-2026!` (already filled in).

## 0 · Opening (30 s)

Log in as **Administrator**.

> "Mizan checks a university timetable before it's published. It measures what the timetable costs students, recommends changes, shows the evidence, and a person approves every change. Everything runs on this laptop. There's no cloud AI, and the data is synthetic, as labelled at the top."

## 1 · Semester improvement (2–3 min), *Baseline semester*

1. **Overview.** Point to the red numbers:
   - **15,000 student-hours a week** lost to gaps, which is 10 hours per student (*Critical*).
   - **Quality 45/100.**
   - **1,500 students (100%)** with a gap of 2 hours or more.
   - **10%** room use.

   > "This timetable is valid: every hard rule passes, as the green bar says. But it's expensive for students."
2. Point to the cohort bars. Every cohort is at 10 h on the hour scale, against the green target line at 0.75 h.
3. Click **Optimize semester** → **Run optimization** (5 sections, 15 s). While it runs:

   > "The solver searches valid alternatives, and every result is re-checked by an independent validator."
4. The proposal opens with the **Preview → Propose → Approve → Publish** strip. Measured on a fresh database:
   - **about 1,800 student-hours a week recovered**
   - **225 students better off**, **0 worse off**, **0 conflicts**
   - Before → after: gap hours 15,000 → 13,200; quality 45 → about 50; 2h+ gaps 1,500 → about 1,275–1,350

   These values turn green.
5. Scroll to **Proposed changes**. Example: **S040 moves from Monday/Wednesday 17:00 to 11:00**.
6. Click **Approve proposal**. The dialog stays open ("Approved · not yet published"); click **Revalidate & publish locally**.

   > "The person decides. Publishing re-checks everything first."
7. Optional, needs the model (about 1–2 min): open **Activity & evidence** → **Start collaboration**. The six agents run with the fine-tuned coordinator (LoRA badge). Impact review can send scheduling back for a revision, and nothing is published by the agents.

## 2 · Mid-semester adaptation (1.5 min)

1. Open **Change requests**. The form starts at **S001, Sunday 08:00**; set **New start time** to **10:00**, type a reason, for example "Professor unavailable", and click **Preview impact**. Previewing saves nothing.
2. It shows **77 new conflicts**, grouped in plain language ("S001 and S0xx meet at the same time. N students are enrolled in both"), each with **Show on timetable**.

   > "Mizan shows exactly why it can't happen."
3. Under **Feasible alternatives** there are 3 valid options. Click **Propose this** on the first, then **Approve proposal**.
4. Optional: in **Semester lab**, drag a class in the weekly timetable. The ghost turns green or red live before you submit.
5. Optional: in **Ask Mizan**, type your rehearsed sentence (Arabic works too). Click **Draft interpretation**: it drafts what it thinks you mean for you to check and correct, and nothing runs until you confirm. Don't say it "understands" (7/30 fully correct on our handwritten test).

## 3 · Capacity shortage → recruitment (1.5 min)

1. In the top bar, switch the scenario to **Staffing shortfall**, then open **Workforce**.
2. It shows a **Verified capacity shortfall** in Machine Learning (course C080):
   - 3 sections needed, 2 covered
   - **1 uncovered** and **36 students without a seat** (red), out of **112 who need the course**
   - an evidence box explaining the finding

   > "This is a proven shortage, not just an arrangement problem the solver couldn't fix."
3. Click **Prepare requisition**. Open **Recruitment**, then **Authorize recruitment**, which is the hiring-manager approval.
4. Click **Add fictional demo CV** → **Analyze evidence**. Each criterion shows *supported* with a verbatim quote, or *unknown*.

   > "Every claim traces to the CV text. Unknown means follow up. It's not a hiring decision."
5. Optional: ask the recruitment agent for "two interview questions grounded in the requirements".

## 4 · Close (30 s)

- Press **العربية**. Every screen switches to Arabic, right-to-left, with the same figures (a test checks this).

  > "Measure the cost, recommend a change, show the evidence. A person approves."
- If asked about the AI: "On a synthetic benchmark of 120 coordinator decisions (generated like the training data), a better prompt took the base model from 75 to 96 correct, and fine-tuning added about 10 more (106; 14 fixed, 4 broken, p ≈ 0.03), mainly on finishing changed timetables and resisting injected instructions. The model never decides a hard rule or the final outcome; code does."
- If asked whether the numbers are real: "The demo semester is synthetic and its starting timetable is deliberately poor: every cohort waits 10 hours a week by construction, so the optimizer's first moves are obvious ones. The point is not the size of the number; it is that every change is checked by an independent validator and approved by a person."

## Say / don't say

- Say "optimal within the searched options", never simply "optimal".
- Say "synthetic data" and "local prototype". Don't claim any university uses it.
- If Ask Mizan misreads a request, point out that it asked for confirmation and ran nothing. That's the safety design.

## If something goes wrong

- A page looks stale: switch the scenario back and forth, or reload.
- Agents or recruitment show "model not running": skip step 1.7 and the evidence analysis, and continue. Everything else works without the model.
- To start over: close the app window, run `Reset Mizan Demo.cmd`, then `Start Mizan.cmd`.
