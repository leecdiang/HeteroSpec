"""Prospective CPU8 freeze. Requires actual final independent review and raw D0 gates."""
import sys,json,hashlib,datetime,os
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve();sys.path.insert(0,str(ROOT/'src/rev2'));sys.path.insert(0,str(ROOT/'source'))
from guards import wall_budget,revision_budget
from source_guard import actual_d0
from native_gate_audit import check as native_check
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
review=json.loads((ROOT/'source/FINAL_REVIEW_BINDING.json').read_bytes());assert review['status']=='scoped-clean'
for x in review['files']:assert h(ROOT/x['path'])==x['sha256'],'post-review drift'
report=ROOT/review['report_path'];assert h(report)==review['report_sha256']
review_report=json.loads(report.read_bytes());assert review_report['status']=='scoped-clean' and not review_report['findings'],'no complete final clean report'
native=native_check(ROOT)
bridge=json.loads((ROOT/'development/BRIDGE_REGRESSIONS.json').read_bytes());assert bridge['status']=='PASS' and len(bridge['cases'])==7
for runid in ['d0-smoke-r2-normal','d0-smoke-r2-journal']:
    r=json.loads((ROOT/'reports'/(runid+'.qualification.json')).read_bytes());assert r['status']=='D0_BRIDGE_SMOKE_PASS'
budget=json.loads((ROOT/'development/BUDGET_GATES.json').read_bytes());assert budget['passed'] is True
regs=json.loads((ROOT/'D0_RESERVATIONS.json').read_bytes());revision_budget(regs);counts=actual_d0(ROOT,regs)
write(ROOT/'D0_GATE_INDEX.json',dict(all_required_passed=True,native=native,actual_d0=counts,bridge_regressions_sha256=h(ROOT/'development/BRIDGE_REGRESSIONS.json'),budget_gates_sha256=h(ROOT/'development/BUDGET_GATES.json'),review_sha256=h(ROOT/'source/FINAL_REVIEW_BINDING.json')))
files={}
for rel in ['source','src/rev2','legacy/repo/benchmarks/b570_supervision_fix_v2','compiled','acquisition/repair']:
    for p in (ROOT/rel).rglob('*'):
        if p.is_file():
            if rel.startswith('legacy/') and '/results/' in p.as_posix() and p.name!='BUILD_RECORD.json':continue
            files[p.relative_to(ROOT).as_posix()]=h(p)
for rel in ['CPU8_PLAN.json','CONFIG.json','ACQUISITION.json','D0_RESERVATIONS.json','D0_GATE_INDEX.json','legacy/ROOT_BINDING.json']:
    files[rel]=h(ROOT/rel)
# win.freeze_check retains its original required inventory names; all are real source/review bytes.
mapping={'PROTOCOL.md':'CPU8_INTEGRATION.md','B570_PROMPT.md':'B570_PROMPT.md','REVIEW_BINDING.json':'REVIEW_BINDING.json','review/REPORT.json':'review/review-2.json','review/STATUS.json':'review/review-2-status.json'}
for dst,src in mapping.items():
    p=ROOT/'acquisition'/dst;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write((ROOT/'acquisition/repair'/src).read_bytes())
    files[p.relative_to(ROOT).as_posix()]=h(p)
utc=datetime.datetime.now(datetime.timezone.utc).isoformat();py='C:/Users/DIANG/AppData/Local/Programs/Python/Python312/python.exe'
frozen=dict(schema=1,uuid=ROOT.name,source_relative='src/rev2',files=files,python=py,python_sha256=h(py),protocol_commit=json.loads((ROOT/'ACQUISITION.json').read_bytes())['protocol_commit'],frozen_utc=utc,scope='CPU8 integration only; no GPU or repeated capability soak',review_status='scoped-clean',budget=dict(task_seconds=21600,d0_seconds=5400,delivery_seconds=1800),formal_cases=8)
a=json.loads((ROOT/'ACQUISITION.json').read_bytes());age=(datetime.datetime.fromisoformat(utc)-datetime.datetime.fromisoformat(a['first_preparation_utc'].replace('Z','+00:00'))).total_seconds()
wall_budget(a,frozen,regs,dict(started_utc=utc,begin_ns=0),dict(task_elapsed_before_watchdog_seconds=age,begin_ns=0,end_ns=0))
write(ROOT/'CAPABILITY_FREEZE.json',frozen)
print(json.dumps(dict(freeze_sha256=h(ROOT/'CAPABILITY_FREEZE.json'),members=len(files),native_gates=native['status'],d0_actual=counts,scope='prospective freeze, not execution PASS'),sort_keys=True))
