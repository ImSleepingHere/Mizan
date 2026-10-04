import React, {useMemo, useState} from 'react';
import {Clock3, MapPin, UserRound, BellRing, CalendarDays, Activity, ShieldCheck, Search, Star, Info, MoveRight, MoveLeft} from 'lucide-react';
import {time, number, useDraft} from './api';
import {SCALES} from './grade';
import {Metric} from './ui';

type R = Record<string, any>;
type M = {day:number, start:number, end:number};

function riyadhNow(){
  const parts = new Intl.DateTimeFormat('en-US', {timeZone:'Asia/Riyadh', weekday:'short', hour:'2-digit', minute:'2-digit', hour12:false}).formatToParts(new Date());
  const get = (k:string) => parts.find(p => p.type === k)?.value || '';
  return {day:['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].indexOf(get('weekday')), minutes:(Number(get('hour')) % 24) * 60 + Number(get('minute'))};
}

/** Gaps (minutes) and campus days of a set of weekly meetings. */
export function weekShape(meetings:M[]){
  const byDay = new Map<number, M[]>();
  meetings.forEach(m => byDay.set(m.day, [...(byDay.get(m.day) || []), m]));
  let gap = 0; const breaks:{day:number, from:number, to:number}[] = [];
  byDay.forEach(list => { list.sort((a, b) => a.start - b.start); list.slice(1).forEach((m, i) => { const g = m.start - list[i].end; if (g > 0) { gap += g; breaks.push({day:m.day, from:list[i].end, to:m.start}); } }); });
  return {gap, days:byDay.size, breaks:breaks.sort((a, b) => (b.to - b.from) - (a.to - a.from))};
}

const hours = (min:number, ar:boolean) => min % 60 === 0 ? `${min / 60} ${ar ? 'ساعة' : min === 60 ? 'hour' : 'hours'}` : `${number(min / 60)} ${ar ? 'ساعة' : 'h'}`;

export function StudentWeek({data, ar, days, courseName, eligible, timetable}:{data:R, ar:boolean, days:string[], courseName:(id:string)=>string, eligible:R[], timetable:React.ReactNode}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const sections:R[] = data.sections || [];
  const prof = (id:string) => (data.professors || []).find((p:R) => p.id === id)?.name || t('Instructor to be confirmed','المحاضر سيُحدد');
  const room = (id:string) => (data.rooms || []).find((r:R) => r.id === id)?.name || id;
  const meetings = sections.flatMap(s => s.meetings.map((m:R) => ({...m, s})));
  const now = riyadhNow();
  const order = (m:R) => ((m.day - now.day + 7) % 7) * 1440 + m.start - (m.day === now.day ? now.minutes : 0);
  const upcoming = meetings.filter(m => !(m.day === now.day && m.end <= now.minutes)).sort((a, b) => order(a) - order(b));
  const next = upcoming[0];
  const today = meetings.filter(m => m.day === now.day).sort((a, b) => a.start - b.start);
  const shape = weekShape(meetings);
  const pm = data.personal_metrics || {};
  const Arrow = ar ? MoveLeft : MoveRight;
  const changes:R[] = data.recent_changes || [];

  return <>
    <section className="panel today">
      <div className="today-next">{next ? <><span className="eyebrow-label">{next.day === now.day && next.start <= now.minutes ? t('Now','الآن') : next.day === now.day ? t('Next class today','المحاضرة التالية اليوم') : t(`Next class · ${days[next.day]}`, `المحاضرة التالية · ${days[next.day]}`)}</span>
        <h2>{courseName(next.s.course_id)}</h2>
        <div className="today-facts"><span><Clock3 size={15}/><bdi>{time(next.start)}–{time(next.end)}</bdi></span><span><MapPin size={15}/>{room(next.s.room_id)}</span><span><UserRound size={15}/>{prof(next.s.professor_id)}</span></div></>
        : <><span className="eyebrow-label">{t('This week','هذا الأسبوع')}</span><h2>{t('No classes scheduled','لا توجد محاضرات')}</h2></>}</div>
      <div className="today-list"><h3>{t('Today','اليوم')} · {days[now.day] || t('Weekend','عطلة نهاية الأسبوع')}</h3>
        {today.length ? <ol>{today.map((m, i) => <li key={i} className={m.end <= now.minutes ? 'past' : ''}><bdi>{time(m.start)}</bdi><span>{courseName(m.s.course_id)}</span><small>{m.s.room_id}</small></li>)}</ol>
          : <p className="muted">{t('No classes today.','لا توجد محاضرات اليوم.')}</p>}</div>
    </section>
    {changes.length > 0 && <section className="panel changes-notice" role="status"><h3><BellRing size={16}/>{t('Your timetable changed in the latest published version','تغيّر جدولك في آخر إصدار منشور')}</h3>
      <ul>{changes.map(c => <li key={c.section_id}><strong>{courseName(c.after.course_id)}</strong>: {c.before ? c.before.meetings.map((m:R) => `${days[m.day]} ${time(m.start)}`).join(', ') : t('new','جديدة')} <Arrow size={13}/> {c.after.meetings.map((m:R) => `${days[m.day]} ${time(m.start)}`).join(', ')}{c.before && c.before.room_id !== c.after.room_id ? ` · ${t('room','القاعة')} ${c.after.room_id}` : ''}</li>)}</ul></section>}
    {timetable}
    <section className="panel week-numbers"><div className="panel-heading"><div><h2>{t('Your week in numbers','أسبوعك بالأرقام')}</h2><p>{t('What each number means, and what is behind it.','معنى كل رقم وما وراءه.')}</p></div></div>
      <div className="metrics-grid"><Metric ar={ar} grade={{value:pm.gap_minutes / 60, scale:SCALES.personalGapHours}} label={t('Waiting between classes','الانتظار بين المحاضرات')} value={number(pm.gap_minutes / 60)} unit={t('h / week','س / أسبوع')} icon={<Clock3/>}
          foot={shape.breaks[0] ? t(`Biggest break: ${hours(shape.breaks[0].to - shape.breaks[0].from, false)} on ${days[shape.breaks[0].day]} (${time(shape.breaks[0].from)}–${time(shape.breaks[0].to)}). Under 1 h a week is good; 6 h or more is critical.`, `أطول استراحة: ${hours(shape.breaks[0].to - shape.breaks[0].from, true)} يوم ${days[shape.breaks[0].day]} (${time(shape.breaks[0].from)}–${time(shape.breaks[0].to)}). أقل من ساعة أسبوعياً جيد؛ 6 ساعات فأكثر حرجة.`) : t('No waiting between classes.','لا انتظار بين المحاضرات.')}/>
        <Metric ar={ar} grade={{value:pm.campus_days, scale:SCALES.campusDays}} label={t('Campus days','أيام الحضور')} value={String(pm.campus_days ?? shape.days)} icon={<CalendarDays/>}
          foot={t(`You come in on ${[...new Set(meetings.map(m => m.day))].sort().map(d => days[d]).join(', ')}. 2–3 days is good; 5 is critical.`, `تحضر أيام ${[...new Set(meetings.map(m => m.day))].sort().map(d => days[d]).join('، ')}. يومان إلى ثلاثة جيد؛ 5 أيام حرجة.`)}/>
        <Metric ar={ar} grade={{value:pm.longest_gap, scale:SCALES.longestGap}} label={t('Longest single break','أطول استراحة واحدة')} value={String(pm.longest_gap ?? 0)} unit={t('min','دقيقة')} icon={<Activity/>}
          foot={t('One break, not the weekly total. 45 min or less is good; 4 hours is critical.','استراحة واحدة وليست المجموع الأسبوعي. 45 دقيقة أو أقل جيد؛ 4 ساعات حرجة.')}/>
        <Metric ar={ar} grade={{value:pm.score, scale:SCALES.quality}} label={t('Week quality','جودة الأسبوع')} value={pm.score === null || pm.score === undefined ? '—' : String(pm.score)} unit="/100" icon={<ShieldCheck/>}
          foot={t('Combines waiting time (40%), longest break (20%), campus days (15%), day length (15%) and regularity (10%).','يجمع وقت الانتظار (40٪) وأطول استراحة (20٪) وأيام الحضور (15٪) وطول اليوم (15٪) والانتظام (10٪).')}/></div>
    </section>
    <EligibleSections eligible={eligible} meetings={meetings} ar={ar} days={days} courseName={courseName} sid={data.id}/>
  </>;
}

function EligibleSections({eligible, meetings, ar, days, courseName, sid}:{eligible:R[], meetings:M[], ar:boolean, days:string[], courseName:(id:string)=>string, sid:string}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const [q, setQ] = useState(''), [shortlist, setShortlist] = useDraft<string[]>(`shortlist:${sid}`, []), [all, setAll] = useState(false);
  const [onlyShort, setOnlyShort] = useState(false);
  const base = weekShape(meetings);
  const groups = useMemo(() => {
    const map = new Map<string, R[]>();
    eligible.filter(e => !q || `${e.course.id} ${e.course.name} ${e.course.name_ar} ${e.section_id} ${e.professor_name || ''}`.toLowerCase().includes(q.toLowerCase()))
      .filter(e => !onlyShort || shortlist.includes(e.section_id))
      .forEach(e => { const after = weekShape([...meetings, ...e.meetings]); map.set(e.course.id, [...(map.get(e.course.id) || []), {...e, addedDays:after.days - base.days, gapChange:after.gap - base.gap}]); });
    map.forEach(list => list.sort((a, b) => a.addedDays - b.addedDays || a.gapChange - b.gapChange));
    return [...map.entries()];
  }, [eligible, q, onlyShort, shortlist, meetings]);
  return <section className="panel eligible"><div className="panel-heading"><div><h2>{t('Sections you could add','شعب يمكنك إضافتها')}</h2>
    <p>{t('Courses you are eligible for, with a section that fits your current week. Suggestions only: registration happens in Edugate.','مقررات أنت مؤهل لها وشعب تناسب أسبوعك الحالي. اقتراحات فقط: التسجيل يتم عبر البوابة الإلكترونية.')}</p></div></div>
    <div className="queue-bar"><div className="search-field"><Search size={15}/><input aria-label={t('Search sections','البحث في الشعب')} placeholder={t('Course, section or instructor…','مقرر أو شعبة أو محاضر…')} value={q} onChange={e => setQ(e.target.value)}/></div>
      <label className="ra-check"><input type="checkbox" checked={onlyShort} onChange={e => setOnlyShort(e.target.checked)}/>{t(`Shortlist only (${shortlist.length})`, `القائمة المختصرة فقط (${shortlist.length})`)}</label></div>
    {!groups.length ? <p className="queue-empty">{q || onlyShort ? t('No sections match. Clear the search to see all options.','لا توجد شعب مطابقة. امسح البحث لعرض جميع الخيارات.') : t('No additional sections fit your week right now.','لا توجد شعب إضافية تناسب أسبوعك حالياً.')}</p>
    : groups.slice(0, all || q ? groups.length : 4).map(([cid, list]) => <div className="course-group" key={cid}><h3>{courseName(cid)} <small>{cid} · {list.length} {t(list.length === 1 ? 'section' : 'sections', 'شعب')}</small></h3>
      <div className="option-rows">{list.map(e => <div className="option-row" key={e.section_id}>
        <button type="button" className={`star ${shortlist.includes(e.section_id) ? 'on' : ''}`} aria-pressed={shortlist.includes(e.section_id)} aria-label={t('Add to shortlist','إضافة للقائمة المختصرة')} onClick={() => setShortlist(s => s.includes(e.section_id) ? s.filter(x => x !== e.section_id) : [...s, e.section_id])}><Star size={15}/></button>
        <div><strong>{e.section_id}</strong><span>{e.meetings.map((m:R) => `${days[m.day]} ${time(m.start)}–${time(m.end)}`).join(' · ')}</span><small>{e.professor_name} · {e.room_id}</small></div>
        <span className={`tt-chip ${e.addedDays > 0 ? 'warn' : 'ok'}`}>{e.addedDays > 0 ? t(`+${e.addedDays} campus day`, `+${e.addedDays} يوم حضور`) : t('No extra campus day','دون يوم حضور إضافي')}</span>
        <span className={`tt-chip ${e.gapChange > 0 ? 'warn' : e.gapChange < 0 ? 'ok' : ''}`}>{e.gapChange === 0 ? t('Waiting time unchanged','وقت الانتظار دون تغيير') : `${e.gapChange > 0 ? '+' : ''}${number(e.gapChange / 60)} ${t('h waiting / week','س انتظار / أسبوع')}`}</span>
        <span className="tt-chip">{e.seats} {t('seats left','مقعد متبقٍ')}</span></div>)}</div></div>)}
    {!all && !q && groups.length > 4 && <button type="button" className="secondary" onClick={() => setAll(true)}>{t(`Show ${groups.length - 4} more courses`, `عرض ${groups.length - 4} مقررات أخرى`)}</button>}
    <p className="muted"><Info size={13}/>{t('Best fit first: fewest extra campus days, then least extra waiting.','الأنسب أولاً: أقل أيام حضور إضافية ثم أقل انتظار إضافي.')}</p>
  </section>;
}
