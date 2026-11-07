"""Independent strict interval arithmetic for the three durable streams."""
from common import MAX_GAP,need
def evaluate(rows,armed,terminal,allow_gap=False):
    previous=None;pending=None;count=0;max_gap=0;errors=[];durations=[]
    for r in rows:
        if r['event']=='READ_BEGIN':
            if pending is not None:errors.append('overlapping read')
            pending=r['begin_ns']
        elif r['event'] in ('READ_END','READ_ERROR','READ_DISCARDED'):
            b,e=r['begin_ns'],r['end_ns']
            if pending!=b or e<b:errors.append('unpaired/reversed read')
            pending=None
            if r['event']=='READ_ERROR':errors.append('read failure');continue
            if r['event']=='READ_DISCARDED' or e>terminal:continue
            anchor=previous if previous is not None else armed
            gap=max(e-b,e-anchor);max_gap=max(max_gap,gap);durations.append(e-b)
            if gap>MAX_GAP:errors.append('effective gap >1s')
            previous=b;count+=1
    tail=terminal-(previous if previous is not None else armed);max_gap=max(max_gap,tail)
    if tail<0:errors.append('terminal before sample')
    if tail>MAX_GAP:errors.append('terminal gap >1s')
    if count==0:errors.append('no valid samples')
    return dict(valid=not errors,errors=errors,valid_reads=count,max_effective_gap_ns=max_gap,max_read_ns=max(durations,default=None),terminal_gap_ns=tail)
def boundary_tests():
    results=[]
    for n in (999999999,1000000000,1000000001):
        rows=[dict(event='READ_BEGIN',begin_ns=0),dict(event='READ_END',begin_ns=0,end_ns=n)]
        r=evaluate(rows,0,n);need(r['valid']==(n<=MAX_GAP),'exact boundary changed');results.append(dict(gap_ns=n,**r))
    return results
