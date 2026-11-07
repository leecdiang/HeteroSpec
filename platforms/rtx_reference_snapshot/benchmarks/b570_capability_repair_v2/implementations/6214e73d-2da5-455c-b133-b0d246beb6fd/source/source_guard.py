"""Exact source-only inventory and budget checks; no native/library loading."""
import os,json,hashlib,datetime
from pathlib import Path
def need(v,m):
    if not v:raise ValueError(m)
def check_sources(root,freeze):
    root=Path(root).resolve()
    prefixes=['source/','src/rev2/','legacy/repo/benchmarks/b570_supervision_fix_v2/host/']
    wanted={p for p in freeze['files'] if any(p.startswith(x) for x in prefixes)}
    actual=set()
    for prefix in prefixes:
        base=root/prefix
        for p in base.rglob('*'):
            need(not p.is_symlink() and not p.is_junction(),'source alias')
            if p.is_file():
                rel=p.relative_to(root).as_posix();need('__pycache__' not in p.parts and p.suffix not in ['.pyc','.pyo','.pyd','.so','.dll'],'non-source file in import tree')
                actual.add(rel)
    need(actual==wanted,'SOURCE_ONLY_INVENTORY_DRIFT')
    for rel in actual:need(hashlib.sha256((root/rel).read_bytes()).hexdigest()==freeze['files'][rel],'SOURCE_DRIFT')
def actual_d0(root,registrations):
    root=Path(root).resolve();total=0;result=[]
    for r in registrations:
        folder=root/r['run'];count=0
        if str(r['run']).startswith('legacy/runs/'):
            paths=list((folder/'external').glob('ROUND.jsonl'))
            if not paths:paths=list((folder/'external').glob('**/ROUND.jsonl'))
        else:paths=list(folder.glob('*/EVENTS.jsonl'))
        for p in paths:
            raw=p.read_bytes();need(not raw or raw.endswith(b'\n'),'partial D0 journal')
            count+=sum(json.loads(x).get('event')=='CASE_BEGIN' for x in raw.splitlines())
        need(count<=r['case_attempts'],'D0_ACTUAL_EXCEEDS_RESERVATION')
        total+=count;result.append(dict(run=r['run'],reserved=r['case_attempts'],actual=count))
    need(total<=20,'D0_ACTUAL_LIMIT');return dict(actual=total,reservations=result)
def d0_now(root):
    from guards import utc,revision_budget
    root=Path(root);origin=utc(json.loads((root/'ACQUISITION.json').read_bytes())['first_preparation_utc'])
    elapsed=(datetime.datetime.now(datetime.timezone.utc)-origin).total_seconds()
    need(0<=elapsed<=5400,'D0_90_MINUTE_LIMIT')
    regs=json.loads((root/'D0_RESERVATIONS.json').read_bytes());revision_budget(regs);return actual_d0(root,regs)
