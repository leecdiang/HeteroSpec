"""Evaluate frozen pure support predicates on actual CPU-exported graphs."""
import argparse, json, pathlib
from common import ROOT, load, save, sha, modules

def main():
    p=argparse.ArgumentParser();p.add_argument('--old',type=pathlib.Path,required=True)
    p.add_argument('--source',type=pathlib.Path,required=True);a=p.parse_args();before=modules()
    bindings=load(ROOT/'SOURCE_BINDINGS.json')
    vk=a.source/'ggml/src/ggml-vulkan/ggml-vulkan.cpp';cpu=a.source/'ggml/src/ggml-cpu/ggml-cpu.c'
    for f in (vk,cpu):
        bound=next(x for x in bindings['backend_sources'] if x['path']==f.relative_to(a.source).as_posix());assert bound['status']=='MATCH' and sha(f)==bound['actual']
    vktext=vk.read_text();assert 'if (a->ne[3] != b->ne[3])' in vktext
    source=[]
    specs=[(vk,18976,'ggml_backend_vk_device_supports_op','SOURCE_PROVEN_PROPERTY','MUL_MAT source batch3 equality mandatory before dispatch'),
           (vk,10242,'ggml_vk_mul_mat','SOURCE_PREDICTED_PATH','p021 special case requires both permuted + one column + source batch3 both1 + device workgroup limits'),
           (vk,10255,'ggml_vk_mul_mat','SOURCE_PREDICTED_PATH','noncontiguous matvec has stride/permutation and device limits'),
           (vk,10263,'ggml_vk_mul_mat','SOURCE_PREDICTED_PATH','general vector: dst.ne1==1 OR small columns and source1.ne2*ne3==1'),
           (vk,9462,'ggml_vk_mul_mat_q_f16','SOURCE_PREDICTED_PATH','matmul split_k depends on runtime device/pipeline, not inferred here'),
           (vk,13846,'ggml_vk_soft_max','SOURCE_PROVEN_PROPERTY','passes mask ne2/ne3 and nb1/2/3; frozen shader bytes lack individual manifest binding'),
           (vk,19275,'ggml_backend_vk_device_supports_op','SOURCE_PROVEN_PROPERTY','softmax source contiguous F32, optional mask F32/F16'),
           (vk,19101,'ggml_backend_vk_device_supports_op','SOURCE_PROVEN_PROPERTY','CONT/CPY/DUP F32 source and destination supported'),
           (cpu,1186,'ggml_compute_forward_mul_mat_one_chunk','SOURCE_PROVEN_PROPERTY','GQA and fourth-axis broadcast use contiguous repetition division'),
           (cpu,222,'type_traits_cpu[GGML_TYPE_F16]','SOURCE_PROVEN_PROPERTY','F16 vector-dot type, CPU may convert F32 source1; llamafile fast path separately reachable'),
           (a.source/'ggml/src/ggml-cpu/ops.cpp',5584,'ggml_compute_forward_soft_max_f32','SOURCE_PROVEN_PROPERTY','mask column i01; mask heads i02%ne12; batch i03%ne13'),
           (a.source/'ggml/src/ggml.c',3730,'ggml_view_impl','SOURCE_PROVEN_PROPERTY','view source retained; descriptors alias owner, cont/concat allocate results'),
           (a.old/'native/local_attention.h',1,'b570_local_attention','SOURCE_PROVEN_PROPERTY','q1 original delegate; q2 PQ slices or QB batch lift'),
           (a.old/'_host/source/llama-graph.cpp',2611,'build_attn_mha','SOURCE_PROVEN_PROPERTY','Q/K/V permutations; no flash/bias/sinks/softcap/alibi admitted; optional V transpose+cont'),
           (a.old/'_host/source/llama-context.cpp',4368,'b570_geometry_bind','SOURCE_PROVEN_PROPERTY','context-owned role:phase:layout:ub:capacity key; sync and invalidate on change'),
           (a.old/'_host/source/llama-graph.h',814,'llm_graph_params::allow_reuse','SOURCE_PROVEN_PROPERTY','reuse requires equal n_tokens, sequences, output and parameter identity; q1/q2 cannot reuse same topology')]
    for f,line,symbol,level,prop in specs:
        root=a.source if f.is_relative_to(a.source) else a.old
        source.append(dict(file=f.relative_to(root).as_posix(),line=line,symbol=symbol,sha256=sha(f),level=level,property=prop))
    rows=[]
    for x in map(json.loads,(ROOT/'DEV_RAW.jsonl').read_text().splitlines()):
        if x['event']!='FIXTURE' or x['geometry']['q']!=2 or x['geometry']['mask']!=1 or x['geometry']['pattern']!=0:continue
        for layout in x['layouts']:
            name=['MQ','PQ','QB'][layout['layout']];ops=[];mul=0
            for node in layout['graph']:
                if node['op'] not in ('MUL_MAT','SOFT_MAX','PERMUTE','CONT','CONCAT'):continue
                r=dict(node)
                if node['op']=='MUL_MAT':
                    stage='QK' if mul%2==0 else 'AV';mul+=1
                    r.update(stage=stage,source0=x['inputs']['k' if stage=='QK' else 'v'],
                     support_predicate='source0.ne3 == source1.ne3',
                     source0_ne3=1,source1_ne3=node['ne'][3],
                     vulkan_support=node['ne'][3]==1,level='SOURCE_PROVEN_PROPERTY')
                    r['conditional_dispatch']='NOT_REACHABLE_THROUGH_SUPPORTS_OP' if name=='QB' else 'general matmul for MQ; matvec for PQ with contiguous fixture K/V. Native noncontiguous/permuted K/V may reach special vector branch subject to device predicates.'
                else:r.update(level='SOURCE_PROVEN_PROPERTY',stage=node['op'])
                ops.append(r)
            rows.append(dict(geometry=x['geometry'],layout=name,actual_CPU_graph=ops,
                 native_operands_and_assignment='UNKNOWN',graph_scope='Actual synthetic CPU graph; not native tensor capture',
                 native_source0_batch3=1,native_source1_batch3=2 if name=='QB' else 1,
                 native_support_predicate_false=name=='QB'))
    assert len(rows)==36
    save(ROOT/'BACKEND_MAP.json',dict(source=source,graphs=rows,
         evidence_levels=['SOURCE_PROVEN_PROPERTY','SOURCE_PREDICTED_PATH','OBSERVED_NATIVE','UNKNOWN'],
         observations_native='Original full endpoints/work/civil request cost only. No per-op actual backend assignment, operand snapshots, GPU branch or arithmetic DAG.',
         support_vs_dispatch='Support failure is not a numeric GPU counterexample. CPU fallback predicted if scheduler follows supports_op; exact placement, copies and device work remain unobserved.',
         shader_body_status='SOURCE_UNAVAILABLE_FOR_FROZEN_BINARY_BINDING',
         no_new_device_queries=True,modules_before=before,modules_after=modules(),gpu_starts=0))
    print(dict(graph_exports=len(rows),QB_support_false=sum(x['native_support_predicate_false'] for x in rows)))

if __name__=='__main__':main()
