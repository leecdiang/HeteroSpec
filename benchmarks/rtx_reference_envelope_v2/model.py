"""M1 finite-resource tile event model. ABSTRACT_REFERENCE,never RTX calibration.

Within a dot, FP32 multiply then ordered FP32 addition is the declared abstract
reference. Tiles only parallelize independent outputs. Softmax has ordered max
and sum passes. Durations are explicit assumptions,not recovered CUDA kernels.
All policies receive the same GQA multicast/cache,full geometry and resource cap.
"""
import collections,copy,csv,heapq,math,random,struct,time,zlib
from pathlib import Path
from common import V,load,save,sha
from analyze import writecsv
def tasks(w):
    D,H,G,S,q=(w[k] for k in ['d','Hq','Hkv','keys','q']);nodes=[]
    def add(stage,owner,mac,scalar,depth,operands,deps,outbytes):
        i=len(nodes);nodes.append(dict(id=i,stage=stage,owner=owner,mac=mac,scalar=scalar,depth=depth,operands=operands,deps=deps,outbytes=outbytes));return i
    av_by_query=collections.defaultdict(list);first=collections.defaultdict(list)
    # Strong baselines see independent heads/queries,not a head0 serial feed.
    for start in range(0,S,64):
        for h in range(H):
            for j in range(q):
                n=min(64,S-start);first[h,j].append(add('QK',h*q+j,n*D,0,4*D,[(f'K/{h//(H//G)}/{start}',n*D*2),(f'Q/{h}/{j}',D*4)],[],n*4))
    for h in range(H):
        for j in range(q):
            owner=h*q+j;soft=add('SOFTMAX',owner,0,5*S,8*S+16,[(f'mask/{j}',S*4)],first[h,j],S*4)
            for start in range(0,D,64):
                n=min(64,D-start);av_by_query[j].append(add('AV',owner,n*S,0,4*S,[(f'V/{h//(H//G)}/{start}',n*S*2)],[soft],n*4))
    for j,parents in av_by_query.items():add('RESTORE',j,0,0,1,[],parents,D*H*4)
    assert sum(n['mac'] for n in nodes)==2*q*H*D*S
    assert sum(n['scalar'] for n in nodes)==5*q*H*S
    return nodes
def simulate(w,r,policy):
    nodes=tasks(w);P=r['engines'];score=w['q']*w['Hq']*w['keys']*4;context=P*64*16;descriptors=len(nodes)*32;queue=r['queue']*32;candidate=policy.startswith('candidate');control_extra=512 if candidate and policy!='candidate_no_overhead' else 0
    memory=score+w['q']*w['Hq']*w['d']*4+context+descriptors+queue+r['cache_bytes']+control_extra
    result=dict(policy=policy,context_bytes=context,score_bytes=score,descriptor_bytes=descriptors,queue_bytes=queue,cache_bytes=r['cache_bytes'],total_storage_bytes=memory,storage_limit_bytes=r['storage_bytes'])
    if memory>r['storage_bytes']:return dict(result,status='UNSUPPORTED_CAPACITY',cycles=None)
    children=[[] for _ in nodes];remaining=[len(n['deps']) for n in nodes];finish=[0]*len(nodes);ready=[]
    for n in nodes:
        for parent in n['deps']:children[parent].append(n['id'])
        if not n['deps']:heapq.heappush(ready,(0,n['id']))
    engines=[0]*P;banks=[0]*r['banks'];dram=0;dispatch=0;cache=collections.OrderedDict();cache_bytes=0;traffic=0;events=[];memory_events=[];served=set()
    use_reuse=policy!='candidate_no_reuse';dynamic=policy not in ['strong_static','candidate_no_dynamic'];lookahead=r['queue'] if dynamic else 1
    while ready:
        choices=[heapq.heappop(ready) for _ in range(min(lookahead,len(ready)))];options=[]
        for release,i in choices:
            n=nodes[i];engine=min(range(P),key=lambda p:engines[p]) if dynamic else n['owner']%P
            operands=n['operands'];miss=sum(size for key,size in operands if not use_reuse or key not in cache);available=max([release]+[cache[key][0] for key,size in operands if use_reuse and key in cache]);bank=zlib.crc32(str(n['owner']).encode())%r['banks'];start=max(engines[engine],available,banks[bank],dispatch)
            transfer=math.ceil((miss+32+(n['outbytes'] if n['stage']=='RESTORE' else 0))/r['BW']);mem_begin=max(release,dram);ready_at=max(available,mem_begin+transfer);read_cycles=math.ceil((sum(size for key,size in operands)+n['outbytes'])/r['bank_BW']);start=max(start,ready_at,banks[bank]+read_cycles)
            cycles=max(math.ceil(n['mac']/r['mac_per_engine']),math.ceil(n['scalar']/r['scalar_per_engine']),n['depth']);end=start+cycles+math.ceil(n['outbytes']/r['bank_BW'])
            hits=sum(size for key,size in operands if use_reuse and key in cache)
            # Strong dynamic minimizes predicted finish in bounded ready window.
            # Candidate instead favors operand reuse;no privileged cache/multicast.
            priority=(-hits,end,i) if candidate and dynamic else (end,i)
            options.append((priority,i,release,engine,bank,start,end,mem_begin,transfer,miss))
        _,i,release,engine,bank,start,end,mem_begin,transfer,miss=min(options,key=lambda x:x[0]);n=nodes[i]
        for item in choices:
            if item[1]!=i:heapq.heappush(ready,item)
        assert all(finish[p]<=start for p in n['deps']);assert start>=engines[engine] and mem_begin>=dram
        if transfer:memory_events.append((mem_begin,mem_begin+transfer))
        dram=mem_begin+transfer;traffic+=miss+32+(n['outbytes'] if n['stage']=='RESTORE' else 0);engines[engine]=end;banks[bank]=end
        overhead=math.ceil(len(choices)/8)+(2 if candidate and policy!='candidate_no_overhead' else 0);dispatch=max(dispatch,release)+overhead
        for key,size in n['operands']:
            if not use_reuse:continue
            if key in cache:cache.move_to_end(key);continue
            if size>r['cache_bytes']:continue
            while cache and cache_bytes+size>r['cache_bytes']:old,(_,b)=cache.popitem(last=False);cache_bytes-=b
            cache[key]=(dram,size);cache_bytes+=size
        finish[i]=end;served.add(i);events.append((engine,start,end));
        for child in children[i]:
            remaining[child]-=1
            if remaining[child]==0:heapq.heappush(ready,(max(finish[p] for p in nodes[child]['deps']),child))
    assert len(served)==len(nodes) and cache_bytes<=r['cache_bytes']
    for engine in range(P):
        ordered=sorted((a,b) for e,a,b in events if e==engine);assert all(a[1]<=b[0] for a,b in zip(ordered,ordered[1:]))
    assert all(a[1]<=b[0] for a,b in zip(memory_events,memory_events[1:]))
    return dict(result,status='SIMULATED',cycles=max(finish),modeled_DRAM_bytes=traffic,MACs=sum(n['mac'] for n in nodes),scalar_ops=sum(n['scalar'] for n in nodes),jobs=len(nodes),finite_resource_invariants=True,schedule_sha256=__import__('hashlib').sha256(str(events).encode()).hexdigest())
def bound(w,r):
    q,H,G,D,S=(w[k] for k in ['q','Hq','Hkv','d','keys']);mac=2*q*H*D*S;scalar=5*q*H*S;B=q*H*D*4+2*S*G*D*2+S*q*4+q*H*D*4
    return dict(MAC_bound=mac/(r['engines']*r['mac_per_engine']),scalar_bound=scalar/(r['engines']*r['scalar_per_engine']),dependency_bound=4*D+12*S+16,compulsory_B_min=B,bandwidth_bound=B/r['BW'],cycles_lower_bound=max(mac/(r['engines']*r['mac_per_engine']),scalar/(r['engines']*r['scalar_per_engine']),4*D+12*S+16,B/r['BW']))
def oracle_tests():
    # Independent complete single-key GQA oracle for all outputs of a small case.
    import numpy as np
    D,H,G,S,q=4,4,2,3,2;Vv=np.arange(G*D*S,dtype=np.float32).reshape(G,D,S)/8;P=np.zeros((q,H,S),np.float32)
    Q=(np.arange(q*H*D,dtype=np.float32).reshape(q,H,D)%7-3)/8;K=(np.arange(G*S*D,dtype=np.float32).reshape(G,S,D)%5-2)/8
    for j in range(q):
        for h in range(H):
            scores=[]
            for k in range(S):
                a=np.float32(0)
                for d in range(D):a=np.float32(a+np.float32(Q[j,h,d]*K[h//(H//G),k,d]))
                scores.append(float(a)/2 if k==j+1 else -math.inf)
            mx=max(scores);exps=[np.float32(math.exp(x-mx)) for x in scores];total=np.float32(0)
            for x in exps:total=np.float32(total+x)
            for k in range(S):P[j,h,k]=np.float32(exps[k]/total)
    actual=np.zeros((q,H,D),np.float32)
    for j in range(q):
        for h in range(H):
            for d in range(D):
                acc=np.float32(0)
                for k in range(S):acc=np.float32(acc+np.float32(P[j,h,k]*Vv[h//(H//G),d,k]))
                actual[j,h,d]=acc
    expected=np.stack([np.stack([Vv[h//(H//G),:,j+1] for h in range(H)]) for j in range(q)])
    assert actual.tobytes()==expected.tobytes();return dict(full_small_output_words=actual.size,reference='explicit unfused ordered FP32 attention;structured exact case',RTX_compatibility='NOT_ESTABLISHED')
def main():
    from run import root
    started=time.monotonic();s=load(root()/'RUN_SPEC.json');workloads=[]
    for family in ['Qwen','SmolLM2','Llama']:
        m=next(c for c in s['contexts'] if c['family']==family)['metadata']
        for q in range(1,5):
            for S in [256,128,1024,4096]:workloads.append(dict(family=family,d=m['Q']['ne'][0],Hq=m['Q']['ne'][2],Hkv=m['K']['ne'][2],q=q,keys=S,cohort='authentic_geometry_padded_extent' if S==256 else 'synthetic_full_visible_extension',reference_kind='ABSTRACT_REFERENCE'))
    common=dict(engines=8,mac_per_engine=16,scalar_per_engine=16,banks=8,cache_bytes=32768,queue=32,storage_bytes=8*1024**2,BW=4096,bank_BW=512)
    regimes={'compute':common,'bandwidth':dict(common,BW=32),'context_port':dict(common,BW=512,bank_BW=16,storage_bytes=256*1024,queue=8)}
    policies=['strong_static','strong_dynamic','candidate','candidate_no_dynamic','candidate_no_reuse','candidate_no_overhead'];rows=[];oracle=oracle_tests()
    for w in workloads:
        for regime,r in regimes.items():
            lower=bound(w,r)
            for policy in policies:
                assert time.monotonic()-started<3600
                result=simulate(w,r,policy);assert result['cycles'] is None or result['cycles']>=lower['cycles_lower_bound'];rows.append(dict(w,regime=regime,resources=r,**lower,**result))
    writecsv(V,'MODEL.csv',rows)
    save(V/'MODEL_REVIEW.json',dict(status='ABSTRACT_MODEL_COMPLETE',rows=len(rows),workloads=len(workloads),unique_original_geometries=len({(w['d'],w['Hq'],w['Hkv']) for w in workloads}),policies=policies,regimes=regimes,oracle=oracle,seconds=time.monotonic()-started,source_sha256=sha(V/'model.py'),source_PR110_review='one shared scheduler under5labels;not reused as distinct baselines',finite_context_storage_and_queue=True,full_geometry=True,RTX_calibrated=False,RTX_numerical_DAG='UNKNOWN',area_frequency_PPA='UNKNOWN',claim='illustrative finite-resource attention model;cannot identify RTX hardware headroom from host latency'))
    print('M1',len(rows),'rows',time.monotonic()-started,'seconds')
if __name__=='__main__':main()
