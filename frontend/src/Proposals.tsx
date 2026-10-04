import React, {useMemo, useState} from 'react';
import {GitCompareArrows, ArrowUpRight, ArrowRight, ArrowLeft, Check, ShieldCheck, Search, RefreshCw, TriangleAlert, Sparkles, Clock3, UsersRound, Info} from 'lucide-react';
import {time, number, useDraft} from './api';
import {SCALES, gradeVars} from './grade';
import {Metric, Delta, Badge, Stations} from './ui';
import {ConflictList} from './Conflicts';

type R = Record<string, any>;

export function relative(iso:string, ar:boolean){
  const diff = (new Date(iso).getTime() - Date.now()) / 1000;
  const fmt = new Intl.RelativeTimeFormat(ar ? 'ar' : 'en', {numeric:'auto'});
  for (const [unit, secs] of [['day', 86400], ['hour', 3600], ['minute', 60]] as const) if (Math.abs(diff) >= secs) return fmt.format(Math.round(diff / secs), unit);
  return fmt.format(Math.round(diff), 'second');
}

/** "Dr. Faculty 01 asks to move Computing Studio 21 (S087): Sunday 10:00 → Tuesday 11:15". */
export function headline(p:R, ar:boolean, days:string[], courseName:(id:string)=>string){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const changes:R[] = p.analysis?.comparison?.changes || [];
  const who = p.actor_name || p.actor || '';
  const first = changes[0];
  const moved = (c:R) => {
    if (!c?.before) return c ? `${c.after.meetings.map((m:R) => `${days[m.day]} ${time(m.start)}`).join(', ')}` : '';
    const i = c.after.meetings.findIndex((m:R, k:number) => m.day !== c.before.meetings[k]?.day || m.start !== c.before.meetings[k]?.start);
    if (i < 0) return c.before.room_id !== c.after.room_id ? `${t('room','القاعة')} ${c.before.room_id} → ${c.after.room_id}` : '';
    const a = c.before.meetings[i], b = c.after.meetings[i];
    return `${days[a.day]} ${time(a.start)} → ${days[b.day]} ${time(b.start)}`;
  };
  switch (p.kind) {
    case 'optimization': return {title:t('Semester improvement','تحسين الفصل الدراسي'), line:t(`${changes.length} sections move`, `${changes.length} شعب تتغير`)};
    case 'own_optimization': return {title:t(`${who}: improve own classes`, `${who}: تحسين مقرراته`), line:changes.map(c => `${c.section_id} ${moved(c)}`).join(' · ')};
    case 'placement': return {title:t(`New section of ${first ? courseName(first.after.course_id) : ''}`, `شعبة جديدة من ${first ? courseName(first.after.course_id) : ''}`), line:first ? moved(first) : ''};
    default: return {title:first ? t(`${who} asks to move ${courseName(first.after.course_id)} (${first.section_id})`, `${who} يطلب نقل ${courseName(first.after.course_id)} (${first.section_id})`) : t('Meeting change','تغيير موعد'),
      line:first ? moved(first) : ''};
  }
}

const TABS = ['decide', 'outdated', 'conflicts', 'history'] as const;
type Tab = typeof TABS[number];
const tabOf = (p:R):Tab => p.stale ? 'outdated' : p.status === 'invalid' ? 'conflicts' : ['recommended', 'approved'].includes(p.status) ? 'decide' : 'history';

export function ProposalQueue({items, ar, days, courseName, onOpen, sid, compact}:{items:R[], ar:boolean, days:string[], courseName:(id:string)=>string, onOpen:(p:R)=>void, sid:string, compact?:boolean}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const [tab, setTab] = useDraft<Tab>(`queue-tab:${sid}`, 'decide');
  const [q, setQ] = useState(''), [sort, setSort] = useState<'new'|'hours'|'harm'>('new');
  const counts = useMemo(() => Object.fromEntries(TABS.map(k => [k, items.filter(p => tabOf(p) === k).length])), [items]);
  const shown = useMemo(() => items.filter(p => compact || tabOf(p) === tab).filter(p => {
    if (!q) return true; const h = headline(p, ar, days, courseName); return `${h.title} ${h.line} ${p.id} ${p.actor_name} ${(p.analysis?.comparison?.changes || []).map((c:R) => c.section_id).join(' ')}`.toLowerCase().includes(q.toLowerCase());
  }).sort((a, b) => sort === 'hours' ? (b.analysis?.comparison?.recovered_hours || 0) - (a.analysis?.comparison?.recovered_hours || 0)
    : sort === 'harm' ? (b.analysis?.comparison?.worsened ?? b.analysis?.comparison?.adverse_count ?? 0) - (a.analysis?.comparison?.worsened ?? a.analysis?.comparison?.adverse_count ?? 0)
    : b.created.localeCompare(a.created)), [items, tab, q, sort, compact]);
  const tabLabel:Record<Tab, string> = {decide:t('Needs a decision','بانتظار القرار'), outdated:t('Outdated','قديمة'), conflicts:t('Conflicting','متعارضة'), history:t('History','السجل')};
  const Go = ar ? ArrowLeft : ArrowRight;
  return <div className="queue">
    {!compact && <div className="queue-bar">
      <div className="segmented queue-tabs" role="tablist">{TABS.map(k => <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? 'selected' : ''} onClick={() => setTab(k)}>{tabLabel[k]} <b>{counts[k]}</b></button>)}</div>
      <div className="search-field"><Search size={15}/><input aria-label={t('Search requests','البحث في الطلبات')} placeholder={t('Course, section or requester…','مقرر أو شعبة أو مقدم الطلب…')} value={q} onChange={e => setQ(e.target.value)}/></div>
      <select aria-label={t('Sort requests','ترتيب الطلبات')} value={sort} onChange={e => setSort(e.target.value as any)}><option value="new">{t('Newest first','الأحدث أولاً')}</option><option value="hours">{t('Most hours saved','الأكثر توفيراً للساعات')}</option><option value="harm">{t('Most students worse off','الأكثر ضرراً للطلاب')}</option></select>
    </div>}
    {!shown.length ? <p className="queue-empty">{q ? t(`No requests match “${q}”.`, `لا توجد طلبات تطابق «${q}».`) : tab === 'decide' ? t('Nothing is waiting for a decision.','لا يوجد ما ينتظر قراراً.') : t('Nothing here.','لا يوجد شيء هنا.')}</p>
    : <div className="proposal-list">{shown.map((p, i) => { const h = headline(p, ar, days, courseName); const c = p.analysis?.comparison || {}; const harm = c.worsened ?? c.adverse_count ?? 0;
      return <button className={`proposal-card ${p.stale ? 'is-stale' : ''}`} style={{animationDelay:`${i * 40}ms`}} key={p.id} onClick={() => onOpen(p)}>
        <div className="proposal-icon"><GitCompareArrows size={20}/></div>
        <div className="grow"><div className="inline"><h3>{h.title}</h3><Badge value={p.status} ar={ar} stale={p.stale}/></div>
          <p>{h.line && <bdi>{h.line}</bdi>}{h.line && ' · '}{relative(p.created, ar)} · v{p.base_revision}{p.stale ? ` → v${p.current_revision}` : ''}</p></div>
        <div className="savings" style={p.status === 'invalid' ? undefined : gradeVars(c.recovered_hours || 0, SCALES.recovered) as React.CSSProperties}>
          <strong>{p.status === 'invalid' ? '—' : number(c.recovered_hours || 0)}</strong><span>{t('student-hours / week','ساعة طالب / أسبوع')}</span>
          {harm > 0 && <em className="harm">{harm} {t('worse off','متضرر')}</em>}</div>
        <ArrowUpRight size={20}/></button>; })}</div>}
    {compact && items.length > shown.length && <span className="muted">{t('More in Recommendations','المزيد في التوصيات')} <Go size={13}/></span>}
  </div>;
}

const signed = (v:number) => `${v > 0 ? '+' : ''}${number(v)}`;

export function ProposalDetail({p, ar, days, courseName, role, busy, onDecision, onReevaluate, onNewOptimization, onAlternative, onShow}:{p:R, ar:boolean, days:string[],
  courseName:(id:string)=>string, role:string, busy:boolean, onDecision:(action:string)=>void, onReevaluate:()=>void, onNewOptimization:()=>void,
  onAlternative:(alt:R)=>void, onShow:(ids:string[])=>void}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const canSchedule = role === 'admin' || role === 'registrar';
  const a = p.analysis || {}, c = a.comparison || {};
  const harm = c.worsened ?? c.adverse_count ?? 0;
  const h = headline(p, ar, days, courseName);
  const local = p.kind !== 'optimization';
  const SectionTime = ({section}:{section:R}) => <>{section.meetings.map((m:R, i:number) => <span className="meeting-line" key={i}>{days[m.day]} <bdi>{time(m.start)}–{time(m.end)}</bdi></span>)}</>;
  const rows:[string, string, string?][] = [['gap_hours', t('Weekly gap hours (all students)','ساعات الفجوات الأسبوعية (جميع الطلاب)')], ['average_days', t('Average campus days','متوسط أيام الحضور')],
    ['score', t('Quality score','درجة الجودة')], ['long_gap_2h', t('Students with 2h+ gaps','طلاب بفجوات ساعتين فأكثر')],
    ['worst_decile_gap_hours', t('Worst-off 10%: weekly gap hours','الـ10٪ الأكثر تأثراً: ساعات الفجوات')], ['load_gini', t('Faculty load spread (Gini)','تفاوت العبء التدريسي (جيني)')], ['room_utilization', t('Room utilization %','استخدام القاعات %')]];
  const Arrow = ar ? ArrowLeft : ArrowRight;
  return <>
    <Stations status={p.status} ar={ar}/>
    <div className="detail-head"><h3>{h.title}</h3>{h.line && <p><bdi>{h.line}</bdi></p>}
      <div className="inline"><Badge value={p.status} ar={ar} stale={p.stale}/><span className="muted">{p.actor_name ? `${p.actor_name} · ` : ''}{p.created ? relative(p.created, ar) : ''} · {t('for version','للإصدار')} {p.base_revision} · {p.id.slice(0, 6)}</span></div></div>
    {p.stale && <div className="ra-block warn stale-block"><h4><TriangleAlert size={15}/>{t('This request is outdated','هذا الطلب قديم')}</h4>
      <p>{t(`It was checked against timetable version ${p.base_revision}; the timetable is now version ${p.current_revision}. It can’t be approved as it is.`, `تم فحصه على الإصدار ${p.base_revision} من الجدول، والجدول الآن في الإصدار ${p.current_revision}. لا يمكن اعتماده بصيغته الحالية.`)}</p>
      <div className="inline">{p.kind === 'change' && role !== 'chair' ? <button className="primary" disabled={busy} onClick={onReevaluate}><RefreshCw size={15}/>{t('Re-evaluate against current timetable','إعادة التقييم على الجدول الحالي')}</button>
        : canSchedule ? <button className="secondary" disabled={busy} onClick={onNewOptimization}><Sparkles size={15}/>{t('Run a new optimization','تشغيل تحسين جديد')}</button> : null}</div></div>}
    {p.reason && <p className="detail-reason">“{p.reason}”</p>}
    <div className="impact-split">
      <div><h4>{t('Benefit','الفائدة')}</h4><div className="metrics-grid compact">
        <Metric still ar={ar} grade={p.status === 'invalid' ? undefined : {value:c.recovered_hours || 0, scale:SCALES.recovered}} label={t('Student-hours saved / week','ساعات طلاب موفّرة أسبوعياً')} value={p.status === 'invalid' ? '—' : number(c.recovered_hours || 0)}/>
        <Metric still label={t('Students better off','طلاب استفادوا')} value={number(c.benefiting || 0)}/></div></div>
      <div><h4>{t('Harm and risk','الضرر والمخاطر')}</h4><div className="metrics-grid compact">
        <Metric still tone={harm ? 'caution' : 'calm'} label={t('Students worse off','طلاب تضرروا')} value={number(harm)} foot={harm ? t('Review who and by how much below.','راجع من تضرر ومقدار الضرر أدناه.') : t('No student’s week gets worse.','لا يسوء أسبوع أي طالب.')}/>
        <Metric still tone={a.conflict_count ? 'caution' : 'calm'} label={t('Conflicts','التعارضات')} value={String(a.conflict_count || 0)}/></div></div>
    </div>
    {a.status && <div className="evidence"><ShieldCheck size={18}/><div><strong>{a.status} · {a.runtime}s</strong><p>{t(a.search_scope || '', 'بحث محدود بالبدائل المسموح بها. النتيجة ليست إثباتاً للأمثلية على جميع الجداول الممكنة.')}</p></div></div>}
    {a.rule_items && <div className="ra-block"><h4>{t('Rules applied','القواعد المطبقة')}</h4><ul className="ra-rules">{a.rule_items.map((r:R) => <li key={r.id}>{t(r.en, r.ar)}</li>)}</ul>{(a.split_times || []).map((x:R) => <p key={x.section_id}>{x.section_id}: {t('meeting times split by rule','أوقات المحاضرات مختلفة بسبب القاعدة')} {x.reasons.map((r:R) => t(r.en, r.ar)).join(t('; ','؛ '))}</p>)}<p className="muted">{t('Independent rule check','التحقق المستقل من القواعد')}: {(a.rule_violations || []).length ? t('violations found','توجد مخالفات') : t('all rules met','جميع القواعد متحققة')}</p></div>}
    <h3>{t('What changes','ما الذي يتغير')}</h3><div className="changes-list">{(c.changes || []).map((x:R) => <div className="change-detail" key={x.section_id}><strong>{x.section_id}<small>{courseName(x.after.course_id)}</small></strong><div>{x.before ? <SectionTime section={x.before}/> : t('New section','شعبة جديدة')}</div><Arrow size={18}/><div className="new-times"><SectionTime section={x.after}/></div><span>{x.after.room_id}</span></div>)}</div>
    {a.issues?.length > 0 && <ConflictList issues={a.issues} ar={ar} onShow={onShow} title={t('Conflicts in the proposed timetable','التعارضات في الجدول المقترح')}/>}
    {c.adverse_students?.length > 0 && <details className="adverse"><summary>{t(`Students who would be worse off (${c.adverse_students.length})`, `الطلاب الذين سيتضررون (${c.adverse_students.length})`)}</summary>
      <p className="muted">{t('Change for each student: proposed minus current week.','التغير لكل طالب: الأسبوع المقترح مقارنة بالحالي.')}</p>
      <div className="adverse-list">{c.adverse_students.map((s:R) => <p key={s.id}><strong>{s.id}</strong> · <bdi>{signed(s.gap_delta)}</bdi> {t('gap minutes / week','دقيقة فجوة أسبوعياً')} · {s.days_delta > 0 ? <><bdi>{signed(s.days_delta)}</bdi> {t('campus day(s)','يوم حضور')}</> : t('no extra campus days','دون أيام حضور إضافية')}</p>)}</div></details>}
    {c.adverse_count > 0 && !c.adverse_students && <p className="muted"><UsersRound size={13}/> {t(`${c.adverse_count} students would have a longer week; the committee sees the details.`, `${c.adverse_count} طالباً سيطول أسبوعهم؛ تطّلع اللجنة على التفاصيل.`)}</p>}
    {a.before_metrics && <details className="context" open={!local}><summary>{local ? t('Whole-timetable context','السياق على مستوى الجدول كله') : t('Before and after, whole timetable','قبل وبعد على مستوى الجدول كله')}</summary>
      <div className="table-scroll comparison-table"><table><thead><tr><th>{t('Measure','المؤشر')}</th><th>{t('Current','الحالي')}</th><th>{t('Proposed','المقترح')}</th></tr></thead><tbody>{rows.map(([key, label]) => <tr key={key}><td>{label}</td><td>{a.before_metrics[key] ?? '—'}</td><td><Delta before={a.before_metrics[key]} after={a.after_metrics[key]} higherIsBetter={['score', 'room_utilization'].includes(key)}/></td></tr>)}</tbody></table></div>
      <p className="muted help-text"><Info size={13}/>{t('Worst-off 10%: average weekly gap hours of the tenth of students with the longest gaps (fairness). Faculty load spread: 0 means every instructor teaches the same share; higher means more uneven. Quality score: 0–100, combining gaps, longest gap, campus days, day length and regularity.','الـ10٪ الأكثر تأثراً: متوسط ساعات الفجوات لعُشر الطلاب الأطول فجوات (العدالة). تفاوت العبء: صفر يعني توزيعاً متساوياً بين المحاضرين، والأعلى يعني تفاوتاً أكبر. درجة الجودة: من 0 إلى 100 وتجمع الفجوات وأطول فجوة وأيام الحضور وطول اليوم والانتظام.')}</p></details>}
    {a.alternatives?.length > 0 && <><h3>{t('Feasible alternatives','بدائل ممكنة')}</h3>{a.alternatives.map((alt:R, i:number) => <div className="alternative" key={i}><div><SectionTime section={alt.section}/><small>{alt.recovered_hours} {t('hours recovered','ساعة مستعادة')} · {alt.worsened} {t('worse off','متضرر')}</small></div><button className="secondary" disabled={busy || role === 'chair'} onClick={() => onAlternative(alt)}>{t('Propose this','اقتراح هذا البديل')}</button></div>)}</>}
    {p.status === 'approved' && !p.stale && <div className="ra-block ask"><h4><Check size={15}/>{t('Approved · not yet published','معتمد · لم يُنشر بعد')}</h4><p>{t(`Publishing makes this the official timetable: version ${p.base_revision} → ${p.base_revision + 1}. It is checked again first.`, `النشر يجعل هذا الجدول رسمياً: الإصدار ${p.base_revision} ← ${p.base_revision + 1}. يُعاد التحقق منه أولاً.`)}</p></div>}
    {canSchedule && !p.stale && <div className="modal-actions">
      {['recommended', 'approved', 'invalid'].includes(p.status) && <button className="danger-text" disabled={busy} onClick={() => onDecision('reject')}>{t('Reject proposal','رفض المقترح')}</button>}
      {p.status === 'recommended' && <button className="primary" disabled={busy} onClick={() => onDecision('approve')}><Check size={17}/>{t('Approve proposal','اعتماد المقترح')}</button>}
      {p.status === 'approved' && <button className="primary" disabled={busy} onClick={() => onDecision('publish')}><ShieldCheck size={17}/>{t('Revalidate & publish locally','التحقق والنشر محلياً')}</button>}</div>}
    {!canSchedule && ['recommended', 'approved'].includes(p.status) && !p.stale && <p className="muted"><Clock3 size={13}/> {t('Waiting for the scheduling committee to decide.','بانتظار قرار لجنة الجدولة.')}</p>}
  </>;
}
