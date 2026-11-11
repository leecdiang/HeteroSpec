"""CPU-only planning and normalized cost checks. Never launches native processes."""
import argparse, json, math
from pathlib import Path

CONFIG = {
    'RTX': {'families': ['Qwen3','SmolLM2','Llama'], 'inputs': 12,
            'arms': ['R','PQ_A','PQ_B','QB'], 'candidate':'QB',
            'controls':['PQ_A','PQ_B'], 'request_ceiling':1776,'worker_ceiling':852},
    'B570': {'families':['Qwen3'], 'inputs':4,
             'arms':['R','BASE_A','BASE_B','SUBMIT'], 'candidate':'SUBMIT',
             'controls':['BASE_A','BASE_B'], 'request_ceiling':156,'worker_ceiling':9}}

def timing_plan(platform, fast=False):
    """Symbolic maximum plan. Host must bind actual input IDs before execution."""
    c=CONFIG[platform]
    if fast and platform!='RTX': raise ValueError('fast comparator is RTX-only')
    arms=c['arms']+(['NATIVE_FAST'] if fast else [])
    rows=[]
    for s in range(4):
        for f in c['families'][s%len(c['families']):]+c['families'][:s%len(c['families'])]:
            for j in range(c['inputs']):
                i=(j+s)%c['inputs']; off=(s+i)%len(arms)
                for a in arms[off:]+arms[:off]:
                    for category in ('warmup','measured'):
                        rows.append({'slot':f'{platform}/{s}/{f}/{i}/{a}/{category}',
                            'session':s,'family':f,'input_index':i,'arm':a,'category':category})
    return rows

def validate_registration(reg):
    """Completeness guard, not authentication or execution authorization."""
    c=CONFIG[reg['platform']]
    if reg.get('status')!='FROZEN_FOR_HOST_REVIEW': raise ValueError('unfrozen design')
    fields=('study_uuid','source_commit','runtime_manifest_sha256','model_manifest_sha256',
            'reference_manifest_sha256','input_manifest_sha256','order_sha256',
            'old_ledger_sha256','authorization_receipt_sha256','freeze_commit')
    if any(not isinstance(reg.get(k),str) or not reg[k].strip() for k in fields):
        raise ValueError('missing identity/reference/authorization field')
    b=reg.get('budget',{})
    for k in ('model_requests','model_workers','other_processes','owned_seconds','storage_bytes',
              'memory_bytes','cleanup_seconds','per_worker_timeout_seconds'):
        v=b.get(k)
        if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v<=0:
            raise ValueError('missing finite budget: '+k)
    if b['model_requests']>c['request_ceiling'] or b['model_workers']>c['worker_ceiling']:
        raise ValueError('design ceiling exceeded')
    if b['cleanup_seconds']>=b['owned_seconds']:raise ValueError('no execution reserve')
    return {'status':'FIELDS_COMPLETE_NOT_AUTHENTICATED','native_launches':0}

def geo(values):
    values=list(values)
    if not values or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in values):
        raise ValueError('positive finite values required')
    return math.exp(sum(map(math.log,values))/len(values))

def analyze(platform, family, records):
    """One complete primary family panel; raw bindings require a separate auditor."""
    c=CONFIG[platform]
    if family not in c['families']: raise ValueError('unknown family')
    expected={(s,i,a,k) for s in range(4) for i in range(c['inputs'])
              for a in c['arms'] for k in ('warmup','measured')}
    data={}
    for r in records:
        if r.get('family')!=family: raise ValueError('mixed families')
        key=(r['session'],r['input_index'],r['arm'],r['category'])
        if key in data or key not in expected: raise ValueError('duplicate/foreign slot')
        if r.get('qualified') is not True or r.get('exit_ok') is not True:
            raise ValueError('unqualified record')
        geo([r['seconds']]); data[key]=r['seconds']
    if set(data)!=expected: raise ValueError('incomplete registered panel; no subset estimate')
    a,b=c['controls'];cand=c['candidate'];ratios=[];aa=[];economics=[];control_economics=[]
    for s in range(4):
        for i in range(c['inputs']):
            t=lambda arm:data[s,i,arm,'measured']
            mean=(t(a)+t(b))/2
            ratios.append((s,i,t(cand)/mean));aa.append((s,i,t(a)/t(b)))
            economics.append(t(cand)/t('R'));control_economics.append(mean/t('R'))
    ratio=geo(v for _,_,v in ratios)
    imbalance=max(abs(geo(v for _,j,v in aa if j==i)-1) for i in range(c['inputs']))
    sessions=[geo(v for j,_,v in ratios if j==s) for s in range(4)]
    benefit=(1-ratio)>max(.02,imbalance) and all(v<1 for v in sessions)
    return {'status':'NORMALIZED_PANEL_RECONSTRUCTION','family':family,
            'candidate_over_dual_control':ratio,'candidate_over_R':geo(economics),
            'dual_control_over_R':geo(control_economics),'aa_max_input':imbalance,
            'session_ratios':sessions,'practical_screen_pass':benefit,
            'scope':'Finite registered panel; caller-supplied qualification flags, not raw/native certification.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('platform',choices=CONFIG)
    p.add_argument('--fast',action='store_true');p.add_argument('--registration',type=Path)
    args=p.parse_args()
    if args.registration:
        r=json.loads(args.registration.read_text());
        if r.get('platform')!=args.platform:raise SystemExit('platform mismatch')
        print(json.dumps(validate_registration(r),indent=2))
    else:
        rows=timing_plan(args.platform,args.fast)
        print(json.dumps({'status':'SYMBOLIC_PLAN_ONLY','rows':rows,'count':len(rows),'native_launches':0},indent=2))
