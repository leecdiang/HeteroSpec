"""Post-timing descriptive audit of complete formal proposal transactions.

No new inferential contrast or GPU work. Works on private raw paths or the
materialized derived public bundle's matching relative layout.
"""
from pathlib import Path, PurePosixPath
import argparse, json

def require(ok,message):
    if not ok:raise ValueError(message)

def audit(work):
    work=Path(work).resolve();read=lambda p:json.loads(p.read_text())
    plan=read(work/'panel-01/PLAN.json');checked=read(work/'panel-01/CHECKED.json')
    require(len(checked)==16,'All fixed workers required');workers={x['id']:x for x in plan['workers']};blocks={}
    for worker in checked:
        meta=workers[worker['id']];require(worker['status']=='COMPLETE' and worker['native_checks_passed'],'Native evidence first')
        for call in worker['requests'][2:]:
            name=call['native_receipt'];require('/panel-01/' in name,'Bound receipt path required')
            relative=PurePosixPath('panel-01/'+name.split('/panel-01/',1)[1]);require('..' not in relative.parts,'Safe relative path')
            row=read(work/str(relative));key=(call['root'],meta['session'])
            armset=blocks.setdefault(key,{});require(meta['arm'] not in armset,'Duplicate block/arm')
            armset[meta['arm']]={k:row[k] for k in ('ids','eog','stop_reason','cycles')}
    require(len(blocks)==64 and all(set(v)==set(plan['arms']) and all(x==next(iter(v.values())) for x in v.values()) for v in blocks.values()),'Formal control transaction mismatch')
    return dict(passed=True,root_session_blocks=64,arms_per_block=4,all_ids_EOG_and_complete_proposal_acceptance_transactions_equal=True,
        scope='All256 formal measurements; complete saved native cycles compared across the four real arms; no internal-state or full-vector claim for clean formal requests')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path);a=p.parse_args();result=audit(a.work)
    if a.out:
        with a.out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    else:print(json.dumps(result,indent=2))
