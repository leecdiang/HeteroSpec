"""Consecutive independent sessions, immutable planned slots, no formal retries."""
from runtime import *
SALT='heterospec-jsa-third-family-20261011-v1'
def schedule():
    tasks=read(PUB/'CONFIRMATION_INPUTS.json')['tasks'];design=read(DESIGN/'DESIGN.json');cs={c['name']:c for c in design['conditions']};families=['Qwen','SmolLM2','Llama'];blocks=[]
    for session in range(2):
        order=families[session:]+families[:session]
        for family in order:
            for rnd,row in enumerate(design['confirmation']['condition_base_rows']):
                conditions=row[session:]+row[:session]
                tids=sorted([t['id'] for t in tasks],key=lambda tid:(hashlib.sha256(f'{SALT}|order|{session}|{rnd}|{tid}'.encode()).hexdigest(),tid))
                for pos,c in enumerate(conditions):
                    name=f's{session}-{family}-r{rnd}-p{pos}-{c}'
                    blocks.append({'block':name,'session':session,'family':family,'round':rnd,'position':pos,'condition':cs[c],'tasks':tids,'slots':[name+'|'+t for t in tids]})
    assert len(blocks)==144 and len({s for b in blocks for s in b['slots']})==3456
    return blocks

def missing(root,b,reason):
    for slot in b['slots']:
        save(root/'missing'/(slot.replace('/','_').replace('|','--')+'.json'),{'slot':slot,'status':reason,'utc':now()})

def main():
    receipt=read(LOCAL/'F0B_REMOTE_RECEIPT.json');assert receipt['status']=='PASS'
    freeze=read(PUB/'F0B.json');plan=read(PUB/'FORMAL_PLAN.json');assert plan['blocks']==schedule()
    for name,h in freeze['code_sha256'].items():assert sha(Path(__file__).parent/name)==h
    for p,h in freeze['runtime_binaries'].items():assert sha(p)==h
    for pair in models().values():
        for m in pair.values():assert sha(m['path'])==m['sha256']
    root=LOCAL/'runs/formal';root.mkdir(parents=True,exist_ok=False)
    with (root/'SINGLE_WRITER.lock').open('x') as f:f.write(str(os.getpid()))
    save(root/'START.json',{'utc':now(),'freeze_commit':receipt['frozen_sha'],'planned_paid_requests':3600})
    inputs=read(PUB/'CONFIRMATION_INPUTS.json')['families'];warm=read(PUB/'ENGINEERING_INPUTS.json')['warmups']
    choices=read(PUB/'ENGINEERING_RESULTS.json')['implementation']
    for b in plan['blocks']:
        for name,h in freeze['code_sha256'].items():assert sha(Path(__file__).parent/name)==h,'frozen formal code drift'
        name=b['block'];d=root/name;family=b['family'];print('FORMAL',name,flush=True)
        if choices[family][b['condition']['name']]['status']!='ADMITTED':
            missing(root,b,'MISSING_IMPLEMENTATION_BLOCKED');continue
        if not cooldown(root/(name+'-COOLING.json')):
            missing(root,b,'MISSING_HOST_ADMISSION');continue
        by_id={t['id']:t for t in inputs[family]}
        try:
            with Resident(d,family,b['condition'],'formal',False) as s:
                s.complete(warm[family],name+'|warmup',True)
                for tid,slot in zip(b['tasks'],b['slots']):
                    try:s.complete(by_id[tid],slot)
                    except Exception as e:print('FORMAL REQUEST FAILED',slot,type(e).__name__,flush=True)
        except Exception as e:
            save(root/(name+'-BLOCK_FAILURE.json'),{'status':'BLOCK_FAILURE','error':repr(e),'utc':now()})
            for slot in b['slots']:
                target=d/('requests/'+slot.replace('/','_').replace('|','--'))
                if not (target/'REQUEST_STARTED.json').exists():save(root/'missing'/(slot.replace('/','_').replace('|','--')+'.json'),{'slot':slot,'status':'MISSING_BLOCK_FAILURE','utc':now()})
    save(root/'COMPLETE.json',{'utc':now(),'started':len(list(root.rglob('REQUEST_STARTED.json'))),'completed':len(list(root.rglob('COMPLETED.json'))),'missing':len(list((root/'missing').glob('*.json'))),'lifetimes_seconds':sum(read(p)['seconds'] for p in root.rglob('LIFETIME.json'))})
    print('FORMAL FINISHED',flush=True)
if __name__=='__main__':main()
