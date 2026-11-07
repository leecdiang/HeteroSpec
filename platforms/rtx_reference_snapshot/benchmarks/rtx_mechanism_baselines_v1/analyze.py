"""CPU descriptive paired contrasts from independently verified timing receipts.

Does not authenticate raw bytes, graph activation or qualification; the executor
must supply those checks. No automatic significance or hardware-benefit decision.
"""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import random
import re
import statistics as st
from plan import validate, ARMS, PRODUCER

HASHES=('host_sha256','runtime_sha256','policy_sha256','logical_input_sha256',
        'physical_input_sha256','reference_sha256','mode_evidence_sha256','audit_sha256')


def summary(pairs, draws):
    if not pairs:
        return dict(blocks=0,sessions=0,ratio=None,difference_us=None,interval=None,pairs=[])
    blocks=[x['block'] for x in pairs]
    if len(blocks)!=len(set(blocks)):raise ValueError('duplicate statistical block')
    strata=defaultdict(list)
    for x in pairs:strata[x['session']].append(x)
    logs=[x['log_ratio'] for x in pairs]
    out=dict(blocks=len(pairs),sessions=len(strata),ratio=math.exp(st.mean(logs)),
             difference_us=st.mean(x['difference_us'] for x in pairs),interval=None,pairs=pairs,
             leave_one_block_out=[math.exp(st.mean(logs[:i]+logs[i+1:])) for i in range(len(logs))] if len(logs)>1 else [])
    if len(pairs)>=4:
        rng=random.Random(20261018); boot=[]
        for _ in range(draws):
            picked=[x for key in sorted(strata) for x in rng.choices(strata[key],k=len(strata[key]))]
            boot.append(math.exp(st.mean(x['log_ratio'] for x in picked)))
        boot.sort();out['interval']=[boot[math.ceil(.025*draws)-1],boot[math.ceil(.975*draws)-1]]
    out['scope']='complete two-session descriptive' if len(pairs)==8 and len(strata)==2 else 'partial/single-session descriptive'
    return out


def average(groups):
    if not groups:return []
    maps=[{p['block']:p for p in group} for group in groups]
    common=set.intersection(*(set(m) for m in maps)); result=[]
    for b in sorted(common):
        pp=[m[b] for m in maps]
        if len({p['session'] for p in pp})!=1:raise ValueError('unpaired sessions')
        result.append(dict(block=b,session=pp[0]['session'],log_ratio=st.mean(p['log_ratio'] for p in pp),
                           difference_us=st.mean(p['difference_us'] for p in pp)))
    return result


def run(plan, records, draws=4000):
    validate(plan)
    if type(draws) is not int or draws<100:raise ValueError('at least 100 draws')
    tasks={t['task_id']:t for t in plan['tasks'] if t['stage'] in ('confirm','producer')}
    seen={}; attempts=set(); identities={}; physical={}; cohorts={}; sessions={}; groups=defaultdict(dict)
    for r in records:
        tid=r.get('task_id')
        if tid not in tasks or tid in seen:raise ValueError('unknown/duplicate task')
        if not isinstance(r.get('attempt_id'),str) or not r['attempt_id'] or r['attempt_id'] in attempts:raise ValueError('attempt identity')
        attempts.add(r['attempt_id']);t=tasks[tid];seen[tid]=r
        if r.get('plan_sha256')!=plan['plan_sha256']:raise ValueError('wrong plan')
        if r.get('layout')!=t['layout'] or r.get('graph_mode')!=t['graph_mode'] or r.get('cost_view')!=t['cost_view']:raise ValueError('wrong treatment/view')
        for flag in ('numerical_qualified','environment_qualified','mode_verified'):
            if type(r.get(flag)) is not bool:raise ValueError('qualification flags must be bool')
        if r.get('status') not in ('QUALIFIED','NUMERICAL_FAILURE','ENVIRONMENT_INVALID','EXECUTION_FAILED','MODE_UNVERIFIED'):raise ValueError('status')
        if not isinstance(r.get('session_id'),str) or not r['session_id']:raise ValueError('actual session')
        values=r.get('measured_us')
        if not isinstance(values,list) or any(type(x) not in (int,float) or not math.isfinite(x) or x<=0 for x in values):raise ValueError('finite positive timings required')
        for h in HASHES:
            if r.get(h) is None and r['status']!='QUALIFIED' and r.get('failure_reason'):continue
            if not re.fullmatch('[0-9a-f]{64}',str(r.get(h))):raise ValueError('missing identity '+h)
        if r['status']=='QUALIFIED' and (not r['numerical_qualified'] or not r['mode_verified'] or len(values)!=t['measured_calls']):raise ValueError('unqualified mode/numerics/count')
        good=r['status']=='QUALIFIED' and r['numerical_qualified'] and r['environment_qualified'] and r['mode_verified']
        if not good:continue
        ckey=(t['stage'],t['case_id']);identity=(r['logical_input_sha256'],r['reference_sha256'])
        if ckey in identities and identities[ckey]!=identity:raise ValueError('logical input/reference drift')
        identities[ckey]=identity
        pkey=ckey+(t['arm'],)
        if pkey in physical and physical[pkey]!=r['physical_input_sha256']:raise ValueError('physical input drift')
        physical[pkey]=r['physical_input_sha256']
        token=tuple(r[h] for h in HASHES[:3])
        if t['stage'] in cohorts and cohorts[t['stage']]!=token:raise ValueError('mixed runtime/source/policy')
        cohorts[t['stage']]=token
        skey=(t['stage'],t['session'])
        if skey in sessions and sessions[skey]!=r['session_id']:raise ValueError('planned session split')
        sessions[skey]=r['session_id']
        groups[t['stage'],t['case_id'],t['graph_mode'],t['block']][t['arm']]=(st.mean(values),r['session_id'])
    contrasts=defaultdict(list)
    def put(key,a,b,block):
        if a[1]!=b[1]:raise ValueError('pair session mismatch')
        contrasts[key].append(dict(block=block,session=a[1],log_ratio=math.log(a[0]/b[0]),difference_us=a[0]-b[0]))
    for (stage,cid,mode,b),g in groups.items():
        required=ARMS if stage=='confirm' else PRODUCER
        if set(g)!=set(required):continue
        comparisons={'AA':('QB_A','QB_B'),'QB_QH':('QB_A','QH_C'),
                     'QB_QH_alt':('QB_B','QH_C'),'PQ_QB':('PQ','QB_A')} if stage=='confirm' else {
                     'QH_conversion':('QH_compact','QH_permuted'),
                     'QB_conversion':('QB_compact','QB_permuted'),
                     'compact_QB_QH':('QB_compact','QH_compact'),
                     'permuted_QB_QH':('QB_permuted','QH_permuted')}
        for label,(a,z) in comparisons.items():put((stage,cid,mode,label),g[a],g[z],b)
        if stage=='confirm' and mode=='ON':
            off=groups.get((stage,cid,'OFF',b),{})
            if set(off)==set(ARMS):
                for arm in ARMS:put((stage,cid,'ON/OFF',arm),g[arm],off[arm],b)
    # Two data realizations do not create extra independent acquisition blocks.
    geometries=defaultdict(list)
    for c in plan['cases']:geometries['confirm',c['geometry_id']].append(c['case_id'])
    for c in plan['producer_cases']:geometries['producer',f"producer-q{c['q']}"] .append(c['case_id'])
    geom_pairs={}
    for (stage,gid),ids in geometries.items():
        labels={(key[2],key[3]) for key in contrasts if key[0]==stage}
        for mode,label in labels:
            geom_pairs[stage,gid,mode,label]=average([contrasts.get((stage,cid,mode,label),[]) for cid in ids])
    edges=[]
    for base,changed,factor in plan['factor_edges']:
        for mode in plan['modes']:
            for label in ('QB_QH','QB_QH_alt','AA'):
                x={p['block']:p for p in geom_pairs.get(('confirm',base,mode,label),[])}
                y={p['block']:p for p in geom_pairs.get(('confirm',changed,mode,label),[])}
                out=[]
                for b in sorted(x.keys()&y.keys()):
                    if x[b]['session']!=y[b]['session']:raise ValueError('edge session mismatch')
                    out.append(dict(block=b,session=x[b]['session'],log_ratio=y[b]['log_ratio']-x[b]['log_ratio'],difference_us=y[b]['difference_us']-x[b]['difference_us']))
                edges.append(dict(base=base,changed=changed,factor=factor,mode=mode,comparison=label,
                                  ratio_of_ratios=summary(out,draws)))
    return dict(plan_sha256=plan['plan_sha256'],observed_hosts=len(seen),expected_timed_hosts=len(tasks),
                coverage=[dict(task_id=tid,stage=t['stage'],case_id=t['case_id'],graph_mode=t['graph_mode'],
                               status=seen[tid]['status'] if tid in seen else 'UNSTARTED') for tid,t in tasks.items()],
                case_contrasts=[dict(stage=k[0],case_id=k[1],mode=k[2],comparison=k[3],summary=summary(v,draws)) for k,v in sorted(contrasts.items())],
                geometry_contrasts=[dict(stage=k[0],geometry_id=k[1],mode=k[2],comparison=k[3],summary=summary(v,draws)) for k,v in sorted(geom_pairs.items())],
                factor_contrasts=edges,hardware='NOT_INFERRED',
                scope='descriptive stratified block bootstrap; no raw/mode authentication; no calibrated significance; missing pairs retained')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--receipts',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--draws',type=int,default=4000)
    args=ap.parse_args();p=json.loads(args.plan.read_text());rs=[json.loads(x) for x in args.receipts.read_text().splitlines() if x.strip()]
    result=run(p,rs,args.draws);args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(observed_hosts=result['observed_hosts'],expected_timed_hosts=result['expected_timed_hosts'])))
