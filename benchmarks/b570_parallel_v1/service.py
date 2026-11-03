"""Frozen blind confirmation, then one six-session Williams crossover."""
from experiment import *
from natural import select
METHODS=['S1','PQ','QB','WB']
WILLIAMS=[[0,1,3,2],[1,2,0,3],[2,3,1,0],[3,0,2,1]]
def natural_slot(r,arm,ub,heavy,stage):
    return dict(kind='natural',arm=arm,ub=1 if arm=='S1' else ub,ids=r['prompt_ids'],cap=128,heavy=heavy,stage=stage)
def setup_panel():
    if not (ROOT/'NATURAL_PANEL.json').exists():select()
    rows=read(ROOT/'NATURAL_PANEL.json')['rows'];plan=[]
    for sess in range(6):
        order=sorted(range(12),key=lambda i:hashval(['service-block-v1',sess,rows[i]['id']]))
        for block,i in enumerate(order):
            for a in WILLIAMS[(block+sess)%4]:
                plan.append(dict(session=sess,block=block,i=i,arm=METHODS[a]))
    put_once(ROOT/'NATURAL_SCHEDULE.json',plan)
    put_once(ROOT/'FAST_SCHEDULE.json',[dict(i=i,session=i//2,position='before' if i%2==0 else 'after') for i in range(12)])
    return rows,plan
def confirm():
    rows,_=setup_panel();freeze=read(ROOT/'FREEZE.json');role=freeze['role'];report=[]
    for i,r in enumerate(rows):
        ref=slots_run(f'blind-{i}-R','reference-B','qwen',1024,[natural_slot(r,'S1',1,True,'qual')])[0]
        for a in METHODS+['FAST']:
            cand=slots_run(f'blind-{i}-{a}',role,'qwen',1024,[natural_slot(r,a,freeze['width'],True,'qual')])[0]
            report.append(dict(i=i,id=r['id'],arm=a,equal=bool(cand and ref and cand['vectors']==ref['vectors'] and cand['greedy']==ref['greedy']),
                reference_vectors=ref['vectors'] if ref else None,candidate_vectors=cand['vectors'] if cand else None,expected_ids=ref['greedy'] if ref else None,actual_ids=cand['greedy'] if cand else None))
    put_once(ROOT/'NATURAL_QUAL.json',report)
def costs():
    panel,plan=setup_panel();freeze=read(ROOT/'FREEZE.json');qual=read(ROOT/'NATURAL_QUAL.json')
    summary=[];native=[]
    def fast(i,sess):
        s=[natural_slot(panel[i],'FAST',freeze['width'],False,stage) for stage in ('warmup','measure')]
        unit=f'paired-native-{i:02d}'
        n=run(unit,freeze['role'],job('qwen',1024,s),allow_failure=True)
        rr=n.get('records',[])
        q=next(x for x in qual if x['i']==i and x['arm']=='FAST')
        if len(rr)==2 and q['actual_ids']:assert all(x['greedy']==q['actual_ids'] for x in rr)
        native.append(dict(i=i,id=panel[i]['id'],session=sess,unit=unit,qualified=q['equal'],seconds=rr[1]['seconds'] if len(rr)==2 else None,error=n.get('error')))
    for k,b in enumerate(plan):
        i=b['i'];a=b['arm'];expected=next(x for x in qual if x['i']==i and x['arm']==a)
        if b['session']==i//2 and i%2==0 and k%4==0:fast(i,b['session'])
        ss=[natural_slot(panel[i],a,freeze['width'],False,s) for s in ('warmup','measure')]
        unit=f'paired-{k:03d}'
        n=run(unit,freeze['role'],job('qwen',1024,ss),timeout=1200,allow_failure=True)
        if len(n.get('records',[]))!=2 and n.get('error') in ('128 MiB device reserve','2 GiB host reserve'):
            unit+='-retry'
            n=run(unit,freeze['role'],job('qwen',1024,ss),timeout=1200,allow_failure=True)
        rs=n.get('records',[]);measured=rs[1] if len(rs)==2 else None
        if measured and expected['actual_ids'] is not None:assert all(v['greedy']==expected['actual_ids'] for v in rs)
        receipt=read(ROOT/'units'/unit/'RECEIPT.json')
        summary.append(dict(**b,id=panel[i]['id'],unit=unit,qualified=expected['equal'],seconds=measured['seconds'] if measured else None,
            warmup_seconds=rs[0]['seconds'] if rs else None,process_seconds=receipt['process_seconds'],owned_seconds=receipt['owned_seconds'],
            graph_calls=measured['graph_calls'] if measured else None,load_seconds=n.get('load_seconds'),error=n.get('error')))
        if b['session']==i//2 and i%2==1 and k%4==3:fast(i,b['session'])
    put_once(ROOT/'NATURAL_COST.json',summary)
    assert len(native)==12
    put_once(ROOT/'FAST_COST.json',native)
    phases=[]
    order=sorted(range(len(panel)),key=lambda i:(panel[i]['tokens'],panel[i]['id']))
    for i in (order[0],order[-1]):
        for a in ('QB','WB'):
            s=dict(natural_slot(panel[i],a,freeze['width'],False,'phase'),phases=True)
            n=run(f'natural-phase-{i}-{a}',freeze['role'],job('qwen',1024,[s]),allow_failure=True)
            rr=n.get('records',[])
            expected=next(r for r in qual if r['i']==i and r['arm']==a)
            if rr and expected['actual_ids']:assert rr[0]['greedy']==expected['actual_ids']
            phases.append(dict(i=i,arm=a,tokens=panel[i]['tokens'],qualified=expected['equal'],phase=rr[0] if rr else None,error=n.get('error')))
    put_once(ROOT/'NATURAL_PHASE.json',phases)
if __name__=='__main__':{'confirm':confirm,'cost':costs}[sys.argv[1]]()
