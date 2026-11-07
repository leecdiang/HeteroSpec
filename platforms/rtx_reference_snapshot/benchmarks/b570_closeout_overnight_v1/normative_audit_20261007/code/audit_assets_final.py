from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).parent;BASE=Path('C:/hs/b570-closeout-v1')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
checked=[];errors=[]
for name,m in load(BASE/'ASSET_POST.json')['checked'].items():
 p=Path(name);actual=sha(p);good=actual==m['sha256'] and p.stat().st_size==m['bytes'];checked.append(dict(path=name,sha256=actual,bytes=p.stat().st_size,matches=good))
 if not good:errors.append(name)
payload=dict(status='PASS' if not errors else 'FAIL',utc=datetime.now(timezone.utc).isoformat(),assets=len(checked),errors=errors,checked=checked,scope='Full byte hashes of original model/runtime/source/manuscript/archive assets inherited from sealed post-manifest; no version-only substitution',additional_model_forwards=0)
(ROOT/'ASSET_REAUDIT.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8',newline='\n');print(dict(status=payload['status'],assets=len(checked),errors=errors),flush=True);assert not errors
