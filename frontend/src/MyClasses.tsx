import React, {useEffect, useState} from 'react';
import {BookOpenCheck, LoaderCircle, Wand2, ShieldCheck, TriangleAlert, Clock3, UsersRound, CalendarDays} from 'lucide-react';
import {api, time, number} from './api';
import {SCALES, gradeVars} from './grade';

type R = Record<string, any>;
// Survives the page refresh that follows a new proposal (the panel re-mounts).
const lastResult:Record<string, R|null> = {};

/** Professor view of their own sections (spec §18.3): aggregates only, and optimization limited to own sections. */
export function MyClasses({sid, ar, days, revision, courseName, onProposal}:{sid:string, ar:boolean, days:string[], revision:number, courseName:(id:string)=>string, onProposal:()=>void}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const [info, setInfo] = useState<R|null>(null), [error, setError] = useState(''), [busy, setBusy] = useState(false);
  const [maxChanges, setMaxChanges] = useState(2), [result, setResultState] = useState<R|null>(lastResult[sid] || null);
  const setResult = (r:R|null) => { lastResult[sid] = r; setResultState(r); };

  useEffect(() => { setResultState(lastResult[sid] || null); setError(''); api(`/scenarios/${sid}/my-classes`).then(setInfo).catch(e => { setInfo(null); setError((e as Error).message); }); }, [sid, revision]);

  async function improve(){
    setBusy(true); setError(''); setResult(null);
    try { const r = await api(`/scenarios/${sid}/optimize`, {max_changes:maxChanges, seconds:10}); setResult(r); if (r.proposal) onProposal(); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }

  if (!info) return error ? <div className="alert error"><TriangleAlert size={16}/><span>{error}</span></div> : null;
  if (!info.sections.length) return null;
  const c = result?.comparison;
  return <section className="panel mc">
    <div className="ra-head"><span className="ra-icon"><BookOpenCheck size={18}/></span><div><h2>{t('My classes','مقرراتي')}</h2>
      <p>{t('Your sections and how their students\' weeks look. Figures are totals only; no student is identified.','شعبك وكيف يبدو أسبوع طلابها. الأرقام إجمالية فقط دون تعريف أي طالب.')}</p></div></div>
    <div className="mc-stats">
      <div><span>{t('Students','الطلاب')}</span><strong>{number(info.students)}</strong></div>
      <div style={gradeVars(info.average_gap_hours, SCALES.gapPerStudent) as React.CSSProperties}><span>{t('Avg. weekly gap','متوسط الفجوات الأسبوعية')}</span><strong>{number(info.average_gap_hours)} <small>{t('h','س')}</small></strong></div>
      <div style={gradeVars(info.average_campus_days, SCALES.campusDays) as React.CSSProperties}><span>{t('Avg. campus days','متوسط أيام الحضور')}</span><strong>{number(info.average_campus_days)}</strong></div>
      <div style={gradeVars(info.students ? info.long_gap_2h / info.students : null, SCALES.longGapShare) as React.CSSProperties}><span>{t('Gaps of 2h or more','فجوات ساعتين فأكثر')}</span><strong>{number(info.long_gap_2h)}</strong></div>
      <div><span>{t('Teaching load','العبء التدريسي')}</span><strong>{number(info.teaching_minutes / 60)} / {number(info.contracted_minutes / 60)} <small>{t('h','س')}</small></strong></div>
    </div>
    <div className="mc-sections">{info.sections.map((s:R) => <div key={s.id} className="mc-section"><strong>{s.id}</strong><span>{courseName(s.course_id)}</span>
      <small><CalendarDays size={12}/>{s.meetings.map((m:R) => `${days[m.day]} ${time(m.start)}–${time(m.end)}`).join(' · ')}</small><small><UsersRound size={12}/>{s.enrolled} / {s.capacity} · {s.room_id}</small></div>)}</div>
    <div className="mc-run">
      <label>{t('Change at most','بحد أقصى')}<select value={maxChanges} onChange={e => setMaxChanges(Number(e.target.value))}>{info.sections.map((_:R, i:number) => <option key={i} value={i + 1}>{i + 1} {t(i ? 'sections' : 'section', i ? 'شعب' : 'شعبة')}</option>)}</select></label>
      <button className="primary" disabled={busy} onClick={() => void improve()}>{busy ? <LoaderCircle size={16} className="spin"/> : <Wand2 size={16}/>}{t('Improve my classes','حسّن مقرراتي')}</button>
      <small className="muted">{t('Only your sections can move. Other sections stay fixed. Any result is a proposal for the scheduling committee.','يمكن نقل شعبك فقط وتبقى بقية الشعب ثابتة. أي نتيجة هي مقترح يُرفع للجنة الجدولة.')}</small>
    </div>
    {error && <div role="alert" className="alert error"><TriangleAlert size={16}/><span>{error}</span></div>}
    {result && <div className="ra-result">
      {c && c.changes?.length ? <>
        <div className="tt-chips"><span className="tt-chip ok"><ShieldCheck size={13}/>{t('Independently validated','تم التحقق بشكل مستقل')}</span>
          <span className="tt-chip"><Clock3 size={13}/><bdi>{c.recovered_hours > 0 ? '+' : ''}{number(c.recovered_hours)}</bdi> {t('student-h / week','ساعة طالب / أسبوع')}</span>
          <span className={`tt-chip ${c.adverse_count ? 'warn' : ''}`}><UsersRound size={13}/>{number(c.adverse_count ?? c.worsened)} {t('worse off','متضرر')}</span>
          <span className="tt-chip">{t('Solver','المحلّل')}: {result.status}</span></div>
        <ul className="ra-rules">{c.changes.map((x:R) => <li key={x.section_id}>{x.section_id}: {x.before.meetings.map((m:R) => `${days[m.day]} ${time(m.start)}`).join(', ')} → {x.after.meetings.map((m:R) => `${days[m.day]} ${time(m.start)}`).join(', ')}{x.before.room_id !== x.after.room_id ? ` · ${x.after.room_id}` : ''}</li>)}</ul>
        <p>{t('Saved as a proposal for committee review. Nothing changes until it is approved and published.','حُفظ كمقترح لمراجعة اللجنة. لا يتغير شيء حتى يُعتمد ويُنشر.')}</p></>
        : <p>{t('No improvement found within these limits; your current timetable is kept.','لم يُعثر على تحسين ضمن هذه الحدود؛ يبقى جدولك الحالي كما هو.')} <span className="muted">({result.status})</span></p>}
    </div>}
  </section>;
}
