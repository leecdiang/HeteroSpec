"""Create isolated numerical source with the actual same-CTA C dispatch."""
from pathlib import Path
import argparse,difflib,hashlib,json,shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
OLD=Path('D:/rtx192-review-v2/native-v2/cores/packed')
SOURCE=HERE/'source'
parser=argparse.ArgumentParser();parser.add_argument('--update-stage',action='store_true');args=parser.parse_args()
if args.update_stage:
    backup=HERE/'source-staging-v1';backup.mkdir(exist_ok=False)
    for name in ['mmvq.cu','ggml-cuda.cu']:
        shutil.copy2(SOURCE/'ggml/src/ggml-cuda'/name,backup/name)
    shutil.copy2(HERE/'SOURCE_PREPARED.json',backup/'SOURCE_PREPARED.json')
    before=json.loads((HERE/'SOURCE_PREPARED.json').read_bytes())['old_source_sha256']
else:
    SOURCE.mkdir(exist_ok=False)
    before={}
    for p in sorted(OLD.rglob('*')):
        relative=p.relative_to(OLD)
        if any(x in ('.git','__pycache__') for x in relative.parts) or not p.is_file():continue
        target=SOURCE/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        before[relative.as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
cuda=SOURCE/'ggml/src/ggml-cuda'
mmvq=cuda/'mmvq.cu';original=(OLD/'ggml/src/ggml-cuda/mmvq.cu').read_text(encoding='utf8')
if hashlib.sha256((OLD/'ggml/src/ggml-cuda/mmvq.cu').read_bytes()).hexdigest()!='d9c69fafab943383b29e525417f5e2157a445c9b1afca97b7d9de23d20a2564a':raise RuntimeError('pinned MMVQ changed')
s=original
def once(old,new):
    global s
    if s.count(old)!=1:raise RuntimeError('source anchor not unique: '+old[:80])
    s=s.replace(old,new)
once('#include "vecdotq.cuh"','#include "vecdotq.cuh"\n#include "hs_pair4_q8.cuh"\n#include "hs_e03_runtime.hpp"\n#include "backend_export_hook.hpp"')
once('    const int64_t s01 = src0->nb[1] / ts_src0;',
'''    hs_e02_backend_export::quantized(src0,src1,dst,src1_q8_1.get(),
        size_t(ne13*ne12*ne11*ne10_padded/QK8_1)*sizeof(block_q8_1),stream);
    const int64_t s01 = src0->nb[1] / ts_src0;''')
anchor='''    if (hs_loop4::marked(dst)) {
        hs_loop4::require(src0,src1,dst);
        if (ids || fusion)throw std::runtime_error("loop4 rejects IDs and fused arithmetic");
        const auto tiles=hs_loop4::plan(ncols_dst,stride_col_y,stride_col_dst,sizeof(block_q8_1));'''
replacement='''    const int hs_arm=hs_e03_selected_arm();
    if(hs_arm<0)throw std::runtime_error("e03 runtime policy not selected");
    if(hs_arm==2 && hs_pair_shape) {
        hs_e03_note_dispatch(2);
        const ggml_cuda_kernel_launch_params launch(dim3(unsigned(ne01/2),1,1),dim3(32,4,1),0,stream);
        ggml_cuda_kernel_launch(hs_two_group_q8,launch,
            static_cast<const block_q8_0 *>(src0->data),reinterpret_cast<const block_q8_1 *>(src1_q8_1.get()),
            dst_d,int(ne00),int(ne01),int(ne10_padded));
        return;
    }
    if (hs_loop4::marked(dst)) {
        if(hs_arm!=0)throw std::runtime_error("e03 marked loop4 graph requires A policy");
        hs_loop4::require(src0,src1,dst);
        if (ids || fusion)throw std::runtime_error("loop4 rejects IDs and fused arithmetic");
        hs_e03_note_dispatch(0);
        const auto tiles=hs_loop4::plan(ncols_dst,stride_col_y,stride_col_dst,sizeof(block_q8_1));'''
once(anchor,replacement)
preflight='''    const bool hs_pair_shape=src0->type==GGML_TYPE_Q8_0 && src1->type==GGML_TYPE_F32 && dst->type==GGML_TYPE_F32 &&
        ne11==4 && ne12==2 && ne13==1 && ne02==1 && ne03==1 && ne1==4 && ne2==2 && ne3==1;
    if(hs_e03_selected_arm()==2 && hs_pair_shape) {
        if(ids||fusion||!ggml_is_contiguous(src0)||!ggml_is_contiguous(src1)||!ggml_is_contiguous(dst) ||
           ne00<=0||ne01<=0||ne00%512!=0||ne01%2!=0||GGML_PAD(ne10,MATRIX_ROW_PADDING)!=ne00 ||
           ne00>INT_MAX||ne01>INT_MAX||ggml_nbytes(src0)>INT_MAX||ggml_nbytes(src1)>INT_MAX||ggml_nbytes(dst)>INT_MAX ||
           ggml_get_op_params_i32(dst,0)!=GGML_PREC_DEFAULT)
            throw std::runtime_error("e03 pair4 descriptor unsupported before quantizer");
        for(const auto * tensor:{src0,src1,static_cast<const ggml_tensor *>(dst)}) {
            if(!tensor->data||!tensor->buffer||tensor->buffer->buft!=ggml_backend_cuda_buffer_type(ctx.device))
                throw std::runtime_error("e03 pair4 requires actual same-device CUDA buffers");
        }
        const auto & device=ggml_cuda_info().devices[ctx.device];
        if(device.warp_size!=32||device.cc!=1200||calc_nwarps(GGML_TYPE_Q8_0,4,get_device_table_id(device.cc))!=4)
            throw std::runtime_error("e03 pair4 requires SM120 native case4 warps");
        if(ggml_backend_buffer_get_usage(src0->buffer)==GGML_BACKEND_BUFFER_USAGE_COMPUTE && src0->view_src &&
           ggml_backend_buffer_get_alloc_size(src0->buffer,src0)!=ggml_nbytes(src0))
            throw std::runtime_error("e03 pair4 rejects padded compute views");
    }
'''
once('    // If src0 is a temporary compute buffer, clear any potential padding.',preflight+'    // If src0 is a temporary compute buffer, clear any potential padding.')
once('''    mul_mat_vec_q_switch_type(
        src0->data, src0->type, src1_q8_1.get(), ids_d, fusion_local, dst_d, ne00,''',
'''    if(ne11==4 && ne12>=2)hs_e03_note_dispatch(1);
    mul_mat_vec_q_switch_type(
        src0->data, src0->type, src1_q8_1.get(), ids_d, fusion_local, dst_d, ne00,''')
mmvq.write_text(s,encoding='utf8',newline='\n')
for src,name in [(ROOT/'native/two_group_q8.cuh','hs_pair4_q8.cuh'),(ROOT/'continuation/native/backend_export_hook.hpp','backend_export_hook.hpp'),
                 (HERE/'hs_e03_runtime.hpp','hs_e03_runtime.hpp'),(HERE/'hs_e03_runtime.cpp','hs_e03_runtime.cpp')]:shutil.copy2(src,cuda/name)
# CMake and direct old-command rebuilds must keep graphs disabled for every arm.
cuda_main=cuda/'ggml-cuda.cu'
raw=(OLD/'ggml/src/ggml-cuda/ggml-cuda.cu').read_text(encoding='utf8')
prefix='#include "hs_e03_runtime.hpp"\n#ifdef GGML_CUDA_USE_GRAPHS\n#error E03_REQUIRES_CUDA_GRAPHS_DISABLED\n#endif\n'
cuda_main.write_text(prefix+raw,encoding='utf8',newline='\n')
(HERE/'DISPATCH.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='frozen/mmvq.cu',tofile='e03/mmvq.cu')),encoding='utf8')
receipt={'schema':'heterospec.e03.runtime-source.v1','old_root':str(OLD),'new_root':str(SOURCE),'files_copied':len(before),'old_source_sha256':before,
    'changed_files':{p:hashlib.sha256((SOURCE/p).read_bytes()).hexdigest() for p in ['ggml/src/ggml-cuda/mmvq.cu','ggml/src/ggml-cuda/ggml-cuda.cu']},
    'numerical_DLL_linked':False,'new_DLL_loaded':False,'GPU_execution':'NOT_RUN','old_DLLs_modified':False,
    'runtime_C_domain':'Q8_0/F32 packed4x2 q8 no IDs/fusion contiguous K%512=0 evenM SM120warp32',
    'outside_C_domain':'old packed route; no new qualification/fallback assertion'}
(HERE/'SOURCE_PREPARED.json').write_text(json.dumps(receipt,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in receipt.items() if k!='old_source_sha256'}))
