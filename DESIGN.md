---
name: MIZAN
description: Scheduling intelligence. Human decisions. A calm information system for evaluating a university semester before publication.
colors:
  paper: "#f6f6f3"
  surface: "#ffffff"
  sunk: "#efefeb"
  ink: "#111111"
  ink-2: "#262624"
  text: "#141413"
  muted: "#5f5f5a"
  faint: "#85857f"
  line: "#e2e2dc"
  line-2: "#cfcfc7"
  signal-blue: "#1d3cff"
  signal-blue-ink: "#1631d9"
  signal-blue-bg: "#ebeeff"
  signal-green: "#00a05a"
  signal-green-ink: "#007a45"
  signal-green-bg: "#e2f4ea"
  signal-orange: "#ff6414"
  signal-orange-ink: "#b54000"
  signal-orange-bg: "#fff0e5"
  signal-red: "#e0102e"
  signal-red-ink: "#bf0d27"
  signal-red-bg: "#fde8eb"
  fallback-teal: "#0a8f9e"
  fallback-magenta: "#b8398c"
typography:
  display:
    fontFamily: "'Archivo Variable', 'Noto Kufi Arabic', system-ui, sans-serif"
    fontSize: "68px"
    fontWeight: 300
    lineHeight: 0.9
    letterSpacing: "-0.035em"
    fontFeature: "tnum"
  headline:
    fontFamily: "'Archivo Variable', 'Noto Kufi Arabic', system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 560
    lineHeight: 1.2
    letterSpacing: "-0.015em"
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
  field: "2px"
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
    backgroundColor: "{colors.signal-blue}"
    textColor: "{colors.surface}"
    rounded: "{rounded.none}"
    padding: "10px 16px"
    height: "40px"
    typography: "{typography.label}"
  button-primary-hover:
    backgroundColor: "{colors.signal-blue-ink}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.none}"
    padding: "10px 16px"
    height: "40px"
  button-text:
    textColor: "{colors.signal-blue-ink}"
    typography: "{typography.label}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.field}"
    padding: "8px 11px"
    height: "38px"
  nav-item:
    backgroundColor: "{colors.ink}"
    textColor: "#b4b4ae"
    padding: "9px 10px"
    height: "38px"
  nav-item-active:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
  badge:
    backgroundColor: "{colors.sunk}"
    textColor: "{colors.muted}"
    rounded: "{rounded.none}"
    padding: "3px 8px"
  badge-recommended:
    backgroundColor: "{colors.signal-orange-bg}"
    textColor: "{colors.signal-orange-ink}"
  badge-published:
    backgroundColor: "{colors.signal-green-bg}"
    textColor: "{colors.signal-green-ink}"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.none}"
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

**Creative North Star: "The Semester as an Information System"**

Mizan is drawn in the Swiss / Otl Aicher lineage: one paper ground, one ink rail, one Sunday–Thursday hour scale, and four flat signal colours that always mean something. Nothing floats on glows or gradients; hierarchy comes from light, thin numerals set large against small, firm labels, from 1px hairlines, and from coloured strips on the top edge of things. The semester reads like a wall chart in a transit authority: calm, exact, and legible at projector distance.

Colour has exactly two jobs. **Department colour** says *which* (blue, green, orange, red assigned by alphabetical department order). **Grade colour** says *how good* (a continuous red → amber → green OKLCH path computed per metric). Everything else is paper, ink and grey. Selection is inversion to ink, not a new hue.

Density is moderate and data-first: 13.5px body, 12–12.5px labels, tabular numerals everywhere. Arabic is a first-class reading direction: Noto Kufi Arabic carries Arabic text, every layout mirrors through logical properties, and every string exists in English and Arabic.

**Key Characteristics:**
- Paper ground (#f6f6f3), ink sidebar rail with a white inverted active item.
- Four flat signal colours used as fields, strips and dots; never gradients, glass or glow.
- Light Archivo numerals (300–450) at large sizes; small semibold labels.
- Square corners, 1px hairlines, 3px colour tops on tiles and timetable blocks.
- Every graded number coloured on a continuous per-metric scale that never snaps at a threshold.
- A 5px four-colour department strip pinned to the top edge of the workspace.

## Colors

Achromatic warm-grey paper and ink carrying four saturated, flat signal colours; each signal comes as a trio of field, ink (text-safe) and tint.

### Primary
- **Signal Blue** (signal-blue): the action colour. Primary buttons, focus rings (2px outline, 2px offset), input focus border plus a 3px blue-tint halo, today's column, the brand square behind م, the model chip, the modal's 4px top edge. Also department colour d0. Its darker **Signal Blue Ink** is the hover fill and the colour of text links and text buttons; **Signal Blue Tint** backs "checking" states and progress banners.

### Secondary
- **Signal Green** (signal-green): success and "good". Live dot, completed station markers, the cohort chart's target tick, the "ok" timetable ghost, published badges (via tint + ink). Department colour d1.
- **Signal Orange** (signal-orange): attention and waiting. The pending-proposals count block, the nav badge, "recommended" badges, the synthetic-data flag. Department colour d2. Orange text always uses **Signal Orange Ink** for contrast.
- **Signal Red** (signal-red): conflict, rejection and overload. Error alerts, blocked stations, the Riyadh now-line in the timetable, over-contract workload bars. Department colour d3.

### Tertiary
- **Fallback Teal** and **Fallback Magenta**: department colours d4 and d5 only, used when a dataset has a fifth or sixth department. Never used for anything else.

### Neutral
- **Paper** (paper): the page ground, the topbar (at 94% opacity) and inset code/quote wells.
- **Surface White** (surface): panels, inputs, secondary buttons, tables.
- **Sunk Grey** (sunk): tags, badges at rest, bar tracks, neutral tile ground.
- **Ink** (ink): the sidebar rail, selection/inversion fills, the "now" station, table header rules and axis baselines.
- **Text / Muted / Faint** (text, muted, faint): body copy, secondary copy and labels, tertiary icons.
- **Hairline / Hairline Strong** (line, line-2): 1px dividers and panel borders; line-2 for input and button strokes.

### Graded scale (computed, not tokenised)
Graded numbers expose three custom properties computed in code from a metric's `bad` and `good` anchors: `--g` (text), `--g-bg` (tile tint), `--g-line` (3px top edge or bar). The hue travels red 25° → amber 70° → green 150° in OKLCH, easing out through yellow-green; ink lightness sits at 0.50–0.54 so amber still reads at AA on paper. Tints are `oklch(0.955 0.045 h)`. Anchors per metric live in one table (quality 35→88, gap hours per student 5→0.75, 2h+ gap share 0.45→0.04, room use 30→82%, campus days 5→2.5, longest gap 240→45 min, recovered hours −10→40, students worsened 40→0, conflicts 5→0). Each graded value also carries a bilingual grade word: Critical / Weak / Fair / Good / Strong (حرج / ضعيف / متوسط / جيد / ممتاز), preceded by an 8px square of `--g-line`.

### Named Rules
**The Two Meanings Rule.** A colour on screen means either *which department* or *how good*. Bar colour = department, number colour = grade. If a colour answers neither question, it is paper, ink or grey.

**The Continuous Grade Rule.** Graded values are coloured from their metric's bad/good anchors on a continuous path. Never introduce a hard threshold, a traffic-light bucket, or a fixed red/green for a metric that has a scale.

**The Alphabetical Department Rule.** Departments take blue, green, orange, red in alphabetical order of department name (d0–d3); teal and magenta are the fifth and sixth fallbacks. Every surface that colours departments sorts the same way, so a department keeps its colour everywhere.

**The Capacity Not Performance Rule.** Individual faculty workload is never graded. Workload bars are blue; only a load over contract turns red. This is capacity planning, not performance evaluation.

## Typography

**Display Font:** Archivo Variable (width axis, self-hosted), falling back to system-ui
**Body Font:** Archivo Variable
**Arabic Font:** Noto Kufi Arabic (400, 600, 700), self-hosted, second in the same stack so Arabic glyphs fall through automatically

**Character:** A grotesque used mostly light and small. The drama is in contrast of weight and size, thin 68px numerals against 12px semibold labels, not in a second typeface. All numerals are tabular.

### Hierarchy
- **Display** (300, 68px, 0.9, −0.035em, width 96%): the one headline figure per page, e.g. weekly gap hours on Overview. 76px at ≥1600px, 52px at ≤540px. The login story headline uses the same voice at 64px.
- **Headline** (560, 26px, 1.2, −0.015em): page titles (h1); 28px on Overview. Modal titles use 20px/560.
- **Metric** (350, 32px, 1.1): numbers in metric tiles; 26px/450 in Overview stat tiles, 24px in compact tiles, 22px/450 in My classes.
- **Title** (600, 16px, 1.3): panel headings (h2); h3 14px/600, h4 12px/600.
- **Body** (400, 13.5px, 1.65, muted): paragraphs; page subtitles 14px capped at 62–68ch.
- **Label** (500–600, 12–12.5px): field labels, table headers, badges, buttons (13px/600), grade words (11.5px/600).
- **Micro** (500, 11px): axis ticks, hour labels, timetable meta lines.

### Named Rules
**The Light Numeral Rule.** Large numbers are light (300–450), never bold. Weight belongs to small labels; size belongs to numbers.

**The Arabic Line Rule.** In RTL, headline letter-spacing resets to 0 and line-height opens (Overview h1 1.5; login headline 54px/1.35 at weight 600) so Kufi ascenders and dots never collide. Never apply Latin negative tracking to Arabic.

## Layout

A fixed 228px ink sidebar on the inline-start edge; the main column carries a sticky 5px department strip, then a sticky 56px topbar (paper at 94% with a hairline bottom), then content at 40px inline padding (56px at ≥1600px), max-width 1640px. The topbar holds context, not the page: live dot + "Fall semester 2026" / page name on the start side; scenario select, synthetic-data flag, language toggle and avatar on the end side. Page headings sit directly under it with no kicker above.

Spacing runs on a 4px base with working steps of 8, 12, 16, 20, 24 and 40px: 8px gaps between tiles, 20px panel inner padding, 24px between panels, 24–26px between major Overview bands. Overview is a two-part hero (display numeral left, three stat tiles right, 48px gap), then a 1.7fr / 1fr grid (cohort chart, semester facts).

Charts share one hour axis. The cohort chart has a fixed hour axis (0 to at least 12h, ticks every 2h) with an ink baseline and a 2px green target tick at the good anchor; every row uses the same scale so bars compare honestly. The timetable is one Sunday–Thursday grid, 58px hour gutter plus five ≥150px day columns, 08:00–18:00, hatched lunch hour, red Riyadh now-line.

Responsive: ≤1200px the hero and Overview grid stack; ≤1150px the sidebar narrows to 200px and the timetable drawer overlays; ≤850px the sidebar collapses to a 64px icon rail, stat tiles stack, the station strip goes vertical, the login story panel hides; ≤540px padding drops to 14px and the breadcrumb shortens.

## Elevation & Depth

Flat by default. Depth is conveyed by tone (paper → white surface → sunk grey), 1px hairlines, and inversion to ink. One shadow exists, and it only appears on things that are genuinely above the page.

### Shadow Vocabulary
- **Lift** (`box-shadow: 0 18px 40px -16px #1113, 0 2px 6px -2px #1111`): modals, the timetable drag ghost, the change dock, the overlaid drawer at narrow widths, and the floating modal error.

### Named Rules
**The Only Lift Rule.** Panels, tiles, cards and buttons have no shadow at rest or on hover. Shadow means "this is floating above the timetable or the page", nothing else.

## Shapes

Square. Buttons, panels, tiles, badges, tags, chips, avatars, the brand square and timetable blocks all have 0 radius; form fields take a barely-there 2px. The single round shape is the 7px live dot, which is a status light. Borders are 1px hairlines; emphasis is a coloured top edge (3px on stat tiles, metric tiles, timetable blocks, dock and request cards; 4px on modals) rather than a heavier outline. Adjacent bordered rows overlap by −1px so shared edges stay single hairlines (station strip, option lists, meeting buttons).

## Components

### Buttons
Firm, flat blocks.
- **Shape:** square (0), minimum 40px tall, 10px × 16px, 13px/600.
- **Primary:** Signal Blue field, white text; hover darkens to Signal Blue Ink; active scales to 0.97.
- **Secondary / Ghost:** white (or transparent) with a line-2 hairline; hover turns the hairline to ink.
- **Text button:** Signal Blue Ink 12.5px/600 with a trailing arrow that nudges 3px toward reading direction on hover (mirrored in RTL).
- **Danger:** red-ink text only, underlined on hover; destructive actions are never blue blocks.

### Chips and Badges
- **Style:** square, 11.5px/600, 3px × 8px, a 7px square of currentColor before the text. Tint ground + ink text from the matching signal: recommended orange, approved blue, published green, invalid/rejected red, draft sunk grey.
- **Timetable chips:** same form for preview results (ok green, bad red, warn orange, checking blue).

### Cards / Containers
- **Corner Style:** square.
- **Background:** white surface on paper.
- **Shadow Strategy:** none (see Elevation).
- **Border:** 1px line hairline; panel heading 18px 20px 12px, panel foot separated by a hairline.
- **Graded tiles:** tint ground `--g-bg`, 3px top `--g-line`, value in `--g`, grade word below. Ungraded tiles fall back to sunk ground and a line-2 top.

### Inputs / Fields
- **Style:** white, 1px line-2 stroke, 2px radius, 38px min height, 13.5px text, blue caret.
- **Focus:** stroke turns Signal Blue plus a 3px blue halo at ~14% alpha; global `:focus-visible` is a 2px blue outline at 2px offset.
- **Disabled:** 45% opacity, not-allowed cursor.
- **Segmented control:** hairline-bordered group; the selected segment inverts to ink with white text.

### Navigation
- **Rail:** ink background, 13px/450 items in #b4b4ae at 38px, 17px line icons at stroke 1.6. Hover lifts to a 7% white wash and white text.
- **Active:** inverts to a white block with ink text at 600 and a Signal Blue icon.
- **Count:** a square orange block with white 11px/700 digits, pushed to the inline end.
- **Mobile:** collapses to a 64px icon rail with labels hidden (aria-labels retained).

### Station Strip (signature)
The proposal lifecycle, Preview → Propose → Approve → Publish, as a row of joined hairline cells with a 20px numbered square in each. Done steps get a green square with a check; the current step inverts fully to ink; a blocked or rejected step turns red tint with a red square and X. The final Publish cell carries a red-ink note "changes the official timetable". Goes vertical at ≤850px.

### Timetable Block (signature)
A department-tinted field (`--cb` ground, `--ct` ink) with a 3px department-coloured top edge; course code 12px/700, name 11.5px, room/capacity/time 11px. Hover fills with the full department colour and white text. **Selection inverts to ink** with white text, keeping the department top edge. Dragging leaves a desaturated 30% origin and shows a lifted dashed-ink ghost that turns solid green (ok), red with a short shake (conflict) or blue (checking) as the live preview returns. Filtered-out blocks dim to 20%.

### Graded Numeral (signature)
Every metric with a scale counts up from 0 over 700ms (ease-out cubic) and settles into its grade colour with a 0.6s colour transition; reduced motion shows the final value immediately. The before/after comparison table grades the *change* (±15% relative anchors) rather than the value.

### Department Strip
A 5px sticky band of four equal blue/green/orange/red segments across the top of the workspace that grows in from the inline start on load. It is the only place the four colours appear without data behind them, as the product's signature mark.

## Do's and Don'ts

### Do:
- **Do** derive every graded colour from `gradeVars()` with the metric's bad/good anchors, and pair it with the bilingual grade word.
- **Do** colour departments by alphabetical order (blue, green, orange, red; teal and magenta only for a fifth and sixth).
- **Do** use a 3px coloured top edge to mark a tile, block or card; use inversion to ink for selection and the current step.
- **Do** keep large numerals light (300–450) and tabular; put weight on small labels.
- **Do** put semester context and the scenario select in the topbar; start each page directly with its heading.
- **Do** write every string with `t(en, ar)` and lay out with logical properties (inset-inline, margin-inline, border-inline); mirror arrows and transform-origins in RTL.
- **Do** keep chart bars on one shared, labelled hour axis with the target marked in green.
- **Do** respect reduced motion: entrance, count-up and bar-grow collapse to the final state.

### Don't:
- **Don't** use gradients, glassmorphism, glows or blurred shadows on panels, tiles or buttons; the only shadow is the lift for floating layers.
- **Don't** round corners beyond the 2px field radius; the live dot is the only circle.
- **Don't** grade individual faculty workload; only overload turns red.
- **Don't** use a hard threshold or three-bucket traffic light for a metric that has a scale.
- **Don't** place a kicker or eyebrow label above headings.
- **Don't** use a signal colour decoratively where it means neither department nor grade.
- **Don't** apply Latin negative letter-spacing to Arabic headings.
