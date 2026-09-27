/**
 * Continuous "how good is this number" colouring.
 * A metric is described by the value that counts as clearly bad and the value that counts as clearly good
 * (either direction). Values between them move smoothly red → amber → green in OKLCH; nothing snaps at a threshold.
 */
export type Scale = {bad:number, good:number};

export const SCALES = {
  quality:{bad:35, good:88},              // 0–100 schedule quality score
  gapPerStudent:{bad:5, good:0.75},       // weekly gap hours per student
  longGapShare:{bad:0.45, good:0.04},     // share of students with a 2h+ gap
  roomUse:{bad:30, good:82},              // % of available room time used
  campusDays:{bad:5, good:2.5},           // days on campus per week
  longestGap:{bad:240, good:45},          // minutes
  personalGapHours:{bad:6, good:0.75},    // one student's weekly gap hours
  recovered:{bad:-10, good:40},           // student-hours per week gained by a proposal
  worsened:{bad:40, good:0},              // students worse off
  conflicts:{bad:5, good:0},
} satisfies Record<string, Scale>;

/** 0 = bad … 1 = good, clamped, eased so the middle of the range reads as amber rather than a muddy mix. */
export function score(value:number|null|undefined, s:Scale){
  if (value === null || value === undefined || !Number.isFinite(value)) return null;
  const k = (value - s.bad) / (s.good - s.bad);
  return Math.max(0, Math.min(1, k));
}

/** Hue path: red 25° → amber 70° → green 150°; the upper half eases out so it passes quickly through olive yellow-green. */
function hue(k:number){ return k < .5 ? 25 + (70 - 25) * (k / .5) : 70 + (150 - 70) * Math.sqrt((k - .5) / .5); }

/** CSS custom properties for a graded element: --g (text/ink), --g-bg (tint), --g-line (strong field). */
export function gradeVars(value:number|null|undefined, s:Scale):Record<string, string>{
  const k = score(value, s);
  if (k === null) return {};
  const h = hue(k).toFixed(1);
  // Amber needs a darker ink to keep ≥4.5:1 on the paper ground; chroma dips slightly in the middle for the same reason.
  const l = (0.5 + 0.04 * Math.abs(k - .5) * 2).toFixed(3), c = (0.15 + 0.03 * Math.abs(k - .5) * 2).toFixed(3);
  return {'--g':`oklch(${l} ${c} ${h})`, '--g-bg':`oklch(0.955 0.045 ${h})`, '--g-line':`oklch(${(0.66+0.08*Math.sin(Math.PI*k)).toFixed(3)} 0.18 ${h})`};
}

/** Short bilingual word for a graded value, for screen readers and the tile foot. */
export function gradeWord(value:number|null|undefined, s:Scale, ar:boolean){
  const k = score(value, s);
  if (k === null) return '';
  const words = ar ? ['حرج','ضعيف','متوسط','جيد','ممتاز'] : ['Critical','Weak','Fair','Good','Strong'];
  return words[Math.min(4, Math.floor(k * 5))];
}
