"""Read-only pre-pilot source/proof/graph-reuse audit; no native execution."""
from pathlib import Path
import datetime,hashlib,json,sys,time
root=Path(sys.argv[1]);work=root/'m2-run-03';audit=root/'m2-audit-03'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
declaration=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    rule='Every qualified clean transaction with >=2 verification cycles must record graph reuse; full live/replay timing receipts will be checked again. Same criterion as original M1 panel.',
    source_and_proof_sha_required=True,declared_before_any_M2_pilot=True,new_native_jobs=0)
with(audit/'ADDITIONAL_PROFILE_CRITERIA.json').open('x')as f:json.dump(declaration,f,indent=2)
while not(work/'qualification-01/NATIVE_CHECKS_COMPLETE.json').exists():
    if(audit/'STATUS.json').exists():raise SystemExit('Native gate stopped; audit deferred for repair')
    time.sleep(5)
freeze=read(work/'SOURCE_FREEZE.json')
for p,digest in freeze['driver_sources'].items():assert sha(Path(p))==digest
summary=read(work/'qualification-01/NATIVE_CHECKS_COMPLETE.json')
for row in summary['proofs']:assert sha(Path(row['path']))==row['sha256'] and read(Path(row['path']))['passed']
records=[]
for epoch in ('m2-run-01','m2-run-02','m2-run-03'):
    for p in(root/epoch/'qualification-01/runs').glob('*/native/*/receipt.json'):
        r=read(p)
        if r.get('capture')is not False or not r.get('draft_enabled'):continue
        assert all(v==0 for v in r['observed_API_calls_within_service'].values())
        if len(r['cycles'])>=2:assert r['graphs_reused']>0
        records.append(dict(logical_path=str(p.relative_to(root)),sha256=sha(p),cycles=len(r['cycles']),graphs_reused=r['graphs_reused'],proposal_mode=r.get('proposal_mode')))
with(audit/'PRE_PILOT_ADDITIONAL_PROFILE_CHECKED.json').open('x')as f:json.dump(dict(passed=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=records,
    qualification_proofs_hash_checked=True,source_bytes_unchanged=True,new_native_jobs=0),f,indent=2)
print(json.dumps(dict(passed=True,qualified_clean_receipts=len(records))),flush=True)
