from host import *
from datetime import datetime,timezone
def coords(C,boundaries,widths):
    return [dict(B=B,q=q,head=h,groups=[q] if h+q<=B else [B-h,h+q-B])
            for B in boundaries for q in widths for h in ([B-q] if q==1 else [B-q,B-q//2]) if h+q<=C]
def register():
    panel=read(DATA);tokens=panel['MATH500/test/prealgebra/1804.json']['prompt_ids']+panel['GSM8K/train/1184']['prompt_ids']
    inputs=(tokens*((4200+len(tokens)-1)//len(tokens)))[:4200]
    write(ROOT/'GEOMETRY_PLAN.json',dict(utc=datetime.now(timezone.utc).isoformat(),reference='original PR152 numerical DLLs scalar P1, context-specific separately instantiated anchors',models=read(ROOT/'ASSETS.json'),tokens=inputs,
        numerical='bitwise all vocabulary rows on common physical KV state and identical teacher-forced token work',
        Q1024=coords(1024,[256,512,768],[1,2,4,8,16,32]),Q4096=coords(4096,[1024,1536,2048,3072],[1,2,4,8,16,32]),
        Q2048=coords(2048,[1024,1536],[1,2,4,8,16,32]),S4096=coords(4096,[256,2048],[2,8,16,32]),arms=['S1','PQ','QB','WB','FAST'],
        repeats=3,qualification_before_cost=True,context_fallback='Q4096 then Q2048 if either original or wide candidate cannot admit both all-GPU contexts at 128MiB/2GiB reserve; unsupported long cells recorded.',
        natural={'context':1024,'candidate_width':32,'cap':128,'domains':['code','math'],'ranges':[[80,255],[256,511],[512,800]],'per_cell':2,'sessions':6,'arms':['S1','PQ','QB','WB'],'immediate_warmup':True,'estimator':'equal input/session paired-log ratio','alignment':'Fresh dense prefix starts at zero. No artificial shift to induce a cut.'},
        phases='Teacher-forced start state restoration outside measured target query interval. Identical all-row logits and greedy reads. Natural service includes fresh context through destruction. FAST numerical failures retained outside qualified rankings.'))
def admit(fam,C,role,ub):
    name=f'admit-{fam}-{C}-{role}-u{ub}'
    n=run(name,role,job(fam,C,[dict(kind='admit',ub=ub)]),allow_failure=True)
    return n.get('status')=='COMPLETE'
def references():
    setup()
    if not (ROOT/'GEOMETRY_PLAN.json').exists():register()
    for fam,C in [('qwen',1024),('qwen',4096),('qwen',2048),('smol',4096)]:
        admit(fam,C,'reference',1)
    slots=[dict(kind='natural',arm='S1',ids=read(DATA)[read(OLD/f'run-primary/B1-{i}.job.json')['slots'][0]['input_id']]['prompt_ids'],ub=1,cap=128,heavy=True) for i in (4,6,2)]
    n=run('original-P1-anchor','reference',job('qwen',1024,slots))
    for i,row in zip((4,6,2),n['records']):
        ref=read(PR165/f'units/original-{i}/native/result.json')['requests'][0]
        hashes=[ref['vectors']['target_initial' if j==0 else f'target_ordinary/{j}']['sha256'] for j in range(ref['endpoint']['length'])]
        assert hashes==row['vectors'] and ref['endpoint']['ids']==row['greedy']
    write(ROOT/'ORIGINAL_ANCHOR.json',dict(status='ORIGINAL_384_VECTORS_PRESERVED',source_manifest=sha(ROOT/'reference/FILES.json')))
if __name__=='__main__':references()
