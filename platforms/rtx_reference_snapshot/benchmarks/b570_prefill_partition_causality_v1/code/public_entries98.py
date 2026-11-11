from pathlib import Path
import json,hashlib
R=Path(r'C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/work/b570-prefill-partition-v1')
fs=list(p for p in R.iterdir() if p.is_file() and p.suffix in ['.json','.jsonl','.md'])
fs+=list(p for p in (R/'code').glob('*.py'))+list(p for p in (R/'native').iterdir() if p.is_file())
fs+=[R/'versions/worker98.diff']
fs+=list(p for p in (R/'baseline').iterdir() if p.is_file())
fs+=list(p for p in (R/'raw').glob('*/*') if p.is_file() and (p.suffix in ['.json','.jsonl','.log'] or p.name.startswith('MODULES.')) and not p.name.endswith(('.trace.json','.memory.json')))
fs+=list(p for p in (R/'receipts').glob('*.*') if p.is_file())
rows=[]
for p in sorted(set(fs)):
 b=p.read_bytes()
 try:s=b.decode('utf8')
 except UnicodeError:continue
 rows.append(dict(path=p.relative_to(R).as_posix(),bytes=len(b),git_sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),content=s))
print(json.dumps(rows,ensure_ascii=False))
