import {useState} from 'react';

const isArabic = () => typeof document !== 'undefined' && document.documentElement.lang === 'ar';

/** Arabic for the backend messages users actually meet; anything else is shown as sent. */
const AR_ERRORS: [RegExp, string][] = [
  [/^Sign in to Mizan/, 'سجّل الدخول إلى ميزان'],
  [/^This action is not available to your role/, 'هذا الإجراء غير متاح لدورك'],
  [/^Scenario not found/, 'الجدول غير موجود'],
  [/^Meeting not found/, 'المحاضرة غير موجودة'],
  [/^Only your own sections/, 'يمكنك طلب تغيير شعبك فقط'],
  [/^This meeting is already scheduled at that time/, 'هذه المحاضرة مجدولة بالفعل في هذا الوقت. لم يُرسل شيء للمراجعة.'],
  [/^Stale proposal/, 'المقترح قديم: تغيّر الجدول بعد إنشائه. أعد تقييمه على الجدول الحالي.'],
  [/^Proposal must be (\w+)/, 'لا يمكن تنفيذ هذا الإجراء في حالة المقترح الحالية'],
  [/^Hard constraints failed; publication blocked/, 'فشلت القيود الإلزامية؛ تم إيقاف النشر'],
  [/^Resolve hard violations before optimization/, 'عالج المخالفات الإلزامية قبل التحسين'],
  [/^Meeting extends past midnight/, 'المحاضرة تتجاوز منتصف الليل'],
  [/^Section not found/, 'الشعبة غير موجودة'],
  [/^Only single meeting changes can be re-evaluated/, 'يمكن إعادة تقييم تغييرات المحاضرة الواحدة فقط. شغّل تحسيناً جديداً بدلاً من ذلك.'],
  [/^Verify instructors and room capacities/, 'تحقق من المحاضرين وسعة القاعات قبل النشر'],
  [/^Instructor name must contain/, 'يجب أن يحتوي اسم المحاضر على حرفين على الأقل دون احتساب المسافات'],
  [/^The instructor ID already belongs to a different name/, 'رقم المحاضر مرتبط باسم مختلف؛ راجع الرقم والاسم'],
];

export function localizeError(message: string) {
  if (!isArabic()) return message;
  const hit = AR_ERRORS.find(([re]) => re.test(message));
  return hit ? hit[1] : message;
}

export async function api(path: string, body?: unknown, method?: string) {
  let response: Response;
  try {
    response = await fetch('/api' + path, {method: method || (body === undefined ? 'GET' : 'POST'), credentials:'same-origin', headers: {'Content-Type':'application/json','X-Mizan-Action':'1'}, ...(body === undefined ? {} : {body:JSON.stringify(body)})});
  } catch {
    throw new Error(isArabic() ? 'تعذّر الوصول إلى خادم ميزان. تأكد أن ميزان يعمل ثم أعد المحاولة.' : 'Mizan’s server can’t be reached. Check that Mizan is still running, then try again.');
  }
  const text = await response.text();
  let result: any = null;
  try { result = text ? JSON.parse(text) : null; } catch { result = undefined; }
  if (!response.ok) {
    const d = result?.detail;
    const message = typeof d === 'string' ? d
      : d && typeof d === 'object' && 'en' in d ? (isArabic() ? d.ar : d.en)
      : Array.isArray(d) ? d.map((x: any) => x.msg).join('; ')
      : (isArabic() ? `تعذّر على الخادم إكمال الطلب (HTTP ${response.status}). أعد المحاولة.` : `The server couldn’t complete this request (HTTP ${response.status}). Try again.`);
    throw new Error(localizeError(message));
  }
  if (result === undefined) throw new Error(isArabic() ? 'أرسل الخادم رداً غير مقروء. أعد المحاولة.' : 'The server sent a response Mizan couldn’t read. Try again.');
  return result;
}
export const time = (minutes:number) => `${Math.floor(minutes/60).toString().padStart(2,'0')}:${(minutes%60).toString().padStart(2,'0')}`;
export const number = (value:number) => new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(value);

/** useState that survives navigating away and back within this browser tab (drafts, search criteria). */
export function useDraft<T>(key: string, initial: T): [T, (v: T | ((p: T) => T)) => void] {
  const read = (k: string): T => { try { const raw = sessionStorage.getItem('mizan:' + k); return raw === null ? initial : JSON.parse(raw) as T; } catch { return initial; } };
  const [state, setState] = useState(() => ({key, value: read(key)}));
  const value = state.key === key ? state.value : read(key);
  const set = (v: T | ((p: T) => T)) => setState(s => {
    const current = s.key === key ? s.value : read(key);
    const next = typeof v === 'function' ? (v as (p: T) => T)(current) : v;
    try { sessionStorage.setItem('mizan:' + key, JSON.stringify(next)); } catch { /* storage unavailable: keep in memory */ }
    return {key, value: next};
  });
  return [value, set];
}
