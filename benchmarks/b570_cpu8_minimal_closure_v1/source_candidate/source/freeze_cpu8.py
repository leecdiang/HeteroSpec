"""Prospective CPU8 freeze. Requires actual final independent review and raw D0 gates."""
import sys,json,hashlib,datetime,os
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve();sys.path.insert(0,str(ROOT/'src/rev2'));sys.path.insert(0,str(ROOT/'source'))
from guards import wall_budget,revision_budget
from budget_v6 import snapshot
snapshot(ROOT,'C') # independently authorized C task, never historical development budget
from operation_roles_v7 import formal_template
formal_id, formal_template_path, _formal_pre_f0 = formal_template(ROOT)
def require(ok, message):
    if not ok:raise ValueError(message)
# A runtime operation contains F0's digest, so it must not exist before F0
# and must never be listed in F0's own byte inventory.
require(not (ROOT/'tools'/(formal_id+'.operation.json')).exists(), 'post-F0 operation exists before freeze')
for artifact in (ROOT/'tools').glob(formal_id+'.*.json'):
    require(artifact == formal_template_path,
            'formal runtime request, capture or settlement exists before F0')
from source_guard import actual_d0
from native_gate_audit import check as native_check
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
from finalize_review_v6 import verify as source_review_verify
review=source_review_verify(ROOT) # exact source bytes and P0-P2 coverage, not native reviewer OS
approval_path=ROOT/'review/A_EXTERNAL_APPROVAL.json'
approval=json.loads(approval_path.read_bytes())
assert approval.get('status')=='SOURCE_REVIEW_PASS' and approval.get('review_report_sha256')==review['report_sha256'] and approval.get('candidate_manifest_sha256')==review['candidate_manifest_sha256'],'independently approved A identity'
assert approval.get('external_provider_reference') and approval.get('independent_reviewer_identity'),'A external attribution absent; provider must be verified before C admission'
from source_review_origin_v7 import check as review_origin_check
review_origin=review_origin_check(ROOT,approval,review)
native=native_check(ROOT)
from engineering_gates_v6 import check as engineering_check
engineering=engineering_check(ROOT)
bridge=json.loads((ROOT/'development/BRIDGE_REGRESSIONS.json').read_bytes());assert bridge['status']=='PASS' and len(bridge['cases'])==7
d0_plan=json.loads((ROOT/'D0_BRIDGE_PLAN.json').read_bytes())
for item in [d0_plan['normal'],d0_plan['journal']]:
    runid=item['run_id']
    r=json.loads((ROOT/item['report_dir']/(runid+'.qualification.json')).read_bytes());assert r['status']=='D0_BRIDGE_SMOKE_PASS'
budget=json.loads((ROOT/'development/BUDGET_GATES.json').read_bytes());assert budget['passed'] is True
regs=json.loads((ROOT/'D0_RESERVATIONS.json').read_bytes());revision_budget(regs,__import__('continuation_policy').load(ROOT));counts=actual_d0(ROOT,regs)
from integration_gates import check as integration_check
integration=integration_check(ROOT)
write(ROOT/'D0_GATE_INDEX.json',dict(all_required_passed=True,integration=integration,native=native,actual_d0=counts,bridge_regressions_sha256=h(ROOT/'development/BRIDGE_REGRESSIONS.json'),budget_gates_sha256=h(ROOT/'development/BUDGET_GATES.json'),review_sha256=review['report_sha256'],a_external_approval_sha256=h(approval_path)))
policy=__import__('continuation_policy').load(ROOT)
files={}
if policy:files['CONTINUATION_POLICY.json']=h(ROOT/'CONTINUATION_POLICY.json')
for rel in ['source','src/rev2','legacy/repo/benchmarks/b570_supervision_fix_v2','compiled','acquisition/repair','acquisition/current']:
    for p in (ROOT/rel).rglob('*'):
        if p.is_file():
            if rel.startswith('legacy/') and '/results/' in p.as_posix() and p.name!='BUILD_RECORD.json':continue
            files[p.relative_to(ROOT).as_posix()]=h(p)
for rel in ['CAMPAIGN.json','OPERATION_POLICY.json','FILESYSTEM_IDENTITY.json','NATIVE_GATE_PATHS.json','OPERATION_ROLE_MAP.json','CPU8_EXECUTION_ENVELOPE.json','ENGINEERING_GATE_BINDING.json','review/CANDIDATE_MANIFEST.json','review/FINAL_REVIEW.json','review/A_EXTERNAL_APPROVAL.json','CPU8_PLAN.json','CONFIG.json','ACQUISITION.json','D0_RESERVATIONS.json','D0_GATE_INDEX.json','legacy/ROOT_BINDING.json','D0_BRIDGE_PLAN.json','INTEGRATION_GATE_BINDING.json','ENTRY_SOURCE_MANIFEST.final.json','preflight/STARTUP.final.json','D0_EVIDENCE_SNAPSHOT/EXPECTED.json','D0_EVIDENCE_SNAPSHOT/PROVENANCE.json','D0_EVIDENCE_SNAPSHOT/legacy/AUDIT_INPUT_MANIFEST-d0-snapshot.json']:
    files[rel]=h(ROOT/rel)
for p in (ROOT/'tools').glob('*.json'):
    require(p.name != formal_id+'.operation.json', 'F0 cannot hash its own runtime operation')
    files[p.relative_to(ROOT).as_posix()]=h(p)
require(files.get(formal_template_path.relative_to(ROOT).as_posix())==h(formal_template_path), 'formal template not pinned by F0')
require(files.get('OPERATION_ROLE_MAP.json')==h(ROOT/'OPERATION_ROLE_MAP.json'), 'formal role map not pinned by F0')
# win.freeze_check retains its original required inventory names; all are real source/review bytes.
mapping={'PROTOCOL.md':'CPU8_INTEGRATION.md','B570_PROMPT.md':'B570_PROMPT.md','REVIEW_BINDING.json':'REVIEW_BINDING.json','review/REPORT.json':'review/review-2.json','review/STATUS.json':'review/review-2-status.json'}
for dst,src in mapping.items():
    p=ROOT/'acquisition'/dst;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write((ROOT/'acquisition/repair'/src).read_bytes())
    files[p.relative_to(ROOT).as_posix()]=h(p)
utc=datetime.datetime.now(datetime.timezone.utc).isoformat();py=json.loads((ROOT/'preflight/TOOLS.json').read_bytes())['python']['path']
plan=json.loads((ROOT/'CPU8_EXECUTION_ENVELOPE.json').read_bytes())
assert plan.get('schema')=='B570_C_FROZEN_ENVELOPE_V1' and plan.get('task_uuid')==json.loads((ROOT/'CAMPAIGN.json').read_bytes()).get('task_uuid'),'new C plan identity'
assert all(type(plan.get(k)) is int and 0<plan[k]<=21600 for k in ('task_wall_seconds','native_prereq_wall_seconds','delivery_wall_seconds')),'explicit new C wall budget required'
frozen=dict(schema=1,uuid=ROOT.name,source_relative='src/rev2',files=files,python=py,python_sha256=h(py),protocol_commit=json.loads((ROOT/'ACQUISITION.json').read_bytes())['protocol_commit'],frozen_utc=utc,scope='CPU8 integration only; no GPU or repeated capability soak',review_status='A_SOURCE_ONLY_EXTERNALLY_APPROVED',a_review_report_sha256=review['report_sha256'],a_external_approval_sha256=h(approval_path),cpu8_execution_envelope_sha256=h(ROOT/'CPU8_EXECUTION_ENVELOPE.json'),budget=dict(task_seconds=plan['task_wall_seconds'],d0_seconds=plan['native_prereq_wall_seconds'],delivery_seconds=plan['delivery_wall_seconds']),formal_cases=8,continuation_policy=policy)
a=json.loads((ROOT/'ACQUISITION.json').read_bytes());age=(datetime.datetime.fromisoformat(utc)-datetime.datetime.fromisoformat(a['first_preparation_utc'].replace('Z','+00:00'))).total_seconds()
wall_budget(a,frozen,regs,dict(started_utc=utc,begin_ns=0),dict(task_elapsed_before_watchdog_seconds=age,begin_ns=0,end_ns=0))
write(ROOT/'CAPABILITY_FREEZE.json',frozen)
print(json.dumps(dict(freeze_sha256=h(ROOT/'CAPABILITY_FREEZE.json'),members=len(files),native_gates=native['status'],d0_actual=counts,scope='prospective freeze, not execution PASS'),sort_keys=True))
