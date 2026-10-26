"""Reconstruct finite paired statistics from complete immutable session records."""
import argparse,csv,itertools,json,math,pathlib,random,statistics,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from rtx_recover import read,sha,save
P=pathlib.Path
CELLS=[(1,'resident'),(3,'resident'),(1,'fresh'),(3,'fresh')]
def quantile(xs,p):
    xs=sorted(xs);x=(len(xs)-1)*p;i=int(x);f=x-i
    return xs[i]*(1-f)+xs[min(i+1,len(xs)-1)]*f
def interval(xs,lo=.025,hi=.975):return [math.exp(quantile(xs,lo)),math.exp(quantile(xs,hi))]
def reconstruct(records):
    blocks={};timing=[]
    for session,data in enumerate(records):
        assert data['status']=='COMPLETE' and data['normal_cleanup_returned']
        for r in data['requests']:
            slot=r['slot'];assert not r['capture'] and not r['counters'];assert r['service_seconds']>0
            timing.append(dict(session=session,input=r['input_id'],task=slot['task'],k=r['k'],lifecycle=r['lifecycle'],label=slot['label'],category=slot['category'],slot_id=slot['slot_id'],service_seconds=r['service_seconds'],request_seconds=r['request_seconds'],setup_seconds=r['setup_seconds'],teardown_seconds=r['teardown_seconds'],output_length=r['length']))
            if slot['category']!='measurement':continue
            key=(session,slot['task'],r['k'],r['lifecycle']);block=blocks.setdefault(key,{})
            assert slot['label'] not in block,'duplicate measurement slot';block[slot['label']]=r
    assert len(blocks)==len(records)*12*4,'missing paired block'
    out=[]
    for (session,task,k,life),v in sorted(blocks.items()):
        assert set(v)=={'PQ_A','PQ_B','QB'},'incomplete arms'
        a,b,q=(v[x] for x in ('PQ_A','PQ_B','QB'))
        for key in ('ids','eog','length','terminal_id','stop_reason','cycles','target_final_kv','draft_final_kv'):
            assert a[key]==b[key]==q[key],'endpoint/state differs in timed block'
        ta,tb,tq=(x['service_seconds'] for x in (a,b,q));pq=(ta+tb)/2
        out.append(dict(session=session,task=task,input=q['input_id'],k=k,lifecycle=life,PQ_A=ta,PQ_B=tb,QB=tq,dual_PQ=pq,log_ratio=math.log(tq/pq),ratio=tq/pq,log_AA=math.log(ta/tb),difference_ms=1000*(tq-pq)))
    return out,timing
def compute(blocks,n_sessions=6,reps=20000,seed=20261026):
    means=[[statistics.mean(b['log_ratio'] for b in blocks if b['session']==s and (b['k'],b['lifecycle'])==c) for c in CELLS] for s in range(n_sessions)]
    rng=random.Random(seed);boots=[]
    for _ in range(reps):
        sample=[means[rng.randrange(n_sessions)] for _ in range(n_sessions)]
        boots.append([statistics.mean(x[c] for x in sample) for c in range(4)])
    cells=[]
    for ci,(k,life) in enumerate(CELLS):
        selected=[b for b in blocks if (b['k'],b['lifecycle'])==(k,life)];logs=[m[ci] for m in means];mean=statistics.mean(logs);ratio=math.exp(mean)
        aa=max(abs(math.exp(statistics.mean(b['log_AA'] for b in selected if b['task']==t))-1) for t in range(12));ci_primary=interval([x[ci] for x in boots],.00625,.99375)
        inputs=[dict(task=t,input=next(b['input'] for b in selected if b['task']==t),ratio=math.exp(statistics.mean(b['log_ratio'] for b in selected if b['task']==t)),difference_ms=statistics.mean(b['difference_ms'] for b in selected if b['task']==t)) for t in range(12)]
        se=statistics.stdev(logs)/math.sqrt(n_sessions)
        cells.append(dict(k=k,lifecycle=life,ratio=ratio,reduction_percent=100*(1-ratio),simultaneous_family95_interval=ci_primary,pointwise95_interval=interval([x[ci] for x in boots]),pointwise_t95=[math.exp(mean-2.5705818356*se),math.exp(mean+2.5705818356*se)],largest_input_AA=aa,
            session_ratios=[math.exp(x) for x in logs],omit_one_session=[math.exp(statistics.mean(logs[:i]+logs[i+1:])) for i in range(n_sessions)],first3_last3=[math.exp(statistics.mean(logs[:3])),math.exp(statistics.mean(logs[3:]))],
            mean_PQ_seconds=statistics.mean(b['dual_PQ'] for b in selected),mean_QB_seconds=statistics.mean(b['QB'] for b in selected),difference_ms=statistics.mean(b['difference_ms'] for b in selected),block_reversals=sum(b['ratio']>=1 for b in selected),blocks=len(selected),inputs=inputs,
            practical_gain_established=ci_primary[1]<.98 and 1-ratio>max(.02,aa) and all(x<0 for x in logs)))
    contrasts=[]
    for name,w in [('k3_over_k1_resident',[-1,1,0,0]),('k3_over_k1_fresh',[0,0,-1,1]),('fresh_over_resident_k1',[-1,0,1,0]),('fresh_over_resident_k3',[0,-1,0,1]),('interaction',[1,-1,-1,1])]:
        values=[sum(a*b for a,b in zip(x,w)) for x in means];boot=[sum(a*b for a,b in zip(x,w)) for x in boots]
        contrasts.append(dict(name=name,ratio_of_layout_ratios=math.exp(statistics.mean(values)),pointwise95_interval=interval(boot),session_contrasts=values,scope='secondary exploratory matched factor contrast; not an absolute service ratio'))
    return dict(cells=cells,secondary_contrasts=contrasts,session_log_layout_ratios=means,bootstrap_replicates=reps,bootstrap_seed=seed,dates='One date; date-level uncertainty not estimable',scope='Fixed exposed inputs; uncertainty clusters independent process sessions on one machine/date')
def writecsv(p,rows):
    with P(p).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=P);ap.add_argument('out',type=P);a=ap.parse_args();root=a.root.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    state=read(root/'formal/CHECKPOINT.json');assert state['status']=='COMPLETE' and len(state['sessions'])==6
    records=[]
    for s in range(6):
        row=state['sessions'][str(s)];assert sha(row['result'])==row['sha256'];records.append(read(row['result']))
    blocks,timing=reconstruct(records);assert len(timing)==936
    answer=compute(blocks);answer['requests']=len(timing);answer['measurements']=sum(t['category']=='measurement' for t in timing);answer['warmups']=sum(t['category']=='warmup' for t in timing);answer['source_hashes']={v['result']:v['sha256'] for v in state['sessions'].values()}
    save(out/'ANALYSIS.json',answer);writecsv(out/'BLOCKS.csv',blocks);writecsv(out/'TIMING.csv',timing)
    print(json.dumps({k:answer[k] for k in ('requests','measurements','warmups')}))
    for c in answer['cells']:print(c['k'],c['lifecycle'],c['ratio'],c['simultaneous_family95_interval'],c['practical_gain_established'])
if __name__=='__main__':main()
