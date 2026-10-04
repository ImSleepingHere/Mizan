import React, {useState} from 'react';
import {CalendarSearch, LoaderCircle, TriangleAlert, UsersRound, DoorOpen, UserRound, Info, Search, Copy, ArrowRight, ArrowLeft, X} from 'lucide-react';
import {api, time, number, useDraft} from './api';

type R = Record<string, any>;

/** Ranked slots from the common free-slot finder (spec §18.5). Counts only; no student is identified. */
export function SlotList({r, ar, days, onUse}:{r:R, ar:boolean, days:string[], onUse?:(slot:R)=>void}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const [copied, setCopied] = useState('');
  if (!r.slots?.length) return <p>{t('No slot was found for these settings.','لم يُعثر على وقت مناسب بهذه الإعدادات.')}</p>;
  const Go = ar ? ArrowLeft : ArrowRight;
  const copy = (s:R) => { const text = `${days[s.day]} ${time(s.start)}–${time(s.end)} · ${s.rooms?.join(', ') || ''}`; void navigator.clipboard?.writeText(text).then(() => setCopied(`${s.day}-${s.start}`)).catch(() => setCopied('')); };
  return <div className="fs-list">
    <p className="muted">{r.merge ? t(`Merged group: ${r.group_size} students`, `المجموعة المدمجة: ${r.group_size} طالباً`) : t(`${r.group_size} students in scope`, `${r.group_size} طالباً ضمن النطاق`)} · {r.duration} {t('min','دقيقة')}</p>
    <ol>{r.slots.map((s:R, i:number) => <li key={`${s.day}-${s.start}`} className={i === 0 ? 'best' : ''}>
      <strong>{days[s.day]} <bdi>{time(s.start)}–{time(s.end)}</bdi></strong>
      <span className={`tt-chip ${s.unavailable ? 'warn' : 'ok'}`}><UsersRound size={13}/>{s.unavailable ? t(`${s.unavailable} of ${s.group_size} can't attend`, `${s.unavailable} من ${s.group_size} لا يستطيعون الحضور`) : t('All students free','جميع الطلاب متاحون')}</span>
      <span className={`tt-chip ${s.rooms ? '' : 'bad'}`}><DoorOpen size={13}/>{s.rooms ? s.rooms.join(', ') : t('No free room','لا توجد قاعة متاحة')}</span>
      {!s.professor_free && <span className="tt-chip bad"><UserRound size={13}/>{t('Professor busy','الأستاذ مشغول')}</span>}
      {s.extra_campus_days > 0 && <span className="tt-chip">{number(s.extra_campus_days)} {t('need an extra campus day','يحتاجون يوم حضور إضافي')}</span>}
      <span className="slot-actions"><button type="button" className="text-button" onClick={() => copy(s)}><Copy size={13}/>{copied === `${s.day}-${s.start}` ? t('Copied','تم النسخ') : t('Copy','نسخ')}</button>
        {onUse && <button type="button" className="text-button" onClick={() => onUse(s)}>{t('Request this time','اطلب هذا الوقت')}<Go size={13}/></button>}</span>
    </li>)}</ol>
    <p className="muted"><Info size={13}/>{t('Found on the weekly timetable; a free slot repeats every teaching week. Date-specific exceptions aren\'t checked yet. Finding a slot books nothing: to move a class there, send a change request for committee approval.','تم البحث في الجدول الأسبوعي؛ الوقت المتاح يتكرر كل أسبوع دراسي. الاستثناءات الخاصة بتواريخ محددة لا يتم فحصها بعد. إيجاد الوقت لا يحجز شيئاً: لنقل محاضرة إليه أرسل طلب تغيير لاعتماد اللجنة.')}</p>
  </div>;
}

type Criteria = {sections:string[], duration:number, days:number[], merge:boolean, same:boolean};
const sameCriteria = (a:Criteria, b:Criteria) => JSON.stringify(a) === JSON.stringify(b);

export function FreeSlotFinder({sid, ar, days, role, sections, courseName, profName, onRequest}:{sid:string, ar:boolean, days:string[], role:string, sections:R[],
  courseName:(id:string)=>string, profName:(id:string)=>string, onRequest?:(sectionId:string, mi:number, day:number, start:number)=>void}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const mine = role === 'professor';
  const [criteria, setCriteria] = useDraft<Criteria>(`slots:${sid}`, {sections:mine && sections[0] ? [sections[0].id] : [], duration:60, days:[], merge:false, same:false});
  const [result, setResult] = useDraft<{criteria:Criteria, r:R}|null>(`slots-result:${sid}`, null);
  const [q, setQ] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const set = (patch:Partial<Criteria>) => setCriteria(c => ({...c, ...patch}));
  const fresh = result && sameCriteria(result.criteria, criteria);
  const label = (s:R) => `${courseName(s.course_id)} · ${s.id}`;
  const summary = (s:R) => `${s.meetings.map((m:R) => `${days[m.day].slice(0, 3)} ${time(m.start)}`).join(', ')} · ${profName(s.professor_id)}`;
  const matches = sections.filter(s => !q || `${s.id} ${courseName(s.course_id)} ${profName(s.professor_id)}`.toLowerCase().includes(q.toLowerCase())).slice(0, 40);
  const known = new Set(sections.map(s => s.id));
  async function find(){
    setBusy(true); setError('');
    try { const r = await api(`/scenarios/${sid}/free-slots`, {sections:criteria.sections, duration:criteria.duration, days:criteria.days, merge:criteria.merge, same_time_for_all:criteria.same && !criteria.merge}); setResult({criteria, r}); }
    catch (e) { setError((e as Error).message); setResult(null); } finally { setBusy(false); }
  }
  const single = criteria.sections.length === 1 ? sections.find(s => s.id === criteria.sections[0]) : null;
  const meetingIndex = single ? single.meetings.findIndex((m:R) => m.end - m.start === criteria.duration) : -1;
  return <section className="panel ra">
    <div className="ra-head"><span className="ra-icon"><CalendarSearch size={18}/></span><div><h2>{t('Find a common time','إيجاد وقت مشترك')}</h2>
      <p>{t('For a revision session, a quiz or teaching sections together: see when the students, the professor and a room are free.','لمحاضرة مراجعة أو اختبار قصير أو دمج شعب: اعرف متى يكون الطلاب والأستاذ وقاعة متاحين.')}</p></div></div>
    <div className="section-picker">
      <div className="picked">{criteria.sections.length ? criteria.sections.map(id => { const s = sections.find(x => x.id === id); return <span key={id} className={`pick-chip ${known.has(id) ? '' : 'bad'}`}>{s ? label(s) : t(`${id} (not in this timetable)`, `${id} (غير موجودة في هذا الجدول)`)}<button type="button" aria-label={t(`Remove ${id}`, `إزالة ${id}`)} onClick={() => set({sections:criteria.sections.filter(x => x !== id)})}><X size={12}/></button></span>; })
        : <span className="muted">{t('No sections chosen yet.','لم تُختر أي شعبة بعد.')}</span>}</div>
      <div className="search-field"><Search size={15}/><input aria-label={t('Find sections','البحث عن شعب')} placeholder={t('Search by course, section or instructor…','ابحث بالمقرر أو الشعبة أو المحاضر…')} value={q} onChange={e => setQ(e.target.value)}/></div>
      {(q || mine) && <div className="pick-list" role="listbox" aria-label={t('Sections','الشعب')}>
        {matches.map(s => { const on = criteria.sections.includes(s.id); return <label key={s.id} className="ra-check pick-option"><input type="checkbox" checked={on} disabled={!on && criteria.sections.length >= 10}
          onChange={e => set({sections:e.target.checked ? [...criteria.sections, s.id] : criteria.sections.filter(x => x !== s.id)})}/><span><strong>{label(s)}</strong><small>{summary(s)}</small></span></label>; })}
        {!matches.length && <p className="muted">{t('No section matches.','لا توجد شعبة مطابقة.')}</p>}
        {mine && sections.length > 1 && <button type="button" className="text-button" onClick={() => set({sections:criteria.sections.length === sections.length ? [] : sections.slice(0, 10).map(s => s.id)})}>{criteria.sections.length === sections.length ? t('Clear all','إلغاء الكل') : t('Select all','تحديد الكل')}</button>}
      </div>}
    </div>
    <div className="ra-edit">
      <label>{t('Length','المدة')}<select value={criteria.duration} onChange={e => set({duration:Number(e.target.value)})}>{[30, 45, 60, 75, 80, 90, 110, 120].map(m => <option key={m} value={m}>{m} {t('min','دقيقة')}</option>)}</select></label>
      <fieldset><legend>{t('Days','الأيام')}</legend>
        <label className="ra-check"><input type="checkbox" checked={!criteria.days.length} onChange={() => set({days:[]})}/>{t('All days','كل الأيام')}</label>
        {days.map((d, i) => <label key={d} className="ra-check"><input type="checkbox" checked={criteria.days.includes(i)} onChange={e => set({days:e.target.checked ? [...criteria.days, i].sort() : criteria.days.filter(x => x !== i)})}/>{d}</label>)}</fieldset>
      <fieldset><legend>{t('Options','خيارات')}</legend>
        <label className="ra-check"><input type="checkbox" checked={criteria.merge} onChange={e => set({merge:e.target.checked})}/>{t('Teach together in one room','دمج في قاعة واحدة')}</label>
        <label className="ra-check"><input type="checkbox" checked={criteria.same && !criteria.merge} disabled={criteria.merge} onChange={e => set({same:e.target.checked})}/>{t('Same time, separate rooms','نفس الوقت بقاعات منفصلة')}</label></fieldset>
    </div>
    <div className="ra-actions">{criteria.merge && criteria.sections.length < 2 && <small className="muted">{t('Choose at least two sections to teach together.','اختر شعبتين على الأقل للدمج.')}</small>}
      <button className="primary" disabled={busy || !criteria.sections.length || !criteria.sections.every(id => known.has(id)) || (criteria.merge && criteria.sections.length < 2)} onClick={() => void find()}>{busy ? <LoaderCircle size={16} className="spin"/> : <CalendarSearch size={16}/>}{t('Find times','ابحث عن الأوقات')}</button></div>
    {error && <div role="alert" className="alert error"><TriangleAlert size={16}/><span>{error}</span></div>}
    {result && !fresh && <div className="ra-block warn" role="status"><p><TriangleAlert size={14}/>{t('The results below are for earlier choices. Search again to update them.','النتائج أدناه لاختيارات سابقة. ابحث مرة أخرى لتحديثها.')}</p></div>}
    {result && <div className={`ra-result ${fresh ? '' : 'out-of-date'}`} aria-hidden={!fresh}>
      <p className="criteria-used">{t('Results for','النتائج لـ')}: {result.criteria.sections.join(', ')} · {result.criteria.duration} {t('min','دقيقة')} · {result.criteria.days.length ? result.criteria.days.map(d => days[d]).join(', ') : t('all days','كل الأيام')}{result.criteria.merge ? ` · ${t('one room','قاعة واحدة')}` : result.criteria.same ? ` · ${t('same time','نفس الوقت')}` : ''}</p>
      {fresh && <SlotList r={result.r} ar={ar} days={days} onUse={onRequest && single && meetingIndex >= 0 && !criteria.merge ? s => onRequest(single.id, meetingIndex, s.day, s.start) : undefined}/>}
    </div>}
  </section>;
}
