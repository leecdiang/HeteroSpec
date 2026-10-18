"""CPU-only, deterministic schedule and logical visibility specification."""
import argparse
import hashlib
import json
import random

PARENT = 'a1f15bfc8222054aa7b94b40f41af0dd0492ddab'
ORDERS = ((0,1,3,2),(1,2,0,3),(2,3,1,0),(3,0,2,1))

def visibility(logical, physical, q):
    if any(type(x) is not int for x in (logical,physical,q)):
        raise ValueError('strict integer extents')
    if not 1 <= q <= logical <= physical <= 4096:
        raise ValueError('invalid extents')
    return [[k < logical-q+j+1 for k in range(physical)] for j in range(q)]

def build():
    cells=[]
    for panel, extents in [('B0',(1023,1024)),('T0',(2,4))]:
        for extent in extents:
            for value in (0,1):
                if panel=='B0':
                    arms=[{'name':n,'layout':'QB','physical':extent+d,'storage':'permuted'}
                          for n,d in [('native_A',0),('native_B',0),('pad_1',1),('pad_2',2)]]
                    q,L=2,extent
                else:
                    arms=[{'name':n,'layout':l,'physical':256,'storage':s} for n,l,s in
                          [('QB_A','QB','permuted'),('QB_B','QB','permuted'),
                           ('QH_permuted','QH_C','permuted'),('QH_compact','QH_C','compact')]]
                    q,L=extent,256
                cells.append(dict(id=f'{panel}-{extent}-v{value}',panel=panel,q=q,logical=L,
                                  value=value,seed=20261018+value,d=128,Hq=32,Hkv=8,arms=arms))
    jobs=[]
    for block in range(8):
        session=block//4
        for panel in (('B0','T0') if session==0 else ('T0','B0')):
            group=[c for c in cells if c['panel']==panel]
            random.Random(122000+block+(0 if panel=='B0' else 100)).shuffle(group)
            for c in group:
                ci=[x['id'] for x in cells if x['panel']==panel].index(c['id'])
                for slot,ai in enumerate(ORDERS[(block%4+ci)%4]):
                    jobs.append(dict(task_id=f"{c['id']}-b{block}-a{ai}",cell=c['id'],panel=panel,
                                     session=session,block=block,slot=slot,arm=c['arms'][ai]['name'],
                                     mode='ON',warmups=8,calls=30))
    body=dict(schema=1,status='DESIGN_ONLY',parent=PARENT,cells=cells,timed_jobs=jobs,
              counts=dict(reference_hosts=40,qualification_hosts=48,timed_hosts=len(jobs),
                          default_hosts=344,default_graph_calls=11400,
                          maximum_hosts=358,maximum_graph_calls=11732))
    body['plan_sha256']=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return body

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
    with open(args.output,'x',encoding='utf-8',newline='\n') as f:
        json.dump(build(),f,indent=2);f.write('\n')
