import React from 'react';
import {TriangleAlert, Eye} from 'lucide-react';

type R = Record<string, any>;

const isStudent = (id:string) => /^ST\d/.test(id) || /^\d{6,}$/.test(id) || id.startsWith('TEST');

/** One plain-language line per conflicting pair, with how many students it affects; codes stay in the details. */
export function groupIssues(issues:R[]){
  const groups = new Map<string, {code:string, records:string[], students:number, count:number, detail:string}>();
  for (const i of issues) {
    const records:string[] = i.records || [];
    const people = records.filter(isStudent).length + (i.student_count || 0);
    const things = records.filter(r => !isStudent(r));
    const key = `${i.code}|${[...things].sort().join('|')}`;
    const g = groups.get(key) || {code:i.code, records:things, students:0, count:0, detail:i.detail};
    g.students += people; g.count += 1;
    groups.set(key, g);
  }
  return [...groups.values()].sort((a, b) => b.students - a.students || b.count - a.count);
}

export function describe(g:{code:string, records:string[], students:number, count:number, detail?:string}, ar:boolean){
  const [a, b, c] = g.records;
  const t = (en:string, arabic:string) => ar ? arabic : en;
  switch (g.code) {
    case 'STUDENT_OVERLAP': return t(`${b ? `${a} and ${b}` : a} meet at the same time. ${g.students || g.count} student${(g.students || g.count) === 1 ? ' is' : 's are'} enrolled in both.`,
      `${b ? `${a} و${b}` : a} في الوقت نفسه. ${g.students || g.count} طالباً مسجلون في الاثنين.`);
    case 'PROFESSOR_OVERLAP': return t(`The instructor (${a}) would teach ${b} and ${c} at the same time.`, `المحاضر (${a}) سيدرّس ${b} و${c} في الوقت نفسه.`);
    case 'ROOM_OVERLAP': return t(`Room ${a} is booked for ${b} and ${c} at the same time.`, `القاعة ${a} محجوزة لـ ${b} و${c} في الوقت نفسه.`);
    case 'CAPACITY': return t(`${a} has more students than its seats or room ${b} allow.`, `عدد طلاب ${a} يتجاوز مقاعدها أو سعة القاعة ${b}.`);
    case 'BLOCKED_TIME': return t(`${a} would meet outside the approved teaching hours.`, `${a} ستكون خارج أوقات التدريس المعتمدة.`);
    case 'PROFESSOR_AVAILABILITY': return t(`The instructor of ${a} isn’t available then.`, `محاضر ${a} غير متاح في هذا الوقت.`);
    case 'ROOM_AVAILABILITY': return t(`Room ${b || ''} isn’t available for ${a} then.`, `القاعة ${b || ''} غير متاحة لـ ${a} في هذا الوقت.`);
    case 'CONTRACTED_HOURS': return t(`${a} would teach more than their contracted hours.`, `${a} سيتجاوز ساعاته التعاقدية.`);
    case 'PREREQUISITE': return t(`${g.students || g.count} student${(g.students || g.count) === 1 ? '' : 's'} in ${a || b} miss a prerequisite.`, `${g.students || g.count} طالباً في ${a || b} لم يكملوا متطلباً سابقاً.`);
    case 'DURATION': return t(`${a} doesn’t keep its required class length.`, `${a} لا تحافظ على مدة المحاضرة المطلوبة.`);
    case 'MEETING_PATTERN': return t(`${a} doesn’t keep its weekly meeting pattern.`, `${a} لا تحافظ على نمط المحاضرات الأسبوعي.`);
    case 'ROOM_TYPE': return t(`Room ${b} lacks the facilities ${a} needs.`, `القاعة ${b} لا تتوفر فيها تجهيزات ${a}.`);
    case 'COMPETENCY': return t(`The instructor ${b} isn’t qualified for ${a}.`, `المحاضر ${b} غير مؤهل لتدريس ${a}.`);
    default: return g.detail || g.code;
  }
}

export function ConflictList({issues, ar, onShow, limit = 12, title}:{issues:R[], ar:boolean, onShow?:(ids:string[])=>void, limit?:number, title?:string}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const groups = groupIssues(issues);
  if (!groups.length) return null;
  return <div className="conflicts">
    {title && <h4>{title}</h4>}
    <ul>{groups.slice(0, limit).map((g, i) => <li key={i}><TriangleAlert size={15}/><span>{describe(g, ar)}</span>
      {onShow && g.records.some(r => /^S\d|^NEW|-/.test(r)) && <button type="button" className="text-button" onClick={() => onShow(g.records.filter(r => /^S\d|^NEW|-/.test(r)))}><Eye size={13}/>{t('Show on timetable','عرض في الجدول')}</button>}</li>)}</ul>
    {groups.length > limit && <p className="muted">{t(`and ${groups.length - limit} more`, `و${groups.length - limit} أخرى`)}</p>}
    <details className="technical"><summary>{t('Technical details','تفاصيل تقنية')}</summary>
      <ul>{groups.map((g, i) => <li key={i}><code>{g.code}</code> · {g.records.join(' · ')}{g.students ? ` · ${g.students} ${t('students','طلاب')}` : ''}</li>)}</ul></details>
  </div>;
}
