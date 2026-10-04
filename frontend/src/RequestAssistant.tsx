import React, {useEffect, useState} from 'react';
import {Sparkles, LoaderCircle, Check, X, Pencil, TriangleAlert, CircleHelp, ShieldCheck, Clock3, UsersRound, Send, CalendarClock, Info} from 'lucide-react';
import {api, time, number, useDraft} from './api';
import {SlotList} from './FreeSlotFinder';

type R = Record<string, any>;
const DAY_KEYS = ['sun','mon','tue','wed','thu'];

const TASKS:Record<string,[string,string]> = {
  move_meeting:['Move one class','نقل محاضرة'], reschedule_with_rules:['Reschedule with rules','إعادة الجدولة بقواعد'],
  find_common_slot:['Find a common free time','إيجاد وقت مشترك'], merge_sections:['Find a time to teach sections together','إيجاد وقت لدمج الشعب'],
  change_room:['Change room','تغيير القاعة'], change_duration:['Change session length','تغيير مدة المحاضرة'],
  change_delivery:['Change delivery mode','تغيير طريقة التدريس'], add_session:['Add a session','إضافة محاضرة'], balance_hours:['Balance hours','موازنة الساعات'],
};
const SCOPES:Record<string,[string,string]> = {own:['My classes','مقرراتي'], sections:['Named sections','الشعب المحددة'], cohort:['A student group','مجموعة طلاب'], semester:['Whole timetable','الجدول كاملاً']};
const DATES:Record<string,[string,string]> = {weekly:['Weekly timetable','الجدول الأسبوعي'], one_off:['One occasion','مرة واحدة'], date_range:['A date range','فترة زمنية']};
const GROUPS:Record<string,[string,string]> = {own_class_students:['students of my class','طلاب مقرري'], all_own_sections:['all my sections','جميع شعبي'], target_sections:['the named sections','الشعب المحددة'], cohort:['a student group','مجموعة طلاب']};

export function RequestAssistant({sid, ar, days, role, onSubmitted, onManual}:{sid:string, ar:boolean, days:string[], role:string, onSubmitted:(proposal:R)=>void, onManual?:()=>void}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const L = (pair?:[string,string]) => pair ? t(pair[0], pair[1]) : '';
  const [text, setText] = useDraft<string>(`ask:${sid}`, ''), [busy, setBusy] = useState(''), [error, setError] = useState('');
  const [model, setModel] = useState<boolean|null>(null);
  useEffect(() => { api('/agents/status').then(r => setModel(!!r.available)).catch(() => setModel(null)); }, []);
  const [req, setReq] = useState<R|null>(null), [result, setResult] = useState<R|null>(null), [edit, setEdit] = useState<R|null>(null);
  const day = (k:string) => days[DAY_KEYS.indexOf(k)] || k;
  const dayList = (ks:string[]) => ks.map(day).join(t(', ','، '));
  const minutes = (m:number) => `${m} ${t('min','دقيقة')}`;

  async function run(label:string, fn:()=>Promise<void>){ setBusy(label); setError(''); try { await fn(); } catch (e) { setError((e as Error).message); } finally { setBusy(''); } }
  const interpret = () => run('interpret', async () => { setResult(null); setEdit(null); setReq(await api('/requests/interpret', {scenario_id:sid, text})); });
  const confirm = () => run('confirm', async () => { const r = await api(`/requests/${req!.id}/confirm`, {}); setReq(r); setResult(r.result); });
  const cancel = () => run('cancel', async () => { await api(`/requests/${req!.id}/cancel`, {}); setReq(null); setResult(null); });
  const revise = () => run('revise', async () => { setReq(await api(`/requests/${req!.id}/revise`, {interpretation:edit})); setEdit(null); });
  const submitMove = (p:R) => run('submit', async () => {
    const proposal = await api(`/scenarios/${sid}/changes`, {section_id:p.section_id, meeting_index:p.meeting_index, day:p.target.day, start:p.target.start, reason:req!.text.slice(0, 1000)});
    onSubmitted(proposal); setReq(null); setResult(null); setText('');
  });

  function rules(i:R){
    const out:string[] = [];
    if (i.target_sections.length) out.push(`${t('Sections','الشعب')}: ${i.target_sections.join(', ')}`);
    if (i.day_filter.length) out.push(`${t('Days','الأيام')}: ${dayList(i.day_filter)}`);
    const m = i.move;
    if (m?.to_day) out.push(`${t('Move to','نقل إلى')} ${day(m.to_day)}`);
    if (m?.shift_minutes != null) out.push(m.shift_minutes > 0 ? t(`${m.shift_minutes} min later`, `تأخير ${m.shift_minutes} دقيقة`) : t(`${-m.shift_minutes} min earlier`, `تقديم ${-m.shift_minutes} دقيقة`));
    if (m?.new_start) out.push(`${t('New start','البداية الجديدة')} ${m.new_start}`);
    const w = i.allowed_time_window;
    if (w?.earliest_start) out.push(`${t('Start at or after','البداية من')} ${w.earliest_start}`);
    if (w?.latest_start) out.push(`${t('Start by','البداية قبل أو عند')} ${w.latest_start}`);
    if (w?.latest_end) out.push(`${t('Finish by','الانتهاء قبل')} ${w.latest_end}`);
    if (w?.days?.length && !i.day_filter.length) out.push(`${t('On','في')} ${dayList(w.days)}`);
    const b = i.min_break;
    if (b) out.push(b.kind === 'one_block' ? t(`One free block of ${b.minutes} min`, `فترة فراغ واحدة ${b.minutes} دقيقة`) : t(`At least ${b.minutes} min between classes`, `${b.minutes} دقيقة على الأقل بين المحاضرات`));
    if (i.day_to_empty) out.push(t(`Move ${day(i.day_to_empty.from_day)} classes to ${day(i.day_to_empty.to_day)}`, `نقل محاضرات ${day(i.day_to_empty.from_day)} إلى ${day(i.day_to_empty.to_day)}`));
    i.protected_sections.forEach((p:R) => out.push(`${t('Keep unchanged','بدون تغيير')}: ${p.section}${p.days.length ? ` (${dayList(p.days)})` : ''}`));
    if (i.locked_days.length) out.push(`${t("Don't touch",'لا تغيير في')}: ${dayList(i.locked_days)}`);
    if (i.keep_days) out.push(t('Keep the days','الإبقاء على الأيام'));
    if (i.keep_time) out.push(t('Keep the time','الإبقاء على الوقت'));
    if (i.keep_room) out.push(t('Keep the room','الإبقاء على القاعة'));
    if (i.max_changes != null) out.push(`${t('Change at most','بحد أقصى')} ${i.max_changes} ${t('sections','شعب')}`);
    const s = i.slot_search;
    if (s) out.push(`${s.duration ? minutes(s.duration) : t('duration not given','المدة غير محددة')} · ${L(GROUPS[s.group])}${s.same_time_for_all ? t(' · same time for all',' · بنفس الوقت للجميع') : ''}`);
    const d = i.duration_change;
    if (d) out.push(d.new_minutes ? `${t('New length','المدة الجديدة')} ${minutes(d.new_minutes)}` : d.direction === 'longer' ? t('Longer sessions','محاضرات أطول') : t('Shorter sessions','محاضرات أقصر'));
    if (i.delivery_mode === 'online') out.push(t('Online','عن بُعد'));
    return out;
  }

  function startEdit(){
    const i = req!.interpretation;
    setEdit({scope:i.scope, target_sections:[...i.target_sections], day_filter:[...i.day_filter], max_changes:i.max_changes,
      keep_days:i.keep_days, keep_time:i.keep_time, keep_room:i.keep_room, date_scope:{...i.date_scope},
      allowed_time_window:i.allowed_time_window ? {...i.allowed_time_window} : {earliest_start:null, latest_start:null, latest_end:null, days:[]}});
  }
  const setWin = (k:string, v:string) => setEdit(e => ({...e, allowed_time_window:{...e!.allowed_time_window, [k]:v || null}}));
  const i = req?.interpretation, res = req?.resolution;
  const openQuestions = (i?.questions?.length || 0) + (res?.questions?.length || 0);
  const BLOCKING = ['DATED_CHANGE','DURATION_CHANGE','ONLINE_DELIVERY','UNDEFINED_GOAL'];
  const blocked = !!i && i.unsupported.some((u:R) => BLOCKING.includes(u.code));
  const nothingSupported = !!i && (blocked || req!.next_step === 'none');
  const canConfirm = req?.status === 'draft' && !res?.blocked && !openQuestions && !nothingSupported;

  return <section className="panel ra">
    <div className="ra-head"><span className="ra-icon"><Sparkles size={18}/></span><div><h2>{t('Ask Mizan','اسأل ميزان')}</h2>
      <p>{t('Describe what you need in Arabic or English. Mizan drafts an interpretation for you to check and correct; nothing runs until you confirm.','اكتب طلبك بالعربية أو الإنجليزية. يكتب ميزان مسودة لتفسير طلبك لتراجعها وتصححها، ولا يُنفَّذ شيء قبل تأكيدك.')}</p></div></div>
    <div className="ra-input">
      <textarea dir="auto" rows={2} maxLength={1500} value={text} onChange={e => setText(e.target.value)} aria-label={t('Your request','طلبك')}
        placeholder={t('e.g. Move my Sunday class one hour earlier, but keep the room','مثال: انقل محاضرة الأحد ساعة أبكر مع الإبقاء على القاعة')}/>
      <button className="primary" disabled={text.trim().length < 3 || !!busy || model === false} onClick={() => void interpret()}>{busy === 'interpret' ? <LoaderCircle size={16} className="spin"/> : <Sparkles size={16}/>}{t('Draft interpretation','صِغ التفسير')}</button>
    </div>
    {model === false && <div className="ra-block warn" role="status"><p><TriangleAlert size={14}/>{t('The local AI service isn’t running, so Ask Mizan can’t read requests right now. Your text is kept for later.','خدمة الذكاء الاصطناعي المحلية متوقفة، لذا لا يستطيع «اسأل ميزان» قراءة الطلبات الآن. سيُحفظ نصك لوقت لاحق.')}
      {onManual && <button type="button" className="text-button" onClick={onManual}>{t('Use the request form instead','استخدم نموذج الطلب بدلاً من ذلك')}</button>}</p></div>}
    {error && <div role="alert" className="alert error"><TriangleAlert size={16}/><span>{error}</span></div>}

    {i && <div className="ra-card">
      <div className="ra-card-head"><div><small>{t("Here's what I understood",'هذا ما فهمته')}</small><h3>{L(TASKS[i.task])}</h3></div>
        <span className="tt-chip">{L(SCOPES[i.scope])}</span><span className={`tt-chip ${i.date_scope.kind === 'weekly' ? '' : 'warn'}`}><CalendarClock size={13}/>{L(DATES[i.date_scope.kind])}{!ar && i.date_scope.phrase ? ` · ${i.date_scope.phrase}` : ''}</span></div>
      <blockquote dir="auto">{req!.text}</blockquote>
      {!edit ? <ul className="ra-rules">{rules(i).map((r, n) => <li key={n}>{r}</li>)}{!rules(i).length && <li className="muted">{t('No extra rules','لا توجد قواعد إضافية')}</li>}</ul> :
      <div className="ra-edit">
        <label>{t('Scope','النطاق')}<select value={edit.scope} onChange={e => setEdit({...edit, scope:e.target.value})}>{Object.entries(SCOPES).map(([k, v]) => <option key={k} value={k}>{L(v)}</option>)}</select></label>
        <label>{t('Sections','الشعب')}<input dir="ltr" value={edit.target_sections.join(', ')} onChange={e => setEdit({...edit, target_sections:e.target.value.split(/[,\s،]+/).filter(Boolean)})} placeholder="S087, S089"/></label>
        <fieldset><legend>{t('Days','الأيام')}</legend>{DAY_KEYS.map(k => <label key={k} className="ra-check"><input type="checkbox" checked={edit.day_filter.includes(k)} onChange={e => setEdit({...edit, day_filter:e.target.checked ? [...edit.day_filter, k] : edit.day_filter.filter((x:string) => x !== k)})}/>{day(k)}</label>)}</fieldset>
        <label>{t('Start at or after','البداية من')}<input type="time" value={edit.allowed_time_window.earliest_start || ''} onChange={e => setWin('earliest_start', e.target.value)}/></label>
        <label>{t('Start by','البداية قبل أو عند')}<input type="time" value={edit.allowed_time_window.latest_start || ''} onChange={e => setWin('latest_start', e.target.value)}/></label>
        <label>{t('Finish by','الانتهاء قبل')}<input type="time" value={edit.allowed_time_window.latest_end || ''} onChange={e => setWin('latest_end', e.target.value)}/></label>
        <label>{t('Change at most','بحد أقصى')}<input type="number" min={0} max={30} value={edit.max_changes ?? ''} onChange={e => setEdit({...edit, max_changes:e.target.value === '' ? null : Number(e.target.value)})}/></label>
        <label>{t('When','متى')}<select value={edit.date_scope.kind} onChange={e => setEdit({...edit, date_scope:{...edit.date_scope, kind:e.target.value}})}>{Object.entries(DATES).map(([k, v]) => <option key={k} value={k}>{L(v)}</option>)}</select></label>
        <fieldset><legend>{t('Keep','الإبقاء على')}</legend>{([['keep_days','Days','الأيام'],['keep_time','Time','الوقت'],['keep_room','Room','القاعة']] as const).map(([k, en, a]) => <label key={k} className="ra-check"><input type="checkbox" checked={edit[k]} onChange={e => setEdit({...edit, [k]:e.target.checked})}/>{t(en, a)}</label>)}</fieldset>
      </div>}

      {i.unsupported.length > 0 && <div className="ra-block warn"><h4><TriangleAlert size={15}/>{t('Not supported yet','غير مدعوم حالياً')}</h4>{i.unsupported.map((u:R) => <p key={u.code}>{t(u.reason_en, u.reason_ar)}</p>)}{blocked && i.date_scope.kind !== 'weekly' && <p className="muted">{t('To apply it to the weekly timetable instead, choose Correct and set When to Weekly timetable.','لتطبيقه على الجدول الأسبوعي بدلاً من ذلك، اختر «تصحيح» ثم اجعل «متى» الجدول الأسبوعي.')}</p>}</div>}
      {req!.date_note && <div className="ra-block"><h4><Info size={15}/>{t('About dates','عن التواريخ')}</h4><p>{t(req!.date_note.en, req!.date_note.ar)}</p></div>}
      {(i.questions.length > 0 || res.questions.length > 0) && <div className="ra-block ask"><h4><CircleHelp size={15}/>{t('Please clarify','يرجى التوضيح')}</h4>
        {[...i.questions, ...res.questions].map((q:R) => <p key={q.code}>{t(q.en, q.ar)}{q.options && <span className="ra-options">{q.options.map((o:R) => <span key={`${o.section_id}-${o.meeting_index}`} className="tt-chip">{o.section_id} · {day(DAY_KEYS[o.day])} <bdi>{time(o.start)}</bdi></span>)}</span>}</p>)}
        <p className="muted">{t('Correct the fields or rephrase the request.','صحّح الحقول أو أعد صياغة الطلب.')}</p></div>}
      {res.issues.length > 0 && <div className="ra-block bad">{res.issues.map((x:R) => <p key={x.code + x.en}><X size={14}/>{t(x.en, x.ar)}</p>)}</div>}
      {req!.status === 'draft' && res.meetings.length > 0 && <p className="muted ra-scope">{res.meetings.length} {t('matching class meetings','محاضرة مطابقة')} · {res.sections.length} {t('sections','شعبة')}</p>}

      {req!.status === 'draft' && <div className="ra-actions">
        {!edit ? <button className="secondary" disabled={!!busy} onClick={startEdit}><Pencil size={15}/>{t('Correct','تصحيح')}</button> :
          <button className="secondary" disabled={!!busy} onClick={() => void revise()}>{busy === 'revise' ? <LoaderCircle size={15} className="spin"/> : <Check size={15}/>}{t('Save corrections','حفظ التصحيح')}</button>}
        <button className="secondary" disabled={!!busy} onClick={() => edit ? setEdit(null) : void cancel()}><X size={15}/>{edit ? t('Discard','تجاهل') : t('Cancel request','إلغاء الطلب')}</button>
        <button className="primary" disabled={!canConfirm || !!edit || !!busy} onClick={() => void confirm()}>{busy === 'confirm' ? <LoaderCircle size={15} className="spin"/> : <Check size={15}/>}{t('Confirm','تأكيد')}</button>
      </div>}

      {result && <div className="ra-result">
        {result.step === 'preview_move' && (result.previews.length ? result.previews.map((p:R) => <div key={p.section_id} className="ra-preview">
          <strong>{p.section_id} · {day(DAY_KEYS[p.day])} <bdi>{time(p.start)}</bdi> → {day(DAY_KEYS[p.target.day])} <bdi>{time(p.target.start)}–{time(p.target.end)}</bdi></strong>
          <div className="tt-chips">{p.error ? <span className="tt-chip bad">{p.error}</span> : <>{p.feasible ? <span className="tt-chip ok"><ShieldCheck size={13}/>{t('No new conflicts','لا تعارضات جديدة')}</span> : <span className="tt-chip bad"><TriangleAlert size={13}/>{p.new_issue_count} {t('new conflicts','تعارضات جديدة')}</span>}
            <span className="tt-chip"><Clock3 size={13}/><bdi>{p.recovered_hours > 0 ? '+' : ''}{number(p.recovered_hours)}</bdi> {t('student-h / week','ساعة طالب / أسبوع')}</span><span className={`tt-chip ${p.worsened ? 'warn' : ''}`}><UsersRound size={13}/>{number(p.worsened)} {t('worse off','متضرر')}</span></>}</div>
          {role !== 'chair' && !p.error && <button className="primary" disabled={!!busy} onClick={() => void submitMove(p)}><Send size={15}/>{p.feasible ? t('Submit change request','إرسال طلب التغيير') : t('Submit & see alternatives','إرسال وعرض البدائل')}</button>}
          <small className="muted">{t('A change request still needs committee approval before publication.','يحتاج طلب التغيير إلى اعتماد اللجنة قبل النشر.')}</small></div>)
          : <p>{t('Mizan needs an exact new time to check this move. Use the timetable to drag the class, or rephrase with a time.','يحتاج ميزان إلى وقت جديد محدد للتحقق من النقل. اسحب المحاضرة في الجدول أو أعد صياغة الطلب مع الوقت.')}</p>)}
        {result.step === 'optimize_with_rules' && <RuleResult r={result} t={t} day={day}/>}
        {result.step === 'find_slots' && (result.status === 'NOT_RUN' ? <p>{result.message}</p> : <SlotList r={result} ar={ar} days={days}/>)}
        {result.step === 'find_slots' && i.unsupported.some((u:R) => u.code === 'EXTRA_SESSION') && <p className="muted">{t('Booking the session itself is not supported yet; use the slot to arrange it.','حجز المحاضرة نفسها غير مدعوم بعد؛ استخدم الوقت المقترح لترتيبها.')}</p>}
      </div>}
    </div>}
  </section>;
}

function RuleResult({r, t, day}:{r:R, t:(en:string, ar:string)=>string, day:(k:string)=>string}){
  const c = r.comparison;
  const fmt = (ms:R[]) => ms.map((m:R) => `${day(DAY_KEYS[m.day])} ${time(m.start)}`).join(', ');
  const statusText:Record<string,[string,string]> = {OPTIMAL:['Best option within the search','أفضل خيار ضمن نطاق البحث'], FEASIBLE:['Valid option found (not proven best)','وُجد خيار صحيح (غير مثبت أنه الأفضل)'],
    INFEASIBLE:['No timetable meets these rules','لا يوجد جدول يحقق هذه القواعد'], UNKNOWN:['Not found within the time limit','لم يُعثر على حل ضمن المهلة'], NOT_RUN:['Not run','لم يُنفَّذ'], INVALID_BASELINE:['The current timetable has violations','الجدول الحالي فيه مخالفات']};
  const s = statusText[r.status];
  return <div className="ra-rule-result">
    <div className="tt-chips"><span className={`tt-chip ${c?.changes?.length ? 'ok' : r.status === 'INFEASIBLE' ? 'bad' : ''}`}>{s ? t(s[0], s[1]) : r.status}</span>
      {c && <><span className="tt-chip"><Clock3 size={13}/><bdi>{c.recovered_hours > 0 ? '+' : ''}{number(c.recovered_hours)}</bdi> {t('student-h / week','ساعة طالب / أسبوع')}</span>
      <span className={`tt-chip ${(c.adverse_count ?? c.worsened) ? 'warn' : ''}`}><UsersRound size={13}/>{number(c.adverse_count ?? c.worsened)} {t('worse off','متضرر')}</span></>}
      {r.rule_violations?.length === 0 && <span className="tt-chip ok"><ShieldCheck size={13}/>{t('All rules checked independently','تم التحقق من جميع القواعد بشكل مستقل')}</span>}</div>
    {r.rule_items && <ul className="ra-rules">{r.rule_items.map((x:R) => <li key={x.id}>{t(x.en, x.ar)}</li>)}</ul>}
    {c?.changes?.length > 0 && <ul className="ra-rules">{c.changes.map((x:R) => <li key={x.section_id}>{x.section_id}: {fmt(x.before.meetings)} → {fmt(x.after.meetings)}{x.before.room_id !== x.after.room_id ? ` · ${x.after.room_id}` : ''}</li>)}</ul>}
    {(r.split_times || []).map((x:R) => <p key={x.section_id} className="muted">{x.section_id}: {t('meeting times split by rule','أوقات المحاضرات مختلفة بسبب القاعدة')} {x.reasons.map((q:R) => t(q.en, q.ar)).join(t('; ','؛ '))}</p>)}
    {r.diagnosis && <div className="ra-block warn"><p>{t(r.diagnosis.en, r.diagnosis.ar)}</p>{r.diagnosis.blocking_rules.map((b:R) => <p key={b.id}><TriangleAlert size={14}/>{t(b.en, b.ar)}</p>)}<p className="muted">{t('Your current timetable is kept.','يبقى جدولك الحالي كما هو.')}</p></div>}
    {r.message && r.status === 'NOT_RUN' && <p>{r.message}</p>}
    {['OPTIMAL','FEASIBLE'].includes(r.status) && !c?.changes?.length && <p>{t('Your timetable already meets these rules; no change is needed.','جدولك يحقق هذه القواعد بالفعل؛ لا حاجة لأي تغيير.')}</p>}
    {r.proposal ? <p><Check size={15}/>{t('Saved as a proposal for committee review. Nothing changes until it is approved and published.','حُفظ كمقترح لمراجعة اللجنة. لا يتغير شيء حتى يُعتمد ويُنشر.')}</p>
      : c?.changes?.length > 0 && <p className="muted">{t('Read-only check: no proposal was created for your role.','فحص للاطلاع فقط: لم يُنشأ مقترح لدورك.')}</p>}
  </div>;
}
