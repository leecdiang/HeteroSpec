"""Read-only v3 evidence and frozen-source review. No backend imports or loads."""
import itertools
import math
import pathlib
import statistics
import struct
import time
from legacy import HERE,OLD,ROOT,OUT,load,save,sha,need,MODES,STAGES,compare,modules
from workers import rows
from analyzer import normalize,validate_semantics
from reference import decode

SOURCE=pathlib.Path('C:/hs/b570-direct-id-v1-src/ggml/src/ggml-vulkan')
V3=ROOT/'host/supervised_numerical_v3'
RAW=ROOT/'host_outputs/supervised_numerical_v3/b570-supervised-numerical-v3-20261015-01'

def main():
    begin=time.monotonic_ns();before=modules()
    need(not (HERE/'OFFLINE_REVIEW.json').exists(),'exclusive offline review')
    source=SOURCE/'ggml-vulkan.cpp';need(sha(source)=='04615c97998a76d2d0b15d2ebb93bf381eb3fb565492d7714d3fc9d1c333b98d','frozen source identity')
    manifest=load(V3/'results/RAW_MANIFEST.json');checked=[]
    for row in manifest['files']:
        p=RAW/row['path'];need(p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'v3 raw identity '+row['path'])
    close=load(RAW/'CLOSEOUT.json');groups={};paths=[];mon=[]
    for record in close['records']:
        s=record['slot'];folder=RAW/s['id']
        if record['status']=='ADMITTED':
            dr=[r for r in rows(folder/'MONITOR.jsonl') if r['event']=='READ_END' and r.get('stream')=='directory']
            if dr:mon.append(dict(index=s['index'],reads=len(dr),max_read_ns=max(r['end_ns']-r['begin_ns'] for r in dr),initial_completion_ns=dr[0]['end_ns']-load(folder/'LIFECYCLE.json')['launch_begin_ns']))
        if record['status']!='ADMITTED' or s.get('q') not in (2,3):continue
        request=load(folder/'REQUEST.wire');raw=rows(folder/'raw.jsonl');graph=next(r['graph'] for r in raw if r['event']=='GRAPH_OUTPUT')
        validate_semantics(request,graph,pathlib.Path(request['input']).read_bytes())
        vectors=normalize(request,graph,folder)
        need(all(vectors[k]==(folder/'normalized'/(k+'.f32')).read_bytes() for k in STAGES),'fresh physical-to-logical reconstruction')
        key=(s['input_id'],s['repeat']);groups.setdefault(key,{})[s['mode']]=vectors
        ts={t['id']:t for t in graph['tensors']};av=[]
        for stage in graph['stages']:
            d=ts[stage['AV']];a,b=(ts[i] for i in d['src']);shape=d['ne']
            # For these actual contiguous V/prob inputs, both specialized
            # noncontiguous branches are excluded by the recorded strides.
            need(a['nb'][0]==2 and a['nb'][1]==2*a['ne'][0] and b['nb'][0]==4 and b['nb'][1]==4*b['ne'][0],'recorded AV dimension01 contiguous')
            branch='MATVEC' if shape[1]==1 or (shape[1]<=8 and b['ne'][2]*b['ne'][3]==1) else 'MATMAT'
            av.append(dict(part=stage['part'],dst=d,src0=a,src1=b,static_dispatch=branch,
                source_V_identity=a['id']==graph['V'],src0_repeat=a['op']=='REPEAT',r2=b['ne'][2]//a['ne'][2],r3=b['ne'][3]//a['ne'][3]))
        paths.append(dict(slot=s,AV=av,raw_sha256=sha(folder/'raw.jsonl')))
    complete={k:v for k,v in groups.items() if set(v)==set(MODES)};need(len(complete)==15,'fifteen complete q2/q3 five-mode records')
    relations=[]
    for key,v in complete.items():
        for a,b in itertools.combinations(MODES,2):relations.append(dict(input_id=key[0],repeat=key[1],pair=a+'/'+b,relation=compare(v[a],v[b])))
    need(all(r['relation']['stages'][s]['bit_mismatches']==0 for r in relations for s in ('QK','softmax')),'complete QK/softmax bitwise fact')
    # A conditional CPU arithmetic experiment, not a GPU kernel emulator.
    models=[]
    items=load(OLD/'INPUTS.json')
    for q,n,hk in ((2,63,8),(3,257,2)):
        item=next(i for i in items if tuple(i['cell']['geometry'][k] for k in ('q','n','hk'))==(q,n,hk))
        v=complete[item['id'],0];f=decode(pathlib.Path(item['path']).read_bytes());prob=[x[0] for x in struct.iter_unpack('<f',v['PQ']['softmax'])]
        rounded=[struct.unpack('<e',struct.pack('<e',x))[0] for x in prob];full=[];half=[]
        for j in range(q):
            for h in range(8):
                group=h//(8//hk)
                for d in range(128):
                    vv=f['V'][(group*128+d)*n:(group*128+d+1)*n];off=(j*8+h)*n
                    full.append(math.fsum(a*b for a,b in zip(vv,prob[off:off+n])))
                    half.append(math.fsum(a*b for a,b in zip(vv,rounded[off:off+n])))
        def describe(predicted,actual):
            actual=[x[0] for x in struct.iter_unpack('<f',actual)]
            bits=b''.join(struct.pack('<f',x) for x in predicted)
            return dict(max_abs=max(abs(a-b) for a,b in zip(predicted,actual)),F32_bit_mismatches=sum(bits[i:i+4]!=struct.pack('<f',actual[i//4]) for i in range(0,len(bits),4)),elements=len(actual))
        models.append(dict(input_id=item['id'],geometry=item['cell']['geometry'],probability_rounding_changed=sum(a!=b for a,b in zip(prob,rounded)),
            model='FP64 fsum of exact V16 times actual GPU probability32, optionally probability rounded to F16; no claimed reduction tree',
            full_probability={m:describe(full,v[m]['AV']) for m in MODES},half_probability={m:describe(half,v[m]['AV']) for m in MODES},
            first=dict(MQ=struct.unpack('<f',v['MQ']['AV'][:4])[0],PQ=struct.unpack('<f',v['PQ']['AV'][:4])[0],full_probability_fsum=full[0],half_probability_fsum=half[0])))
    sources=[dict(path=str(p),sha256=sha(p)) for p in [source,SOURCE/'vulkan-shaders/mul_mm.comp',SOURCE/'vulkan-shaders/mul_mm_funcs.glsl',SOURCE/'vulkan-shaders/mul_mat_vec.comp',SOURCE/'vulkan-shaders/mul_mat_vec_base.glsl',SOURCE/'vulkan-shaders/types.glsl',SOURCE/'vulkan-shaders/vulkan-shaders-gen.cpp'] if p.exists()]
    save(HERE/'OFFLINE_REVIEW.json',dict(v3_raw_files_verified=len(manifest['files']),v3_raw_manifest_sha256=sha(V3/'results/RAW_MANIFEST.json'),
        admitted_q2_q3_hosts=len(paths),complete_five_mode_groups=len(complete),full_relations=relations,actual_AV_descriptors=paths,
        conditional_CPU_AV_models=models,frozen_sources=sources,v3_directory_by_slot=mon,
        CPU_wall_seconds=(time.monotonic_ns()-begin)/1e9,modules_before=before,modules_after=modules(),new_GPU_hosts=0,device_queries=0,graph_computes=0,
        limitations=['Static source branch is not a dispatch trace','Actual selected SPIR-V specialization, accumulator flags and hardware reduction order were not logged','No model accuracy or RTX inference','v3 remains incomplete; no samples imported to v4']))
    print(dict(raw_files=len(manifest['files']),admitted_q2q3=len(paths),complete_groups=len(complete),CPU_models=models))

if __name__=='__main__':main()
