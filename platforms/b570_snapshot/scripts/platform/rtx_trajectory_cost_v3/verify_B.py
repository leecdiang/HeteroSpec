"""Independent frozen B schedule, new ID gates, raw intervals and statistics."""
import math,random,itertools
from pathlib import Path
from verify_common import read,require,check_run,difference,arr
def median3(v):return sorted(v)[1]
def gm(v):return math.exp(math.fsum(math.log(x) for x in v)/len(v))
def quantile(v,p):
    v=sorted(v);k=(len(v)-1)*p;lo=math.floor(k);hi=math.ceil(k);return v[lo]*(hi-k)+v[hi]*(k-lo) if lo!=hi else v[lo]
def check_numbers(a,b):
    if isinstance(b,dict):
        require(isinstance(a,dict),'statistic object shape')
        for k,v in b.items():require(k in a,'missing statistic '+k);check_numbers(a[k],v)
    elif isinstance(b,list):
        require(isinstance(a,list) and len(a)==len(b),'statistic array shape')
        for x,y in zip(a,b):check_numbers(x,y)
    elif isinstance(b,float):require(isinstance(a,(int,float)) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),'wrong statistic/direction')
    else:require(a==b,'reported gate/statistic differs')
def calculate(rows,p,schedule):
    tasks=p['task_ids'];cs=p['conditions'];N=len(tasks)
    perms=list(itertools.permutations(cs));orders=[list(x) for x in perms for _ in range(N*3//6)];random.Random(2026100103).shuffle(orders)
    require(schedule==[{'block':i,'task_id':t,'repetition':r,'order':orders[i]} for i,(t,r) in enumerate(itertools.product(tasks,[1,2,3]))],'frozen balanced schedule differs')
    expected=[(b['task_id'],b['repetition'],c) for b in schedule for c in b['order']]
    require([(r['task_id'],r['repetition'],r['canonical_condition']) for r in rows]==expected,'B complete schedule/order')
    require(len(rows)==len({r['run_id'] for r in rows})==N*9,'B duplicated/missing new runs')
    lookup={(r['task_id'],r['repetition'],r['canonical_condition']):r for r in rows}
    stable={t:len({arr(lookup[t,r,cs[0]]['generated_ids']) for r in [1,2,3]})==1 for t in tasks}
    medians={t:{c:median3([lookup[t,r,c]['timer']['milliseconds'] for r in [1,2,3]]) for c in cs} for t in tasks}
    rng=random.Random(2026100104);stream=[[rng.randrange(N) for _ in range(N)] for _ in range(10000)];paths={}
    for c in cs[1:]:
        pairs=[{'task_id':t,'repetition':r,'first_divergence':difference(lookup[t,r,cs[0]]['generated_ids'],lookup[t,r,c]['generated_ids'])} for t in tasks for r in [1,2,3]]
        count=sum(x['first_divergence'] is None for x in pairs);ok=count==N*3 and all(stable.values());ratios=[medians[t][cs[0]]/medians[t][c] for t in tasks];draws=[gm([ratios[i] for i in indices]) for indices in stream] if ok else []
        paths[c]={'status':'QUALIFIED' if ok else 'BLOCKED','exact_pairs':count,'total_pairs':N*3,'comparisons':pairs,'speedup':gm(ratios) if ok else None,'CI':[quantile(draws,.025),quantile(draws,.975)] if ok else None,'prompt_ratios':dict(zip(tasks,ratios)) if ok else None,'candidate_faster_prompts':sum(x>1 for x in ratios) if ok else None,'raw_timing_role':'admissible instrumented cost' if ok else 'diagnostic only'}
    secondary=None
    if all(paths[c]['status']=='QUALIFIED' for c in cs[1:]):
        ratios=[medians[t][cs[1]]/medians[t][cs[2]] for t in tasks];draws=[gm([ratios[i] for i in ix]) for ix in stream];secondary={'contrast':'batched/serialized prompt medians; >1 serialized faster','ratio':gm(ratios),'CI':[quantile(draws,.025),quantile(draws,.975)]}
    return {'status':'COMPLETE_VALID','execution_complete':True,'valid_complete_runs':len(rows),'distinct_prompts':N,'reference_repeat_stability':stable,'paths':paths,'prompt_median_ms':medians,'absolute_ms':{c:{'geometric_mean':gm([medians[t][c] for t in tasks]),'median':median3([medians[t][c] for t in tasks]) if N==3 else sorted(medians[t][c] for t in tasks)[N//2] if N%2 else sum(sorted(medians[t][c] for t in tasks)[N//2-1:N//2+1])/2,'min':min(medians[t][c] for t in tasks),'max':max(medians[t][c] for t in tasks)} for c in cs},'secondary':secondary,'endpoint_counts':{c:{term:sum(lookup[t,r,c]['termination']==term for t in tasks for r in [1,2,3]) for term in ['EOS','limit']} for c in cs},'interpretation_limit':'Post-prefill instrumented request latency, including condition-dependent logs; not throughput or energy'}
def full(root,metadata=None):
    root=Path(root);metadata=Path(metadata or root/'benchmarks/rtx_trajectory_cost_v3');p=read(metadata/'JOINT_PROTOCOL.json')['B'];schedule=read(metadata/'B_matched_cost/schedule.json');m=read(root/'work/B-formal/records.json');rows=m['runs']
    import verify_receipts,verify_joint
    verify_joint.launch_order(metadata,'B_FORMAL',m['started_utc'])
    last_thermal=verify_receipts.thermal(metadata);gpu=read(metadata/'ENVIRONMENT.json')['gpu']['values'][:3]
    previous=None;receipt=read(metadata/'B_START_REMOTE_RECEIPT.json')
    for r in rows:
        v=check_run(root/r['path'],metadata=metadata);require(v['ids']==r['generated_ids'] and v['timer']==r['timer'],'B raw/manifest observations')
        require(r['phase']=='B_FORMAL' and r['implementation']=='TIMER','B shared/old/original observation forbidden')
        require(r['source_head']==receipt['commit'] and receipt['remote_ack_utc']<m['started_utc']<=r['started_utc']<r['ended_utc']<=m['ended_utc'],'B source/process envelope')
        if (metadata/'F0_MANIFEST.json').exists():
            frozen=read(metadata/'F0_MANIFEST.json')['files'];prefix='benchmarks/rtx_trajectory_cost_v3/'
            require(r['protocol_sha256']==frozen[prefix+'JOINT_PROTOCOL.json']['sha256'] and r['asset_identity_sha256']==frozen[prefix+'ASSET_IDENTITY.json']['sha256'],'B frozen source/asset identities')
        verify_receipts.host_run(r,gpu);require(last_thermal<r['started_utc'],'B started before thermal entry')
        if previous is not None:require(r['started_monotonic_ns']-previous>=2_000_000_000,'fixed two-second idle missing')
        previous=r['ended_monotonic_ns']
    receipt=read(metadata/'B_START_REMOTE_RECEIPT.json');require(receipt['remote_ack_utc']<m['started_utc'] and receipt['full_retrieval_verified'],'B-start ordering')
    result=calculate(rows,p,schedule);check_numbers(read(metadata/'B_matched_cost/REPORT.json'),result);return {'status':'PASS','independent':True,'result':result}
