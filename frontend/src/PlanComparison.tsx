import React, {useEffect, useState} from 'react';
import {GitCompareArrows, LoaderCircle, ShieldCheck, TriangleAlert} from 'lucide-react';
import {api, number, time} from './api';

type R = Record<string, any>;
export const planName = (key:string, ar:boolean) => ({
  time_saved: ar ? 'أكثر وقت مستعاد' : 'Most time saved',
  fewest_changes: ar ? 'أقل تغييرات' : 'Fewest changes',
  balanced: ar ? 'أثر أكثر توازناً' : 'Balanced impact',
} as Record<string,string>)[key] || key;

export function PlanComparison({sid, revision, ar, canEdit, days, courseName, onSelect}:{
  sid:string, revision:number, ar:boolean, canEdit:boolean, days:string[], courseName:(id:string)=>string, onSelect:(p:R)=>Promise<void>
}){
  const t = (en:string, arabic:string) => ar ? arabic : en;
  const [result,setResult] = useState<R|null>(null), [loading,setLoading]=useState(true);
  const [busy,setBusy]=useState(''), [error,setError]=useState('');
  const [limit,setLimit]=useState(5), [seconds,setSeconds]=useState(15), [elapsed,setElapsed]=useState(0);
  useEffect(()=>{let alive=true;setLoading(true);api(`/scenarios/${sid}/plan-comparisons`).then(r=>{if(alive){setResult(r);if(r){setLimit(r.limits.max_changes);setSeconds(r.limits.seconds)}}}).catch(e=>{if(alive)setError(e.message)}).finally(()=>{if(alive)setLoading(false)});return()=>{alive=false}},[sid,revision]);
  useEffect(()=>{if(busy!=='search')return;setElapsed(0);const started=Date.now();const timer=window.setInterval(()=>setElapsed(Math.floor((Date.now()-started)/1000)),1000);return()=>window.clearInterval(timer)},[busy]);
  const stale=!!result && (result.stale || result.base_revision!==revision);
  async function generate(){
    setBusy('search');setError('');
    try{setResult(await api(`/scenarios/${sid}/plan-comparisons`,{revision,max_changes:limit,seconds}))}
    catch(e){setError((e as Error).message)}finally{setBusy('')}
  }
  async function select(key:string){
    if(!result)return;setBusy(key);setError('');
    try{const p=await api(`/plan-comparisons/${result.id}/${key}/select`,{});await onSelect(p)}
    catch(e){setError((e as Error).message)}finally{setBusy('')}
  }
  const objectives:Record<string,string>={
    time_saved:t('Reduce total student waiting time first, then campus days and changes.','تقليل وقت انتظار الطلاب أولاً، ثم أيام الحضور والتغييرات.'),
    fewest_changes:t('Change the fewest sections while recovering at least 1% of current gap time.','تغيير أقل عدد من الشعب مع استعادة ١٪ على الأقل من وقت الفجوات الحالي.'),
    balanced:t('Reduce gaps for the worst-off 10% first, then spread relief across students with long waits.','تقليل فجوات الـ١٠٪ الأكثر تأثراً أولاً، ثم توزيع التحسين على الطلاب ذوي الانتظار الطويل.'),
  };
  const status=(s:string)=>s==='OPTIMAL'?t('Best within searched options','الأفضل ضمن البدائل المدروسة'):s==='FEASIBLE'?t('Valid; search time limit reached','صالح؛ انتهت مدة البحث'):s==='UNKNOWN'?t('Search ended without a plan','انتهى البحث دون خطة'):s==='INFEASIBLE'?t('No improvement within these options and limits','لا يوجد تحسين ضمن هذه البدائل والحدود'):t('No validated improvement','لا يوجد تحسين متحقق منه');
  const rows:{label:string,current:number|string,value:(p:R)=>number|string}[]=[
    {label:t('Gap hours / week','ساعات الفجوات أسبوعياً'),current:result?.before.gap_hours??0,value:p=>p.after.gap_hours},
    {label:t('Hours recovered / week','الساعات المستعادة أسبوعياً'),current:'—',value:p=>p.comparison.recovered_hours},
    {label:t('Sections changed','الشعب المتغيرة'),current:0,value:p=>p.comparison.changes.length},
    {label:t('Students better off','الطلاب المستفيدون'),current:0,value:p=>p.comparison.benefiting},
    {label:t('Students worse off','الطلاب المتضررون'),current:0,value:p=>p.comparison.worsened},
    {label:t('Average campus days','متوسط أيام الحضور'),current:result?.before.average_days??0,value:p=>p.after.average_days},
    {label:t('Worst-off 10%: average gap hours','الـ١٠٪ الأكثر تأثراً: متوسط ساعات الفجوات'),current:result?.before.worst_decile_gap_hours??0,value:p=>p.after.worst_decile_gap_hours},
    {label:t('Largest increase in weekly gaps (minutes)','أكبر زيادة في الفجوات الأسبوعية (دقائق)'),current:0,value:p=>Math.max(0,p.comparison.worst_increase_minutes)},
    {label:t('Hard conflicts','التعارضات الإلزامية'),current:result?.before.conflict_count??0,value:p=>p.conflict_count},
  ];
  return <div className="plan-comparison">
    <p>{t('Compare three priorities against the same timetable. Searching changes nothing; choose a plan to prepare a proposal for approval.','قارن ثلاث أولويات على الجدول نفسه. البحث لا يغيّر شيئاً؛ اختر خطة لإعداد مقترح ينتظر الاعتماد.')}</p>
    {canEdit?<div className="plan-controls"><label>{t('Maximum sections to change','الحد الأقصى للشعب المتغيرة')}<input type="number" min={0} max={30} value={limit} disabled={!!busy} onChange={e=>setLimit(Number(e.target.value))}/></label>
      <label>{t('Search seconds per plan','مدة البحث لكل خطة بالثواني')}<input type="number" min={1} max={30} value={seconds} disabled={!!busy} onChange={e=>setSeconds(Number(e.target.value))}/></label>
      <button className="primary" disabled={loading||!!busy||!Number.isInteger(limit)||limit<0||limit>30||!Number.isInteger(seconds)||seconds<1||seconds>30} onClick={()=>void generate()}><GitCompareArrows size={17}/>{t('Generate three plans','إنشاء ثلاث خطط')}</button>
    </div>:<p className="readonly-note">{t('The scheduling committee generates and selects plans. You can review the saved comparison.','تنشئ لجنة الجدولة الخطط وتختار منها. يمكنك مراجعة المقارنة المحفوظة.')}</p>}
    {canEdit&&<p className="muted">{t(`Three searches: up to ${seconds*3} seconds of solver time, plus validation.`, `ثلاث عمليات بحث: حتى ${seconds*3} ثانية للبحث، إضافة إلى التحقق.`)}</p>}
    {busy==='search'&&<p role="status"><LoaderCircle size={16} className="spin"/> {t(`Searching and validating three plans… ${elapsed}s`, `جارٍ البحث والتحقق من ثلاث خطط… ${elapsed} ث`)}</p>}
    {error&&<div className="alert error" role="alert"><TriangleAlert size={16}/>{error}</div>}
    {loading&&<p role="status">{t('Loading saved comparison…','جارٍ تحميل المقارنة المحفوظة…')}</p>}
    {!loading&&!result&&!busy&&<p className="queue-empty">{t('No plans compared yet. Generate a comparison to explore the trade-offs.','لم تُقارن خطط بعد. أنشئ مقارنة لاستكشاف أثر كل خيار.')}</p>}
    {result&&<>
      <div className="plan-summary"><strong>{t(`Timetable version ${result.base_revision} · ${result.distinct_plans} distinct validated plans`, `إصدار الجدول ${result.base_revision} · ${result.distinct_plans} خطط مختلفة متحقق منها`)}</strong><span><ShieldCheck size={15}/>{t('Every available plan independently validated','كل خطة متاحة متحقق منها بشكل مستقل')}</span></div>
      <p className="muted">{t(`This comparison used at most ${result.limits.max_changes} changed sections and ${result.limits.seconds} search seconds per plan.`, `استخدمت هذه المقارنة حداً أقصى ${result.limits.max_changes} شعب متغيرة و${result.limits.seconds} ثوانٍ للبحث لكل خطة.`)}</p>
      {stale&&<div className="ra-block bad" role="alert">{t('Outdated comparison: the timetable changed. Generate three plans again before selecting.','المقارنة قديمة: تغيّر الجدول. أنشئ الخطط مجدداً قبل الاختيار.')}</div>}
      {result.imported&&<p className="ra-block ask">{t('Imported schedule: validation covers the available data and assumptions. Verified rooms and instructors are still required before publication.','جدول مستورد: يشمل التحقق البيانات المتاحة والافتراضات. يظل توثيق القاعات والمحاضرين مطلوباً قبل النشر.')}</p>}
      <div className="plan-table-scroll" tabIndex={0} role="region" aria-label={t('Plan comparison table','جدول مقارنة الخطط')}><table className="plan-table"><thead><tr><th scope="col">{t('Measure','المؤشر')}</th><th scope="col">{t('Current','الحالي')}</th>{result.plans.map((p:R)=><th scope="col" key={p.key} data-plan={p.key}><h3>{planName(p.key,ar)}</h3><p>{objectives[p.key]}</p><small>{status(p.status)}</small>{p.same_as&&<p className="plan-identical">{t(`Same timetable as ${planName(p.same_as,false)}; no distinct alternative found.`, `نفس جدول «${planName(p.same_as,true)}»؛ لم يُعثر على بديل مختلف.`)}</p>}</th>)}</tr></thead>
        <tbody>{rows.map((r,i)=><tr key={i} data-measure={i}><th scope="row">{r.label}</th><td>{typeof r.current==='number'?number(r.current):r.current}</td>{result.plans.map((p:R)=><td key={p.key} className={i===4&&p.available&&p.comparison.worsened>0?'plan-harm':''}>{p.available?number(r.value(p) as number):'—'}</td>)}</tr>)}</tbody>
        <tfoot><tr><th scope="row">{t('Next step','الخطوة التالية')}</th><td>—</td>{result.plans.map((p:R)=><td key={p.key}><button className="secondary" aria-label={t(`Review ${planName(p.key,false)}`,`مراجعة ${planName(p.key,true)}`)} disabled={!canEdit||!!busy||stale||!p.available} onClick={()=>void select(p.key)}>{busy===p.key?<LoaderCircle size={15} className="spin"/>:null}{t('Review this plan','مراجعة هذه الخطة')}</button></td>)}</tr></tfoot></table></div>
      <p className="muted">{t('A student can benefit on waiting time and still be worse off on campus days. Harm means extra gaps or campus days; zero harm is a measured result, not a guarantee. These are bounded searches, not every possible university timetable.','قد يستفيد الطالب من تقليل الانتظار ويتضرر بزيادة أيام الحضور. الضرر يعني زيادة الفجوات أو أيام الحضور؛ انعدام الضرر نتيجة مقاسة وليس ضماناً. البحث محدود ولا يشمل كل الجداول الجامعية الممكنة.')}</p>
      <details><summary>{t('See which classes change','عرض المحاضرات المتغيرة')}</summary>{result.plans.filter((p:R)=>p.available).map((p:R)=><section key={p.key}><h3>{planName(p.key,ar)}</h3>{p.comparison.changes.map((c:R)=><div className="plan-change" key={c.section_id}><strong>{courseName(c.after.course_id)} · {c.section_id}</strong><span>{c.before.meetings.map((m:R)=>`${days[m.day]} ${time(m.start)}–${time(m.end)}`).join(' · ')} → {c.after.meetings.map((m:R)=>`${days[m.day]} ${time(m.start)}–${time(m.end)}`).join(' · ')}</span>{c.before.room_id!==c.after.room_id&&<small>{t('Room','القاعة')}: {c.before.room_id} → {c.after.room_id}</small>}</div>)}</section>)}</details>
    </>}
  </div>;
}
