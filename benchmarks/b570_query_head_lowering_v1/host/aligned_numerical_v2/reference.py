"""Independent logical FP64 reference, decoded from stored F32/F16 bytes.

No candidate pack/view/head-lowering helper is used. Scale is rounded to F32,
then all reference sums/exp/normalization use scalar binary64 in fixed order.
"""
import math
import struct
from panel_common import need

SCALE=struct.unpack('<f',struct.pack('<f',1/math.sqrt(128)))[0]

def decode(data):
    need(len(data)>=28,'input header')
    q,n,h,hk,storage,mask,pattern=struct.unpack('<7i',data[:28])
    need(1<=q<=4 and n>=q and h>0 and hk>0 and h%hk==0,'reference domain')
    need((storage,mask,pattern)==(1,0,0),'frozen storage/mask/pattern')
    sizes=(128*q*h*4,128*n*hk*2,128*n*hk*2,32*n*4);pos=28;raw=[]
    for size in sizes:raw.append(data[pos:pos+size]);pos+=size
    need(pos==len(data) and all(len(b)==s for b,s in zip(raw,sizes)),'stored input size')
    values=[list(x[0] for x in struct.iter_unpack(fmt,b)) for fmt,b in zip(('<f','<e','<e','<f'),raw)]
    need(all(math.isfinite(x) for v in values[:3] for x in v),'finite input QKV')
    need(all(x==0 or x==-math.inf for x in values[3]),'causal mask values')
    return dict(q=q,n=n,h=h,hk=hk,raw=raw,Q=values[0],K=values[1],V=values[2],mask=values[3])

def solve(data):
    f=decode(data);q,n,h,hk=(f[k] for k in ('q','n','h','hk'))
    score=[];prob=[];value=[]
    for j in range(q):
        need(any(math.isfinite(x) for x in f['mask'][j*n:(j+1)*n]),'nonempty mask row')
        for head in range(h):
            group=head//(h//hk);row=[]
            for key in range(n):
                total=0.
                for d in range(128):total+=f['Q'][(j*h+head)*128+d]*f['K'][(group*n+key)*128+d]
                row.append(total)
            weighted=[s*SCALE+f['mask'][j*n+k] for k,s in enumerate(row)]
            top=max(weighted);need(math.isfinite(top),'defined softmax')
            weights=[math.exp(x-top) for x in weighted];z=0.
            for x in weights:z+=x
            need(math.isfinite(z) and z>0,'positive softmax denominator')
            weights=[x/z for x in weights]
            for d in range(128):
                total=0.
                for key in range(n):total+=weights[key]*f['V'][(group*128+d)*n+key]
                value.append(total)
            score.extend(row);prob.extend(weights)
    return dict(QK=score,softmax=prob,AV=value,final=list(value),scale_f32=SCALE)

def fp64_metrics(actual,expected):
    need(len(actual)==len(expected) and len(actual)>0,'full reference extent')
    out=dict(elements=len(actual),max_abs=0.,max_relative_defined=0.,relative_undefined_at_zero=0,
             zero_reference_nonzero_actual=0,max_ULP_against_F32_rounded_reference=0,nonfinite_actual=0,
             nonfinite_reference=0,first_nonzero_abs=None,abs_error_bins={'zero':0,'le1e-7':0,'le1e-5':0,'le1e-3':0,'gt1e-3':0})
    def order(x):
        b=struct.unpack('<I',struct.pack('<f',x))[0];m=b&0x7fffffff
        return 0x80000000-m if b>>31 else 0x80000000+m
    for i,(a,b) in enumerate(zip(actual,expected)):
        if not math.isfinite(a):out['nonfinite_actual']+=1;continue
        if not math.isfinite(b):out['nonfinite_reference']+=1;continue
        e=abs(a-b);out['max_abs']=max(out['max_abs'],e)
        if b:out['max_relative_defined']=max(out['max_relative_defined'],e/abs(b))
        else:
            out['relative_undefined_at_zero']+=1;out['zero_reference_nonzero_actual']+=a!=0
        ulp=abs(order(a)-order(b));out['max_ULP_against_F32_rounded_reference']=max(out['max_ULP_against_F32_rounded_reference'],ulp)
        label='zero' if e==0 else 'le1e-7' if e<=1e-7 else 'le1e-5' if e<=1e-5 else 'le1e-3' if e<=1e-3 else 'gt1e-3'
        out['abs_error_bins'][label]+=1
        if e and out['first_nonzero_abs'] is None:out['first_nonzero_abs']=dict(index=i,actual=a,reference_FP64=b,abs_error=e)
    out['scope']='Descriptive errors, no tolerance, PASS cutoff or GPU/FP64 bitwise requirement'
    return out
