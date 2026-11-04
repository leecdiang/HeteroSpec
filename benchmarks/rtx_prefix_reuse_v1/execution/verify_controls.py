"""Read-only verification of every timed/warm aligned-control endpoint and plan."""
from analyze import *
proof=[]
for s in range(2):
    launch=read(ROOT/f'aligned-cost-s{s}/launch.json');freeze=read(ROOT/'SOURCE_POLICY_FREEZE.json')
    assert launch['exe']==freeze['source']['exe'] and launch['source']==freeze['source']['source']
    units=read(ROOT/f'aligned-cost-s{s}/input.json')['units'];assert len(units)==48
    for u in units:
        i=int(u['id'].split('/')[0][1:]);r=read(ROOT/f'aligned-cost-s{s}'/u['id']/'receipt.json');ref=read(ROOT/f'aligned-r-{i:02}/R-r0/receipt.json')
        planned=[{k:x[k] for k in ('head','width')} for x in study.plan(0,len(u['tokens']),u['arm'])]
        assert r['output']==ref['output'] and r['final_position']==ref['final_position'] and r['calls']==planned and r['physical_dense_head']==0
        proof.append(dict(session=s,id=u['id'],passed=True))
put(ROOT/'ALIGNED_TIMING_VALIDATION.json',dict(slots=len(proof),proof=proof));print('all96 aligned timed/warm endpoints and plans passed')
