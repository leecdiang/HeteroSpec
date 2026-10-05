"""V3 shared paths and durable JSON; no model inference at import."""
import hashlib, json, os, time
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'benchmarks/rtx_trajectory_cost_v3'
OLD=Path('C:/Users/ASUS/Documents/Codex/2026-09-30/an-zh-a/work/HeteroSpec')
ASSET=Path('D:/HeteroSpec-PC')
ENGINEERING=[f'HumanEval/{i}' for i in [64,106,119,128,129,3,10,19,20,28,32,44]]
def now():return datetime.now(timezone.utc).isoformat()
def save(p,o):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(o,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
    # Windows readers/antivirus may briefly deny an atomic replace. Retry only
    # this durable metadata operation, never a model run or statistical sample.
    for attempt in range(40):
        try:tmp.replace(p);return
        except PermissionError:
            if attempt==39:raise
            time.sleep(.05)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ledger(event):
    event={'utc':now(),'monotonic_ns':__import__('time').monotonic_ns(),**event}
    p=STUDY/'EXECUTION_LEDGER.jsonl'
    with p.open('ab') as f:f.write(json.dumps(event,separators=(',',':')).encode()+b'\n');f.flush();os.fsync(f.fileno())
