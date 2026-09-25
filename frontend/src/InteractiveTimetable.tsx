import React, {useEffect, useMemo, useRef, useState} from 'react';
import {CalendarDays, Check, GripVertical, LoaderCircle, MapPin, MoveRight, MoveLeft, Search, ShieldCheck, TriangleAlert, UserRound, UsersRound, X, Undo2, Send, Clock3} from 'lucide-react';
import {api, time, number} from './api';

type R = Record<string, any>;
type Slot = {day:number, start:number};
type Drag = {sectionId:string, mi:number, duration:number, grab:number, origin:Slot, target:Slot|null, moved:boolean, x0:number, y0:number, pointerId:number};
type Pending = {sectionId:string, mi:number, origin:Slot, target:Slot};

const OPEN = 480, CLOSE = 1080, PX = 1.2, SNAP = 15;
const HOURS = Array.from({length:(CLOSE-OPEN)/60+1}, (_, i) => OPEN + i*60);

function riyadhNow(){
  const parts = new Intl.DateTimeFormat('en-US', {timeZone:'Asia/Riyadh', weekday:'short', hour:'2-digit', minute:'2-digit', hour12:false}).formatToParts(new Date());
  const get = (t:string) => parts.find(p => p.type === t)?.value || '';
  const day = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].indexOf(get('weekday'));
  return {day, minutes: (Number(get('hour')) % 24) * 60 + Number(get('minute'))};
}

/** Lay out overlapping meetings side by side (lanes), per day column. */
function layout<T extends {start:number, end:number}>(items:T[]){
  const sorted = [...items].sort((a, b) => a.start - b.start || b.end - a.end);
  const out: (T & {lane:number, lanes:number})[] = [];
  let cluster: (T & {lane:number, lanes:number})[] = [], clusterEnd = -1, laneEnds:number[] = [];
  const flush = () => { const n = Math.max(1, laneEnds.length); cluster.forEach(c => c.lanes = n); out.push(...cluster); cluster = []; laneEnds = []; };
  for (const item of sorted) {
    if (item.start >= clusterEnd && cluster.length) flush();
    let lane = laneEnds.findIndex(end => end <= item.start);
    if (lane === -1) { lane = laneEnds.length; laneEnds.push(item.end); } else laneEnds[lane] = item.end;
    cluster.push({...item, lane, lanes:1});
    clusterEnd = Math.max(clusterEnd, item.end);
  }
  flush();
  return out;
}

export function InteractiveTimetable({data, sid, ar, days, role, courseName, onSubmitted, onOpenChanges}:{
  data:R, sid:string, ar:boolean, days:string[], role:string,
  courseName:(id:string)=>string, onSubmitted:(proposal:R)=>void, onOpenChanges:(sectionId:string, mi:number, m:R)=>void}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const staff = ['admin','registrar','chair'].includes(role);
  const canEditRole = ['admin','registrar','professor'].includes(role);
  const cohorts = useMemo(() => [...new Set<string>((data.students || []).map((s:R) => s.cohort))], [data]);
  const departments = useMemo(() => [...new Set<string>((data.courses || []).map((c:R) => c.department))].sort(), [data]);
  const [cohort, setCohort] = useState<string>(''), [room, setRoom] = useState(''), [prof, setProf] = useState('');
  const [hidden, setHidden] = useState<Set<string>>(new Set()), [query, setQuery] = useState(''), [view, setView] = useState<'week'|'list'>('week');
  const [selected, setSelected] = useState<{sectionId:string, mi:number}|null>(null);
  const [drag, setDrag] = useState<Drag|null>(null), [pending, setPending] = useState<Pending|null>(null);
  const [previews, setPreviews] = useState<Record<string, R|'loading'|{error:string}>>({});
  const [reason, setReason] = useState(''), [submitting, setSubmitting] = useState(false), [error, setError] = useState('');
  const [now, setNow] = useState(riyadhNow());
  const [formDay, setFormDay] = useState(0), [formStart, setFormStart] = useState(540);
  const timer = useRef<number|undefined>(undefined);
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setCohort(cohorts[0] || ''); setSelected(null); setPending(null); setPreviews({}); }, [sid, data.revision, cohorts.join('|')]);
  useEffect(() => { const id = window.setInterval(() => setNow(riyadhNow()), 60000); return () => window.clearInterval(id); }, []);

  const courses = useMemo(() => Object.fromEntries((data.courses || []).map((c:R) => [c.id, c])), [data]);
  const professors = useMemo(() => Object.fromEntries((data.professors || []).map((p:R) => [p.id, p])), [data]);
  const rooms = useMemo(() => Object.fromEntries((data.rooms || []).map((r:R) => [r.id, r])), [data]);
  const enrolled = useMemo(() => { const m:Record<string, number> = {}; (data.students || []).forEach((s:R) => s.sections.forEach((id:string) => m[id] = (m[id] || 0) + 1)); return m; }, [data]);
  const deptIndex = (sectionOrCourse:R) => Math.max(0, departments.indexOf(courses[sectionOrCourse.course_id]?.department));
  const canEdit = (_s:R) => canEditRole;

  const visible = useMemo(() => {
    let list:R[] = data.sections || [];
    if (staff && cohort !== 'all') {
      const ids = new Set<string>();
      (data.students || []).filter((s:R) => !cohort || s.cohort === cohort).forEach((s:R) => s.sections.forEach((id:string) => ids.add(id)));
      if (cohort) list = list.filter(s => ids.has(s.id));
    }
    if (room) list = list.filter(s => s.room_id === room);
    if (prof) list = list.filter(s => s.professor_id === prof);
    return list.filter(s => !hidden.has(courses[s.course_id]?.department));
  }, [data, cohort, room, prof, hidden, staff, courses]);

  const matches = (s:R) => !query || `${s.id} ${s.course_id} ${courseName(s.course_id)} ${s.room_id} ${s.professor_id}`.toLowerCase().includes(query.toLowerCase());
  const key = (sectionId:string, mi:number, slot:Slot) => `${sid}:${data.revision}:${sectionId}:${mi}:${slot.day}:${slot.start}`;

  async function preview(sectionId:string, mi:number, slot:Slot){
    const k = key(sectionId, mi, slot);
    if (previews[k] && previews[k] !== 'loading') return previews[k];
    setPreviews(p => ({...p, [k]:'loading'}));
    try {
      const r = await api(`/scenarios/${sid}/preview-change`, {section_id:sectionId, meeting_index:mi, day:slot.day, start:slot.start});
      setPreviews(p => ({...p, [k]:r})); return r;
    } catch (e) { const v = {error:(e as Error).message}; setPreviews(p => ({...p, [k]:v})); return v; }
  }

  function slotFromPoint(x:number, y:number, d:Drag):Slot|null{
    const col = document.elementsFromPoint(x, y).find(el => (el as HTMLElement).dataset?.ttDay !== undefined) as HTMLElement|undefined;
    if (!col) return null;
    const rect = col.getBoundingClientRect();
    let start = Math.round(((y - rect.top) / PX + OPEN - d.grab) / SNAP) * SNAP;
    start = Math.max(OPEN, Math.min(CLOSE - d.duration, start));
    return {day:Number(col.dataset.ttDay), start};
  }

  function onPointerDown(e:React.PointerEvent, s:R, mi:number, m:R){
    if (e.button !== 0 || !canEdit(s)) return;
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    setDrag({sectionId:s.id, mi, duration:m.end - m.start, grab:(e.clientY - rect.top) / PX, origin:{day:m.day, start:m.start}, target:null, moved:false, x0:e.clientX, y0:e.clientY, pointerId:e.pointerId});
  }
  function onPointerMove(e:React.PointerEvent){
    if (!drag || e.pointerId !== drag.pointerId) return;
    const moved = drag.moved || Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) > 5;
    if (!moved) return;
    const target = slotFromPoint(e.clientX, e.clientY, drag);
    if (target && (target.day !== drag.target?.day || target.start !== drag.target?.start)) {
      window.clearTimeout(timer.current);
      const same = target.day === drag.origin.day && target.start === drag.origin.start;
      if (!same) timer.current = window.setTimeout(() => void preview(drag.sectionId, drag.mi, target), 110);
    }
    setDrag({...drag, moved:true, target:target || drag.target});
  }
  function onPointerUp(e:React.PointerEvent, s:R, mi:number){
    if (!drag || e.pointerId !== drag.pointerId) return;
    const d = drag; setDrag(null); window.clearTimeout(timer.current);
    if (!d.moved) { setSelected({sectionId:s.id, mi}); return; }
    if (d.target && (d.target.day !== d.origin.day || d.target.start !== d.origin.start)) {
      setPending({sectionId:d.sectionId, mi:d.mi, origin:d.origin, target:d.target}); setReason(''); setError('');
      void preview(d.sectionId, d.mi, d.target);
    }
  }

  async function submit(){
    if (!pending) return;
    setSubmitting(true); setError('');
    try {
      const p = await api(`/scenarios/${sid}/changes`, {section_id:pending.sectionId, meeting_index:pending.mi, day:pending.target.day, start:pending.target.start,
        reason: reason.trim().length >= 3 ? reason.trim() : t('Moved in the interactive timetable', 'نُقل من الجدول التفاعلي')});
      setPending(null); onSubmitted(p);
    } catch (e) { setError((e as Error).message); } finally { setSubmitting(false); }
  }

  const byDay = useMemo(() => days.map((_, day) => layout(visible.flatMap(s => s.meetings.map((m:R, mi:number) => ({s, m, mi, start:m.start, end:m.end, day:m.day}))).filter(x => x.day === day))), [visible, days]);
  const selectedSection = selected ? (data.sections || []).find((s:R) => s.id === selected.sectionId) : null;
  const dragSection = drag ? (data.sections || []).find((s:R) => s.id === drag.sectionId) : null;
  const pendingSection = pending ? (data.sections || []).find((s:R) => s.id === pending.sectionId) : null;
  const dragPreview = drag?.target ? previews[key(drag.sectionId, drag.mi, drag.target)] : undefined;
  const pendingPreview = pending ? previews[key(pending.sectionId, pending.mi, pending.target)] : undefined;
  const formPreview = selected ? previews[key(selected.sectionId, selected.mi, {day:formDay, start:formStart})] : undefined;
  const Arrow = ar ? MoveLeft : MoveRight;

  useEffect(() => { if (selectedSection) { const m = selectedSection.meetings[selected!.mi]; setFormDay(m.day); setFormStart(m.start); } }, [selected?.sectionId, selected?.mi]);

  const PreviewChips = ({p}:{p:any}) => {
    if (!p) return null;
    if (p === 'loading') return <span className="tt-chip checking"><LoaderCircle size={13} className="spin"/>{t('Checking…','جارٍ التحقق…')}</span>;
    if (p.error) return <span className="tt-chip bad"><TriangleAlert size={13}/>{p.error}</span>;
    return <>{p.feasible ? <span className="tt-chip ok"><ShieldCheck size={13}/>{t('No new conflicts','لا تعارضات جديدة')}</span> : <span className="tt-chip bad"><TriangleAlert size={13}/>{p.new_issue_count} {t('new conflicts','تعارضات جديدة')}</span>}
      <span className={`tt-chip ${p.recovered_hours > 0 ? 'ok' : p.recovered_hours < 0 ? 'bad' : ''}`}><Clock3 size={13}/><bdi>{p.recovered_hours > 0 ? '+' : ''}{number(p.recovered_hours)}</bdi> {t('student-h / week','ساعة طالب / أسبوع')}</span>
      <span className={`tt-chip ${p.worsened ? 'warn' : ''}`}><UsersRound size={13}/>{number(p.worsened)} {t('worse off','متضرر')}</span></>;
  };
  const issueLabel = (code:string) => ar ? ({STUDENT_OVERLAP:'تعارض طلاب', PROFESSOR_OVERLAP:'تعارض أستاذ', ROOM_OVERLAP:'تعارض قاعة', BLOCKED_TIME:'خارج أوقات التدريس', PROFESSOR_AVAILABILITY:'الأستاذ غير متاح', ROOM_AVAILABILITY:'القاعة غير متاحة', MEETING_PATTERN:'نمط المحاضرات'} as Record<string,string>)[code] || code : code.replaceAll('_',' ').toLowerCase();

  return <section className="panel timetable-panel tt">
    <div className="tt-toolbar">
      <div className="tt-title"><span className="tt-title-icon"><CalendarDays size={18}/></span><div><h2>{t('Weekly timetable','الجدول الأسبوعي')}</h2><p>{canEditRole ? t('Drag any class to a new time. Mizan checks it live before you submit.','اسحب أي محاضرة إلى وقت جديد، وسيتحقق ميزان منها مباشرة قبل الإرسال.') : t('Tap a class to see its details.','اضغط على أي محاضرة لعرض التفاصيل.')}</p></div></div>
      <div className="tt-controls">
        <div className="tt-search"><Search size={15}/><input aria-label={t('Highlight classes','تمييز المحاضرات')} placeholder={t('Highlight course, room, faculty…','ميّز مقرراً أو قاعة أو أستاذاً…')} value={query} onChange={e => setQuery(e.target.value)}/></div>
        {staff && <select aria-label={t('Cohort','المجموعة')} value={cohort} onChange={e => setCohort(e.target.value)}><option value="all">{t('All sections','جميع الشعب')}</option>{cohorts.map(c => <option key={c} value={c}>{c}</option>)}</select>}
        {staff && <select aria-label={t('Room','القاعة')} value={room} onChange={e => setRoom(e.target.value)}><option value="">{t('All rooms','كل القاعات')}</option>{(data.rooms || []).map((r:R) => <option key={r.id} value={r.id}>{r.id} · {r.name}</option>)}</select>}
        {staff && <select aria-label={t('Faculty','الأستاذ')} value={prof} onChange={e => setProf(e.target.value)}><option value="">{t('All faculty','كل الأساتذة')}</option>{(data.professors || []).map((p:R) => <option key={p.id} value={p.id}>{p.name}</option>)}</select>}
        <div className="segmented"><button className={view === 'week' ? 'selected' : ''} onClick={() => setView('week')}>{t('Week','أسبوع')}</button><button className={view === 'list' ? 'selected' : ''} onClick={() => setView('list')}>{t('List','قائمة')}</button></div>
      </div>
    </div>
    <div className="tt-legend">{departments.map((d, i) => <button key={d} className={`tt-legend-item d${i % 6} ${hidden.has(d) ? 'off' : ''}`} onClick={() => { const n = new Set(hidden); n.has(d) ? n.delete(d) : n.add(d); setHidden(n); }} aria-pressed={!hidden.has(d)}><span/>{ar ? d.replace('Computing','الحوسبة').replace('Business','الأعمال').replace('Engineering','الهندسة').replace('Design','التصميم') : d}</button>)}<span className="tt-count">{visible.length} {t('sections','شعبة')} · {visible.reduce((a, s) => a + s.meetings.length, 0)} {t('meetings','محاضرة')}</span></div>

    {view === 'week' ? <div className="tt-body">
      <div className="tt-scroll"><div className={`tt-grid ${drag?.moved ? 'dragging' : ''}`} ref={gridRef} style={{['--tt-height' as any]:`${(CLOSE-OPEN)*PX}px`}}>
        <div className="tt-corner">{t('Riyadh','الرياض')}</div>
        {days.map((d, i) => <div key={d} className={`tt-day-head ${now.day === i ? 'today' : ''}`}><span>{d}</span>{now.day === i && <small>{t('Today','اليوم')}</small>}</div>)}
        <div className="tt-axis">{HOURS.map(h => <span key={h} style={{top:(h-OPEN)*PX}}><bdi>{time(h)}</bdi></span>)}</div>
        {days.map((_, day) => <div key={day} className={`tt-day ${now.day === day ? 'today' : ''} ${drag?.moved && drag.target?.day === day ? 'drop-target' : ''}`} data-tt-day={day}>
          {HOURS.slice(0, -1).map(h => <div key={h} className={`tt-hour ${h === 720 ? 'lunch' : ''}`} style={{top:(h-OPEN)*PX, height:60*PX}}/>) }
          {now.day === day && now.minutes >= OPEN && now.minutes <= CLOSE && <div className="tt-now" style={{top:(now.minutes-OPEN)*PX}}><span/></div>}
          {byDay[day].map(({s, m, mi, lane, lanes}, i) => {
            const isDragging = drag?.moved && drag.sectionId === s.id && drag.mi === mi;
            const isPending = !!pending && pending.sectionId === s.id && pending.mi === mi;
            const dim = !matches(s);
            const cap = enrolled[s.id];
            return <button key={s.id + mi} type="button"
              className={`tt-block d${deptIndex(s) % 6} ${canEdit(s) ? 'draggable' : ''} ${isDragging ? 'lifted' : ''} ${isPending ? 'pending-origin' : ''} ${dim ? 'dim' : ''} ${selected?.sectionId === s.id ? 'selected' : ''} ${(m.end - m.start) * PX < 58 ? 'short' : ''}`}
              style={{top:(m.start-OPEN)*PX + 2, height:(m.end-m.start)*PX - 4, insetInlineStart:`calc(${lane/lanes*100}% + 4px)`, width:`calc(${100/lanes}% - 8px)`, animationDelay:`${Math.min(i, 24) * 22}ms`}}
              onPointerDown={e => onPointerDown(e, s, mi, m)} onPointerMove={onPointerMove} onPointerUp={e => onPointerUp(e, s, mi)} onPointerCancel={() => setDrag(null)}
              onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSelected({sectionId:s.id, mi}); } }}
              aria-label={`${courseName(s.course_id)} ${s.id}, ${days[m.day]} ${time(m.start)}–${time(m.end)}, ${s.room_id}`}>
              {canEdit(s) && <GripVertical className="tt-grip" size={13}/>}
              <strong>{s.course_id}<span>{s.id}</span></strong>
              <span className="tt-name">{courseName(s.course_id)}</span>
              <small><bdi>{time(m.start)}–{time(m.end)}</bdi> · {s.room_id}{cap !== undefined ? <> · {cap}/{s.capacity}</> : null}</small>
            </button>;
          })}
          {drag?.moved && drag.target?.day === day && dragSection && (() => { const p:any = dragPreview; const state = !p ? '' : p === 'loading' ? 'checking' : p.error || !p.feasible ? 'bad' : 'ok'; return <div className={`tt-ghost ${state}`} style={{top:(drag.target.start-OPEN)*PX + 2, height:drag.duration*PX - 4}}>
            <strong>{dragSection.course_id} <bdi>{time(drag.target.start)}–{time(drag.target.start + drag.duration)}</bdi></strong>
            <small>{state === 'checking' ? t('Checking…','جارٍ التحقق…') : state === 'ok' ? <>{t('Fits','مناسب')} · {p.recovered_hours > 0 ? '+' : ''}{number(p.recovered_hours)} h</> : state === 'bad' ? (p.error || `${p.new_issue_count} ${t('conflicts','تعارضات')}`) : t('Release to stage the move','أفلت لتجهيز النقل')}</small>
          </div>; })()}
          {pending && pending.target.day === day && pendingSection && <div className={`tt-ghost staged ${pendingPreview && pendingPreview !== 'loading' && !(pendingPreview as any).error && (pendingPreview as any).feasible ? 'ok' : pendingPreview === 'loading' || !pendingPreview ? 'checking' : 'bad'}`} style={{top:(pending.target.start-OPEN)*PX + 2, height:(pendingSection.meetings[pending.mi].end - pendingSection.meetings[pending.mi].start)*PX - 4}}>
            <strong>{pendingSection.course_id} <bdi>{time(pending.target.start)}</bdi></strong><small>{t('Proposed','مقترح')}</small></div>}
        </div>)}
      </div></div>

      <aside className={`tt-drawer ${selectedSection ? 'open' : ''}`} aria-hidden={!selectedSection}><div className="tt-drawer-inner">
        {selectedSection && (() => { const s = selectedSection, c = courses[s.course_id], p = professors[s.professor_id], r = rooms[s.room_id], cap = enrolled[s.id]; return <>
          <div className="tt-drawer-head"><span className={`tt-dot d${deptIndex(s) % 6}`}/><div><small>{c?.department} · {s.course_id}</small><h3>{courseName(s.course_id)}</h3></div><button aria-label={t('Close','إغلاق')} onClick={() => setSelected(null)}><X size={18}/></button></div>
          <div className="tt-facts">
            <div><UserRound size={15}/><span>{p?.name || s.professor_id}</span></div>
            <div><MapPin size={15}/><span>{r ? `${r.name} · ${r.capacity} ${t('seats','مقعد')}` : s.room_id}</span></div>
            {cap !== undefined && <div className="tt-capacity"><UsersRound size={15}/><span>{cap} / {s.capacity} {t('enrolled','مسجل')}</span><i><b style={{width:`${Math.min(100, cap / s.capacity * 100)}%`}}/></i></div>}
          </div>
          <h4>{t('Meetings','المحاضرات')}</h4>
          <div className="tt-meetings">{s.meetings.map((m:R, i:number) => <button key={i} className={selected!.mi === i ? 'active' : ''} onClick={() => setSelected({sectionId:s.id, mi:i})}><span>{days[m.day]}</span><bdi>{time(m.start)}–{time(m.end)}</bdi></button>)}</div>
          {canEdit(s) && <div className="tt-move">
            <h4>{t('Move this meeting','نقل هذه المحاضرة')}</h4>
            <div className="two-inputs"><label>{t('Day','اليوم')}<select value={formDay} onChange={e => setFormDay(Number(e.target.value))}>{days.map((d, i) => <option key={d} value={i}>{d}</option>)}</select></label>
            <label>{t('Start','البداية')}<select value={formStart} onChange={e => setFormStart(Number(e.target.value))}>{Array.from({length:(CLOSE-OPEN)/SNAP}, (_, i) => OPEN + i*SNAP).filter(v => v + (s.meetings[selected!.mi].end - s.meetings[selected!.mi].start) <= CLOSE).map(v => <option key={v} value={v}>{time(v)}</option>)}</select></label></div>
            <div className="tt-chips"><PreviewChips p={formPreview}/></div>
            <div className="inline"><button className="secondary" onClick={() => void preview(s.id, selected!.mi, {day:formDay, start:formStart})}><ShieldCheck size={15}/>{t('Check','تحقق')}</button>
            <button className="primary" disabled={formDay === s.meetings[selected!.mi].day && formStart === s.meetings[selected!.mi].start} onClick={() => { const m = s.meetings[selected!.mi]; setPending({sectionId:s.id, mi:selected!.mi, origin:{day:m.day, start:m.start}, target:{day:formDay, start:formStart}}); void preview(s.id, selected!.mi, {day:formDay, start:formStart}); }}><Arrow size={15}/>{t('Stage move','تجهيز النقل')}</button></div>
          </div>}
          {role !== 'student' && <button className="text-button tt-open" onClick={() => onOpenChanges(s.id, selected!.mi, s.meetings[selected!.mi])}>{t('Open in change requests','فتح في طلبات التغيير')}<Arrow size={14}/></button>}
        </>; })()}
      </div></aside>
    </div> : <>
      <div className="search-field"><Search size={16}/><input placeholder={t('Find a course or section…','ابحث عن مقرر أو شعبة…')} value={query} onChange={e => setQuery(e.target.value)}/></div>
      <div className="table-scroll"><table><thead><tr><th>{t('Section','الشعبة')}</th><th>{t('Course','المقرر')}</th><th>{t('Meetings','المواعيد')}</th><th>{t('Room','القاعة')}</th><th>{t('Faculty','الأستاذ')}</th><th>{t('Enrolled','المسجلون')}</th></tr></thead>
      <tbody>{visible.filter(matches).map(s => <tr key={s.id} onClick={() => { setView('week'); setSelected({sectionId:s.id, mi:0}); }}><td><span className={`tt-dot d${deptIndex(s) % 6}`}/><strong>{s.id}</strong></td><td>{courseName(s.course_id)}</td><td>{s.meetings.map((m:R, i:number) => <span className="meeting-line" key={i}>{days[m.day]} <bdi>{time(m.start)}–{time(m.end)}</bdi></span>)}</td><td>{s.room_id}</td><td>{professors[s.professor_id]?.name || s.professor_id}</td><td>{enrolled[s.id] ?? '—'} / {s.capacity}</td></tr>)}</tbody></table></div></>}

    {pending && pendingSection && <div className="tt-dock" role="region" aria-label={t('Proposed move','النقل المقترح')}>
      <div className="tt-dock-move"><span className={`tt-dot d${deptIndex(pendingSection) % 6}`}/><div><strong>{pendingSection.course_id} · {pendingSection.id}</strong><small>{days[pending.origin.day]} <bdi>{time(pending.origin.start)}</bdi> <Arrow size={12}/> {days[pending.target.day]} <bdi>{time(pending.target.start)}</bdi></small></div></div>
      <div className="tt-chips"><PreviewChips p={pendingPreview}/></div>
      {pendingPreview && pendingPreview !== 'loading' && (pendingPreview as any).new_issues?.length > 0 && <div className="tt-issues">{(pendingPreview as any).new_issues.slice(0, 3).map((i:R, n:number) => <span key={n}><TriangleAlert size={12}/>{issueLabel(i.code)} · {i.records.slice(0, 3).join(', ')}</span>)}</div>}
      <input aria-label={t('Reason','السبب')} placeholder={t('Reason (optional)','السبب (اختياري)')} value={reason} onChange={e => setReason(e.target.value)} maxLength={1000}/>
      {error && <span className="tt-chip bad">{error}</span>}
      <div className="tt-dock-actions"><button className="secondary" onClick={() => setPending(null)}><Undo2 size={15}/>{t('Undo','تراجع')}</button>
      <button className="primary" disabled={submitting || pendingPreview === 'loading'} onClick={() => void submit()}>{submitting ? <LoaderCircle size={15} className="spin"/> : (pendingPreview as any)?.feasible ? <Send size={15}/> : <Check size={15}/>}{(pendingPreview as any)?.feasible ? t('Submit change request','إرسال طلب التغيير') : t('Submit & see alternatives','إرسال وعرض البدائل')}</button></div>
      <small className="tt-dock-note">{t('Nothing changes until the proposal is approved and published.','لا يتغير شيء حتى يُعتمد المقترح ويُنشر.')}</small>
    </div>}
  </section>;
}
