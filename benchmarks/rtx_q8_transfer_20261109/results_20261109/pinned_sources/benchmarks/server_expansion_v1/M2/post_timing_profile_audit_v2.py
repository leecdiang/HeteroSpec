"""Apply the prospectively recorded M1 clean graph-reuse guard to all slots."""
from pathlib import Path
import datetime,hashlib,json,sys,time
root=Path(sys.argv[1]);work=root/'m2-run-03';audit=root/'m2-audit-03'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
while not(audit/'ADDITIONAL_PROFILE_CRITERIA.json').exists():
    if(audit/'STATUS.json').exists():raise SystemExit('Declaration absent after coordinator terminal; retain failure')
    time.sleep(1)
while not(work/'panel-01/CHECKED.json').exists():
    if(audit/'STATUS.json').exists():raise SystemExit('Full panel absent; no full timing profile claim')
    time.sleep(2)
plan=read(work/'panel-01/PLAN.json');rows=[]
for w in plan['workers']:
    job=read(work/'panel-01'/w['job']);dest=work/'panel-01/runs'/w['id']
    for entry in job['inputs']:
        p=dest/'native'/entry['name']/'receipt.json';r=read(p)
        assert not r['capture']and all(v==0 for v in r['observed_API_calls_within_service'].values())
        if len(r['cycles'])>=2:assert r['graphs_reused']>0
        rows.append(dict(worker=w['id'],request=entry['name'],receipt_sha256=sha(p),cycles=len(r['cycles']),graphs_reused=r['graphs_reused']))
assert len(rows)==144
with(audit/'PILOT_ADDITIONAL_PROFILE_CHECKED.json').open('x')as f:json.dump(dict(passed=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    criteria_sha256=sha(audit/'ADDITIONAL_PROFILE_CRITERIA.json'),records=rows,all144_clean_requests_checked=True,new_native_jobs=0),f,indent=2)
print(json.dumps(dict(passed=True,requests=len(rows))),flush=True)
