"""CPU-only reconstruction of numerical qualification, paired effects and missing blocks."""
from pathlib import Path
import argparse,json,math,hashlib,statistics
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def gmean(values):return math.exp(math.fsum(map(math.log,values))/len(values)) if values else None
def pairs(rows,left,right,keys):
    blocks={}
    for r in rows:
        if r['arm'] not in (left,right):continue
        blocks.setdefault(tuple(r[k] for k in keys),{})[r['arm']]=r
    values=[]
    for key,v in blocks.items():
        if left not in v or right not in v:continue
        a,b=v[left],v[right]
        if a['seconds'] and b['seconds'] and a['qualified'] and b['qualified']:
            values.append(dict(key=key,ratio=a['seconds']/b['seconds']))
    return dict(left=left,right=right,eligible=len(values),all_blocks=len(blocks),
                geometric_ratio=gmean([x['ratio'] for x in values]),left_slower=sum(x['ratio']>1 for x in values),pairs=values)
def recompute(root,verify=False):
    root=Path(root);controls=[];checked=set()
    def vector(h):
        if verify and h not in checked:
            p=root/'vectors'/h[:2]/h
            with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h
            checked.add(h)
    for p in sorted(root.glob('CONTROL-*.json')):
        for s in read(p):
            a,b=s['actual_vectors'],s['reference_vectors']
            assert s['equal']==bool(a and a==b)
            for h in (a or [])+(b or []):vector(h)
            controls.append(s)
    times=[r for p in sorted(root.glob('TIMES-*.json')) for r in read(p)]
    sk=['family','C','B','head','q','rep'];fx={}
    for family,C in sorted({(r['family'],r['C']) for r in times}):
        for crossing in (False,True):
            sub=[r for r in times if r['family']==family and C==r['C'] and (len(r['groups'])>1)==crossing]
            fx[f'{family}/{C}/cross={crossing}']=[pairs(sub,x,'QB',sk) for x in ('WB','PQ','S1')]
    natural=[]
    if (root/'NATURAL_QUAL.json').is_file():
        for r in read(root/'NATURAL_QUAL.json'):
            ref,cand=r['reference_vectors'],r['candidate_vectors']
            assert r['equal']==bool(cand and cand==ref and r['actual_ids']==r['expected_ids'])
            for h in (ref or [])+(cand or []):vector(h)
    if (root/'NATURAL_COST.json').is_file():
        ns=read(root/'NATURAL_COST.json')
        natural=[pairs(ns,x,'QB',['session','id']) for x in ('WB','PQ','S1')]
    spent=[read(p) for p in (root/'units').glob('*/RECEIPT.json')]
    stats={}
    for r in controls:
        k=f"{r['family']}/{r['C']}/{r['arm']}"
        c=stats.setdefault(k,{'equal':0,'attempted_cells':0,'observed':0,'reference_available':0})
        c['attempted_cells']+=1;c['observed']+=int(r['observed']);c['reference_available']+=int(r['ref']);c['equal']+=int(r['equal'])
    return dict(controls=stats,fixed=fx,natural=natural,owned_seconds=sum(r.get('owned_seconds',0) for r in spent),
        process_seconds=sum(r.get('process_seconds',0) for r in spent),units=len(spent),unsuccessful_units=sum(not r.get('success',False) for r in spent),verified_unique_vectors=len(checked))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--verify-objects',action='store_true')
    a=p.parse_args();print(json.dumps(recompute(a.root,a.verify_objects),indent=2))

