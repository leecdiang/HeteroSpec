"""Stage an exact additive MMVQ capture patch, without editing/rebuilding old DLLs."""
from pathlib import Path
import argparse
import difflib,hashlib,json,shutil

HERE=Path(__file__).resolve().parent
CORE=Path('D:/rtx192-review-v2/native-v2/cores/packed')
source=CORE/'ggml/src/ggml-cuda/mmvq.cu'
raw=source.read_bytes()
expected='d9c69fafab943383b29e525417f5e2157a445c9b1afca97b7d9de23d20a2564a'
if hashlib.sha256(raw).hexdigest()!=expected:raise RuntimeError('MMVQ source identity changed')
s=raw.decode('utf8')
needle='    const int64_t s01 = src0->nb[1] / ts_src0;'
if s.count(needle)!=1:raise RuntimeError('quantized capture anchor not unique')
hook='''    hs_e02_backend_export::quantized(src0,src1,dst,src1_q8_1.get(),
        size_t(ne13*ne12*ne11*ne10_padded/QK8_1)*sizeof(block_q8_1),stream);

'''
parser=argparse.ArgumentParser()
parser.add_argument('--out',default='backend-source-patch-v2')
args=parser.parse_args()
out=HERE/args.out
if out.parent!=HERE:raise RuntimeError('isolated output directory required')
out.mkdir(exist_ok=False)
modified=s.replace(needle,hook+needle)
dispatch='''    hs_e02_backend_export::dispatch(int(type),c_ncols_dst,small_k,halve_iters,has_fusion,ids!=nullptr,
        block_nums,block_dims,nbytes_shared,stride_row_x,stride_col_y,stride_col_dst,
        stride_channel_x,stride_channel_y,stride_channel_dst);
'''
fusion_anchor='            ggml_cuda_kernel_launch(mul_mat_vec_q<type, c_ncols_dst, true, small_k, halve_iters>'
plain_anchor='    ggml_cuda_kernel_launch(mul_mat_vec_q<type, c_ncols_dst, false, small_k, halve_iters>'
if modified.count(fusion_anchor)!=1 or modified.count(plain_anchor)!=1:raise RuntimeError('dispatch anchors not unique')
modified=modified.replace(fusion_anchor,dispatch+fusion_anchor).replace(plain_anchor,dispatch+plain_anchor)
first='#include "mmvq.cuh"'
if modified.count(first)!=1:raise RuntimeError('include anchor not unique')
modified=modified.replace(first,first+'\n#include "backend_export_hook.hpp"')
(out/'mmvq.cu').write_text(modified,encoding='utf8',newline='\n')
shutil.copy2(HERE/'backend_export_hook.hpp',out/'backend_export_hook.hpp')
(out/'MMVQ_CAPTURE.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),modified.splitlines(True),fromfile='frozen/mmvq.cu',tofile='e02-capture/mmvq.cu')),encoding='utf8')
receipt={'parent_sha256':expected,'new_sha256':hashlib.sha256(modified.encode()).hexdigest(),
         'status':'SOURCE_PATCH_PREPARED_NOT_BUILT_NOT_EXECUTED','old_source_modified':False,
         'arithmetic_changed':False,'capture_sync_added':True,'clean_performance_admitted':False,
         'full_backend_launch_budget_enforcement':'NOT_IMPLEMENTED','model_requests':0,'GPU_launches':0}
(out/'SOURCE.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps(receipt))
