"""Independent raw semantics: ignores convenience pass flags and timing claims."""
import hashlib,json,math,struct
from pathlib import Path
def load(p):return json.loads(Path(p).read_bytes())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def census(expected,actual):
    assert actual['GPU_initializations']==1 and actual['graph_computes']==0
    def key(r):return (r['descriptor_id'],r['layout'],r['stage_outputs'])
    exp={key(r):r for r in expected['records']};got={key(r):r for r in actual['records']}
    assert len(got)==len(actual['records'])==len(exp)==1680 and set(got)==set(exp)
    variants={name:{} for name in ('QH_C','QH_D')}
    for k,e in exp.items():
        a=got[k];assert len(a['nodes'])==len(e['nodes'])
        full=True
        for n,p in zip(a['nodes'],e['nodes']):
            assert {x:v for x,v in n.items() if x not in ('CUDA_support','placement')}=={x:v for x,v in p.items() if x not in ('CUDA_support','placement')}
            assert type(n['CUDA_support'])is bool
            if not n['metadata_only']:full &= n['CUDA_support']
        assert a['full_support'] is full
        if k[1] in variants:variants[k[1]][(k[0],k[2])]=full
    selected='NO_ADMITTED_QH'
    for name in ('QH_C','QH_D'):
        assert len(variants[name])==336
        if all(variants[name].values()) and selected=='NO_ADMITTED_QH':selected=name
    return dict(selected_QH=selected,complete_graphs=1680,source_bound_node_identity='PASS',graph_computes=0)
def completed_intervals(record):
    intervals=record['raw_completed_intervals'];times=record['completed_host_wall_ms'];assert len(intervals)==len(times)>0
    previous=None;out=[]
    for r,t in zip(intervals,times):
        a,b=r['begin_ns'],r['end_ns'];assert type(a)is int and type(b)is int and b>a
        assert previous is None or a>=previous;previous=b
        derived=(b-a)/1e6;assert type(t)in(int,float) and math.isfinite(t) and abs(t-derived)<.000002
        out.append(derived)
    assert 'cudaDeviceSynchronize' in record['synchronization']
    return out
def canonical(root,metadata):
    ne,nb=metadata['ne'],metadata['nb'];assert metadata['type']==0
    b=(Path(root)/metadata['file']).read_bytes();out=bytearray()
    for h in range(ne[2]):
        for j in range(ne[1]):
            for d in range(ne[0]):
                off=d*nb[0]+j*nb[1]+h*nb[2];assert off+4<=len(b);out.extend(b[off:off+4])
    assert ne[3]==1;return bytes(out)
def numeric(a,b):
    assert len(a)==len(b) and len(a)%4==0;maxerr=0.0;maxulp=0;nonfinite=0;different=0
    for (u,),(v,) in zip(struct.iter_unpack('<I',a),struct.iter_unpack('<I',b)):
        if u==v:continue
        different+=1
        if (u&0x7f800000)==0x7f800000 or (v&0x7f800000)==0x7f800000:nonfinite+=1;continue
        x=struct.unpack('<f',struct.pack('<I',u))[0];y=struct.unpack('<f',struct.pack('<I',v))[0];maxerr=max(maxerr,abs(x-y))
        rank=lambda w:0x80000000-(w&0x7fffffff) if w>>31 else 0x80000000+w
        maxulp=max(maxulp,abs(rank(u)-rank(v)))
    return dict(bitwise_equal=a==b,different_words=different,max_error=maxerr,max_ULP=maxulp,nonfinite_mismatches=nonfinite)
def endpoints(original,candidate,cap,eog):
    def value(r):
        ids=r['tokens'];assert isinstance(ids,list) and all(type(x)is int for x in ids)
        assert r['tokens_predicted']==len(ids) and len(ids)<=cap and r.get('truncated') is False
        stop=r['stop_type'];assert stop in ('eos','limit')
        assert (stop=='limit' and len(ids)==cap) or (stop=='eos' and ids and ids[-1] in eog)
        assert not any(x in eog for x in ids[:-1]);return ids,stop
    return value(original)==value(candidate)
def modules(receipt,pins,runtime):
    seen={}
    for path in receipt:
        p=Path(path);name=p.name
        if name.lower() in {n.lower() for n in pins}:
            expected=next(h for n,h in pins.items() if n.lower()==name.lower());assert p.resolve().parent==Path(runtime).resolve() and digest(p)==expected;seen[name.lower()]=expected
    assert {'ggml-base.dll','ggml-cuda.dll','cublas64_12.dll','cublaslt64_12.dll','cudart64_12.dll'}<=set(seen)
    return seen
