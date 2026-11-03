"""Frozen blind confirmation, then one six-session Williams crossover."""
from experiment import *
from natural import select
METHODS=['S1','PQ','QB','WB']
WILLIAMS=[[0,1,3,2],[1,2,0,3],[2,3,1,0],[3,0,2,1]]
def natural_slot(r,arm,ub,heavy,stage):
    return dict(kind='natural',arm=arm,ub=ub,ids=r['prompt_ids'],cap=128,heavy=heavy,stage=stage)
def setup_panel():
    if not (ROOT/'NATURAL_PANEL.json').exists():select()
    rows=read(ROOT/'NATURAL_PANEL.json')['rows'];plan=[]
    for sess in range(6):
        order=sorted(range(12),key=lambda i:hashval(['service-block-v1',sess,rows[i]['id']]))
        for block,i in enumerate(order):
            for a in WILLIAMS[(block+sess)%4]:
                plan.append(dict(session=sess,block=block,i=i,arm=METHODS[a]))
    put_once(ROOT/'NATURAL_SCHEDULE.json',plan)
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
    summary=[]
    for k,b in enumerate(plan):
        i=b['i'];a=b['arm'];expected=next(x for x in qual if x['i']==i and x['arm']==a)
        ss=[natural_slot(panel[i],a,freeze['width'],False,s) for s in ('warmup','measure')]
        n=run(f'paired-{k:03d}',freeze['role'],job('qwen',1024,ss),timeout=1200,allow_failure=True)
        if len(n.get('records',[]))!=2 and n.get('error') in ('128 MiB device reserve','2 GiB host reserve'):
            n=run(f'paired-{k:03d}-retry',freeze['role'],job('qwen',1024,ss),timeout=1200,allow_failure=True)
        rs=n.get('records',[]);measured=rs[1] if len(rs)==2 else None
        if measured and expected['actual_ids'] is not None:assert all(v['greedy']==expected['actual_ids'] for v in rs)
        summary.append(dict(**b,id=panel[i]['id'],qualified=expected['equal'],seconds=measured['seconds'] if measured else None,
            graph_calls=measured['graph_calls'] if measured else None,load_seconds=n.get('load_seconds'),error=n.get('error')))
    put_once(ROOT/'NATURAL_COST.json',summary)
if __name__=='__main__':{'confirm':confirm,'cost':costs}[sys.argv[1]]()

