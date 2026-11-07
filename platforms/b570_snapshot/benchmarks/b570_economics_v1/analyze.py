"""Complete-panel same-contract analysis; root is the resampling unit."""
import argparse,itertools,json,math,random
from pathlib import Path

def quantile(xs,p):
    a=sorted(xs);x=(len(a)-1)*p;i=int(x);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(x-i)

def analyze(plan,records,draws=10000,seed=20261106):
    if type(draws)!=int or draws<1000:raise ValueError('Too few predeclared draws')
    expected={r['slot']:r for r in plan['slots']};actual={r['slot']:r for r in records}
    if len(expected)!=len(plan['slots']):raise ValueError('Duplicate planned slot')
    if len(actual)!=len(records) or set(actual)!=set(expected):raise ValueError('Incomplete/duplicate panel; do not impute')
    data={};profiles=set()
    for slot,e in expected.items():
        r=actual[slot]
        for key in ('root_id','session','period','arm','kind'):
            if r[key]!=e[key]:raise ValueError('Slot binding mismatch')
        if r['status']!='COMPLETE' or r['qualified'] is not True or r['timing_mode']!=0:
            raise ValueError('Non-clean or unqualified timing')
        profiles.add(r['reference_family'])
        t=r['service_s']
        if isinstance(t,bool) or not math.isfinite(t) or t<=0:raise ValueError('Invalid service')
        if r['kind']=='measure':data[r['root_id'],r['session'],r['arm']]=t
    if len(profiles)!=1:raise ValueError('Do not pool model/reference/deployment families')
    roots=plan['roots'];arms=plan['arms'];sessions=plan['sessions']
    if not roots or len(roots)!=len(set(roots)):raise ValueError('Bad roots')
    pairs=list(itertools.combinations(arms,2));alpha=.05/len(pairs)
    rng=random.Random(seed);samples=[[rng.randrange(len(roots)) for _ in roots] for _ in range(draws)]
    totals={a:sum(data[r,s,a] for r in roots for s in range(sessions)) for a in arms}
    result=[]
    for a,b in pairs:
        ta=[sum(data[r,s,a] for s in range(sessions)) for r in roots]
        tb=[sum(data[r,s,b] for s in range(sessions)) for r in roots]
        logs=[sum(math.log(data[r,s,a]/data[r,s,b]) for s in range(sessions))/sessions for r in roots]
        boots_total=[sum(ta[i] for i in ix)/sum(tb[i] for i in ix) for ix in samples]
        boots_log=[math.exp(sum(logs[i] for i in ix)/len(ix)) for ix in samples]
        result.append({'numerator':a,'denominator':b,'above_one_favors':b,
            'total_ratio':totals[a]/totals[b], 'total_family95':[quantile(boots_total,alpha/2),quantile(boots_total,1-alpha/2)],
            'root_log_ratio':math.exp(sum(logs)/len(logs)),
            'root_log_family95':[quantile(boots_log,alpha/2),quantile(boots_log,1-alpha/2)],
            'root_ratios':[math.exp(x) for x in logs],
            'mean_seconds_a_minus_b':(totals[a]-totals[b])/(len(roots)*sessions)})
    return {'status':'COMPLETE_PAIRED_PANEL','primary':'total_complete_service',
            'independent_roots':len(roots),'sessions':sessions,'service_totals_s':totals,
            'contrasts':result,'best_fixed':min(totals,key=totals.get),'bootstrap_draws':draws,
            'bootstrap_seed':seed,'equivalence_claim':False,'cross_family_pooling':False}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('plan','records','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();x=json.loads(a.records.read_text());x=x.get('records',x) if isinstance(x,dict) else x
    result=analyze(json.loads(a.plan.read_text()),x)
    with a.out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
