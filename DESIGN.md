---
name: MIZAN
description: "Scheduling intelligence. Human decisions. Campus Experience: warm campus imagery around precise scheduling evidence."
colors:
  paper: "#eee8de"
  surface: "#fffcf7"
  sunk: "#f3ecdf"
  ink: "#172126"
  ink-2: "#303533"
  text: "#252923"
  muted: "#68645b"
  faint: "#807b70"
  line: "#e3dbcf"
  line-2: "#cfc3b3"
  signal-blue: "#4b6c9f"
  signal-blue-ink: "#315583"
  signal-blue-bg: "#e6edf7"
  signal-green: "#529573"
  signal-green-ink: "#286646"
  signal-green-bg: "#e5f0e5"
  signal-orange: "#eaaa62"
  signal-orange-ink: "#925018"
  signal-orange-bg: "#fff0da"
  signal-red: "#b95042"
  signal-red-ink: "#9a342c"
  signal-red-bg: "#fae5de"
  fallback-teal: "#0a8f9e"
  fallback-magenta: "#b8398c"
  rail: "#111c21"
  action: "#f4a252"
  action-ink: "#332619"
typography:
  display:
    fontFamily: "'Archivo Variable', 'Noto Kufi Arabic', system-ui, sans-serif"
    fontSize: "66px"
    fontWeight: 450
    lineHeight: 1
    letterSpacing: "-0.025em"
    fontFeature: "tnum"
  headline:
    fontFamily: "Georgia, 'Noto Kufi Arabic', serif"
    fontSize: "30px"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  metric:
    fontFamily: "'Archivo Variable', 'Noto Kufi Arabic', system-ui, sans-serif"
    fontSize: "32px"
    fontWeight: 350
    lineHeight: 1.1
    letterSpacing: "-0.02em"
    fontFeature: "tnum"
  title:
    fontFamily: "'Archivo Variable', 'Noto Kufi Arabic', system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "'Archivo Variable', 'Noto Kufi Arabic', system-ui, sans-serif"
    fontSize: "13.5px"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "'Archivo Variable', 'Noto Kufi Arabic', system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 600
    lineHeight: 1.3
  micro:
    fontFamily: "'Archivo Variable', 'Noto Kufi Arabic', system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 500
    lineHeight: 1.3
rounded:
  none: "0px"
  field: "6px"
  small: "5px"
  card: "9px"
  modal: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  2xl: "24px"
  3xl: "40px"
components:
  button-primary:
    backgroundColor: "{colors.action}"
    textColor: "{colors.action-ink}"
    rounded: "{rounded.field}"
    padding: "10px 16px"
    height: "40px"
    typography: "{typography.label}"
  button-primary-hover:
    backgroundColor: "#ffb96f"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.field}"
    padding: "10px 16px"
    height: "40px"
  button-text:
    textColor: "{colors.signal-orange-ink}"
    typography: "{typography.label}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.field}"
    padding: "8px 11px"
    height: "38px"
  nav-item:
    backgroundColor: "{colors.rail}"
    textColor: "#d6dfe0"
    padding: "9px 10px"
    height: "40px"
  nav-item-active:
    backgroundColor: "#453629"
    textColor: "#ffc586"
  badge:
    backgroundColor: "{colors.sunk}"
    textColor: "{colors.muted}"
    rounded: "{rounded.small}"
    padding: "3px 8px"
  badge-recommended:
    backgroundColor: "{colors.signal-orange-bg}"
    textColor: "{colors.signal-orange-ink}"
  badge-published:
    backgroundColor: "{colors.signal-green-bg}"
    textColor: "{colors.signal-green-ink}"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
  station-now:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    padding: "9px 12px"
  segmented-selected:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    padding: "7px 13px"
---

# Design System: MIZAN

## Overview

**Creative North Star: "Campus Experience"**

Campus Experience places live scheduling evidence within a recognisable university setting. Warm sand and cream surfaces, a deep blue-black rail, apricot actions, and the supplied Al Yamamah campus photograph establish the atmosphere. Soft corners and serif English headings replace the previous square information-system world.

The image is context, not evidence of institutional adoption. All numbers remain live scenario data; synthetic-data labelling, role permissions, validation and explicit human decisions remain visible. The photograph is user supplied at `frontend/src/assets/al-yamamah-campus.jpg` and bundled locally by Vite. `frontend/src/style.css` supplies structural and interaction styles; `frontend/src/campus.css`, loaded afterward, supplies this visual world.

Compact Archivo body text and tabular numerals keep the workspace practical. Arabic uses self-hosted Noto Kufi Arabic with logical layout and full bilingual strings. Photo overlays support legibility; pale grade labels keep continuous metric grading readable beside white hero numbers.

**Key Characteristics:**
- Warm sand ground, cream panels and a deep campus rail with apricot active navigation.
- User-supplied campus photography in the overview, rail, login and subdued page backgrounds.
- Serif English headings, compact Archivo data and first-class Noto Kufi Arabic.
- Soft 5–12px corners, thin warm borders and restrained floating-layer shadows.
- White overview hero values paired with continuously graded labels on cream chips.
- Department charts, a room-use ring and role-aware actions use live scenario data.

## Colors

A warm campus palette supports compact operational evidence. Frontmatter records the current root tokens; computed metric colours remain owned by `frontend/src/grade.ts`.

### Primary
Apricot action and its dark ink are used for primary buttons, the letter mark and modal emphasis. Primary hover is lighter apricot. Focus outlines are brown (#a36124); fields use a warm border (#b8793d) and a translucent amber halo. Text actions use orange ink.

### Secondary
Muted blue, green, orange and red support operational state and department charts. Success and published states use green; waiting/recommended states use orange; conflicts, rejected states and overload use red. State colours remain separate from the continuous severity scale. Overview icon wells use pale green, violet and apricot as visual identifiers, not as metric grades.

### Tertiary
Teal and magenta remain fifth and sixth department fallbacks. The room-use ring uses warm ochre (#d88b45) against a pale track (#e7d9c6): arc length reports utilization, not a categorical grade.

### Neutral
Sand paper is the workspace ground; cream surface holds operational panels and fields; sunk cream supports inset content. Deep rail and ink anchor navigation, selections and current workflow steps. Warm grey text levels and hairlines separate detail without heavy outlines. The overview uses warm white type over a darkened image and translucent brown stat tiles.

### Graded scale
`gradeVars()` emits `--g` (ink), `--g-bg` (tint), and `--g-line` (strong field). The OKLCH hue path is red 25° → amber 70° → green 150°. Metric anchors remain quality 35→88, weekly gap hours per student 5→0.75, 2h+ gap share 0.45→0.04, room use 30→82%, campus days 5→2.5, longest gap 240→45 minutes, personal weekly gaps 6→0.75 hours, recovered hours −10→40, students worsened 40→0 and conflicts 5→0. Critical / Weak / Fair / Good / Strong labels are bilingual. Missing values receive no grade.

**The Continuous Grade Rule.** Keep gradeVars() and each metric's bad/good anchors. Colour moves continuously red → amber → green; bilingual grade words accompany the scale. Hero values may be white for photo contrast, but their cream-backed grade labels retain the computed colour.

**The Department Identity Rule.** Assign department hues in alphabetical order: blue, green, orange, red, then teal and magenta. Department identity is separate from metric severity; the chart explains the distinction.

**The Capacity Not Performance Rule.** Individual faculty workload is never graded. Workload bars are blue; only a load over contract turns red. This is capacity planning, not performance evaluation.

## Typography

English page headings use Georgia with Arabic fallback; body, labels and data use self-hosted Archivo Variable with Noto Kufi Arabic. Arabic page headings use the body font stack, open line height and zero tracking.

- **Display:** the overview number is 66px/450, line-height 1; 74px at ≥1600px, 55px at ≤850px and 46px at ≤540px. It remains warm white on the photograph.
- **Headline:** base h1 is 30px/400; page headings are 29px and overview 32px/1.18. Overview steps down to 29px, 27px and 25px across smaller widths; Arabic mobile overview is 23px.
- **Metric:** ordinary metric tiles retain 32px/350; overview stat values use 28px/450, reducing to 25px and then 24px.
- **Title:** panels use 16px/600, overview chart headings 15px.
- **Body:** 13.5px/400 with 1.65 line height; page subtitles 13px.
- **Label / Micro:** mostly 11–12.5px; compact navigation uses 12px. Units, labels and grades stay adjacent to their values.

**The Arabic Line Rule.** Use Noto Kufi Arabic for Arabic headings, reset Latin negative tracking to zero, preserve open line heights and mirror directional layout through logical properties.

## Layout

The fixed rail is 212px wide at the inline start. A sticky topbar begins at the top of the workspace, at least 64px high, with scenario, language and synthetic-data controls. The old four-colour department strip is hidden. Main content has 28px top and 30px inline padding, maximum width 1600px; wide screens use 46px inline padding.

The overview layers a photo-backed title and large weekly-gap figure above four stat tiles. Two columns (1.2fr / 1fr, 18px gap) hold cohort gap bars and room capacity, followed by decisions and quick actions. The cohort chart is vertical, with one shared labelled hour scale and department-coloured bars; numeric labels are independently graded. The room-use ring represents used versus unused room time with visible percentages. Counts and actions reflect the selected scenario and role.

At ≤1200px the rail narrows to 190px and padding to 24px. At ≤1000px the overview panels stack and stats become two columns. At ≤850px the rail becomes 64px icons, the rail photo disappears, and the topbar wraps. At ≤540px inline padding becomes 14px, controls compact, facts stack and action tiles place icons above labels. Photo height increases across narrow breakpoints so the hero remains backed by the image. Existing timetable overflow and drawer behavior remain structural base styles.

## Elevation & Depth

Opaque cream panels sit on sand with thin warm borders and no ambient card shadows. Campus photography uses dark-to-clear and image-to-paper overlays. Overview stat tiles use a translucent brown ground, a pale border and 12px backdrop blur. Reduced-transparency preference removes the blur and uses solid brown. Modals, timetable ghosts, docks and overlay drawers retain the base floating-layer shadow (`0 18px 40px -16px #1113, 0 2px 6px -2px #1111`).

**The Evidence Surface Rule.** Keep detailed operational panels opaque and legible. Photo overlays and translucent dark tiles belong to the campus overview; reduced transparency makes those tiles solid.

## Shapes

Corners are softly curved: fields and buttons 6px, badges and timetable blocks 5px, overview stat tiles 8px, panels and cards 9px, modals 12px. The brand mark has 6px corners; avatars and the room-use visualization are circular. Thin borders provide structure. Department top edges and computed grade accents persist where inherited components use them.

## Components

### Buttons and fields
Primary buttons use apricot with dark text; hover lightens the fill. Secondary buttons use cream with a hairline. Buttons retain 40px minimum height and the base pressed feedback. Inputs use 6px corners, 38px minimum height and warm focus feedback. Text links use orange ink and direction-aware arrows. Disabled actions preserve existing permission and pending-state logic.

### Navigation
The deep rail includes a subdued campus image at its lower edge. Items are 40px minimum height with 6px corners. Active items use brown with apricot text/icon and a 2px inset accent at the reading edge. The count badge is pale apricot with dark digits. At mobile widths, accessible icon labels remain available as visual labels hide.

### Cards and grade labels
Operational cards use cream, warm borders and 9px corners. Ordinary graded tiles retain the computed tint and numeric colour. Overview tiles use dark translucent surfaces and white values; compact cream grade chips show the continuous grade ink and marker. The large gap figure follows the same white-number/graded-label distinction.

### Charts
Cohort column height uses one shared hour scale, colour identifies the department and the label colour reports severity. The utilization ring uses a conic fill clamped to 0–100%, with visible used/unused labels and an accessible percentage. Neither chart invents data or changes the underlying scheduling metrics.

### Proposal lifecycle and timetable
Preview → Propose → Approve → Publish remains a joined station strip: completed green, current ink, stopped red, and an explicit publication consequence. End cells now have soft corners. Timetable meetings retain department top edges, ink selection, drag preview states and a keyboard move form, with 5px corners. Department assignment remains alphabetical; timetable blocks and overview bars share the muted root palette, with legible department tints and ink.

### Campus imagery and motion
The locally bundled user photograph appears in the login story, the rail and page backgrounds, with the largest expression on Overview. The image does not replace labels or operational evidence. Existing count-ups run for 700ms and grade transitions for 0.6s; reduced motion displays final values immediately. Reduced transparency removes overview tile blur.

## Do's and Don'ts

### Do:
- **Do** derive graded colours from gradeVars() and preserve their bilingual labels, including cream-backed labels beside white hero numbers.
- **Do** keep synthetic data, validation status and human approval explicit.
- **Do** use the supplied local campus photograph and retain readable overlays.
- **Do** keep large numerals light and tabular, with compact labels.
- **Do** keep semester context, scenario selection and language controls in the topbar.
- **Do** write every UI string with t(en, ar), mirror layout and respect reduced motion.
- **Do** use one labelled scale for cohort bars and retain clear room-use labels.

### Don't:
- **Don't** grade faculty performance or turn workload into a quality score.
- **Don't** replace continuous metric colours with hard traffic-light thresholds.
- **Don't** infer university adoption, real institutional data or new capabilities from the campus photo.
- **Don't** obscure grade words, units, conflict warnings or the synthetic-data label with imagery.
- **Don't** apply Latin negative letter-spacing to Arabic headings.
