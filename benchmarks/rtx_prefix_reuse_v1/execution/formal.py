"""Held-out runner. Requires authenticated peer receipts; never creates them."""
from common_calibration import *
def gate():
    # A local boolean alone is deliberately insufficient: retain fetched immutable
    # peer receipt bytes and a receipt tying both exact cohort/tokenizer identities.
    g=read(ROOT/'COMMON_BLIND_GATE.json')
    for role in ('rtx','b570'):
        x=g[role];assert x['commit'] and x['repository_url'].startswith('https://github.com/leecdiang/HeteroSpec/')
        for name,h in x['receipt_files'].items():assert sha(ROOT/name)==h
    assert g['shared_cohort_sha256']==sha(ROOT/'common-panel.json')
    assert g['shared_token_rows_sha256']==sha(ROOT/'tokenize01/tokens.jsonl')
    assert g['capacity']==4096 and g['both_source_policy_freezes_verified'] is True
    assert read(ROOT/'SOURCE_POLICY_FREEZE.json')['source_sha256']==study.digest(read(ROOT/'candidate07/binding.json'))
    return read(ROOT/'common-cohort.json')['test']
def unit(r,i,arm,kind):
    policy=read(ROOT/'COMMON_POLICY.json');panel=read(ROOT/'common-panel.json')
    return dict(id=f'i{i:02}/{arm}/{kind}',tokens=r['request_ids'],head=study.lcp(r['cached_ids'],r['request_ids']),arm=arm,cap=128,capture=kind=='heavy',state=str(ROOT/f'main-r-{i:02}/r0/prefix.bin'),selection_bin=panel['test'][i]['selection_bin'],policy={k:v['arm'] for k,v in policy['bins'].items()})
def refs():
    for i,r in enumerate(gate()):
        run(f'main-r-{i:02}','oracle02',dict(mode='requests',capacity=4096,units=[dict(id=f'r{k}',tokens=r['request_ids'],head=study.lcp(r['cached_ids'],r['request_ids']),arm='R',cap=128,capture=True) for k in range(2)]),requests=2)
def qualify():
    proof=[]
    for i,r in enumerate(gate()):
        units=[unit(r,i,a,k) for a in study.ARMS for k in ('heavy','off')]
        d=run(f'main-q-{i:02}','candidate07',dict(mode='requests',capacity=4096,units=units),requests=8)
        ref=ROOT/f'main-r-{i:02}/r0';rr=read(ref/'receipt.json');v={p.name:sha(p) for p in ref.glob('*.f32')}
        for arm in ('R-repeat',*study.ARMS):
            heavy=ROOT/f'main-r-{i:02}/r1' if arm=='R-repeat' else d/f'i{i:02}'/arm/'heavy';h=read(heavy/'receipt.json');off=h if arm=='R-repeat' else read(heavy.parent/'off/receipt.json')
            if arm!='R-repeat':
                planned=study.plan(study.lcp(r['cached_ids'],r['request_ids']),len(r['request_ids'])-study.lcp(r['cached_ids'],r['request_ids']),h['arm'])
                assert h['calls']==off['calls']==[{k:x[k] for k in ('head','width')} for x in planned]
                assert h['physical_dense_head']==study.lcp(r['cached_ids'],r['request_ids'])
            assert h['final_position']==len(r['request_ids'])+len(h['output'])-2
            proof.append(dict(index=i,arm=arm,vectors_equal=v=={p.name:sha(p) for p in heavy.glob('*.f32')},state_equal=sha(ref/'final.bin')==sha(heavy/'final.bin'),output_equal=rr['output']==h['output']==off['output'],position_equal=rr['final_position']==h['final_position']==off['final_position']))
    put(ROOT/'MAIN_QUALIFICATION.json',proof)
    assert all(all(v for k,v in r.items() if k.endswith('equal')) for r in proof)
def cost():
    rows=gate();proof=read(ROOT/'MAIN_QUALIFICATION.json');assert len(proof)==160 and all(all(v for k,v in r.items() if k.endswith('equal')) for r in proof)
    p=read(ROOT/'common-panel.json');schedule=study.schedule(p);put(ROOT/'main-schedule.json',schedule)
    byid={r['id']:(i,r) for i,r in enumerate(rows)}
    for s in range(4):
        units=[unit(byid[x['id']][1],byid[x['id']][0],x['arm'],x['kind']) for x in schedule['records'] if x['session']==s]
        run(f'main-cost-s{s}','candidate07',dict(mode='requests',capacity=4096,units=units),requests=256)
def aligned():
    rows=gate()[:8];proof=[]
    for i,r in enumerate(rows):
        def make(a,k):return dict(id=a+'-'+k,tokens=r['request_ids'],head=0,arm=a,cap=128,capture=k!='off')
        ref=run(f'aligned-r-{i:02}','oracle02',dict(mode='requests',capacity=4096,units=[make('R',k) for k in ('r0','r1')]),requests=2)
        d=run(f'aligned-q-{i:02}','candidate07',dict(mode='requests',capacity=4096,units=[make(a,k) for a in study.FIXED for k in ('heavy','off')]),requests=6)
        baseline=ref/'R-r0';b=read(baseline/'receipt.json');v={p.name:sha(p) for p in baseline.glob('*.f32')}
        for a,p in [('R-repeat',ref/'R-r1')]+[(a,d/(a+'-heavy')) for a in study.FIXED]:
            h=read(p/'receipt.json');o=h if a=='R-repeat' else read(d/(a+'-off')/'receipt.json')
            proof.append(dict(index=i,arm=a,vectors_equal=v=={p.name:sha(p) for p in p.glob('*.f32')},state_equal=sha(baseline/'final.bin')==sha(p/'final.bin'),output_equal=b['output']==h['output']==o['output']))
    put(ROOT/'ALIGNED_QUALIFICATION.json',proof);assert all(all(v for k,v in p.items() if k.endswith('equal')) for p in proof)
    for s in range(2):
        units=[]
        for i,r in enumerate(rows):
            for j in range(3):
                a=study.FIXED[(i+s+j)%3]
                for kind in ('warmup','measure'):units.append(dict(id=f'i{i:02}/{a}/{kind}',tokens=r['request_ids'],head=0,arm=a,cap=128,capture=False))
        run(f'aligned-cost-s{s}','candidate07',dict(mode='requests',capacity=4096,units=units),requests=48)
if __name__=='__main__':
    for arg in sys.argv[1:]:globals()[arg]()
