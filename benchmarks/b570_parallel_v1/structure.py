"""Fixed-work common-state comparison, with a separate original scalar reference."""
from host import *
import statistics,math
from functools import lru_cache
PLAN=ROOT/'GEOMETRY_PLAN.json'
ARMS=['S1','PQ','QB','WB','FAST']
def select_configs(role):
    gate=[]
    for fam,C in [('qwen',1024),('qwen',4096),('qwen',2048),('smol',4096)]:
        n=run(f'admit-{fam}-{C}-{role}-u32',role,job(fam,C,[dict(kind='admit',ub=32)]),allow_failure=True)
        gate.append((fam,C,n['status'],n.get('min_free_device'),n.get('error')))
    write(ROOT/f'ADMISSION-{role}.json',gate);return gate
@lru_cache
def sequences(fam):
    if fam in ('qwen','qwen_target'):return read(PLAN)['tokens']
    pool=read(PR165/'pool-00/POOL.json')['rows']
    selected=sorted(pool,key=lambda v:hashval(['smol-heldout',v['id']]))[:4]
    txt=ROOT/f'{fam}-input.jsonl';out=ROOT/f'{fam}-tokenized.jsonl'
    if not txt.exists():
        txt.write_text(''.join(json.dumps({'id':v['id'],'formatted_prompt':v['text']})+'\n' for v in selected),encoding='utf-8')
        tok=Path('I:/HeteroSpec/b570-llama-20261102/tokenizer-build-00/build/Release/operator_replay.exe')
        command([tok,MODELS[fam][0],txt,out],ROOT/f'{fam}-tokenizer.log')
    ids=[x for line in out.read_text(encoding='utf-8').splitlines() for x in json.loads(line)['prompt_ids']]
    return (ids*((4200+len(ids)-1)//len(ids)))[:4200]
def configurations(role):
    a=read(ROOT/('ADMISSION-'+role+'.json'));ok={(m,c) for m,c,s,*_ in a if s=='COMPLETE'}
    assert ('qwen',1024) in ok and ('smol',4096) in ok
    long=next((c for c in (4096,2048) if ('qwen',c) in ok and read(ROOT/f'units/admit-qwen-{c}-reference-u1/RECEIPT.json')['success']),None)
    return [('qwen',1024,'Q1024')]+([('qwen',long,'Q'+str(long))] if long else [])+[('smol',4096,'S4096')]
def seed(fam,C,key):
    coords=read(PLAN)[key];heads=sorted({p['head'] for p in coords})
    role='reference-D' if fam=='qwen_target' else 'reference-O'
    if not (ROOT/f'R-{fam}-{C}.json').exists():
        write(ROOT/f'R-{fam}-{C}.json',dict(context=C,original_manifest=sha(ROOT/role/'FILES.json'),models=MODELS[fam][:1] if fam=='qwen_target' else MODELS[fam],anchor=sha(ROOT/'ORIGINAL_ANCHOR.json'),recipe='original numerical DLLs, UB1 P1 8 threads F16 KV, fixed original query tokens'))
    return run(f'seed-{fam}-{C}',role,job(fam,C,[dict(kind='seed',ids=sequences(fam),heads=heads)]),timeout=1800)
def slot(fam,C,point,arm,heavy,trace=False):
    h=point['head'];w=point['q']
    return dict(kind='grid',arm=arm,base=h,ids=sequences(fam)[h:h+w],state=str(ROOT/f'units/seed-{fam}-{C}/native/state-{h}.bin'),ub=w,heavy=heavy,trace=trace)
def refs(fam,C,key):
    points=read(PLAN)[key];tag=f'r-grid-{fam}-{C}'
    slots=[dict(slot(fam,C,p,'S1',True),ub=1) for p in points]
    return recover(tag,'reference-O',fam,C,slots)
def recover(tag,role,fam,C,slots):
    """Continue only the unmeasured suffix after an owned process was cleaned up."""
    records=[]
    offset=0
    stalled=0
    for attempt in range(20):
        name=tag if attempt==0 else f'{tag}-resume{attempt}-at{offset}'
        pending=slots[offset:] if attempt==0 else slots[offset:offset+8]
        n=run(name,role,job(fam,C,pending),timeout=1800,allow_failure=True)
        part=n.get('records',[])
        assert all(p['slot']==s for p,s in zip(part,pending))
        records.extend(part);offset+=len(part)
        if offset==len(slots):return dict(records=records,status='COMPLETE')
        stalled=0 if part else stalled+1
        if stalled>=2 or n.get('error') not in (None,'128 MiB device reserve','2 GiB host reserve'):break
    return dict(records=records,status='INCOMPLETE',error=n.get('error') or n['status'])
def compare(fam,C,key,role,points=None,tag='qual'):
    allpoints=read(PLAN)[key]
    points=points or allpoints;reference=refs(fam,C,key)['records'];results=[]
    # Separate short units keep failures local without timing a selected subset.
    for B in sorted({p['B'] for p in points}):
        pp=[p for p in points if p['B']==B]
        for arm in ARMS:
            slots=[slot(fam,C,p,arm,True) for p in pp]
            name=f'{tag}-{role}-{fam}-{C}-b{B}-{arm}'
            n=recover(name,role,fam,C,slots)
            for i,p in enumerate(pp):
                row=n.get('records',[])[i] if i<len(n.get('records',[])) else None
                j=allpoints.index(p);ref=reference[j] if j<len(reference) else None
                results.append(dict(family=fam,C=C,**p,arm=arm,success=row is not None,
                   equal=row['vectors']==ref['vectors'] if row and ref else False,
                   differing_rows=[k for k,(l,r) in enumerate(zip(row['vectors'],ref['vectors'],strict=True)) if l!=r] if row and ref else None,
                   error=n.get('error'),unit=name))
    dest=ROOT/f'{tag}-{role}-{fam}-{C}.json'
    if dest.exists():assert read(dest)==results
    else:write(dest,results)
    return results
if __name__=='__main__':
    role=sys.argv[2] if len(sys.argv)>2 else 'candidate-A'
    if sys.argv[1]=='admit':select_configs(role)
    elif sys.argv[1]=='seed':
        for fam,C,key in configurations(role):seed(fam,C,key);refs(fam,C,key)
    elif sys.argv[1]=='pilot':
        key='Q1024';points=[p for p in read(PLAN)[key] if p['B']==256 and p['q'] in (2,8,16,32)]
        compare('qwen',1024,key,role,points,'pilot')
    elif sys.argv[1]=='qual':
        for fam,C,key in configurations(role):compare(fam,C,key,role)

