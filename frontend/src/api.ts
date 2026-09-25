export async function api(path: string, body?: unknown, method?: string) {
  const response = await fetch('/api' + path, {method: method || (body === undefined ? 'GET' : 'POST'), credentials:'same-origin', headers: {'Content-Type':'application/json','X-Mizan-Action':'1'}, ...(body === undefined ? {} : {body:JSON.stringify(body)})});
  const result = await response.json();
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : JSON.stringify(result.detail || result));
  return result;
}
export const time = (minutes:number) => `${Math.floor(minutes/60).toString().padStart(2,'0')}:${(minutes%60).toString().padStart(2,'0')}`;
export const number = (value:number) => new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(value);
