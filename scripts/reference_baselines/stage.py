"""Materialize three projection baselines from the same frozen candidate.
CUDA changes are source-staged only until an actual CUDA build succeeds.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
GRAPH='src/llama-graph.cpp';CUDA='ggml/src/ggml-cuda/ggml-cuda.cu';MMVQ='ggml/src/ggml-cuda/mmvq.cu';BACKEND='ggml/src/ggml-backend.cpp';CPU='ggml/src/ggml-cpu/ggml-cpu.c'
PINNED={CPU:'b505cb601520698550eba53750888510046c56fe31e130aac78d30e590baa8d0',GRAPH:'3b1a6df5a5a7fc902642f42d9373a4d1ae6cf2013a50003698f30bbd3f0f522e',CUDA:'0832b007fb5cd0165dd80116ea7833c5acda6dfd44f89f2c248d5d977a3e1fde',MMVQ:'49a8f1d60c06a3c4b7b95fcc6aa0406338a4afc94fdf7fc2d30d94f3670aa525',BACKEND:'5a9094517d11dcafe43c51af97bfe3d6afe75d73096be4b899bae7025b1edd31'}
START='        // Dense F32 columns share one Q8 weight.'
END='        for (int64_t i = first_tail; i < cur->ne[1]; i += 4) {'
def once(text,old,new):
    if text.count(old)!=1:raise ValueError('source drift: '+old[:100])
    return text.replace(old,new,1)
def graph_variant(text,arm):
    if arm=='packed':return text
    if text.count(START)!=1 or text.count(END)!=1:raise ValueError('projection anchor drift')
    a=text.index(START);b=text.index(END,a)
    replacement=''
    if arm=='backend_loop4':
        replacement='''        if (ggml_is_contiguous(w) && ggml_is_contiguous(cur) && w->ne[2]==1 && w->ne[3]==1) {
            res = ggml_mul_mat(ctx0,w,cur);
            hs_loop4::mark(res);
            ggml_format_name(res,"hs_backend_loop4_%s",w->name);
            first_tail=cur->ne[1]; // the backend handles every 4-column slice and tail
        }
'''
    elif arm!='graph_tiles':raise ValueError('unknown arm')
    result=text[:a]+replacement+text[b:]
    return ('#include "../ggml/src/hs_loop4_tensor.hpp"\n'+result) if arm=='backend_loop4' else result

def backend_variant(cuda,mmvq):
    anchor='static void ggml_cuda_mul_mat(ggml_backend_cuda_context & ctx, const ggml_tensor * src0, const ggml_tensor * src1, ggml_tensor * dst) {'
    guard='''
    if (hs_loop4::marked(dst)) {
        hs_loop4::require(src0,src1,dst);
#if defined(GGML_USE_HIP) || defined(GGML_USE_MUSA)
        throw std::runtime_error("loop4 baseline is NVIDIA-CUDA-only");
#endif
        for (const auto * t : {src0,src1,static_cast<const ggml_tensor *>(dst)})
            if (!t->data || !t->buffer || t->buffer->buft!=ggml_backend_cuda_buffer_type(ctx.device))
                throw std::runtime_error("loop4 requires actual same-device CUDA residency");
        const bool bad_padding=ggml_backend_buffer_get_usage(src0->buffer)==GGML_BACKEND_BUFFER_USAGE_COMPUTE &&
            ggml_nbytes(src0)!=ggml_backend_buffer_get_alloc_size(src0->buffer,src0) && src0->view_src;
        if (bad_padding)throw std::runtime_error("loop4 cannot reproduce original padding branch");
        const auto & device=ggml_cuda_info().devices[ctx.device];
        if(device.warp_size!=32)throw std::runtime_error("loop4 requires NVIDIA warp32");
        for (int64_t col=0;col<src1->ne[1];col+=4) {
            const auto width=std::min<int64_t>(4,src1->ne[1]-col);
            // Require the original dispatcher to select MMVQ for EACH old tile.
            if (ggml_cuda_should_use_mmvf(src0->type,device.cc,src0->ne,src0->nb,width) ||
                ggml_cuda_should_use_mmf(src0->type,device.cc,device.warp_size,src0->ne,src0->nb,width,false) ||
                !ggml_cuda_should_use_mmvq(src0->type,device.cc,width))
                throw std::runtime_error("loop4 old tile dispatch is not MMVQ");
        }
        // Existing quantizer executes on the wide input; the same old MMVQ
        // specializations are invoked by the marked path below, four at a time.
        ggml_cuda_mul_mat_vec_q(ctx,src0,src1,nullptr,dst);
        return;
    }
'''
    cuda=once(cuda,anchor,anchor+guard)
    proc='static void * ggml_backend_cuda_reg_get_proc_address(ggml_backend_reg_t reg, const char * name) {'
    cuda=once(cuda,proc,'static uint32_t hs_loop4_capability() { return uint32_t(hs_loop4::marker); }\n'+proc+'\n    if (strcmp(name,"hs_backend_loop4_capability_v1")==0) return (void *)hs_loop4_capability;')
    cuda='#include "../hs_loop4_tensor.hpp"\n'+cuda
    call='''    mul_mat_vec_q_switch_type(
        src0->data, src0->type, src1_q8_1.get(), ids_d, fusion_local, dst_d, ne00,
        ne01,              ncols_dst,     s01, stride_col_y,     stride_col_dst,
        ne02, nchannels_y, nchannels_dst, s02, stride_channel_y, stride_channel_dst,
        ne03,              ne3,           s03, s13,              s3,               ids_stride, stream);'''
    loop='''    if (hs_loop4::marked(dst)) {
        hs_loop4::require(src0,src1,dst);
        if (ids || fusion)throw std::runtime_error("loop4 rejects IDs and fused arithmetic");
        const auto tiles=hs_loop4::plan(ncols_dst,stride_col_y,stride_col_dst,sizeof(block_q8_1));
        for (const auto & tile : tiles) {
            const void * quantized=src1_q8_1.get()+tile.input_byte_offset;
            float * output=dst_d+tile.output_float_offset;
            // Singleton channel/sample dimensions: use exactly the old tile's
            // derived contiguous strides, not the wide graph's unused strides.
            mul_mat_vec_q_switch_type(src0->data,src0->type,quantized,nullptr,fusion_local,output,ne00,
                ne01,int(tile.width),s01,stride_col_y,stride_col_dst,
                1,1,1,s02,int(tile.input_group_blocks),int(tile.output_group_floats),
                1,1,s03,int(tile.input_group_blocks),int(tile.output_group_floats),0,stream);
        }
        return;
    }
'''
    mmvq=once(mmvq,call,loop+call)
    # Validate plan/ranges before quantization or any compute-padding memset.
    first='    // If src0 is a temporary compute buffer, clear any potential padding.'
    pre='''    if (hs_loop4::marked(dst)) {
        hs_loop4::require(src0,src1,dst);
        if (ids || fusion)throw std::runtime_error("loop4 rejects IDs and fused arithmetic");
        hs_loop4::plan(ne11,GGML_PAD(ne10,MATRIX_ROW_PADDING)/QK8_1,nb1/sizeof(float),sizeof(block_q8_1));
    }
'''
    mmvq=once(mmvq,first,pre+first)
    return cuda,'#include "../hs_loop4_tensor.hpp"\n'+mmvq

def backend_boundary(text):
    helper='''#include "hs_loop4_tensor.hpp"
static bool hs_loop4_device_capable(ggml_backend_dev_t device) {
    if(!device)return false;
    auto reg=ggml_backend_dev_backend_reg(device);
    if(!reg || std::strcmp(ggml_backend_reg_name(reg),"CUDA")!=0)return false;
    auto capability=reinterpret_cast<uint32_t (*)()>(ggml_backend_reg_get_proc_address(reg,"hs_backend_loop4_capability_v1"));
    return capability && capability()==uint32_t(hs_loop4::marker);
}
static bool hs_loop4_graph_capable(ggml_backend_t backend,ggml_cgraph * graph) {
    for(int i=0;i<ggml_graph_n_nodes(graph);++i)
        if(hs_loop4::marked(ggml_graph_node(graph,i)) && !hs_loop4_device_capable(ggml_backend_get_device(backend)))return false;
    return true;
}
'''
    # Include after normal backend headers so declarations and opaque types exist.
    anchor='enum ggml_status ggml_backend_graph_compute_async(ggml_backend_t backend, struct ggml_cgraph * cgraph) {'
    text=once(text,anchor,anchor+'\n    if (!hs_loop4_graph_capable(backend,cgraph)) return GGML_STATUS_FAILED;')
    anchor='ggml_backend_graph_plan_t ggml_backend_graph_plan_create(ggml_backend_t backend, struct ggml_cgraph * cgraph) {'
    text=once(text,anchor,helper+'\n'+anchor+'\n    if (!hs_loop4_graph_capable(backend,cgraph)) return nullptr;')
    anchor='bool ggml_backend_dev_supports_op(ggml_backend_dev_t device, const struct ggml_tensor * op) {'
    text=once(text,anchor,anchor+'\n    if (hs_loop4::marked(op) && !hs_loop4_device_capable(device)) return false;')
    return text

def stage(candidate,out):
    candidate=candidate.resolve();out=out.resolve()
    if out.exists() or out.is_relative_to(candidate) or candidate.is_relative_to(out):raise ValueError('fresh output outside source required')
    if any(p.is_symlink() for p in candidate.rglob('*')):raise ValueError('source symlinks unsupported')
    paths=[GRAPH,CUDA,MMVQ,BACKEND,CPU];raw={p:(candidate/p).read_bytes() for p in paths}
    for p,data in raw.items():
        if hashlib.sha256(data).hexdigest()!=PINNED[p]:raise ValueError('frozen source hash mismatch: '+p)
    def encode(path,value):
        return value.replace('\n','\r\n').encode() if b'\r\n' in raw[path] else value.encode()
    text={p:v.decode().replace('\r\n','\n') for p,v in raw.items()}
    payload={}
    for arm in ['packed','graph_tiles','backend_loop4']:
        payload[arm]={GRAPH:encode(GRAPH,graph_variant(text[GRAPH],arm))}
        if arm=='backend_loop4':
            c,m=backend_variant(text[CUDA],text[MMVQ]);payload[arm][CUDA]=encode(CUDA,c);payload[arm][MMVQ]=encode(MMVQ,m);payload[arm][BACKEND]=encode(BACKEND,backend_boundary(text[BACKEND]))
            cpu_anchor='enum ggml_status ggml_graph_compute(struct ggml_cgraph * cgraph, struct ggml_cplan * cplan) {'
            cpu_guard='\n    for (int i=0;i<ggml_graph_n_nodes(cgraph);++i) {\n        struct ggml_tensor * node=ggml_graph_node(cgraph,i);\n        if (node->op==GGML_OP_MUL_MAT && node->op_params[HS_LOOP4_MARKER_SLOT]==HS_LOOP4_MARKER) return GGML_STATUS_FAILED;\n    }'
            payload[arm][CPU]=encode(CPU,'#include "../hs_loop4_marker.h"\n'+once(text[CPU],cpu_anchor,cpu_anchor+cpu_guard))
            for name in ['loop4_plan.hpp','loop4_tensor.hpp','loop4_marker.h']:
                payload[arm]['ggml/src/hs_'+name]=(ROOT/'src/reference_baselines'/name).read_bytes().replace(b'"loop4_plan.hpp"',b'"hs_loop4_plan.hpp"').replace(b'"loop4_marker.h"',b'"hs_loop4_marker.h"')
        if arm=='packed':payload[arm]={} # byte-for-byte frozen candidate
    out.mkdir(parents=True)
    for arm,files in payload.items():
        shutil.copytree(candidate,out/arm)
        for path,data in files.items():(out/arm/path).write_bytes(data)
    result={'status':'SOURCE_STAGED_CUDA_NOT_COMPILED','original_sha256':{p:hashlib.sha256(v).hexdigest() for p,v in raw.items()},
      'arms':{arm:{p:hashlib.sha256(v).hexdigest() for p,v in files.items()} for arm,files in payload.items()},
      'gpu_runs':0,'quantization_launch_count':'EXPECTED_FROM_SOURCE_NOT_MEASURED',
      'reference':'original oracle/runtime binary is separate and remains untouched'}
    (out/'BASELINE_STAGE.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(stage(a.candidate,a.out),indent=2))
