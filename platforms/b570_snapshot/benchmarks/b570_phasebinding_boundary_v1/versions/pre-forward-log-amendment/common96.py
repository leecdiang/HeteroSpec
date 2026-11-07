import os,sys,json,hashlib,time,subprocess,shutil,zipfile
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
PRIOR=Path(os.environ.get('HETEROSPEC_PR92_RESTORED','C:/hs/b570-evidence-remote-restored-v1'))
PINNED_CAS=Path(os.environ.get('HETEROSPEC_PR92_CAS','C:/hs/b570-evidence-run-v1/REMOTE_COMPLETE_CAS.zip'))
PS=Path('C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
TARGET=Path(os.environ.get('HETEROSPEC_TARGET_Q6','C:/hs/b570-mem-run-v1/models/Meta-Llama-3.1-8B-Instruct-Q6_K.gguf'))
DRAFT=Path(os.environ.get('HETEROSPEC_DRAFT_Q4','C:/hs/b570-opt-run-v1/models/Llama-3.2-1B-Instruct-Q4_K_M.gguf'))
os.environ['ComSpec']=r'C:\Windows\System32\cmd.exe'
os.environ['PATHEXT']='.COM;.EXE;.BAT;.CMD'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
def now(): return datetime.now(timezone.utc).isoformat()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(tmp,p)
def event(**x):
 with (ROOT/'LEDGER.jsonl').open('a',encoding='utf8',newline='\n') as f:
  f.write(json.dumps(dict(utc=now(),**x))+'\n');f.flush();os.fsync(f.fileno())
def safe_file(rel): 
 p=ROOT/rel;assert p.resolve().is_relative_to(ROOT.resolve());return p
def check_step(name,argv,cwd=None,timeout=120):
 p=subprocess.run(argv,cwd=cwd,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=timeout)
 (ROOT/'versions'/f'{name}.stdout.log').write_bytes(p.stdout);(ROOT/'versions'/f'{name}.stderr.log').write_bytes(p.stderr)
 save(ROOT/'receipts'/f'{name}.json',dict(argv=argv,returncode=p.returncode,utc=now()))
 assert p.returncode==0,p.stdout.decode(errors='replace')+p.stderr.decode(errors='replace')
 return p.stdout
