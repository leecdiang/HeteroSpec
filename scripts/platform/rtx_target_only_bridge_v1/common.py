"""Small transport utilities; comparison/verification lives in separate programs."""
import hashlib, json, os, pathlib, subprocess
from datetime import datetime, timezone
ROOT = pathlib.Path(__file__).resolve().parents[3]
DOC = ROOT / 'benchmarks/rtx_target_only_bridge_v1'
OUT = ROOT / 'work/rtx-target-only-bridge-v1'
ASSET = pathlib.Path(os.environ.get('HETEROSPEC_ASSET_ROOT', 'D:/HeteroSpec-PC'))
PRIOR = pathlib.Path(os.environ.get('HETEROSPEC_PRIOR_ROOT', 'D:/HeteroSpec-RTX-Target-V1'))
PIN = '16aeada781c475c9641e09c90e93fb0a0e136c34'
TASKS = ['HumanEval/'+str(i) for i in [143,31,25,81,15,141,142,18,136,99,148,140,87,76,26,49,40,109,66]]
EOG = {128247,151643,151645,151662,151663,151664}
def now(): return datetime.now(timezone.utc).isoformat()
def load(p): return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with pathlib.Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp')
    with tmp.open('w',encoding='utf-8',newline='\n') as f:
        json.dump(x,f,indent=2,ensure_ascii=True);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def canon(x): return json.dumps(x,separators=(',',':'),sort_keys=True).encode()
def clean_env():
    keys=['SystemRoot','WINDIR','TEMP','TMP','PATH','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE']
    return {k:os.environ[k] for k in keys if k in os.environ}
