"""Independent B-arm native timer, pairing, median, geomean and bootstrap check."""
import argparse, itertools, json, math, random, re
from pathlib import Path
from verify_common import read, meta, require, validate_phase, package_checks

def median3(values):
    a,b,c=sorted(values);return b
def quantile(xs,p):
    v=sorted(xs);pos=(len(v)-1)*p;a=math.floor(pos);b=math.ceil(pos);return v[a]*(b-pos)+v[b]*(pos-a) if a!=b else v[a]
def check(root,asset_root=None):
    m=meta(root);protocol=read(m/'protocol.json');p=protocol['latency'];data=validate_phase(root,'formal','latency',m)
    expected=[];rng=random.Random(p['schedule_seed'])
    for t in p['task_ids']:
        for rep in (1,2,3):
            order=['TARGET_REFERENCE','RTX_SERIALIZED_K2'];rng.shuffle(order)
            expected.extend((t,rep,c) for c in order)
    require([tuple(x) for x in data['schedule']]==expected and len(data['runs'])==180,'B fixed randomized coverage differs')
    thermal=read(m/'latency/THERMAL_PRECHECK.json');require(thermal['status']=='PASS','host pre-B stability missing')
    k={};timers={}
    pattern=rb'HS_TIMER start_qpc=(\d+) end_qpc=(\d+) frequency=(\d+) start_steady_ns=(\d+) end_steady_ns=(\d+) count=(\d+) terminal_id=(\d+)'
    for r in data['runs']:
        key=r['task_id'],r['repetition'],r['condition'];k[key]=r['generated_ids']
        events=re.findall(pattern,(root/'formal/runs'/r['run_id']/'stderr.txt').read_bytes());require(len(events)==1,'native timer event missing/duplicate')
        start,end,freq,sns,ens,count,terminal=map(int,events[0]);require(end>start and ens>sns and freq>0,'invalid timer interval')
        ms=1000*(end-start)/freq;other=(ens-sns)/1e6
        require(count==len(k[key]) and terminal==k[key][-1],'native end count/ID differs')
        require(abs(ms-other)<=max(.020,.001*ms),'native clock record disagreement')
        require(ms==r['timer']['milliseconds'],'timer analysis differs')
        timers[key]=ms
    pairs=[];rows=[];exact=0
    for t in p['task_ids']:
        for rep in (1,2,3):
            left=k[t,rep,'TARGET_REFERENCE'];right=k[t,rep,'RTX_SERIALIZED_K2'];diff=None
            for i,(a,b) in enumerate(itertools.zip_longest(left,right)):
                if a!=b:diff={'index':i,'reference_id':a,'candidate_id':b};break
            same=left==right;exact+=same;pairs.append({'task_id':t,'repetition':rep,'exact':same,'first_divergence':diff})
        ref=median3([timers[t,r,'TARGET_REFERENCE'] for r in (1,2,3)]);ser=median3([timers[t,r,'RTX_SERIALIZED_K2'] for r in (1,2,3)])
        rows.append({'task_id':t,'reference_median_ms':ref,'serialized_median_ms':ser,'ratio':ref/ser})
    published=read(m/'latency/REPORT.json');require(published['comparisons']==pairs and published['per_prompt']==rows and published['exact_pairs']==exact,'B pairs/prompt medians differ')
    if exact==90:
        logs=[math.log(row['ratio']) for row in rows];mean=math.exp(math.fsum(logs)/30);rng=random.Random(2026093002);boot=[]
        for _ in range(10000):boot.append(math.exp(math.fsum(logs[rng.randrange(30)] for _ in range(30))/30))
        ci=[quantile(boot,.025),quantile(boot,.975)]
        require(math.isclose(mean,published['speedup'],rel_tol=1e-12) and all(math.isclose(x,y,rel_tol=1e-12) for x,y in zip(ci,published['bootstrap_95_ci'])),'independent B estimator/bootstrap differs')
    else:require(published['speedup'] is None and published['status']=='QUALIFICATION_BLOCKED','invalid speed claim after failed IDs')
    result={'status':'PASS','scientific_status':published['status'],'pairs_independently_recomputed':90,'native_timer_intervals_checked':180,'prompt_count':30,'speedup':published['speedup'],'bootstrap_95_ci':published.get('bootstrap_95_ci')}
    result.update(package_checks(root,m,'latency',asset_root));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--asset-root',type=Path);a=p.parse_args();print(json.dumps(check(a.root,a.asset_root),indent=2))
