"""Bounded deterministic event model: shared supply, independent ordered contexts.

All mappings deliberately use the same legal stable-priority schedule in this
rectangular parity panel. B1 already has both proposed capabilities. No claim
about optimal ragged scheduling or a novel hardware capability is inferred.
"""
from collections import Counter
import fp32

MAPPINGS=('B0_FIXED_SHARED','B1_PACKED_MULTICAST','A_CONTEXT','A_SUPPLY','C_JOINT')

def simulate(w,r,mapping):
    if mapping not in MAPPINGS:raise ValueError('unknown mapping')
    q,k,c=w['q'],w['keys'],w['channels'];n=q*c
    if n>r['contexts'] or r['buffer_bytes']<64+20*n+12*(q+c):raise ValueError('insufficient key-wave/context/control capacity; no free spill')
    if type(r.get('extra_issue_latency',0))is not int or r.get('extra_issue_latency',0)<0:raise ValueError('nonnegative mapping/switch latency required')
    for key in ('lanes','issue_rate','compute_latency','contexts','context_ports','context_write_ports','buffer_bytes','banks','bank_ports','broadcast_words','memory_ports','memory_latency','queue_depth','output_ports','output_latency','store_queue_depth'):
        if type(r[key])is not int or r[key]<1:raise ValueError('positive integer resource required: '+key)
    if r['broadcast_words']<2 or r['bank_ports']<2:raise ValueError('atomic two-operand read requires two bank/fanout ports; no free staging')
    if not (type(q)is int and 1<=q<=4 and type(k)is int and k>0 and type(c)is int and c>0):raise ValueError('invalid workload geometry')
    if len(w['P'])!=q or any(len(row)!=k for row in w['P']) or len(w['V'])!=k or any(len(row)!=c for row in w['V']):raise ValueError('input dimensions differ')
    for row in w['P']+w['V']:
        for b in row:fp32.decode(b)
    trace=[];stage=[0]*n;acc=[0]*n;tmp=[None]*n;busy=set();done=set()
    resident={};remaining=Counter();fetching={};pending={};stores={};store_issued=set();cycle=0;wait=Counter();fetches=0;peak=0
    def emit(kind,**kw):trace.append(dict(cycle=cycle,kind=kind,owner=w['owner'],epoch=w['epoch'],**kw))
    def addresses(context,t):
        j,ch=divmod(context,c);return [f'P:{j}:{t}',f'V:{t}:{ch}']
    def bits(key):
        role,a,b=key.split(':');a,b=int(a),int(b)
        return w['P'][a][b] if role=='P' else w['V'][a][b]
    def bank(key):
        role,a,b=key.split(':');return (int(a)*c+int(b))%r['banks']
    def writes_due(due):return sum(x[0]==due for x in pending.values())+sum(x[0]==due for x in stores.values())
    while len(done)<n:
        if cycle>1000000:raise RuntimeError('bounded progress failure')
        banks=Counter();seen_reads=set();issued=0;context_access=0;broadcast=0
        for uid,(due,context,t,op,result) in list(pending.items()):
            if due==cycle:
                emit('DONE',uid=uid,context=context,bits=result);del pending[uid];busy.remove(context)
                if op=='MUL':tmp[context]=result
                else:acc[context]=result;tmp[context]=None
                stage[context]+=1
        for key,due in list(fetching.items()):
            if due==cycle:
                del fetching[key];resident[key]=bits(key)
                banks[bank(key)]+=1
                parts=key.split(':');uses=c if parts[0]=='P' else q
                remaining[key]=uses;emit('FILL',key=key,bits=resident[key],uses=uses)
        for context,(due,result) in list(stores.items()):
            if due==cycle:
                emit('COMMIT',context=context,bits=result);done.add(context);del stores[context]
        output_issues=0
        for context in range(n):
            if stage[context]!=2*k or context in store_issued:continue
            if output_issues>=r['output_ports'] or len(stores)>=r['store_queue_depth'] or context_access>=r['context_ports']:
                wait['output_backpressure']+=1;continue
            due=cycle+r['output_latency']
            if writes_due(due)>=r['context_write_ports']:wait['writeback']+=1;continue
            emit('STORE',uid=f'OUT:{context}',context=context,bits=acc[context])
            stores[context]=(due,acc[context]);store_issued.add(context);output_issues+=1;context_access+=1
        # Stable ordering is legal fixed scheduling; no baseline is forced serial.
        for context in range(n):
            if context in done or context in busy or stage[context]>=2*k:continue
            t=stage[context]//2;op='ADD' if stage[context]%2 else 'MUL'
            if len(pending)>=r['queue_depth']:wait['backpressure']+=1;continue
            if issued>=r['lanes']*r['issue_rate']:wait['compute']+=1;continue
            if context_access>=r['context_ports']:wait['context']+=1;continue
            due=cycle+r['compute_latency']+r.get('extra_issue_latency',0)
            if writes_due(due)>=r['context_write_ports']:wait['writeback']+=1;continue
            inputs=addresses(context,t) if op=='MUL' else []
            if any(key not in resident for key in inputs):wait['memory']+=1;continue
            need=Counter(bank(key) for key in inputs if key not in seen_reads)
            if any(banks[b]+v>r['bank_ports'] for b,v in need.items()):wait['bank']+=1;continue
            if broadcast+len(inputs)>r['broadcast_words']:wait['broadcast']+=1;continue
            j,ch=divmod(context,c)
            result=fp32.mul(w['P'][j][t],w['V'][t][ch]) if op=='MUL' else fp32.add(acc[context],tmp[context])
            uid=f'{context}:{t}:{op}';emit('ISSUE',uid=uid,context=context,t=t,op=op,bits=result,inputs=inputs)
            pending[uid]=(due,context,t,op,result)
            busy.add(context);issued+=1;context_access+=1;broadcast+=len(inputs);banks.update(need);seen_reads.update(inputs)
            for key in inputs:
                remaining[key]-=1
                if not remaining[key]:del resident[key]
        # Fetch only the oldest incomplete key wave, so no unbounded lookahead.
        active_t=[stage[i]//2 for i in range(n) if i not in done and stage[i]<2*k]
        oldest=min(active_t) if active_t else k
        wanted=[]
        for context in range(n):
            if context in done or stage[context]>=2*k or stage[context]//2!=oldest:continue
            wanted.extend(addresses(context,oldest))
        fetched=0
        for key in dict.fromkeys(wanted):
            if key in resident or key in fetching:continue
            # Do not refetch a fully consumed address from an advanced context.
            role,a,b=key.split(':');a,b=int(a),int(b)
            consumers=[i for i in range(n) if (i//c==a if role=='P' else i%c==b)]
            needed=sum(stage[i]<=2*oldest and i not in busy for i in consumers)
            if not needed:continue
            if fetched>=r['memory_ports'] or len(fetching)>=r['queue_depth']:wait['supply_queue']+=1;continue
            due=cycle+r['memory_latency']
            if sum(d==due and bank(address)==bank(key) for address,d in fetching.items())>=r['bank_ports']:
                wait['fill_bank']+=1;continue
            if 64+n*20+(len(resident)+len(fetching)+1)*12>r['buffer_bytes']:wait['buffer']+=1;continue
            fetching[key]=due;emit('FETCH',key=key);fetched+=1;fetches+=1
        peak=max(peak,64+n*20+(len(resident)+len(fetching))*12)
        cycle+=1
    return dict(cycles=cycle-1,output=acc,trace=trace,waits=dict(wait),fetch_words=fetches,
                supply_bytes_at_declared_memory_level=fetches*4,
                partial_result_bytes=2*q*k*c*4,context_bundle_traffic_bytes=(4*q*k*c+2*n)*20,output_bytes=n*4,
                peak_buffer_bytes=peak,model_level='abstract operand store to local tagged buffer; no RTX DRAM calibration')
