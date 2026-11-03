"""Prospective allocator-only capacity intervention. No changes to placement or kernels."""
from structure import *
def investigate():
    # Test one allocator limit chosen from the 128 MiB required reserve.
    # Do not select separate allocation policies by arm or by observed timing.
    block=128*1024**2
    for role,ub in [('reference-B',1),('candidate-B',32)]:
        for draft_ctx in (True,False):
            name=f'alloc128-{role}-qwen-1024-draft{int(draft_ctx)}'
            r=run(name,role,job('qwen',1024,[dict(kind='admit',ub=ub,draft_context=draft_ctx)],block_bytes=block),allow_failure=True)
            print(name,r.get('min_free_device'),r.get('error'),flush=True)
def smoke():
    for fam,C,key in [('smol',4096,'S4096'),('qwen',4096,'Q4096')]:
        seed(fam,C,key)
        # Compare both sides of the earliest boundary first. Keep full refs for confirmation.
        points=read(PLAN)[key];B=min(p['B'] for p in points)
        points=[p for p in points if p['B']==B and p['q'] in (8,32)]
        rs=run(f'first-ref-{fam}-{C}','reference-B',job(fam,C,[dict(slot(fam,C,p,'S1',True),ub=1) for p in points]),allow_failure=True)
        for a in ARMS:
            n=run(f'first-{fam}-{C}-{a}','candidate-B',job(fam,C,[slot(fam,C,p,a,True) for p in points]),allow_failure=True)
            print(fam,C,a,[(r['slot']['base'],len(r['vectors']),r['vectors']==ref['vectors']) for r,ref in zip(n.get('records',[]),rs.get('records',[]))],flush=True)
if __name__=='__main__':investigate();smoke()

