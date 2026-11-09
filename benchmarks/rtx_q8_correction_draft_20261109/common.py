"""Pinned paths and pure helpers for this bounded supplemental epoch."""
from pathlib import Path
import datetime,hashlib,json,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
ORIGINAL=REPO.parent/'q8rtx211/benchmarks/rtx_q8_transfer_20261109/results_20261109'
AUDIT=REPO.parent/'q8rtx213-audit/benchmarks/rtx_q8_freeze_audit_20261109'
OLD=Path('D:/rtx211-q8-20261109')
RUNTIME=REPO.parent/'q8rtx213-supplement-runtime-20261109'
LOCK=Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        while b:=f.read(4*1024**2):h.update(b)
    return h.hexdigest()
def canonical(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
def put(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2,ensure_ascii=False)

def inherit():
    old=read(HERE/'LEDGER_SNAPSHOT.json')
    assert sha(old['legacy']['path'])==old['legacy']['sha256'],'Legacy RTX ledger changed'
    assert sha(old['epoch']['path'])==old['epoch']['sha256'],'RTX PR213 ledger changed; reconcile before admission'
    return old

def source_check():
    s=read(HERE/'EXECUTION_SOURCE_BINDINGS.json')
    for path,h in s['files'].items():assert sha(path)==h,('Frozen source/input changed',path)
    parent=read(ORIGINAL/'SOURCE_BINDINGS.json')
    for path,item in parent['files'].items():assert sha(path)==item['sha256'],('Numerical/toolchain closure changed',path)
    return s

def reader_class():
    sys.path.insert(0,str(AUDIT));from core import Reader
    return Reader
