"""Independent small scalar models and byte-layout checks. Not GGML/GPU emulation."""
import math
import struct
from core import Geometry, need


def f16(x):
    return struct.unpack('<e',struct.pack('<e',x))[0]


def fixture(g: Geometry, mask='causal', pattern='dyadic'):
    g.check(); need(mask in ('causal','single','holes'), 'mask pattern')
    need(pattern in ('dyadic','structured'), 'data pattern')
    # Q logical index order differs from the packed candidate's execution order.
    q=[[[((17*j+7*h+3*d)%23-11)/16 if pattern=='dyadic' else float(d==(j+h)%g.d)
        for d in range(g.d)] for h in range(g.h)] for j in range(g.q)]
    k=[[[f16(((5*a+11*t+7*d)%29-14)/32) for d in range(g.d)] for t in range(g.n)] for a in range(g.hk)]
    v=[[[f16(((13*a+7*d+3*t)%31-15)/32) for t in range(g.n)] for d in range(g.dv)] for a in range(g.hk)]
    m=[]
    for j in range(g.q):
        right=g.n-g.q+j
        allowed=[t<=right for t in range(g.n)] if mask=='causal' else (
            [t==(j*3)%g.n for t in range(g.n)] if mask=='single' else [t<=right and (t+j)%3!=1 for t in range(g.n)])
        allowed[0]=True if mask=='holes' else allowed[0]
        need(any(allowed),'all-masked row rejected')
        m.append([0. if yes else -math.inf for yes in allowed])
    return dict(q=q,k=k,v=v,mask=m)


def logical(g: Geometry, f):
    """Logical j,h reference; math.fsum defines this CPU model only."""
    ans=[]
    for j in range(g.q):
        for h in range(g.h):
            a=h//(g.h//g.hk)
            s=[math.fsum(f['q'][j][h][d]*f['k'][a][t][d] for d in range(g.d)) / math.sqrt(g.d)+f['mask'][j][t] for t in range(g.n)]
            mx=max(s); need(math.isfinite(mx),'undefined softmax')
            e=[math.exp(x-mx) for x in s]; z=math.fsum(e); p=[x/z for x in e]
            ans.extend(math.fsum(p[t]*f['v'][a][d][t] for t in range(g.n)) for d in range(g.dv))
    return ans


def packed(g: Geometry, f, dense=False, fault=None):
    """Packed r-major traversal with separate indexing. No claim of GPU arithmetic."""
    need(fault in (None,'gqa_modulo','wrong_mask','wrong_output','wrong_pack'),'unknown injected fault')
    qpack=[x for h in range(g.h) for j in range(g.q) for x in f['q'][j][h]]
    heads=g.h*g.q; out=[0.]*(heads*g.dv)
    maskpack=[row[:] for _h in range(g.h) for row in f['mask']] if dense else f['mask']
    for r in range(heads):
        h,j=divmod(r,g.q)
        a=r//(heads//g.hk) if fault!='gqa_modulo' else r%g.hk
        mr=r if dense else r%g.q
        if fault=='wrong_mask':mr=0
        qr=r if fault!='wrong_pack' else (j*g.h+h)
        scores=[]
        for t in range(g.n):
            value=math.fsum(qpack[qr*g.d+d]*f['k'][a][t][d] for d in range(g.d))
            scores.append(value/math.sqrt(g.d)+maskpack[mr][t])
        top=max(scores); need(math.isfinite(top),'undefined candidate softmax')
        weights=[math.exp(s-top) for s in scores]; norm=math.fsum(weights)
        row=[math.fsum((weights[t]/norm)*f['v'][a][d][t] for t in range(g.n)) for d in range(g.dv)]
        dest=(j*g.h+h)*g.dv if fault!='wrong_output' else r*g.dv
        out[dest:dest+g.dv]=row
    return out


def address_audit(g: Geometry):
    """Use actual byte buffers to check compact/permuted packing and output order."""
    g.check(); stride=g.q_strides(); offset=32
    buf=bytearray(offset+4*g.d*g.q*g.h)
    for j in range(g.q):
        for h in range(g.h):
            for d in range(g.d):
                value=(j*g.h+h)*g.d+d
                struct.pack_into('<f',buf,offset+d*stride[0]+j*stride[1]+h*stride[2],value)
    checks=0
    for r in range(g.h*g.q):
        h,j=divmod(r,g.q)
        need(r//(g.q*(g.h//g.hk))==h//(g.h//g.hk),'GQA mismatch')
        for d in range(g.d):
            got=struct.unpack_from('<f',buf,offset+d*stride[0]+j*stride[1]+h*stride[2])[0]
            need(got==(j*g.h+h)*g.d+d,'address mismatch'); checks+=1
    return checks
