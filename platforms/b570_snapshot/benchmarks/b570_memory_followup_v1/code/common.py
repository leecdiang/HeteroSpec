import json,hashlib,os,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
R=Path('C:/hs/b570-mem-run-v1');REPO=Path('C:/hs/b570-mem-v1');DOC=REPO/'docs/experiments/b570_memory_followup_20261011';PUBLIC=REPO/'benchmarks/b570_memory_followup_v1'
def now():return datetime.now(timezone.utc).isoformat()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8');os.replace(tmp,p)
def event(**x):
 with (R/'LEDGER.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(dict(utc=now(),**x))+'\n');f.flush();os.fsync(f.fileno())
def git(*args,cwd=REPO):return subprocess.check_output(['git',*args],cwd=cwd)
