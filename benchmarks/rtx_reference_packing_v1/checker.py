"""Independent exact-rational numeric and event/resource checker.

Does not import the scheduler or its integer F32 arithmetic implementation.
"""
from collections import Counter
from fractions import Fraction
from functools import lru_cache

@lru_cache(maxsize=100000)
def value(bits):
    if type(bits)is not int or not 0<=bits<2**32:raise ValueError('F32 word required')
    s=-1 if bits>>31 else 1;e=(bits>>23)&255;m=bits&0x7fffff
    if e==255:raise ValueError('nonfinite input rejected')
    if e:m+=8388608
    power=e-150 if e else -149
    return Fraction(s*m)*(2**power if power>=0 else Fraction(1,2**(-power)))

@lru_cache(maxsize=100000)
def round_fraction(x,negative_zero=False):
    sign=0x80000000 if x<0 or (x==0 and negative_zero) else 0;x=abs(x)
    lo,hi=0,0x7f7fffff
    while lo<hi:
        mid=(lo+hi+1)//2
        if value(mid)<=x:lo=mid
        else:hi=mid-1
    if lo==0x7f7fffff:
        half=(value(lo)-value(lo-1))/2
        if x>=value(lo)+half:raise OverflowError('reference overflow')
        return sign|lo
    a,b=value(lo),value(lo+1)
    chosen=lo if x-a<b-x or (x-a==b-x and lo%2==0) else lo+1
    return sign|chosen

def product(a,b):return round_fraction(value(a)*value(b),bool((a^b)>>31))
def summed(a,b):return round_fraction(value(a)+value(b),a==b==0x80000000)

def reference(w):
    output=[]
    for j in range(w['q']):
        for c in range(w['channels']):
            acc=0
            for t in range(w['keys']):acc=summed(acc,product(w['P'][j][t],w['V'][t][c]))
            output.append(acc)
    return output

def validate(w,r,trace,output):
    q,k,c=w['q'],w['keys'],w['channels'];n=q*c
    assert n<=r['contexts'] and 64+n*20<r['buffer_bytes']
    stage=[0]*n;acc=[0]*n;tmp=[None]*n;pending={};completed=set();last_cycle=-1
    resident={};readers=Counter();cycle_counts=Counter();bank_counts=Counter();commits=set()
    memory_queue={};active_context=Counter();buffer_peak=0;queue_peak=0;read_this_cycle=set();stores={};store_issued=set()
    def bank(key):
        role,a,b=key.split(':');return (int(a)*c+int(b))%r['banks']
    def payload(key):
        role,a,b=key.split(':');a,b=int(a),int(b)
        if role=='P':assert 0<=a<q and 0<=b<k;return w['P'][a][b],c
        assert role=='V' and 0<=a<k and 0<=b<c
        return w['V'][a][b],q
    for ev in trace:
        cycle=ev['cycle'];assert cycle>=last_cycle
        if cycle!=last_cycle:cycle_counts.clear();bank_counts.clear();read_this_cycle.clear();last_cycle=cycle
        kind=ev['kind'];key=ev.get('key');uid=ev.get('uid')
        assert ev['epoch']==w['epoch']
        assert ev['owner']==w['owner']
        if kind=='FETCH':
            assert key not in resident and key not in memory_queue
            cycle_counts['fetch']+=1;assert cycle_counts['fetch']<=r['memory_ports']
            assert len(memory_queue)<r['queue_depth']
            memory_queue[key]=cycle+r['memory_latency']
        elif kind=='FILL':
            assert key in memory_queue and cycle==memory_queue.pop(key)
            expected,uses=payload(key);assert ev['bits']==expected and ev['uses']==uses
            bank_counts[bank(key)]+=1;assert bank_counts[bank(key)]<=r['bank_ports']
            resident[key]=ev['bits'];readers[key]=ev['uses']
        elif kind=='ISSUE':
            assert uid not in pending and uid not in completed
            context=ev['context'];t=ev['t'];op=ev['op']
            assert uid==f'{context}:{t}:{op}' and 0<=t<k and op in ('MUL','ADD')
            assert 0<=context<n and stage[context]==2*t+(op=='ADD')
            assert not active_context[context]
            assert len(pending)<r['queue_depth']
            cycle_counts['compute']+=1;cycle_counts['context_access']+=1
            assert cycle_counts['compute']<=r['lanes']*r['issue_rate']
            assert cycle_counts['context_access']<=r['context_ports']
            j,ch=divmod(context,c)
            if op=='MUL':
                expected=[f'P:{j}:{t}',f'V:{t}:{ch}'];assert ev['inputs']==expected
                for address in expected:
                    assert address in resident and readers[address]>0
                    parts=address.split(':');bank_id=(int(parts[1])*c+int(parts[2]))%r['banks']
                    if address not in read_this_cycle:
                        bank_counts[bank_id]+=1;assert bank_counts[bank_id]<=r['bank_ports'];read_this_cycle.add(address)
                cycle_counts['broadcast']+=2;assert cycle_counts['broadcast']<=r['broadcast_words']
                expected_value=product(resident[expected[0]],resident[expected[1]])
                for address in expected:
                    readers[address]-=1
                    if not readers[address]:del resident[address]
            else:
                assert op=='ADD' and tmp[context] is not None
                expected_value=summed(acc[context],tmp[context])
            assert ev['bits']==expected_value
            pending[uid]=(cycle+r['compute_latency']+r.get('extra_issue_latency',0),context,t,op,expected_value)
            active_context[context]+=1
        elif kind=='DONE':
            cycle_counts['context_write']+=1;assert cycle_counts['context_write']<=r['context_write_ports']
            assert uid in pending;due,context,t,op,bits=pending.pop(uid)
            assert cycle==due and ev['context']==context and ev['bits']==bits
            assert uid not in completed;completed.add(uid);active_context[context]-=1
            if op=='MUL':tmp[context]=bits
            else:acc[context]=bits;tmp[context]=None
            stage[context]+=1
        elif kind=='STORE':
            context=ev['context'];assert 0<=context<n and stage[context]==2*k and context not in store_issued
            assert uid==f'OUT:{context}' and ev['bits']==acc[context] and len(stores)<r['store_queue_depth']
            cycle_counts['output']+=1;assert cycle_counts['output']<=r['output_ports']
            cycle_counts['context_access']+=1;assert cycle_counts['context_access']<=r['context_ports']
            stores[context]=(cycle+r['output_latency'],ev['bits']);store_issued.add(context)
        elif kind=='COMMIT':
            context=ev['context'];assert stage[context]==2*k and context not in commits
            assert context in stores and stores.pop(context)==(cycle,ev['bits'])
            cycle_counts['context_write']+=1;assert cycle_counts['context_write']<=r['context_write_ports']
            assert ev['bits']==acc[context];commits.add(context)
        else:raise AssertionError('unknown event')
        capacity=64+n*20+(len(resident)+len(memory_queue))*12
        assert capacity<=r['buffer_bytes']
        buffer_peak=max(buffer_peak,capacity);queue_peak=max(queue_peak,len(pending),len(memory_queue),len(stores))
    assert not pending and not memory_queue and not stores and not resident and len(commits)==n
    assert all(x==2*k for x in stage) and len(completed)==2*q*k*c
    assert output==acc==reference(w)
    return dict(numerical='PASS',trace='PASS',buffer_peak_bytes=buffer_peak,queue_peak=queue_peak,
                commits=len(commits),micro_operations=len(completed))
