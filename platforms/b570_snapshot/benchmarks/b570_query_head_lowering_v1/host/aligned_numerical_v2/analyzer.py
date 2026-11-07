"""Independent full-byte/shape/address/GQA/mask and scalar numerical analysis.

No backend, candidate builder or native source is imported. FP64 errors and
finite cross-representation differences are descriptive, never tolerance gates.
"""
import hashlib
import itertools
import math
import pathlib
import struct
from panel_common import need,digest,STAGES
from reference import decode,solve,fp64_metrics

META_OPS={'NONE','VIEW','RESHAPE','PERMUTE','TRANSPOSE'}

def payloads(data,request):
    f=decode(data);g=request['cell']['geometry']
    need((f['q'],f['n'],f['h'],f['hk'])==tuple(g[k] for k in ('q','n','h','hk')),'input geometry identity')
    p=list(f['raw'])
    if request['mode']=='PQ' and f['q']>1:
        p.extend(f['raw'][3][j*f['n']*4:(j+1)*f['n']*4] for j in range(f['q']))
    return p

class Memory:
    def __init__(self,desc,request,data):
        self.d=desc;self.t={t['id']:t for t in desc['tensors']};self.cache={}
        p=payloads(data,request);ids=[desc[k] for k in ('Q_base','K','V','mask')]+[s['tensor'] for s in desc['slabs']]
        need(len(ids)==len(p),'bound input count');self.inputs=dict(zip(ids,p))
    def root_bytes(self,root):
        if root in self.inputs:return self.inputs[root]
        if root in self.cache:return self.cache[root]
        t=self.t[root]
        need(t['op']=='CONT' and len(t['src'])==1,'input mapping must not traverse arithmetic output')
        source=self.t[t['src'][0]];b=bytearray()
        # Q CONT preserves logical dimensions; output-restoration CONT is not
        # used in any input address proof and cannot enter here.
        need(t['ne']==source['ne'],'Q pack CONT dimensions')
        for i3 in range(t['ne'][3]):
            for i2 in range(t['ne'][2]):
                for i1 in range(t['ne'][1]):
                    for i0 in range(t['ne'][0]):b.extend(self.read(source['id'],[i0,i1,i2,i3]))
        self.cache[root]=bytes(b);return self.cache[root]
    def read(self,ident,idx):
        t=self.t[ident];need(all(0<=i<n for i,n in zip(idx,t['ne'])),'logical input index bounds')
        if t['op']=='REPEAT' and t['view_root']==-1:
            src=self.t[t['src'][0]];return self.read(src['id'],[i%n for i,n in zip(idx,src['ne'])])
        root=t['view_root'] if t['view_root']!=-1 else ident
        b=self.root_bytes(root);e=4 if t['type']=='f32' else 2
        at=t['view_offset']+sum(i*s for i,s in zip(idx,t['nb']))
        need(0<=at and at+e<=len(b),'source byte bounds');return b[at:at+e]

def validate_semantics(request,desc,data):
    f=decode(data);q,n,h,hk=(f[k] for k in ('q','n','h','hk'));mode=request['mode']
    ts={t['id']:t for t in desc['tensors']}
    need(set(ts)==set(range(len(ts))),'unique complete context IDs')
    need(desc['common_original']==(q==1 or mode=='MQ'),'common original graph admission')
    qt=ts[desc['Q']]
    need(qt['ne']==[128,q,h,1] and qt['nb']==[4,512*h,512,512*h*q] and qt['view_offset']==0,'Q0 preserved shape/stride')
    need(ts[desc['K']]['ne']==[128,n,hk,1] and ts[desc['K']]['type']=='f16','K input')
    need(ts[desc['V']]['ne']==[n,128,hk,1] and ts[desc['V']]['type']=='f16','V input')
    need(ts[desc['mask']]['ne']==[n,32,1,1],'original32-row mask retained')
    for t in ts.values():
        need(len(t['ne'])==len(t['nb'])==4 and all(x>0 for x in t['ne']),'positive tensor dimensions')
        e=4 if t['type']=='f32' else 2
        span=e+sum((a-1)*b for a,b in zip(t['ne'],t['nb']))
        need(span==t['bytes'],'exact strided byte span')
        if t['view_root']!=-1:
            root=ts[t['view_root']];need(root['view_root']==-1 and t['view_offset']+span<=root['bytes'],'flattened view root bounds')
    need(len(desc['stages'])==(q if mode=='PQ' and q>1 else 1),'complete attention chain count')
    need(len(desc['slabs'])==(q if mode=='PQ' and q>1 else 0),'PQ slab count')
    for j,slab in enumerate(desc['slabs']):
        need(slab['source_mask_byte_offset']==j*n*4 and slab['bytes']==n*4,'PQ exact mask source')
    need(desc['packed_q']==(q>1 and mode in ('QH_C','QH_D')),'retain actual Q CONT')
    need(desc['dense_mask']==(q>1 and mode=='QH_D'),'retain dense mask REPEAT')
    need(desc['copied_kv']==(q>1 and mode=='REPEAT4'),'retain actual KV REPEAT')
    m=Memory(desc,request,data);qchecks=0;maskchecks=0;kvchecks=0
    for j in range(q):
        for key in range(n):
            expected=0. if key<=n-q+j else -math.inf
            need(f['mask'][j*n+key]==expected,'fixed causal mask logical bytes')
        stage=desc['stages'][j if mode=='PQ' and q>1 else 0]
        score,prob,av=(ts[stage[k]] for k in ('QK','softmax','AV'))
        need(score['op']=='MUL_MAT' and score['op_parameters'][0]==10 and prob['op']=='SOFT_MAX' and av['op']=='MUL_MAT','precision/operation contract')
        need(prob['src'][0]==score['id'] and av['src'][1]==prob['id'],'real QK-softmax-AV linkage')
        need(prob['op_parameters'][0]==struct.unpack('<i',struct.pack('<f',1/math.sqrt(128)))[0] and prob['op_parameters'][1]==0,'stored scale and no ALiBi')
        ki,qi,vi,mi=(ts[ident] for ident in (score['src'][0],score['src'][1],av['src'][0],prob['src'][1]))
        if mode=='REPEAT4' and q>1:
            need(ki['op']==vi['op']=='REPEAT' and ki['src'][0]==desc['K'] and vi['src'][0]==desc['V'],'actual repeated original KV')
        else:need(ki['id']==desc['K'] and vi['id']==desc['V'],'original KV object ownership')
        if mode=='PQ' and q>1:
            need(mi['view_root']==desc['slabs'][j]['tensor'] and mi['view_offset']==0,'bound slab, not disconnected original mask view')
        for head in range(h):
            col=j if mode=='MQ' or q==1 else 0
            batch=j if mode=='REPEAT4' and q>1 else 0
            folded=head*q+j if mode in ('QH_C','QH_D') and q>1 else head
            need(score['ne'][2]%ki['ne'][2]==0 and score['ne'][3]%ki['ne'][3]==0,'valid GQA/batch ratio')
            kh=folded//(score['ne'][2]//ki['ne'][2]);kb=batch//(score['ne'][3]//ki['ne'][3])
            need(kh==head//(h//hk),'GQA source head group')
            need(av['ne'][2]%vi['ne'][2]==0 and av['ne'][3]%vi['ne'][3]==0,'valid AV GQA/batch ratio')
            vh=folded//(av['ne'][2]//vi['ne'][2]);vb=batch//(av['ne'][3]//vi['ne'][3])
            need(vh==head//(h//hk),'AV source head group')
            for d in range(128):
                got=m.read(qi['id'],[d,col,folded,batch]);at=((j*h+head)*128+d)*4
                need(got==f['raw'][0][at:at+4],'Q exact logical address');qchecks+=1
            for key in range(n):
                got=m.read(mi['id'],[key,col,folded%mi['ne'][2],batch%mi['ne'][3]])
                need(got==f['raw'][3][(j*n+key)*4:(j*n+key+1)*4],'mask logical query identity');maskchecks+=1
                # Affine inner-axis strides are checked above; both endpoint
                # elements of every row/head/query are independently checked.
                for d in (0,127):
                    kg=(kh*n+key)*128+d;vg=(kh*128+d)*n+key
                    need(m.read(ki['id'],[d,key,kh,kb])==f['raw'][1][kg*2:kg*2+2],'K source bytes')
                    need(m.read(vi['id'],[key,d,vh,vb])==f['raw'][2][vg*2:vg*2+2],'V source bytes');kvchecks+=2
    return dict(Q_byte_addresses=qchecks,mask_byte_addresses=maskchecks,KV_endpoint_affine_addresses=kvchecks,
                all_view_bounds=True,original_KV_ownership=True,source='Independent symbolic addresses; actual CONT/REPEAT execution requires native result')

def read_stage(path,t):
    b=path.read_bytes();need(len(b)==math.prod(t['ne'])*4 and len(b)>0,'full stage element count')
    values=[x[0] for x in struct.iter_unpack('<f',b)]
    bad=[i for i,x in enumerate(values) if not math.isfinite(x)]
    need(not bad,'nonfinite GPU output '+path.name+' count='+str(len(bad))+' first='+str(bad[0] if bad else None))
    return b,values

def normalize(request,desc,folder):
    g=request['cell']['geometry'];q,n,h=(g[k] for k in ('q','n','h'));mode=request['mode']
    ts={t['id']:t for t in desc['tensors']};dest=pathlib.Path(folder)/'vectors';logical={};expected=set()
    for stage,prefix,extent in (('QK','qk',n),('softmax','sm',n),('AV','av',128)):
        parts=[]
        for s in desc['stages']:
            name=f'{prefix}-{s["part"]}.f32';expected.add(name)
            b,_=read_stage(dest/name,ts[s[stage]]);parts.append(b)
        result=bytearray()
        for j in range(q):
            part=j if mode=='PQ' and q>1 else 0;t=ts[desc['stages'][part][stage]]
            for head in range(h):
                col=j if mode=='MQ' or q==1 else 0
                batch=j if mode=='REPEAT4' and q>1 else 0
                folded=head*q+j if mode in ('QH_C','QH_D') and q>1 else head
                for el in range(extent):
                    idx=[el,col,folded,batch];need(all(i<ne for i,ne in zip(idx,t['ne'])),'stage logical layout')
                    at=sum(i*s for i,s in zip(idx,t['nb']));need(at+4<=len(parts[part]),'stage byte address')
                    result.extend(parts[part][at:at+4])
        need(len(result)==q*h*extent*4,'complete normalized extent');logical[stage]=bytes(result)
    final=ts[desc['final']];need(final['ne']==[128*h,q,1,1],'final restored shape')
    expected.add('final.f32');logical['final'],_=read_stage(dest/'final.f32',final)
    need({p.name for p in dest.glob('*.f32')}==expected,'exact complete stage file inventory')
    need(logical['AV']==logical['final'],'AV-to-final restoration must preserve actual bits')
    return logical

def compare(left,right):
    result={};first=None
    def order(x):m=x&0x7fffffff;return 0x80000000-m if x>>31 else 0x80000000+m
    for stage in STAGES:
        a,b=left[stage],right[stage];need(len(a)==len(b) and len(a)%4==0 and a,'complete pair extent')
        maximum=0.;relative=0.;ulp=0;bad=0;first_index=None;undefined=0
        for i in range(0,len(a),4):
            x,y=struct.unpack('<f',a[i:i+4])[0],struct.unpack('<f',b[i:i+4])[0]
            need(math.isfinite(x) and math.isfinite(y),'nonfinite comparison')
            e=abs(x-y);maximum=max(maximum,e)
            if y:relative=max(relative,e/abs(y))
            else:undefined+=1
            u,v=struct.unpack('<I',a[i:i+4])[0],struct.unpack('<I',b[i:i+4])[0]
            ulp=max(ulp,abs(order(u)-order(v)))
            if a[i:i+4]!=b[i:i+4]:
                bad+=1
                if first_index is None:first_index=i//4
        result[stage]=dict(elements=len(a)//4,bitwise_equal=a==b,bit_mismatches=bad,max_abs=maximum,
             max_relative_defined=relative,relative_undefined_at_zero=undefined,max_ULP=ulp,nonfinite=0,first_mismatch_index=first_index)
        if a!=b and first is None:first=stage
    return dict(stages=result,first_bitwise_divergence_stage=first,all_stages_bitwise_equal=first is None)

def analyze_files(request,desc,folder,input_data,reference=None):
    semantic=validate_semantics(request,desc,input_data);p=payloads(input_data,request)
    identities=[]
    for i,b in enumerate(p):
        before=pathlib.Path(folder)/f'vectors/input-{i}.before.bin';after=pathlib.Path(folder)/f'vectors/input-{i}.after.bin'
        need(before.read_bytes()==b and after.read_bytes()==b,'input before/after byte identity')
        identities.append(dict(input=i,source_sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
    logical=normalize(request,desc,folder);ref=reference if reference is not None else solve(input_data)
    f=decode(input_data);masked=0;mass_error=0.
    probabilities=[x[0] for x in struct.iter_unpack('<f',logical['softmax'])]
    for j in range(f['q']):
        for head in range(f['h']):
            row=probabilities[(j*f['h']+head)*f['n']:(j*f['h']+head+1)*f['n']]
            mass_error=max(mass_error,abs(math.fsum(row)-1))
            for key,p in enumerate(row):
                if f['mask'][j*f['n']+key]==-math.inf:
                    need(p==0.,'strict masked softmax zero');masked+=1
    metrics={s:fp64_metrics([x[0] for x in struct.iter_unpack('<f',logical[s])],ref[s]) for s in STAGES}
    first=next((s for s in STAGES if metrics[s]['first_nonzero_abs'] is not None),None)
    g=request['cell']['geometry'];slab=g['q']*g['n']*4 if request['mode']=='PQ' and g['q']>1 else 0
    return dict(structural=semantic,input_identity=identities,FP64_error=metrics,first_nonzero_FP64_error_stage=first,
         strict_masked_zero_elements=masked,descriptive_max_softmax_mass_error=mass_error,
         numerical_PASS_tolerance=None,normalized_sha256={s:hashlib.sha256(b).hexdigest() for s,b in logical.items()},
         PQ_extra_CPU_copy_bytes=slab,PQ_extra_API_upload_bytes=slab,PQ_extra_logical_storage_bytes=slab),logical
