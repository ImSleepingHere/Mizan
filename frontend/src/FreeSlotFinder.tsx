import React, {useState} from 'react';
import {CalendarSearch, LoaderCircle, TriangleAlert, UsersRound, DoorOpen, UserRound, Info} from 'lucide-react';
import {api, time, number} from './api';

type R = Record<string, any>;

/** Ranked slots from the common free-slot finder (spec §18.5). Counts only; no student is identified. */
export function SlotList({r, ar, days}:{r:R, ar:boolean, days:string[]}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  if (!r.slots?.length) return <p>{t('No slot was found for these settings.','لم يُعثر على وقت مناسب بهذه الإعدادات.')}</p>;
  return <div className="fs-list">
    <p className="muted">{r.merge ? t(`Merged group: ${r.group_size} students`, `المجموعة المدمجة: ${r.group_size} طالباً`) : t(`${r.group_size} students in scope`, `${r.group_size} طالباً ضمن النطاق`)} · {r.duration} {t('min','دقيقة')}</p>
    <ol>{r.slots.map((s:R, i:number) => <li key={`${s.day}-${s.start}`} className={i === 0 ? 'best' : ''}>
      <strong>{days[s.day]} <bdi>{time(s.start)}–{time(s.end)}</bdi></strong>
      <span className={`tt-chip ${s.unavailable ? 'warn' : 'ok'}`}><UsersRound size={13}/>{s.unavailable ? t(`${s.unavailable} of ${s.group_size} can't attend`, `${s.unavailable} من ${s.group_size} لا يستطيعون الحضور`) : t('All students free','جميع الطلاب متاحون')}</span>
      <span className={`tt-chip ${s.rooms ? '' : 'bad'}`}><DoorOpen size={13}/>{s.rooms ? s.rooms.join(', ') : t('No free room','لا توجد قاعة متاحة')}</span>
      {!s.professor_free && <span className="tt-chip bad"><UserRound size={13}/>{t('Professor busy','الأستاذ مشغول')}</span>}
      {s.extra_campus_days > 0 && <span className="tt-chip">{number(s.extra_campus_days)} {t('need an extra campus day','يحتاجون يوم حضور إضافي')}</span>}
    </li>)}</ol>
    <p className="muted"><Info size={13}/>{t('Found on the weekly timetable; a free slot repeats every teaching week. Date-specific exceptions aren\'t checked yet. Finding a slot books nothing.','تم البحث في الجدول الأسبوعي؛ الوقت المتاح يتكرر كل أسبوع دراسي. الاستثناءات الخاصة بتواريخ محددة لا يتم فحصها بعد. إيجاد الوقت لا يحجز شيئاً.')}</p>
  </div>;
}

export function FreeSlotFinder({sid, ar, days, role, sections}:{sid:string, ar:boolean, days:string[], role:string, sections:R[]}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const mine = role === 'professor';
  const [chosen, setChosen] = useState<string[]>(mine && sections[0] ? [sections[0].id] : []), [typed, setTyped] = useState('');
  const [duration, setDuration] = useState(60), [dayset, setDayset] = useState<number[]>([]);
  const [merge, setMerge] = useState(false), [same, setSame] = useState(false);
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [result, setResult] = useState<R|null>(null);
  const ids = mine ? chosen : typed.toUpperCase().split(/[,\s،]+/).filter(Boolean).map(x => /^\d+$/.test(x) ? `S${x.padStart(3, '0')}` : x);
  async function find(){
    setBusy(true); setError(''); setResult(null);
    try { setResult(await api(`/scenarios/${sid}/free-slots`, {sections:ids, duration, days:dayset, merge, same_time_for_all:same && !merge})); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return <section className="panel ra">
    <div className="ra-head"><span className="ra-icon"><CalendarSearch size={18}/></span><div><h2>{t('Find a common time','إيجاد وقت مشترك')}</h2>
      <p>{t('For a revision session, a quiz or teaching sections together: see when the students, the professor and a room are free.','لمحاضرة مراجعة أو اختبار قصير أو دمج شعب: اعرف متى يكون الطلاب والأستاذ وقاعة متاحين.')}</p></div></div>
    <div className="ra-edit">
      {mine ? <fieldset><legend>{t('Sections','الشعب')}</legend>{sections.map((s:R) => <label key={s.id} className="ra-check"><input type="checkbox" checked={chosen.includes(s.id)} onChange={e => setChosen(e.target.checked ? [...chosen, s.id] : chosen.filter(x => x !== s.id))}/>{s.id}</label>)}</fieldset>
        : <label>{t('Sections','الشعب')}<input dir="ltr" value={typed} onChange={e => setTyped(e.target.value)} placeholder="S087, S089"/></label>}
      <label>{t('Length','المدة')}<select value={duration} onChange={e => setDuration(Number(e.target.value))}>{[30, 45, 60, 75, 90, 120].map(m => <option key={m} value={m}>{m} {t('min','دقيقة')}</option>)}</select></label>
      <fieldset><legend>{t('Days (none = any)','الأيام (بدون اختيار = أي يوم)')}</legend>{days.map((d, i) => <label key={d} className="ra-check"><input type="checkbox" checked={dayset.includes(i)} onChange={e => setDayset(e.target.checked ? [...dayset, i] : dayset.filter(x => x !== i))}/>{d}</label>)}</fieldset>
      <fieldset><legend>{t('Options','خيارات')}</legend>
        <label className="ra-check"><input type="checkbox" checked={merge} onChange={e => setMerge(e.target.checked)}/>{t('Teach together in one room','دمج في قاعة واحدة')}</label>
        <label className="ra-check"><input type="checkbox" checked={same && !merge} disabled={merge} onChange={e => setSame(e.target.checked)}/>{t('Same time, separate rooms','نفس الوقت بقاعات منفصلة')}</label></fieldset>
    </div>
    <div className="ra-actions"><button className="primary" disabled={busy || !ids.length || (merge && ids.length < 2)} onClick={() => void find()}>{busy ? <LoaderCircle size={16} className="spin"/> : <CalendarSearch size={16}/>}{t('Find times','ابحث عن الأوقات')}</button></div>
    {error && <div role="alert" className="alert error"><TriangleAlert size={16}/><span>{error}</span></div>}
    {result && <div className="ra-result"><SlotList r={result} ar={ar} days={days}/></div>}
  </section>;
}
