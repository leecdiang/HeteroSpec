"""One fixed design. Preserve missing cells and the first failed native attempt."""
from structure import *
from itertools import groupby
ROLE='candidate-D'
def put_once(path,value):
    if path.exists():assert read(path)==value
    else:write(path,value)
def slots_run(tag,role,fam,C,slots,**opts):
    out=[None]*len(slots);i=0
    while i<len(slots):
        name=f'{tag}-at{i}'
        n=run(name,role,job(fam,C,slots[i:],**opts),timeout=1800,allow_failure=True)
        part=n.get('records',[])
        for row in part:
            assert row['slot']==slots[i];out[i]=row;i+=1
        if i==len(slots):break
        # A failed coordinate gets one fresh owned process. Following coordinates
        # retain their own opportunity even if the failed slot cannot be admitted.
        if n['status']!='COMPLETE':
            if n.get('error') in ('128 MiB device reserve','2 GiB host reserve'):
                r=run(f'{tag}-single{i}',role,job(fam,C,[slots[i]],**opts),timeout=900,allow_failure=True)
                if r.get('records'):out[i]=r['records'][0]
            i+=1
        else:raise ValueError('incomplete successful process')
    return out
def config(fam,C):
    return ('Q' if fam.startswith('qwen') else 'S')+str(C)
def control(fam,C):
    key=config(fam,C);points=read(PLAN)[key]
    seed(fam,C,key)
    records=[]
    for B,iterator in groupby(points,key=lambda p:p['B']):
        group=list(iterator);base=f'ctlB-{fam}-{C}-b{B}'
        original=[dict(slot(fam,C,p,'S1',True),ub=1) for p in group]
        # Original C1024 references already recorded are consumed in place.
        lookup={}
        if C==1024:
            for u in (ROOT/'units').glob('r-grid-qwen-1024*'):
                for r in read(u/'native/result.json')['records']:lookup[hashval(r['slot'])]=r
        missing=[s for s in original if hashval(s) not in lookup]
        if missing:
            new=slots_run(base+'-R','reference-D',fam,C,missing)
            lookup.update((hashval(s),r) for s,r in zip(missing,new))
        for arm in ARMS:
            rows=slots_run(base+'-'+arm,ROLE,fam,C,[slot(fam,C,p,arm,True) for p in group])
            for p,s,r in zip(group,original,rows):
                ref=lookup.get(hashval(s));diff=None
                if r and ref:
                    diff=[i for i,(v,w) in enumerate(zip(r['vectors'],ref['vectors'],strict=True)) if v!=w]
                records.append(dict(family=fam,C=C,**p,arm=arm,observed=r is not None,ref=ref is not None,equal=diff==[],first_diff=diff[0] if diff else None,
                     graph_calls=r['graph_calls'] if r else None,greedy=r['greedy'] if r else None,actual_vectors=r['vectors'] if r else None,reference_vectors=ref['vectors'] if ref else None))
        put_once(ROOT/f'{base}.json',[r for r in records if r['B']==B])
    put_once(ROOT/f'CONTROL-{fam}-{C}.json',records)
def fixed(fam,C):
    checks=read(ROOT/f'CONTROL-{fam}-{C}.json')
    for rep in range(3):
        for B in sorted({r['B'] for r in checks}):
            group=[r for r in checks if r['B']==B]
            # Same checkpoint, inputs and all-row outputs across arms. Mix the
            # ordering within each replicate, without looking at any timing.
            group.sort(key=lambda r:hashval(['common-state-v1',rep,r['head'],r['q'],r['arm']]))
            ss=[slot(fam,C,r,r['arm'],False) for r in group]
            rows=slots_run(f'timeB-{fam}-{C}-b{B}-r{rep}',ROLE,fam,C,ss)
            table=[]
            for g,r in zip(group,rows):
                if r and g['greedy'] is not None:assert r['greedy']==g['greedy']
                table.append(dict(family=fam,C=C,B=B,head=g['head'],q=g['q'],arm=g['arm'],groups=g['groups'],rep=rep,qualified=g['equal'],seconds=r['seconds'] if r else None,calls=r['graph_calls'] if r else None))
            put_once(ROOT/f'TIMES-{fam}-{C}-b{B}-r{rep}.json',table)
if __name__=='__main__':{'control':control,'fixed':fixed}[sys.argv[1]](sys.argv[2],int(sys.argv[3]))

