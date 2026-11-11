"""Freeze a tokenized held-out pool without executing candidate model outputs."""
from __future__ import annotations
import argparse, hashlib
from lr_common import *
BANDS={'short':(128,384),'long':(512,768)}

def select(candidates,exposures,n=24,seed='llama-mechanism-transfer-v1'):
    need(n>=12 and n%12==0,'use 12/24/36... crossed input cells')
    fields=('id','text_sha256','prompt_ids_sha256');seen={k:set() for k in fields}
    for x in exposures:
        for k in fields:
            if x.get(k):seen[k].add(x[k])
    pools={(d,b):[] for d in ('code','math') for b in BANDS}
    for x in candidates:
        input_check(x);need(all(x.get(k) for k in fields),'missing exposure identity')
        need(x.get('source_revision') and x.get('tokenizer_sha256'),'unbound source/tokenizer')
        if any(x[k] in seen[k] for k in fields):continue
        domain=x.get('domain');need(domain in ('code','math'),'domain must be explicit')
        for band,(lo,hi) in BANDS.items():
            if lo<=len(x['prompt_ids'])<=hi:pools[domain,band].append(dict(x,stratum=band))
    chosen=[];used={k:set() for k in fields}
    for cell,pool in pools.items():
        rank=lambda x:hashlib.sha256((seed+'|'+x['prompt_ids_sha256']).encode()).digest()
        group=[]
        for x in sorted(pool,key=rank):
            if any(x[k] in used[k] for k in fields):continue
            group.append(x)
            for k in fields:used[k].add(x[k])
            if len(group)==n//4:break
        need(len(group)==n//4,'insufficient unexposed natural pool in '+str(cell));chosen+=group
    return {'study_id':STUDY,'seed':seed,'selection':'pre-output SHA256 rank; no padding/truncation',
      'source_pool_sha256':digest(candidates),'exposure_sha256':digest(exposures),'inputs':chosen}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pool',required=True);p.add_argument('--exposures',required=True)
    p.add_argument('--n',type=int,default=24);p.add_argument('--out',required=True);a=p.parse_args()
    save(a.out,select(read(a.pool),read(a.exposures),a.n),exclusive=True)
