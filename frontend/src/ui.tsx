import React, {useEffect, useState} from 'react';
import {Check, X, Info} from 'lucide-react';
import {number} from './api';
import {gradeVars, gradeWord, type Scale} from './grade';

function useReducedMotion(){return typeof window!=='undefined'&&window.matchMedia?.('(prefers-reduced-motion: reduce)').matches}

/** Decorative count-up for dashboards only. Decision screens pass `still` and show exact values at once (UX review X03). */
export function CountUp({value}:{value:number}){const [shown,setShown]=useState(0);const reduced=useReducedMotion();useEffect(()=>{if(reduced||!Number.isFinite(value)){setShown(value);return}let frame=0;const began=performance.now(),from=0,duration=700;const tick=(now:number)=>{const k=Math.min(1,(now-began)/duration),e=1-Math.pow(1-k,3);setShown(from+(value-from)*e);if(k<1)frame=requestAnimationFrame(tick)};frame=requestAnimationFrame(tick);return()=>cancelAnimationFrame(frame)},[value,reduced]);return <bdi>{number(Number.isInteger(value)?Math.round(shown):Math.round(shown*10)/10)}</bdi>}

export function Metric({label,value,unit,icon,foot,accent,grade,ar,still,tone,help}:{label:string,value:string,unit?:string,icon?:React.ReactNode,foot?:string,accent?:boolean,grade?:{value:number|null|undefined,scale:Scale},ar?:boolean,still?:boolean,tone?:'caution'|'calm',help?:string}){
 const numeric=/^-?[\d,]+(\.\d+)?$/.test(value)?Number(value.replaceAll(',','')):null;
 const g=grade?gradeVars(grade.value,grade.scale):{};
 const word=grade?gradeWord(grade.value,grade.scale,!!ar):'';
 return <div className={`metric ${accent?'accent':''} ${grade&&word?'graded-tile':''} ${tone?`tone-${tone}`:''}`} style={g as React.CSSProperties}>
  <div className="metric-label"><span>{label}{help&&<span className="help-dot" title={help} aria-label={help} role="img"><Info size={12}/></span>}</span>{icon&&<span className="metric-icon">{icon}</span>}</div>
  <div className="metric-value">{numeric===null||still?<bdi>{value}</bdi>:<CountUp value={numeric}/>}{unit&&<small>{unit}</small>}</div>
  {word&&<span className="grade-word">{word}</span>}{foot&&<p>{foot}</p>}</div>}

export function Modal({title,children,onClose,wide}:{title:string,children:React.ReactNode,onClose:()=>void,wide?:boolean}){
 const ar=typeof document!=='undefined'&&document.documentElement.lang==='ar';
 useEffect(()=>{const fn=(e:KeyboardEvent)=>{if(e.key==='Escape')onClose()};document.addEventListener('keydown',fn);return()=>document.removeEventListener('keydown',fn)},[onClose]);
 return <div className="modal-backdrop" onClick={e=>{if(e.target===e.currentTarget)onClose()}}><section role="dialog" aria-modal="true" aria-label={title} className={`modal ${wide?'wide-modal':''}`}><div className="modal-heading"><h2>{title}</h2><button onClick={onClose} aria-label={ar?'إغلاق':'Close'}><X size={20}/></button></div>{children}</section></div>}

export function Delta({before,after,higherIsBetter}:{before:any,after:any,higherIsBetter:boolean}){
 if(typeof before!=='number'||typeof after!=='number')return <strong>{after??'—'}</strong>;
 const diff=after-before, rel=before===0?(diff===0?0:Math.sign(diff)):diff/Math.abs(before);
 const gain=(higherIsBetter?1:-1)*rel;
 const style=Math.abs(diff)<1e-9?{}:gradeVars(gain,{bad:-0.15,good:0.15});
 return <strong style={style as React.CSSProperties}>{after}{Math.abs(diff)>1e-9&&<span className="delta"><bdi>{diff>0?'+':''}{Math.round(diff*100)/100}</bdi></span>}</strong>;
}

export function statusText(s:string,ar:boolean,stale?:boolean){
 const t=(en:string,a:string)=>ar?a:en;
 if(stale)return t('Outdated','قديم');
 return ({recommended:t('Ready for review','جاهز للمراجعة'),approved:t('Approved · not yet published','معتمد · لم يُنشر بعد'),published:t('Published','منشور'),invalid:t('Conflicts found','تعارضات'),rejected:t('Rejected','مرفوض'),superseded:t('Replaced by a newer request','استُبدل بطلب أحدث'),draft:t('Draft','مسودة')} as Record<string,string>)[s]||s;
}
export function Badge({value,ar,stale}:{value:string,ar:boolean,stale?:boolean}){return <span className={`badge ${stale?'stale':value}`}><span/>{statusText(value,ar,stale)}</span>}

export function Stations({status,ar}:{status:string,ar:boolean}){
 const t=(en:string,a:string)=>ar?a:en;
 const steps=[t('Preview','معاينة'),t('Propose','اقتراح'),t('Approve','اعتماد'),t('Publish','نشر')];
 const at=({draft:1,recommended:1,approved:2,published:3,invalid:1,rejected:2,superseded:1} as Record<string,number>)[status]??1;
 const stopped=status==='invalid'||status==='rejected'||status==='superseded';
 return <ol className="stations" aria-label={t('Decision stages','مراحل القرار')}>{steps.map((label,i)=>{
   const cls=stopped&&i===at?'stop':i<at||(status==='published'&&i===3)?'done':i===at?'now':'';
   return <li key={i} className={`${cls} ${i===3?'final':''}`} aria-current={i===at?'step':undefined}><i>{cls==='done'?<Check size={12}/>:cls==='stop'?<X size={12}/>:i+1}</i><span>{stopped&&i===at?(status==='invalid'?t('Blocked: conflicts','متوقف: تعارضات'):status==='superseded'?t('Replaced','مستبدل'):t('Rejected','مرفوض')):label}</span>{i===3&&status!=='published'&&<small>{t('changes the official timetable','يغيّر الجدول الرسمي')}</small>}</li>})}</ol>;
}
