"""S0 build only. Recompile changed CUDA TUs; never initializes a GPU."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import difflib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import time
from support import fresh, need, read, sha


HEADER = r'''#pragma once
#include "ggml.h"
#include <cstring>
#include <stdexcept>
#include <cstdint>
extern "C" void hs_work_quant(uint64_t, uint64_t);
extern "C" void hs_work_dot(uint64_t);
extern "C" void hs_work_backend();
extern "C" void hs_work_quant_payload(const void*,uint64_t,uint64_t,void*);
static_assert(GGML_MAX_OP_PARAMS >= 64,"Private final matmul metadata slot required");
constexpr int hs_strong_marker_slot=15;
constexpr int hs_strong_marker=0x48534231;
inline bool hs_strong_marked(const ggml_tensor * t) {
    return t && t->op==GGML_OP_MUL_MAT && t->op_params[hs_strong_marker_slot]==hs_strong_marker;
}
inline void hs_strong_mark(ggml_tensor* t) {
    if(!t || t->op!=GGML_OP_MUL_MAT || t->op_params[hs_strong_marker_slot]!=0)
        throw std::runtime_error("Occupied or unsupported backend-loop metadata");
    t->op_params[hs_strong_marker_slot]=hs_strong_marker;
}
inline void hs_strong_require(const ggml_tensor * w, const ggml_tensor * x, const ggml_tensor * y) {
    if (!w || !x || !y || !hs_strong_marked(y) || y->op_params[1]!=0 ||
        (w->type != GGML_TYPE_Q4_K && w->type != GGML_TYPE_Q6_K) ||
        x->type != GGML_TYPE_F32 || y->type != GGML_TYPE_F32 ||
        w->ne[0] <= 0 || w->ne[0] % 256 || x->ne[0] != w->ne[0] ||
        x->ne[1] < 1 || x->ne[1] > 32 || y->ne[0] != w->ne[1] || y->ne[1] != x->ne[1] ||
        w->ne[2] != 1 || w->ne[3] != 1 || x->ne[2] != 1 || x->ne[3] != 1 ||
        y->ne[2] != 1 || y->ne[3] != 1 || !ggml_is_contiguous(w) ||
        !ggml_is_contiguous(x) || !ggml_is_contiguous(y) || w->view_src) {
        throw std::runtime_error("strong REF1 backend rejects descriptor; no fallback");
    }
}
'''


def patch_tree(tree, output):
    cuda = tree/'ggml/src/ggml-cuda'
    (cuda/'hs_strong_ref1.hpp').write_text(HEADER)
    changes = []
    p = cuda/'ggml-cuda.cu'
    old = p.read_text()
    anchor = 'static void ggml_cuda_mul_mat(ggml_backend_cuda_context & ctx, const ggml_tensor * src0, const ggml_tensor * src1, ggml_tensor * dst) {'
    need(old.count(anchor) == 1, 'Backend entry changed')
    branch = r'''
    if (hs_strong_marked(dst)) {
        hs_strong_require(src0, src1, dst);
        for (const auto * t : {src0, src1, static_cast<const ggml_tensor *>(dst)}) {
            if (!t->data || !t->buffer || t->buffer->buft != ggml_backend_cuda_buffer_type(ctx.device)) {
                throw std::runtime_error("strong REF1 requires same-device CUDA storage");
            }
        }
        if (ggml_cuda_info().devices[ctx.device].warp_size != 32) {
            throw std::runtime_error("strong REF1 requires warp32");
        }
        hs_work_backend();
        ggml_cuda_mul_mat_vec_q(ctx, src0, src1, nullptr, dst);
        return;
    }
'''
    new = '#include "hs_strong_ref1.hpp"\n' + old.replace(anchor, anchor+branch, 1)
    p.write_text(new)
    changes.append((p, old, new))
    p = cuda/'mmvq.cu'
    old = p.read_text()
    quant = '        quantize_row_q8_1_cuda(src1_d, nullptr, src1_q8_1.get(), src0->type, ne10, s11, s12, s13, ne10_padded, ne11, ne12, ne13, stream);'
    need(old.count(quant) == 1, 'Original batch quantizer changed')
    new = old.replace(quant, '        hs_work_quant(ne13*ne12*ne11, ne13*ne12*ne11*ne10_padded*sizeof(block_q8_1)/QK8_1);\n'+quant+
        '\n        hs_work_quant_payload(src1_q8_1.get(),ne13*ne12*ne11,ne13*ne12*ne11*ne10_padded*sizeof(block_q8_1)/QK8_1,stream);')
    anchor = '    if (hs_loop4::marked(dst)) {'
    at = new.rfind(anchor)
    need(at > new.index('const int64_t ids_stride'), 'Final MMVQ dispatch anchor')
    branch = r'''
    if (hs_strong_marked(dst)) {
        hs_strong_require(src0, src1, dst);
        if (ids || fusion) {
            throw std::runtime_error("strong REF1 rejects IDs or fused descriptors");
        }
        for (int64_t col = 0; col < ne11; ++col) {
            const void * input = src1_q8_1.get() + col*s11*sizeof(block_q8_1);
            float * output = dst_d + col*s1;
            hs_work_dot(1);
            mul_mat_vec_q_switch_type(src0->data, src0->type, input, nullptr, fusion_local,
                output, ne00, ne01, 1, s01, s11, s1,
                1, 1, 1, s02, s11, ne0, 1, 1, s03, s11, ne0, 0, stream);
        }
        return;
    }
    hs_work_dot(ncols_dst*nchannels_dst*ne3);
'''
    new = '#include "hs_strong_ref1.hpp"\n' + new[:at] + branch + new[at:]
    p.write_text(new)
    changes.append((p, old, new))
    for p, old, new in changes:
        (output/(p.name+'.diff')).write_text(''.join(difflib.unified_diff(
            old.splitlines(True),new.splitlines(True),fromfile='pinned/'+p.name,tofile='strong/'+p.name)))
    return [p for p, _, _ in changes]


def command(out, label, argv, cwd, timeout=1800):
    directory = out/label
    directory.mkdir()
    begin = time.monotonic()
    with (directory/'stdout.log').open('xb') as so, (directory/'stderr.log').open('xb') as se:
        p = subprocess.run(argv,cwd=cwd,stdin=subprocess.DEVNULL,stdout=so,stderr=se,timeout=timeout)
    fresh(directory/'command.json',dict(argv=argv,cwd=str(cwd),returncode=p.returncode,
                                       wall_s=time.monotonic()-begin))
    need(p.returncode == 0, 'Build failed: '+label)


def build(root, out):
    out.mkdir()
    source = root/'q32-q4-full-build-04/loop4/source'
    original = root/'run-01/build-loop4-01/native'
    source_lock = read(root/'run-01/stage-04/SOURCE_LOCK.json')
    locked_source = root/'run-01/stage-04/sources/loop4'
    for rel, digest in source_lock['sources']['loop4'].items():
        need(sha(locked_source/rel) == digest, 'Original source changed: '+rel)
    tree = out/'source'
    shutil.copytree(source,tree,ignore=shutil.ignore_patterns('.git','__pycache__'))
    changed = patch_tree(tree,out)
    command(out,'compile-marker-cpu-test',['/usr/bin/c++','-std=c++17','-O2',
        '-I'+str(tree/'ggml/include'),'-I'+str(tree/'ggml/src/ggml-cuda'),
        str(Path(__file__).parent/'marker_cpu_test.cpp'),'-o',str(out/'marker-cpu-test')],out)
    command(out,'run-marker-cpu-test',[str(out/'marker-cpu-test')],out,timeout=30)
    commands = read(original/'compile_commands.json')
    objects = []
    jobs = []
    for p in changed:
        unit = next(x for x in commands if x['file'].endswith('/'+p.name))
        args = [x.replace(str(locked_source),str(tree)) for x in shlex.split(unit['command'])]
        obj = out/(p.name+'.o')
        args[args.index('-o')+1] = str(obj)
        args += ['-MD','-MF',str(out/(p.name+'.d'))]
        objects.append(obj)
        jobs.append((p.name,args))
    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks=[pool.submit(command,out,'compile-'+label,args,original) for label,args in jobs]
        for task in tasks:
            task.result()
    original_archive = original/'llama/ggml/src/ggml-cuda/libggml-cuda.a'
    archive = out/'libggml-cuda.a'
    shutil.copyfile(original_archive,archive)
    command(out,'replace-archive',['ar','r',str(archive),*[str(p)for p in objects]],out)
    source_dir = Path(__file__).parent
    cuda_include = '/usr/local/cuda-12.5/targets/x86_64-linux/include'
    cpu_args = ['/usr/bin/c++','-std=c++17','-O3','-fPIC','-I'+str(source_dir),'-I'+cuda_include]
    includes = ['-I'+str(tree/p) for p in ['include','src','ggml/include','vendor','ggml/src/ggml-cuda']]
    obj = out/'operand-worker.o'
    command(out,'compile-worker',cpu_args+includes+['-c',str(source_dir/'operand_worker.cpp'),
                '-o',str(obj),'-MD','-MF',str(out/'operand-worker.d')],out)
    counts = out/'work-counts.o'
    command(out,'compile-counts',cpu_args+['-c',str(source_dir/'work_counts.cpp'),'-o',str(counts),
                '-MD','-MF',str(out/'work-counts.d')],out)
    baseline_link = read(root/'q32-q4-full-build-10/loop4/link/command.json')['argv']
    link = []
    for arg in baseline_link:
        if arg.endswith('/frontend.o'):
            link += [str(obj),str(counts)]
        elif arg.endswith('/transfer-worker'):
            link.append(str(out/'operand-worker'))
        elif arg.startswith('-Wl,-Map='):
            link.append('-Wl,-Map='+str(out/'operand-worker.map'))
        elif arg.endswith('/libggml-cuda.a'):
            link.append(str(archive))
        elif arg.endswith('/libllama.a'):
            continue
        else:
            link.append(arg)
    for symbol in ['cudaLaunchKernel','cudaLaunchKernelExC','cudaMemcpyAsync','cudaMemcpy',
                   'cudaMemcpy2DAsync','cudaMalloc','cudaMallocAsync','cudaStreamSynchronize','cudaDeviceSynchronize']:
        link.append('-Wl,--wrap='+symbol)
    command(out,'link-worker',link,original)
    members = subprocess.check_output(['ar','t',str(archive)],text=True).splitlines()
    need(len(members) == len(set(members)), 'Duplicate archive member')
    old_members = subprocess.check_output(['ar','t',str(original_archive)],text=True).splitlines()
    need(members == old_members, 'Archive member identities changed')
    changed_names = {p.name for p in objects}
    identities = []
    for name in members:
        import hashlib
        old_sha = hashlib.sha256(subprocess.check_output(['ar','p',str(original_archive),name])).hexdigest()
        new_sha = hashlib.sha256(subprocess.check_output(['ar','p',str(archive),name])).hexdigest()
        need(old_sha == new_sha or name in changed_names, 'Unexpected changed member: '+name)
        identities.append(dict(member=name,old_sha256=old_sha,new_sha256=new_sha))
    binary = out/'operand-worker'
    fresh(out/'BUILD.json',dict(status='CPU_BUILT_NOT_NUMERICALLY_QUALIFIED',executable=str(binary),
          executable_sha256=sha(binary),changed_cuda_sources=[dict(path=str(p),sha256=sha(p))for p in changed],
          original_archive_sha256=sha(original_archive),new_archive_sha256=sha(archive),members=identities,
          flags_from_recorded_compile_commands=True,original_scalar_dot_kernels_unchanged=True,
          independent_R_linked=False,native_model_requests_started=0,
          limitations=['Full model integration, complete transitive closure and numeric GPU qualification pending',
                       'API launch counters exclude opaque library internals; VMM allocations not counted']))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    need(not a.out.exists(),'Fresh build directory')
    try:
        build(a.root,a.out)
    except BaseException as error:
        if a.out.exists():
            fresh(a.out/'BUILD_FAILED.json',dict(status='CPU_BUILD_FAILED',error_type=type(error).__name__,
                  reason=str(error),native_model_requests_started=0,GPU_admitted=False))
        raise


if __name__=='__main__':
    main()
