import React, {useEffect, useState} from 'react';
import {ShieldCheck, HelpCircle, EyeOff, LoaderCircle, TriangleAlert} from 'lucide-react';
import {api} from './api';

type R = Record<string, any>;

/** What an imported timetable knows, assumes and cannot see; verified data is required before publication. */
export function Readiness({sid, ar, canEdit, revision, onChanged}:{sid:string, ar:boolean, canEdit:boolean, revision:number, onChanged:()=>void}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const [r, setR] = useState<R|null>(null), [open, setOpen] = useState<''|'rooms'|'instructors'>(''), [text, setText] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  useEffect(() => { api(`/edugate/${sid}/readiness`).then(setR).catch(() => setR(null)); }, [sid, revision]);
  if (!r) return null;
  const start = (kind:'rooms'|'instructors') => { setOpen(kind); setError(''); setText((kind === 'rooms' ? r.assumed.rooms : r.assumed.instructors).map((id:string) => `${id}, `).join('\n')); };
  async function save(){
    setBusy(true); setError('');
    try {
      const lines = text.split('\n').map(l => l.trim()).filter(Boolean).map(l => { const i = l.indexOf(','); return i < 0 ? [l, ''] : [l.slice(0, i).trim(), l.slice(i + 1).trim()]; }).filter(([, v]) => v);
      const body = open === 'rooms' ? {rooms:lines.map(([id, v]) => { const n = Number(v); if (!Number.isInteger(n) || n <= 0) throw new Error(t(`Seats for ${id} must be a whole number.`, `يجب أن يكون عدد مقاعد ${id} رقماً صحيحاً.`)); return {id, capacity:n}; })}
        : {instructors:lines.map(([section_id, name]) => ({section_id, name}))};
      if (!lines.length) throw new Error(t('Add at least one line with a value after the comma.','أضف سطراً واحداً على الأقل بقيمة بعد الفاصلة.'));
      setR(await api(`/edugate/${sid}/verify`, body)); setOpen(''); onChanged();
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return <div className="readiness">
    <h3>{t('Data readiness','جاهزية البيانات')}</h3>
    <p className="muted">{r.ready_to_publish ? t('Rooms and instructors are verified. This timetable can be published after approval.','القاعات والمحاضرون موثقون. يمكن نشر هذا الجدول بعد الاعتماد.')
      : t('You can explore and optimize now. Publishing needs verified room capacities and instructors.','يمكنك الاستكشاف والتحسين الآن. النشر يتطلب توثيق سعة القاعات والمحاضرين.')}</p>
    <div className="readiness-grid">
      <div className="ok"><h4><ShieldCheck size={15}/>{t('Verified','موثق')}</h4><ul>
        <li>{t(`Student clashes checked for ${r.verified.student_conflicts} imported student${r.verified.student_conflicts === 1 ? '' : 's'}`, `فُحصت تعارضات ${r.verified.student_conflicts} طالباً مستورداً`)}</li>
        {r.verified.rooms > 0 && <li>{t(`${r.verified.rooms} room capacities`, `سعة ${r.verified.rooms} قاعات`)}</li>}
        {r.verified.instructors > 0 && <li>{t(`${r.verified.instructors} section instructors`, `محاضرو ${r.verified.instructors} شعب`)}</li>}</ul></div>
      <div className="warn"><h4><HelpCircle size={15}/>{t('Assumed','مفترض')}</h4><ul>
        {r.assumed.rooms.length > 0 && <li>{t(`${r.assumed.rooms.length} room capacities (40 seats)`, `سعة ${r.assumed.rooms.length} قاعات (40 مقعداً)`)}{canEdit && <button type="button" className="text-button" onClick={() => start('rooms')}>{t('Verify','توثيق')}</button>}</li>}
        {r.assumed.instructors.length > 0 && <li>{t(`${r.assumed.instructors.length} instructors (one placeholder per section)`, `${r.assumed.instructors.length} محاضرين (محاضر افتراضي لكل شعبة)`)}{canEdit && <button type="button" className="text-button" onClick={() => start('instructors')}>{t('Verify','توثيق')}</button>}</li>}
        <li>{t('Rooms and instructors free outside these classes','القاعات والمحاضرون متاحون خارج هذه المحاضرات')}</li></ul></div>
      <div className="missing"><h4><EyeOff size={15}/>{t('Not visible to Mizan','غير مرئي لميزان')}</h4><ul>
        <li>{t('Other bookings of these rooms','الحجوزات الأخرى لهذه القاعات')}</li><li>{t('Students whose schedules were not imported','الطلاب الذين لم تُستورد جداولهم')}</li></ul></div>
    </div>
    {open && <div className="verify-form">
      <label>{open === 'rooms' ? t('One room per line: room, seats','قاعة في كل سطر: القاعة، عدد المقاعد') : t('One section per line: section, instructor name','شعبة في كل سطر: الشعبة، اسم المحاضر')}
        <textarea dir="auto" rows={Math.min(8, text.split('\n').length + 1)} value={text} onChange={e => setText(e.target.value)} placeholder={open === 'rooms' ? 'A-01, 45' : 'MKT201-201, Dr. …'}/></label>
      {error && <div role="alert" className="alert error"><TriangleAlert size={16}/><span>{error}</span></div>}
      <div className="ra-actions"><button type="button" className="secondary" onClick={() => setOpen('')}>{t('Cancel','إلغاء')}</button>
        <button type="button" className="primary" disabled={busy} onClick={() => void save()}>{busy ? <LoaderCircle size={16} className="spin"/> : <ShieldCheck size={16}/>}{t('Save verified data','حفظ البيانات الموثقة')}</button></div>
      <small className="muted">{t('Saving creates a new timetable version; earlier proposals become outdated and can be re-run.','الحفظ ينشئ إصداراً جديداً من الجدول؛ تصبح المقترحات السابقة قديمة ويمكن إعادة تشغيلها.')}</small>
    </div>}
  </div>;
}
