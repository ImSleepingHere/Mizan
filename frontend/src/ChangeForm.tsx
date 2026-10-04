import React, {useEffect, useMemo, useState} from 'react';
import {ShieldCheck, Send, LoaderCircle, TriangleAlert, Clock3, UsersRound, MoveRight, MoveLeft, Info} from 'lucide-react';
import {api, time, number, useDraft} from './api';
import {ConflictList} from './Conflicts';

type R = Record<string, any>;
export type Handoff = {sectionId:string, mi:number, day:number, start:number};

/** Choose a change → preview its impact (nothing saved) → send it for review. Spec flow standardised after UX review I03/I12. */
export function ChangeForm({sid, data, ar, days, courseName, handoff, onSubmitted, onShow}:{sid:string, data:R, ar:boolean, days:string[],
  courseName:(id:string)=>string, handoff:Handoff|null, onSubmitted:(p:R)=>void, onShow:(ids:string[])=>void}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const sections:R[] = data.sections || [];
  const [draft, setDraft] = useDraft<{sectionId:string, mi:number, day:number, start:number, reason:string}>(`change:${sid}`,
    {sectionId:sections[0]?.id || '', mi:0, day:sections[0]?.meetings[0]?.day ?? 0, start:sections[0]?.meetings[0]?.start ?? 480, reason:''});
  const [preview, setPreview] = useState<R|null>(null), [busy, setBusy] = useState(''), [error, setError] = useState('');
  useEffect(() => { if (handoff) { setDraft(d => ({...d, sectionId:handoff.sectionId, mi:handoff.mi, day:handoff.day, start:handoff.start})); } }, [handoff]);
  const section = sections.find(s => s.id === draft.sectionId) || sections[0];
  const current = section?.meetings[Math.min(draft.mi, (section?.meetings.length || 1) - 1)];
  const duration = current ? current.end - current.start : 60;
  const close = data.policy?.close_minute ?? 1080, open = data.policy?.open_minute ?? 480;
  const starts = useMemo(() => Array.from({length:Math.max(0, Math.floor((close - open) / 15) + 1)}, (_, i) => open + i * 15).filter(v => v + duration <= close), [open, close, duration]);
  const unchanged = !!current && current.day === draft.day && current.start === draft.start;
  const Arrow = ar ? MoveLeft : MoveRight;
  const set = (patch:Partial<typeof draft>) => { setDraft(d => ({...d, ...patch})); setPreview(null); setError(''); };

  async function runPreview(){
    setBusy('preview'); setError(''); setPreview(null);
    try { setPreview(await api(`/scenarios/${sid}/preview-change`, {section_id:section.id, meeting_index:draft.mi, day:draft.day, start:draft.start, alternatives:true})); }
    catch (e) { setError((e as Error).message); } finally { setBusy(''); }
  }
  async function send(){
    setBusy('send'); setError('');
    try { const p = await api(`/scenarios/${sid}/changes`, {section_id:section.id, meeting_index:draft.mi, day:draft.day, start:draft.start, reason:draft.reason.trim()});
      setPreview(null); setDraft(d => ({...d, reason:''})); onSubmitted({...p, reason:draft.reason.trim()}); }
    catch (e) { setError((e as Error).message); } finally { setBusy(''); }
  }
  async function propose(alt:R){
    setBusy('alt'); setError('');
    try { const p = await api(`/scenarios/${sid}/alternative`, {section:alt.section, reason:draft.reason.trim() || 'Feasible alternative to the requested move'}); onSubmitted(p); }
    catch (e) { setError((e as Error).message); } finally { setBusy(''); }
  }

  if (!section) return <p>{t('There are no sections you can change in this timetable.','لا توجد شعب يمكنك تغييرها في هذا الجدول.')}</p>;
  const reasonOk = draft.reason.trim().length >= 3;
  return <form className="change-form" onSubmit={e => { e.preventDefault(); void runPreview(); }}>
    <label>{t('Class','المقرر')}<select value={section.id} onChange={e => { const s = sections.find(x => x.id === e.target.value); set({sectionId:e.target.value, mi:0, day:s?.meetings[0]?.day ?? 0, start:s?.meetings[0]?.start ?? 480}); }}>
      {sections.map(s => <option key={s.id} value={s.id}>{courseName(s.course_id)} · {s.id} · {s.meetings.map((m:R) => `${days[m.day].slice(0, 3)} ${time(m.start)}`).join(', ')}</option>)}</select></label>
    <label>{t('Meeting to move','المحاضرة المراد نقلها')}<select value={draft.mi} onChange={e => { const m = section.meetings[Number(e.target.value)]; set({mi:Number(e.target.value), day:m.day, start:m.start}); }}>
      {section.meetings.map((m:R, i:number) => <option key={i} value={i}>{days[m.day]} · {time(m.start)}–{time(m.end)}</option>)}</select></label>
    <div className="two-inputs"><label>{t('New day','اليوم الجديد')}<select value={draft.day} onChange={e => set({day:Number(e.target.value)})}>{days.map((d, i) => <option key={d} value={i}>{d}</option>)}</select></label>
      <label>{t('New start time','وقت البداية الجديد')}<select value={draft.start} onChange={e => set({start:Number(e.target.value)})}>{starts.map(v => <option key={v} value={v}>{time(v)}</option>)}</select></label></div>
    <div className="change-summary" aria-live="polite">
      <span>{days[current.day]} <bdi>{time(current.start)}–{time(current.end)}</bdi></span><Arrow size={15}/>
      <strong>{days[draft.day]} <bdi>{time(draft.start)}–{time(draft.start + duration)}</bdi></strong>
      <small>{t(`ends ${time(draft.start + duration)} · ${duration} min, same as now · teaching hours ${time(open)}–${time(close)}`, `تنتهي ${time(draft.start + duration)} · ${duration} دقيقة كما هي · ساعات التدريس ${time(open)}–${time(close)}`)}</small>
    </div>
    <label><span>{t('Reason','السبب')} <em className="required">{t('required','مطلوب')}</em></span>
      <textarea aria-label="Reason" value={draft.reason} onChange={e => setDraft(d => ({...d, reason:e.target.value}))} minLength={3} maxLength={1000}
        placeholder={t('e.g. Lab clash for second-year students on Sunday mornings','مثال: تعارض المختبر لطلاب السنة الثانية صباح الأحد')}/></label>
    {unchanged && <p className="form-note"><Info size={14}/>{t('This is the meeting’s current time. Choose a different day or start time.','هذا هو الموعد الحالي للمحاضرة. اختر يوماً أو وقتاً مختلفاً.')}</p>}
    <div className="ra-actions"><button className="secondary" disabled={!!busy || unchanged}>{busy === 'preview' ? <LoaderCircle size={16} className="spin"/> : <ShieldCheck size={16}/>}{t('Preview impact','معاينة الأثر')}</button></div>
    {error && <div role="alert" className="alert error"><TriangleAlert size={16}/><span>{error}</span></div>}
    {preview && <div className="change-result">
      <div className="tt-chips">
        {preview.feasible ? <span className="tt-chip ok"><ShieldCheck size={13}/>{t('No new conflicts','لا تعارضات جديدة')}</span> : preview.blocked_by_existing ? <span className="tt-chip warn"><TriangleAlert size={13}/>{t(`Adds no conflicts, but the timetable already has ${preview.existing_issue_count}`, `لا يضيف تعارضات، لكن في الجدول ${preview.existing_issue_count} تعارضاً مسبقاً`)}</span> : <span className="tt-chip bad"><TriangleAlert size={13}/>{preview.new_issue_count} {t('new conflicts','تعارضات جديدة')}</span>}
        <span className={`tt-chip ${preview.recovered_hours > 0 ? 'ok' : preview.recovered_hours < 0 ? 'bad' : ''}`}><Clock3 size={13}/><bdi>{preview.recovered_hours > 0 ? '+' : ''}{number(preview.recovered_hours)}</bdi> {t('student-h / week','ساعة طالب / أسبوع')}</span>
        <span className="tt-chip"><UsersRound size={13}/>{number(preview.benefiting)} {t('better off','مستفيد')}</span>
        <span className={`tt-chip ${preview.worsened ? 'warn' : ''}`}><UsersRound size={13}/>{number(preview.worsened)} {t('worse off','متضرر')}</span>
      </div>
      <ConflictList issues={preview.new_issues || []} ar={ar} onShow={onShow}/>
      {preview.alternatives?.length > 0 && <><h3>{t('Feasible alternatives','بدائل ممكنة')}</h3>{preview.alternatives.map((a:R, i:number) => <div className="alternative" key={i}>
        <div>{a.section.meetings.map((m:R, j:number) => <span className="meeting-line" key={j}>{days[m.day]} <bdi>{time(m.start)}–{time(m.end)}</bdi></span>)}<small>{number(a.recovered_hours)} {t('hours recovered','ساعة مستعادة')} · {a.worsened} {t('worse off','متضرر')} · {a.section.room_id}</small></div>
        <button type="button" className="secondary" disabled={!!busy} onClick={() => void propose(a)}>{t('Propose this','اقتراح هذا البديل')}</button></div>)}</>}
      {preview.blocked_by_existing && <p className="form-note"><Info size={14}/>{t('This timetable must be free of conflicts before any change can be approved. Fix the existing conflicts first (Semester lab → Validation findings).','يجب أن يخلو الجدول من التعارضات قبل اعتماد أي تغيير. عالج التعارضات الموجودة أولاً (مختبر الفصل ← نتائج التحقق).')}</p>}
      {!preview.feasible && !preview.blocked_by_existing && !preview.alternatives?.length && <p className="form-note"><Info size={14}/>{t('No conflict-free alternative was found for this class within its current days and room.','لم يُعثر على بديل خالٍ من التعارضات لهذه الشعبة ضمن أيامها وقاعتها الحالية.')}</p>}
      <div className="ra-actions">
        {!reasonOk && <small className="muted">{t('Add a reason to send this request.','أضف سبباً لإرسال الطلب.')}</small>}
        <button type="button" className={preview.feasible ? 'primary' : 'secondary'} disabled={!!busy || !reasonOk} onClick={() => void send()}>{busy === 'send' ? <LoaderCircle size={16} className="spin"/> : <Send size={16}/>}
          {preview.feasible ? t('Send for review','إرسال للمراجعة') : t('Send anyway, marked as conflicting','إرسال رغم التعارض')}</button></div>
      <small className="tt-dock-note">{t('Previewing saves nothing. Sending creates a request for the scheduling committee; nothing changes until it is approved and published.','المعاينة لا تحفظ شيئاً. الإرسال ينشئ طلباً للجنة الجدولة، ولا يتغير شيء حتى يُعتمد ويُنشر.')}</small>
    </div>}
  </form>;
}
