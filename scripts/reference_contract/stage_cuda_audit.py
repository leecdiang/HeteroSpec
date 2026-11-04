"""Stage actual CUDA dispatch observation; CUDA compilation is a separate gate.
Enforcement refuses execution until complete numerical qualification exists.
Collect-only mode changes execution policy (fusion/capture/stream optimizations off).
"""
from pathlib import Path
import hashlib,json,argparse
ROOT=Path(__file__).resolve().parents[2]
def once(text,old,new):
    if text.count(old)!=1:raise ValueError('CUDA source anchor drift: '+old[:100])
    return text.replace(old,new,1)
def transform(cuda,mmvq,digest):
    begin='static void ggml_cuda_mul_mat(ggml_backend_cuda_context & ctx, const ggml_tensor * src0, const ggml_tensor * src1, ggml_tensor * dst) {'
    start=cuda.index(begin);end=cuda.index('// returns true when ggml_cuda_mul_mat_id',start)
    part=cuda[start:end]
    replacements={
      'ggml_cuda_mul_mat_cublas(ctx, src0, src1, dst);':'hs_cuda_audit_route(ctx,src0,src1,dst,"cublas");\n        ggml_cuda_mul_mat_cublas(ctx, src0, src1, dst);',
      'ggml_cuda_mul_mat_vec_f(ctx, src0, src1, nullptr, dst);':'hs_cuda_audit_route(ctx,src0,src1,dst,"mmvf");\n        ggml_cuda_mul_mat_vec_f(ctx, src0, src1, nullptr, dst);',
      'ggml_cuda_mul_mat_vec_f(ctx, src1, src0, nullptr, &dst_vec);':'hs_cuda_audit_route(ctx,src1,src0,&dst_vec,"mmvf_transposed");\n        ggml_cuda_mul_mat_vec_f(ctx, src1, src0, nullptr, &dst_vec);',
      'ggml_cuda_mul_mat_f(ctx, src0, src1, nullptr, dst);':'hs_cuda_audit_route(ctx,src0,src1,dst,"mmf");\n        ggml_cuda_mul_mat_f(ctx, src0, src1, nullptr, dst);',
      'ggml_cuda_mul_mat_vec_q(ctx, src0, src1, nullptr, dst);':'hs_cuda_audit_route(ctx,src0,src1,dst,"mmvq");\n        ggml_cuda_mul_mat_vec_q(ctx, src0, src1, nullptr, dst);',
      'ggml_cuda_mul_mat_q(ctx, src0, src1, nullptr, dst);':'hs_cuda_audit_route(ctx,src0,src1,dst,"mmq");\n        ggml_cuda_mul_mat_q(ctx, src0, src1, nullptr, dst);',
    }
    for old,new in replacements.items():
        expected=2 if 'cublas' in old else 1
        if part.count(old)!=expected:raise ValueError('CUDA dispatch call count drift')
        part=part.replace(old,new)
    cuda=cuda[:start]+'#define HS_CUDA_AUDIT_SOURCE_DIGEST "'+digest+'"\n#include "hs_cuda_audit_runtime.inc"\n'+part+cuda[end:]
    cuda=once(cuda,'    if (graph->is_enabled()) {','    if (graph->is_enabled() && !hs_cuda_audit_active()) {')
    cuda=once(cuda,'int nodes_to_skip = ggml_cuda_try_fuse(cuda_ctx, cgraph, i);','int nodes_to_skip = hs_cuda_audit_active() ? 0 : ggml_cuda_try_fuse(cuda_ctx, cgraph, i);')
    anchor='static void ggml_backend_cuda_graph_optimize(ggml_backend_t backend, ggml_cgraph * cgraph, ggml_backend_graph_optimize_params * params) {'
    cuda=once(cuda,anchor,anchor+'\n    if (hs_cuda_audit_active()) return; // no new fusion/concurrent stream plans')
    anchor='static enum ggml_status ggml_backend_cuda_graph_compute(ggml_backend_t backend, ggml_cgraph * cgraph) {\n    ggml_backend_cuda_context * cuda_ctx = (ggml_backend_cuda_context *) backend->context;'
    preflight='''
    if (hs_cuda_audit_active()) {
        // No complete pre-launch specialization proof exists yet. Enforcing
        // mode refuses the whole split before any of its kernels are launched.
        if (!hs_cuda_audit_collecting()) return GGML_STATUS_FAILED;
#if defined(GGML_USE_HIP) || defined(GGML_USE_MUSA)
        return GGML_STATUS_FAILED; // observation extractor not qualified for these backends
#endif
        if (!cuda_ctx->stream_context().concurrent_events.empty()) return GGML_STATUS_FAILED;
        for (int i=0;i<cgraph->n_nodes;++i) {
            const auto * n=cgraph->nodes[i];
            if (n->op==GGML_OP_MUL_MAT_ID) return GGML_STATUS_FAILED;
            if (n->op==GGML_OP_MUL_MAT && ggml_get_op_params_i32(n,1)!=0) return GGML_STATUS_FAILED;
        }
    }
'''
    cuda=once(cuda,anchor,anchor+preflight)
    anchor='static void * ggml_backend_cuda_reg_get_proc_address(ggml_backend_reg_t reg, const char * name) {'
    cuda=once(cuda,anchor,anchor+'\n    if (strcmp(name,"hs_cuda_exchange_audit_v1")==0) return (void *)hs_cuda_exchange_audit;')
    declaration='#include <stdint.h>\n#include <stddef.h>\nextern "C" void hs_cuda_audit_mmvq(int,int,int,int,int,int,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,const uint64_t *,size_t);\n'
    mmvq=declaration+mmvq
    anchor='    if constexpr (c_ncols_dst == 1) {'
    # This exact branch is unique inside the template's switch-fusion function.
    a=mmvq.index('static void mul_mat_vec_q_switch_fusion(');b=mmvq.index(anchor,a)
    mmvq=mmvq[:b]+'''    const uint64_t hs_launch_arguments[]={ncols_x,nchannels_y.x,nchannels_y.y,nchannels_y.z,
        stride_row_x,stride_col_y,stride_col_dst,channel_ratio.x,channel_ratio.y,channel_ratio.z,
        stride_channel_x,stride_channel_y,stride_channel_dst,sample_ratio.x,sample_ratio.y,sample_ratio.z,
        stride_sample_x,stride_sample_y,stride_sample_dst,ids_stride};
    hs_cuda_audit_mmvq(int(type),c_ncols_dst,small_k,halve_iters,has_fusion,ids!=nullptr,
        block_nums.x,block_nums.y,block_nums.z,block_dims.x,block_dims.y,block_dims.z,nbytes_shared,hs_launch_arguments,20);
'''+mmvq[b:]
    return cuda,mmvq

def stage(tree):
    if not (tree/'EXECUTION_CONTRACT_STAGE.json').is_file():
        raise ValueError('CUDA audit patch requires a separately staged source tree')
    folder=tree/'ggml/src/ggml-cuda';a=folder/'ggml-cuda.cu';b=folder/'mmvq.cu'
    original=[a.read_bytes(),b.read_bytes()]
    manifest=[str(p.relative_to(folder)).encode()+b'\0'+p.read_bytes() for p in sorted(folder.rglob('*')) if p.is_file()]
    digest=hashlib.sha256(b'\0'.join(manifest)).hexdigest()
    x,y=transform(*(v.decode().replace('\r\n','\n') for v in original),digest)
    # Compute every transformation before changing the staged tree.
    payload={a:x.encode(),b:y.encode()}
    for source,target in [('cuda_audit.h','hs_cuda_audit.h'),('cuda_audit_runtime.inc','hs_cuda_audit_runtime.inc')]:
        payload[folder/target]=(ROOT/'src/reference_batching'/source).read_bytes()
    for p,data in payload.items():p.write_bytes(data)
    result={'status':'CUDA_SOURCE_STAGED_NOT_COMPILED','cuda_source_manifest_sha256':digest,
      'files':{str(p.relative_to(tree)):hashlib.sha256(data).hexdigest() for p,data in payload.items()},
      'enforcement':'always reject before split launch; no production qualification',
      'observation':'actual selected route, post-packing shape/stride/residency, actual MMVQ launch template; not numerical proof'}
    (tree/'CUDA_AUDIT_STAGE.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--staged-tree',type=Path,required=True);a=p.parse_args();print(json.dumps(stage(a.staged_tree),indent=2))
