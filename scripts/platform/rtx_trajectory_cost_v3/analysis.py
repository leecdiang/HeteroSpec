"""Report producer. Independent verifiers recompute from raw evidence separately."""
import math,random,statistics
from itertools import zip_longest
def diff(a,b):
    for i,(x,y) in enumerate(zip_longest(a,b)):
        if x!=y:return {'index':i,'left_id':x,'right_id':y}
    return None
def gm(v):return math.exp(sum(math.log(x) for x in v)/len(v))
def percentile(v,p):
    v=sorted(v);x=(len(v)-1)*p;a=int(x);b=min(a+1,len(v)-1);return v[a]+(v[b]-v[a])*(x-a)
def B_report(records,p):
    tasks=p['task_ids'];cs=p['conditions'];expected=[(t,r,c) for t in tasks for r in [1,2,3] for c in cs]
    lookup={(r['task_id'],r['repetition'],r['canonical_condition']):r for r in records}
    if len(lookup)!=len(expected) or any(k not in lookup or lookup[k]['status']!='VALID' or not lookup[k].get('timer') for k in expected):return {'status':'INCOMPLETE_OPERATIONAL_FAILURE','execution_complete':False,'attempted_runs':len(records),'speedup':None,'CI':None}
    stable={t:len({tuple(lookup[t,r,cs[0]]['generated_ids']) for r in [1,2,3]})==1 for t in tasks}
    medians={t:{c:statistics.median(lookup[t,r,c]['timer']['milliseconds'] for r in [1,2,3]) for c in cs} for t in tasks}
    rng=random.Random(2026100104);indices=[[rng.randrange(len(tasks)) for _ in tasks] for _ in range(10000)];paths={}
    for c in cs[1:]:
        pairs=[{'task_id':t,'repetition':r,'first_divergence':diff(lookup[t,r,cs[0]]['generated_ids'],lookup[t,r,c]['generated_ids'])} for t in tasks for r in [1,2,3]]
        exact=sum(x['first_divergence'] is None for x in pairs);qualified=exact==len(tasks)*3 and all(stable.values());ratios=[medians[t][cs[0]]/medians[t][c] for t in tasks]
        draws=[gm([ratios[i] for i in ix]) for ix in indices] if qualified else []
        paths[c]={'status':'QUALIFIED' if qualified else 'BLOCKED','exact_pairs':exact,'total_pairs':len(tasks)*3,'comparisons':pairs,'speedup':gm(ratios) if qualified else None,'CI':[percentile(draws,.025),percentile(draws,.975)] if qualified else None,'prompt_ratios':dict(zip(tasks,ratios)) if qualified else None,'candidate_faster_prompts':sum(x>1 for x in ratios) if qualified else None,'raw_timing_role':'admissible instrumented cost' if qualified else 'diagnostic only'}
    secondary=None
    if all(paths[c]['status']=='QUALIFIED' for c in cs[1:]):
        ratios=[medians[t][cs[1]]/medians[t][cs[2]] for t in tasks];draws=[gm([ratios[i] for i in ix]) for ix in indices]
        secondary={'contrast':'batched/serialized prompt medians; >1 serialized faster','ratio':gm(ratios),'CI':[percentile(draws,.025),percentile(draws,.975)]}
    return {'status':'COMPLETE_VALID','execution_complete':True,'valid_complete_runs':len(records),'distinct_prompts':len(tasks),'reference_repeat_stability':stable,'paths':paths,'prompt_median_ms':medians,'absolute_ms':{c:{'geometric_mean':gm([medians[t][c] for t in tasks]),'median':statistics.median(medians[t][c] for t in tasks),'min':min(medians[t][c] for t in tasks),'max':max(medians[t][c] for t in tasks)} for c in cs},'secondary':secondary,'endpoint_counts':{c:{term:sum(lookup[t,r,c]['termination']==term for t in tasks for r in [1,2,3]) for term in ['EOS','limit']} for c in cs},'interpretation_limit':'Post-prefill instrumented request latency, including condition-dependent logs; not throughput or energy'}
def A_report(records,p):
    tasks=p['task_ids'];cs=p['conditions'];lookup={(r['task_id'],r['repetition'],r['canonical_condition']):r for r in records}
    if len(lookup)!=len(tasks)*15 or any(r['status']!='VALID' for r in records):return {'status':'INCOMPLETE_OPERATIONAL_FAILURE','execution_complete':False,'attempted_runs':len(records)}
    comparisons={}
    for label,l,r in [('UB2_live',1,4),('H2_live',2,4),('R_ONLY_live',3,4),('reference_live',0,4),('H2_R_ONLY',2,3)]:
        rows=[{'task_id':t,'repetition':rep,'first_divergence':diff(lookup[t,rep,cs[l]]['generated_ids'],lookup[t,rep,cs[r]]['generated_ids'])} for t in tasks for rep in [1,2,3]]
        comparisons[label]={'exact_pairs':sum(x['first_divergence'] is None for x in rows),'total_pairs':len(tasks)*3,'distinct_prompts':len(tasks),'wholly_exact_prompts':sum(all(x['first_divergence'] is None for x in rows if x['task_id']==t) for t in tasks),'comparisons':rows}
    divergent=[t for t in tasks if any(x['first_divergence'] for x in comparisons['reference_live']['comparisons'] if x['task_id']==t)]
    stable={t+'|'+c:len({tuple(lookup[t,r,c]['generated_ids']) for r in [1,2,3]})==1 for t in tasks for c in cs}
    candidates={label:{'status':('MATCH_DISCRIMINATING' if divergent else 'MATCH_NONDISCRIMINATING') if v['exact_pairs']==len(tasks)*3 else 'PARTIAL_MATCH','reference_divergent_prompt_results':[{'task_id':t,'all_three_exact':all(x['first_divergence'] is None for x in v['comparisons'] if x['task_id']==t)} for t in divergent]} for label,v in comparisons.items() if label in ['UB2_live','H2_live','R_ONLY_live']}
    return {'status':'COMPLETE_VALID' if all(stable.values()) else 'LIVE_REPEAT_INSTABILITY','execution_complete':True,'valid_complete_runs':len(records),'distinct_prompts':len(tasks),'comparisons':comparisons,'reference_divergent_prompts':divergent,'repeat_stability':stable,'candidates':candidates,'interpretation_limit':'Two predefined candidates on this frozen cohort; no necessity, uniqueness, minimality or cross-backend generalization'}
