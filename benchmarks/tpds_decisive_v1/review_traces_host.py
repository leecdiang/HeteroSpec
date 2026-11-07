import sys,json,collections,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build_host import put,ROOT,sha

rows=[]
for model,version in [('8B',5),('0.6B',4)]:
    for arm in ('graph_tiles','backend_loop4','packed'):
        base=Path('D:/rtx184-runs')/f'O-replay-v{version}-{model}-{arm}-trace'
        for p in sorted(base.glob('*/*-gpu.json')):
            width=int(p.name.split('-')[0]);events=json.loads(p.read_bytes());kernels=[x for x in events if x['kind']=='kernel'];names=collections.Counter(x['name'] for x in kernels)
            quant=sum(n for name,n in names.items() if 'quantize_q8_1' in name);mmvq=sum(n for name,n in names.items() if 'mul_mat_vec_q' in name)
            if arm=='backend_loop4':assert quant==1 and mmvq==math.ceil(width/4),(model,p,quant,mmvq)
            rows.append(dict(model=model,arm=arm,width=width,projection=p.parent.name,trace=str(p),trace_sha256=sha(p),kernels=dict(names),quantize_launches=quant,mmvq_launches=mmvq,kernel_ns=sum(x['end']-x['start'] for x in kernels)))
        assert len(list(base.glob('*/*-gpu.json')))==72
bridge=json.loads((ROOT/'O-RUNTIME-BRIDGE.json').read_bytes());assert bridge['all_equal']
put(ROOT/'O-TRACE-REVIEW.json',dict(actual_loop4_route_verified=True,rows=rows,loop4_contract='one actual quantize_q8_1 launch and ceil(q/4) actual MMVQ launches, including bounded tail for all 144 model/projection/width cells',runtime_bridge=str(ROOT/'O-RUNTIME-BRIDGE.json'),small_model_trace_scope='v4 and v5 executable/core/CUDA/base identical; v5 adds CPU buffer registration only, all 72 small-model outputs rechecked on v5',clean_timing_separate=True,temporary_quantized_activation_bytes_accessible=False,temporary_activation_limitation='CUDA temporary Q8_1 storage is not exported; quantization launch and final bit equality verified, intermediate byte equality not claimed',event_sums_not_additive_wall_time=True))
print('verified',len(rows),'actual GPU traces')
