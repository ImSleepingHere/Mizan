# Mizan: university scheduling applications research

Research date: 5 October 2026 (Asia/Riyadh)

## Purpose and instructions for the receiving AI

This brief summarizes web research performed in this conversation. Use it to assess Mizan's competitors and positioning. Preserve the distinction between a university's official deployment, a product supporting that university's students, and a vendor advertising a capability. Do not treat absent public evidence as proof that a product or feature does not exist. Recheck sources before making procurement decisions or public claims. This was a targeted search, not an exhaustive market survey or a hands-on product evaluation.

## Mizan reference scope

The local source was `docs/MIZAN - Project Documentation v6.md`, dated 5 October 2026. Mizan checks university timetables, measures student waiting time and campus days, recommends improvements, independently validates proposals, previews changes, and requires human approval and publication. It compares three plans: most time saved, fewest changes, and balanced impact. It also analyzes teaching coverage and prepares recruitment from evidenced shortages. It supports English and Arabic, local execution, and Edugate schedule imports/exports.

The release is a local hackathon demonstration, not a confirmed institutional deployment. University authentication and richer institutional data remain separate work. Ordinary optimization does not guarantee zero individual harm. No software tests or historical AI benchmarks were rerun for this research.

## International university examples

### Purdue University, USA - UniTime

Official university evidence confirms UniTime use. Purdue describes instructor, course and program preferences, student conflict reduction using prior-term joint enrollment patterns, and room scheduling. Changes to official course times or locations require authorization. UniTime documentation describes optimization balancing student conflicts with faculty time, room preferences and other class relationships, plus demand-based student scheduling. This is the closest technical comparison identified in the search; that ranking is an assessment, not a benchmark.

Sources: [Purdue academic scheduling](https://purdue.edu/registrar/faculty-staff/scheduling/academic/); [Purdue UniTime knowledge base](https://service.purdue.edu/TDClient/32/Purdue/KB/Category/26/Unitime); [UniTime course timetabling](https://help-unitime.unitime.org/uct_courses.php); [UniTime student scheduling](https://www.unitime.org/uct_students.php).

### Monash University, Australia - Syllabus Plus, Allocate+ and MUTTS

Monash's official timetable systems page lists these three systems as maintained and run by its timetable systems group. This confirms named systems in university documentation. It does not establish the exact current modules, configuration or optimization objectives; the page's maintenance date was not established.

Source: [Monash timetable systems](https://adm.monash.edu/timetable/).

### University of Southampton, UK - Scientia Syllabus Plus

The university's curriculum and timetabling team explicitly states that it maintains the Syllabus Plus timetabling database and links to Banner and Kx. Its remit includes teaching and examination timetables and room bookings. The source does not demonstrate Mizan-style individual student harm reporting.

Source: [Southampton curriculum and timetabling](https://www.southampton.ac.uk/studentadmin/about-saa/registry-faculty/curriculum-timetabling.page).

### Universite libre de Bruxelles (ULB), Belgium - TimeEdit

University guidance identifies TimeEdit Viewer. A vendor case study, dated 14 November 2023, describes implementation beginning in February 2021, scheduling, room allocation, publication and handling changes. University evidence confirms the timetable service; implementation outcomes are vendor-reported. Do not infer adoption of every TimeEdit module.

Sources: [ULB timetable guidance](https://www.ulb.be/fr/horaires/sacha); [TimeEdit news and ULB case study](https://www.academy.timeedit.com/news). The vendor link is an aggregate news page and may change.

### University of Huddersfield, UK - Scientia

Official timetabling policy and accessibility documentation identify Scientia and describe responsibilities for central and school timetabling teams. Exact deployed optimization objectives were not established.

Sources: [Timetabling and room booking policy](https://www.hud.ac.uk/media/policydocuments/Timetabling-and-Room-Booking-Policy.pdf); [Scientia accessibility statement](https://students.hud.ac.uk/media/universityofhuddersfield/studentsx27website/hudstudy/DAS-213-TimetablingScientia.pdf).

### Tilburg University, Netherlands - TimeEdit Viewer

Official student instructions explicitly identify TimeEdit Viewer for program and personal schedules. This confirms viewing functionality, not university-wide optimization or the full TimeEdit suite.

Source: [Tilburg schedule instructions](https://www.tilburguniversity.edu/students/administration/registration/education/time-edit-viewer).

## Saudi findings

### Trtebh (Tarteeba) - a tool serving Saudi university students

The product website describes generating possible schedules from selected courses, filtering by preferred attendance times and days off, and supporting Imam Mohammad Ibn Saud Islamic University, King Saud University and Princess Nourah University. The site credits its creators and is focused on Saudi universities. This supports describing it as a local student scheduling example, but a Saudi registered company or legal ownership was not verified.

Adoption status: product support for these universities is confirmed by the vendor; official university procurement, endorsement or registrar use was not found. Student usage volume was not independently verified. It helps select among existing class options; the reviewed page does not establish that it changes institutional meeting times, instructor assignments or room allocations.

Source: [Trtebh product website](https://trtebh.com/).

### King Saud University - e-Register and EduGate

KSU's official systems department page, last updated 29 June 2026, confirms operating e-Register and EduGate. It describes timetable preparation, timetable modification request periods, early automatic student registration, and trial registration assuming student success to check that course sections meet registration demand. This is strong evidence of actual university use and meaningful overlap with scheduling and capacity planning.

Limits: the source does not prove that the underlying software is Saudi-developed, that it minimizes student gaps, or that it offers Mizan's three-plan comparison, independent validation or recruitment workflow. Do not equate trial registration with proof of an optimization engine.

Source: [KSU systems and electronic services department](https://dar.ksu.edu.sa/ar/edugate-dep).

### Al Yamamah University - EduGate

The official registration page links an EduGate portal and describes registration and schedule modification services. This confirms an official academic portal, but does not establish automatic institutional timetable optimization or Saudi product origin.

Source: [Al Yamamah registration](https://yu.edu.sa/registration/).

### EduX - Saudi vendor, university adoption unverified

The vendor identifies itself as a Saudi software company for schools and nurseries and advertises automatic timetable generation. No university deployment was verified in this search. Treat the scheduling capability as a vendor claim, not a tested result or a confirmed university implementation.

Source: [EduX vendor website](https://dc-edux.com/).

## Assessment and defensible positioning

Established products substantially overlap with Mizan's scheduling functions. Avoid claims that conventional systems only detect clashes: UniTime explicitly documents optimization, demand-based scheduling, faculty preferences and room preferences. Human authorization is also not unique to Mizan, as Purdue's policy illustrates.

Mizan can be positioned around its particular combination of measured student waiting-time costs, explicit benefit/harm disclosure, three-plan comparison, deterministic validation, English/Arabic interface, local operation, Edugate exchange and shortage-to-recruitment workflow. These are verified from Mizan's specification, not proven exclusive to Mizan. The reviewed competitor sources did not establish an exact full-workflow equivalent.

Suggested wording: "Universities already use scheduling systems such as UniTime, Scientia and TimeEdit. Mizan focuses on making the student cost of timetable changes visible and supporting evidence-based scheduling and staffing decisions."

Saudi conclusion: official use of related academic systems is confirmed at KSU and Al Yamamah. A locally focused student scheduling tool is documented through Trtebh. A Saudi-developed product officially deployed at a university and matching Mizan's full workflow was not verified. This is an evidence gap, not proof of absence.

## Questions for further research

- Who develops and owns the specific EduGate/e-Register implementations at KSU and Al Yamamah?
- Which university offices officially deploy automated timetable optimization, and which products/modules do they use?
- Do those implementations measure gaps, campus days, individual harm and worst-off cohorts?
- Are Trtebh's university relationships official partnerships or independent support for published course data?
- Can product documentation or institutional procurement records establish Saudi-developed alternatives and actual deployment dates?

No university staff or vendors were contacted. No authenticated systems were inspected. No competitor performance, cost, security or deployment benchmark was performed.
