"""Download the pinned official training weights without a duplicate global cache."""
from pathlib import Path
import hashlib,json,httpx
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'model_manifest.json').read_text())
out=ROOT/'base';out.mkdir(exist_ok=True)
with httpx.Client(follow_redirects=True,timeout=120) as client:
 for info in manifest['files']:
  name=info['rfilename'];p=out/name;digest=info.get('lfs',{}).get('sha256')
  if p.exists() and p.stat().st_size==info.get('size'):
   with p.open('rb') as f:
    if not digest or hashlib.file_digest(f,'sha256').hexdigest()==digest:continue
  partial=p.with_suffix(p.suffix+'.download')
  with client.stream('GET',f"https://huggingface.co/{manifest['repo']}/resolve/{manifest['revision']}/{name}") as r,partial.open('wb') as f:
   r.raise_for_status();n=0;last=0
   for chunk in r.iter_bytes(4*1024*1024):
    f.write(chunk);n+=len(chunk)
    if n-last>=512*1024*1024:print(name,n//1024//1024,'MiB',flush=True);last=n
  assert partial.stat().st_size==info['size']
  if digest:
   with partial.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
  partial.replace(p);print('Verified',name,flush=True)
print('Official base weights ready',flush=True)
