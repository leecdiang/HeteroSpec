"""Two fixed cells for the explicitly mapped 64-dimensional 9:3 GQA case."""
from experiment import *
def probe():
    c=1024;pts=[dict(B=256,q=8,head=h,groups=g) for h,g in [(248,[8]),(252,[4,4])]]
    put_once(ROOT/'TINY_PROTOCOL.json',dict(points=pts,C=c,arms=ARMS,purpose='guard-specific geometry check; no timing or model-wide claim',oracle=sha(ROOT/'reference-D/FILES.json')))
    for r in ('reference-D',ROLE):
        d=run(f'tiny-gate-{r}',r,job('tiny',c,[dict(kind='admit',ub=1 if r.startswith('reference') else 8)]),allow_failure=True)
        if d['status']!='COMPLETE':
            put_once(ROOT/'TINY_RESULT.json',{'status':'CAPACITY','role':r});return
    seq=sequences('tiny')
    run('seed-tiny-1024','reference-D',job('tiny',c,[dict(kind='seed',ids=seq,heads=[248,252])]))
    refs=slots_run('tiny-oracle','reference-D','tiny',c,[dict(slot('tiny',c,p,'S1',True),ub=1) for p in pts])
    out=[]
    for a in ARMS:
        cand=slots_run('tiny-'+a,ROLE,'tiny',c,[slot('tiny',c,p,a,True) for p in pts])
        for p,r,s in zip(pts,cand,refs):out.append(dict(**p,arm=a,actual=r['vectors'] if r else None,reference=s['vectors'] if s else None,equal=bool(r and s and r['vectors']==s['vectors'])))
    put_once(ROOT/'TINY_RESULT.json',out)
if __name__=='__main__':probe()

