# MIZAN — evidence behind the pitch numbers

Checked 4 October 2026. Rule for the deck: a number is either **measured in Mizan on the synthetic demo semester** (say so on the slide) or **from a cited source** below. Nothing else.

## 1. Our own figures (synthetic, measured by the app)

| Figure | Where it comes from | How to say it |
|---|---|---|
| 15,000 gap hours / week | Built into the baseline generator (`backend/fixtures.py`): every cohort has 1-hour classes at 08, 10, 13, 15, 17 on two days → 5 h gaps/day → 10 h/week × 1,500 students. A deliberately poor starting timetable, not a real-world measurement. | "In our demo semester of 1,500 synthetic students, the starting timetable wastes 10 hours per student per week." |
| 100% of students with a 2 h+ gap | Same construction (10:00→13:00 gap for everyone). | Only as a demo figure. |
| 10% room use | 20 of 40 rooms used 10 of 50 weekly hours. Constructed, like the gaps; any resemblance to real figures (§2.4) is a coincidence, not validation. | Only as a demo figure: "In the demo campus, rooms are used 10% of the time." Quote the UK research separately, never as a comparison. |
| ≈ +1,800 h recovered, 0 students worse off (15 s run) | Measured by the solver, independently validated (`docs/demo-script.md`). About 12% of the demo gap hours. Mechanical too: cohorts are identical, so one moved 17:00 section closes gaps for all 75 students of a group (≈ 225 students × 8 h). It shows the method, not real-world performance. | "Mizan recovered ~1,800 student-hours a week in 15 seconds, and nobody's week got worse." |

## 2. Published research

### 2.1 Saudi Arabia — timetable design drives absences (strongest, local)
Larabi-Marie-Sainte, Jan, Al-Matouq, Alabduhadi (2021). *The impact of timetable on student's absences and performance.* PLoS ONE 16(6): e0253256. https://pmc.ncbi.nlm.nih.gov/articles/PMC8232426/
- Prince Sultan University, Riyadh; 4,325 students (Engineering 2,661, Computer Science 1,664), 2016/17–2018/19.
- Three timetable factors explain absences: courses per semester, lectures per day, **free timeslots (breaks) per day**. Absences predicted with 87% accuracy from these factors.
- When breaks per day grow large, absences rise (correlation 0.37 and 0.40). The relationship is non-linear: both overloaded and near-empty days hurt.
- Absences vs GPA: r = −0.71 (GPA ≈ 3.89 − 0.063 × absences).
- Authors recommend **automated timetabling** to produce balanced timetables and minimise predicted absences.

### 2.2 UK — causal evidence from quasi-random timetables
Delavande, Del Bono, Holford, Williams (2025). *Timetables, Attendance and Academic Achievement in Higher Education.* IZA Discussion Paper 17979. https://docs.iza.org/dp17979.pdf
- 307,488 student-events, 170 modules; students assigned to class slots quasi-randomly.
- Back-to-back classes **raise** attendance by 1.5 percentage points; a day with a single class **lowers** it by 0.9 pp (mean attendance 65%).
- Honest caveat: net effect on grades was small. **Do not claim Mizan raises GPA.** Claim attendance and student time.
- Recommendation: avoid one-event days; schedule short back-to-back sequences, then a break.

### 2.3 UK — students' "gap tolerance"
Kirby-Hawkins, H. *What time is good for you?* SRHE conference paper (University of Hull pilot, 2017). https://srhe.ac.uk/arc/18/0621.pdf
- 40% of respondents said a gap of just 1 hour may change their attendance; only 3% would tolerate 4 h+.
- Small sample (37 of 176 students) — use as a supporting quote, not a headline number.

### 2.4 Room utilisation
- Smart Space Forum with SmartViz, 30+ UK institutions, reported in Times Higher Education (23 July 2026): teaching spaces used about **20%** of the time on average; some buildings about 10%. https://www.timeshighereducation.com/node/744086
- Saudi Arabia: Alghamdi, N. (2018). *Space, Like Time, Is Money: Evaluating Space Utilisation in Saudi Arabian Universities.* Springer, pp. 3–40, DOI 10.1007/978-3-319-76885-4_1. Five college buildings in five universities; "almost all spaces … were not utilised as they should be." (No percentage available in the abstract.)

### 2.5 Automated timetabling works at scale
- UniTime at Purdue (39,000 students, ~9,000 classes, 570 rooms) has been used university-wide since 2007. https://help.unitime.org/student-scheduling — proof that solver-based timetabling is used in practice; Mizan's difference is human-approved changes, professor requests in Arabic/English, and fully local AI.

### 2.6 Our fine-tuned coordinator (measured, synthetic benchmark)
- `training/coordinator/deployed_ablation.md`: base + original prompt 75/120 → base + training prompt 96/120 → fine-tuned 106/120 (fine-tuning alone: 14 fixed / 4 broken, p ≈ 0.03). Same generator as the training data.
- Say: "a better prompt did most of the work; fine-tuning added about 10 correct decisions out of 120". Do not use the older "111 vs 75" (it changed prompt and adapter together).

## 3. Not to use
- "Registrars spend 4–8 weeks per timetable" and "12–18% of students hit a conflict in week one": from a vendor marketing page (OpenEduCat), no study behind them.
- Any claim that fewer gaps raise grades: the UK causal study found little effect on attainment; the Saudi link is correlational.
