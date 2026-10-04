import React, {useEffect, useState} from 'react';
import {FileUp, FileDown, LoaderCircle, TriangleAlert, Plus, X, ArrowRight, Info} from 'lucide-react';
import {api, time} from './api';

type R = Record<string, any>;
const SHORT_DAYS = {en:['Su','Mo','Tu','We','Th'], ar:['أحد','اثنين','ثلاثاء','أربعاء','خميس']};
const toMinutes = (v:string) => { const [h, m] = v.split(':').map(Number); return Number.isFinite(h) && Number.isFinite(m) ? h*60+m : null; };

/** Al Yamamah schedules in and out: read an Edugate PDF or the phone-app screenshot, review, add to Mizan;
 *  print any timetable or proposal back in the Edugate "student schedule" layout. */
export function EdugateExchange({sid, ar, days, role, students, proposals, kind, onImported}:{sid:string, ar:boolean, days:string[], role:string,
  students:R[], proposals:R[], kind:string, onImported:(id:string)=>void}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const canImport = role === 'admin' || role === 'registrar';
  const [busy, setBusy] = useState(''), [error, setError] = useState('');
  const [doc, setDoc] = useState<R|null>(null), [rows, setRows] = useState<R[]>([]);
  const [studentId, setStudentId] = useState(''), [studentName, setStudentName] = useState(''), [term, setTerm] = useState('');
  const [target, setTarget] = useState(''), [timetables, setTimetables] = useState<R[]>([]);
  const [exportStudent, setExportStudent] = useState(students[0]?.id || ''), [source, setSource] = useState('');
  useEffect(() => { if (canImport) api('/edugate/timetables').then(setTimetables).catch(() => setTimetables([])); }, [canImport, sid]);
  useEffect(() => { setExportStudent(students[0]?.id || ''); setSource(''); }, [sid]);

  async function read(file:File){
    setBusy('read'); setError(''); setDoc(null);
    try {
      const form = new FormData(); form.append('file', file);
      const r = await fetch('/api/edugate/read', {method:'POST', headers:{'X-Mizan-Action':'1'}, body:form});
      const body = await r.json();
      if (!r.ok) throw new Error(typeof body.detail === 'object' ? (ar ? body.detail.ar : body.detail.en) : body.detail);
      setDoc(body); setRows(body.rows); setStudentId(body.student_id || ''); setTerm(body.term || '');
      setTarget(kind === 'edugate' ? sid : '');
    } catch (e) { setError((e as Error).message); } finally { setBusy(''); }
  }
  const edit = (i:number, patch:R) => setRows(rs => rs.map((r, j) => j === i ? {...r, ...patch, warnings:(r.warnings||[]).filter((w:R) => !Object.keys(patch).some(k => w.key === k || (k === 'start' || k === 'end') && w.key === 'inferred'))} : r));
  const incomplete = rows.some(r => r.start == null || r.end == null || !r.days?.length || !r.code);
  async function add(){
    setBusy('import'); setError('');
    try {
      const r = await api('/edugate/import', {student_id:studentId.trim(), student_name:studentName.trim(), term:term || null,
        scenario_id:target || null, rows:rows.map(({warnings, ...row}) => row)});
      setDoc(null); setRows([]); onImported(r.id);
    } catch (e) { setError((e as Error).message); } finally { setBusy(''); }
  }
  const href = `/api/edugate/export?scenario_id=${encodeURIComponent(sid)}&student_id=${encodeURIComponent(exportStudent)}${source ? `&proposal_id=${source}` : ''}`;
  const exportable = proposals.filter(p => !['rejected', 'invalid'].includes(p.status));

  return <section className="panel ra eg">
    <div className="ra-head"><span className="ra-icon"><FileUp size={18}/></span><div><h2>{t('Edugate schedules','جداول البوابة الإلكترونية')}</h2>
      <p>{canImport ? t('Bring in a student schedule from Edugate (PDF) or the app (screenshot), optimize it, and print the result in the same Edugate layout.','استورد جدول طالب من البوابة (PDF) أو من التطبيق (لقطة شاشة)، ثم حسّنه واطبع النتيجة بنفس تنسيق البوابة.')
        : t('Print your timetable in the Edugate layout.','اطبع جدولك بتنسيق البوابة الإلكترونية.')}</p></div></div>
    {error && <div className="ra-block bad" role="alert"><p><TriangleAlert size={15}/>{error}</p></div>}

    {canImport && !doc && <label className="eg-drop">
      <input type="file" accept=".pdf,.png,.jpg,.jpeg,image/*,application/pdf" disabled={!!busy} onChange={e => { const f = e.target.files?.[0]; if (f) void read(f); e.target.value = ''; }}/>
      {busy === 'read' ? <><LoaderCircle className="spin" size={18}/>{t('Reading the schedule on this PC…','جارٍ قراءة الجدول على هذا الجهاز…')}</>
        : <><FileUp size={18}/><span><strong>{t('Import a schedule','استيراد جدول')}</strong> · {t('Edugate PDF or app screenshot','ملف PDF من البوابة أو لقطة شاشة من التطبيق')}</span></>}
    </label>}

    {canImport && doc && <div className="ra-card">
      <div className="ra-card-head"><div><small>{doc.format === 'edugate_pdf' ? t('Edugate “Student schedule” PDF','ملف «جدول الطالب» من البوابة') : t('App screenshot (My Courses)','لقطة شاشة من التطبيق (مقرراتي)')}</small>
        <h3>{t(`${rows.length} courses read — check them before adding`,`تمت قراءة ${rows.length} مقررات — راجعها قبل الإضافة`)}</h3></div>
        <button className="secondary" onClick={() => { setDoc(null); setRows([]); }}><X size={15}/>{t('Discard','تجاهل')}</button></div>
      <div className="eg-scroll"><table className="eg-table">
        <thead><tr><th>{t('Course','المقرر')}</th><th>{t('Section','الشعبة')}</th><th>{t('Days','الأيام')}</th><th>{t('Start','البداية')}</th><th>{t('End','النهاية')}</th><th>{t('Room','القاعة')}</th><th/></tr></thead>
        <tbody>{rows.map((r, i) => <React.Fragment key={i}><tr className={r.warnings?.length ? 'warn' : ''}>
          <td><input dir="ltr" aria-label={t('Course code','رمز المقرر')} value={r.code} onChange={e => edit(i, {code:e.target.value.toUpperCase(), code_ar:null})}/><small>{ar ? r.name_ar : r.name}</small></td>
          <td><input aria-label={t('Section','الشعبة')} className="eg-short" value={r.section} onChange={e => edit(i, {section:e.target.value})}/></td>
          <td><div className="eg-days">{days.map((d, di) => <button type="button" key={di} aria-pressed={r.days.includes(di)} className={r.days.includes(di) ? 'on' : ''}
            aria-label={d} title={d} onClick={() => edit(i, {days:r.days.includes(di) ? r.days.filter((x:number) => x !== di) : [...r.days, di].sort()})}>{SHORT_DAYS[ar ? 'ar' : 'en'][di]}</button>)}</div></td>
          <td><input type="time" dir="ltr" aria-label={t('Start','البداية')} className={r.start == null ? 'missing' : ''} value={r.start == null ? '' : time(r.start)} onChange={e => edit(i, {start:toMinutes(e.target.value)})}/></td>
          <td><input type="time" dir="ltr" aria-label={t('End','النهاية')} className={r.end == null ? 'missing' : ''} value={r.end == null ? '' : time(r.end)} onChange={e => edit(i, {end:toMinutes(e.target.value)})}/></td>
          <td><input dir="ltr" aria-label={t('Room','القاعة')} className="eg-short" value={r.room} onChange={e => edit(i, {room:e.target.value.toUpperCase()})}/></td>
          <td><button type="button" className="icon-button" aria-label={t('Remove row','حذف الصف')} onClick={() => setRows(rs => rs.filter((_, j) => j !== i))}><X size={14}/></button></td>
        </tr>{r.warnings?.length > 0 && <tr className="eg-note"><td colSpan={7}>{r.warnings.map((w:R) => <span key={w.key} className="tt-chip warn"><TriangleAlert size={12}/>{ar ? w.ar : w.en}</span>)}</td></tr>}</React.Fragment>)}</tbody>
      </table></div>
      <button type="button" className="text-button" onClick={() => setRows(rs => [...rs, {code:'', name:'', name_ar:'', section:'', activity:'', credits:null, days:[], start:null, end:null, room:'', warnings:[]}])}><Plus size={14}/>{t('Add a course','إضافة مقرر')}</button>
      <div className="ra-edit">
        <label>{t('Student ID','رقم الطالب')}<input value={studentId} onChange={e => setStudentId(e.target.value.replace(/[^A-Za-z0-9-]/g, ''))}/></label>
        <label>{t('Student name','اسم الطالب')}<input value={studentName} onChange={e => setStudentName(e.target.value)}/></label>
        <label>{t('Term','الفصل الدراسي')}<input value={term} placeholder="2026/2027" onChange={e => setTerm(e.target.value)}/></label>
        <label>{t('Add to','إضافة إلى')}<select value={target} onChange={e => setTarget(e.target.value)}>
          <option value="">{t('A new Edugate timetable','جدول جديد من البوابة')}</option>
          {timetables.map(tt => <option key={tt.id} value={tt.id}>{tt.name} · {tt.students} {t('students','طلاب')}</option>)}</select></label>
      </div>
      <p className="muted"><Info size={13}/>{t('Read on this PC; the file is not stored. Instructors, room sizes and other bookings are not in the schedule, so Mizan uses placeholders for them. Students who share a course and section share it here too.','تمت القراءة على هذا الجهاز ولا يُحفظ الملف. المحاضرون وسعة القاعات والحجوزات الأخرى غير موجودة في الجدول، لذا يستخدم ميزان قيماً افتراضية لها. الطلاب المشتركون في نفس المقرر والشعبة يتشاركونها هنا أيضاً.')}</p>
      <div className="ra-actions"><button className="primary" disabled={!!busy || incomplete || !studentId.trim() || !studentName.trim() || !rows.length} onClick={() => void add()}>
        {busy === 'import' ? <LoaderCircle className="spin" size={16}/> : <ArrowRight size={16}/>}{t('Add to Mizan and optimize','أضف إلى ميزان وحسّن')}</button></div>
      {incomplete && <p className="muted"><TriangleAlert size={13}/>{t('Fill in every highlighted time and day first.','أكمل الأوقات والأيام المظللة أولاً.')}</p>}
    </div>}

    {students.length > 0 && <div className="eg-export">
      <h3><FileDown size={16}/>{t('Export in the Edugate layout','تصدير بتنسيق البوابة')}</h3>
      <div className="ra-edit">
        {role !== 'student' && <label>{t('Student','الطالب')}<input list="eg-students" aria-label={t('Student to export','الطالب المراد تصديره')} value={exportStudent} onChange={e => setExportStudent(e.target.value)}/>
          <datalist id="eg-students">{students.slice(0, 2000).map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</datalist></label>}
        {role !== 'student' && <label>{t('Timetable','الجدول')}<select aria-label={t('Timetable to export','الجدول المراد تصديره')} value={source} onChange={e => setSource(e.target.value)}>
          <option value="">{t('Current timetable','الجدول الحالي')}</option>
          {exportable.map(p => <option key={p.id} value={p.id}>{t('Proposal','مقترح')} {p.id.slice(0, 6)} · {p.status}</option>)}</select></label>}
      </div>
      <a className={`primary${students.some(s => s.id === exportStudent) ? '' : ' disabled'}`} href={href} target="_blank" rel="noreferrer"
        aria-disabled={!students.some(s => s.id === exportStudent)}><FileDown size={16}/>{t('Download schedule (PDF)','تنزيل الجدول (PDF)')}</a>
    </div>}
  </section>;
}
