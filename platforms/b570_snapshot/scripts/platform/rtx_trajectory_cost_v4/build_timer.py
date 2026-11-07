"""Build an isolated b10839 timer CLI; never modify historical trees."""
import argparse, difflib, hashlib, json, shutil, subprocess, tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'benchmarks/rtx_trajectory_cost_v4'

def main():
    p=argparse.ArgumentParser();p.add_argument('--source-tar',type=Path,required=True);a=p.parse_args()
    src=ROOT/'work/timer-source';build=ROOT/'work/timer-build'
    src.mkdir(parents=True,exist_ok=True)
    with tarfile.open(a.source_tar) as t:t.extractall(src,filter='data')
    file=src/'tools/server/server-context.cpp'; original=file.read_text(encoding='utf-8');s=original
    s=s.replace('#include <utility>','#include <utility>\n#include <chrono>\n#include <cstdio>')
    s=s.replace('    server_slot_stats stats;', '''    server_slot_stats stats;
    int64_t hs_qpc_start = 0;
    int64_t hs_steady_start = 0;
    bool hs_timing = false;
    void hs_start() {
        LARGE_INTEGER q; QueryPerformanceCounter(&q);
        hs_qpc_start = q.QuadPart;
        hs_steady_start = std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count();
        hs_timing = true;
    }
    void hs_finish(int count, int terminal_id) {
        LARGE_INTEGER q, f; QueryPerformanceCounter(&q); QueryPerformanceFrequency(&f);
        const int64_t ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count();
        GGML_ASSERT(hs_timing && count > 0 && count <= 128);
        // Write both endpoint pairs only AFTER the measured end.
        fprintf(stderr, "HS_TIMER start_qpc=%lld end_qpc=%lld frequency=%lld start_steady_ns=%lld end_steady_ns=%lld count=%d terminal_id=%d\\n",
            (long long)hs_qpc_start, (long long)q.QuadPart, (long long)f.QuadPart,
            (long long)hs_steady_start, (long long)ns, count, terminal_id);
        hs_timing = false;
    }''')
    start=s.index('        // initialize samplers\n')
    end=s.index('        // the per-request limit takes priority',start)
    block=s[start:end]
    s=s[:start]+'''        // Per-request sampler creation/seed is deferred until synchronized prefill.
        // This campaign uses fresh contexts, greedy sampling, no backend sampler,
        // no grammar, no parent tasks, and no synthetic probabilities.
'''+s[end:]
    # The CLI parameters are checked by the runner; postpone the complete request
    # sampler setup, rather than silently excluding its constructor/seed cost.
    block=block.replace('task.', 'slot.task->')
    block=block.replace('slot.smpl.reset(common_sampler_init(model_tgt, slot.task->params.sampling));',
        'auto hs_sampling = slot.task->params.sampling;\n                slot.smpl.reset(common_sampler_init(model_tgt, hs_sampling));')
    block=block.replace('send_error(task,', 'send_error(slot,')
    block=block.replace('return false;', 'throw;')
    needle='''                // prompt evaluated for next-token prediction
                slot.state = SLOT_STATE_GENERATING;'''
    replacement='''                // Both target and draft initial prompt prefill have completed.
                llama_synchronize(ctx_tgt);
                if (ctx_dft) llama_synchronize(ctx_dft);
                slot.hs_start();
'''+block+'''                slot.init_sampler();
                // prompt evaluated for next-token prediction
                slot.state = SLOT_STATE_GENERATING;'''
    assert s.count(needle)==1;s=s.replace(needle,replacement)
    # Do not accept prompt tokens into a sampler before it has been created.
    needle='''                        slot.init_sampler();'''
    assert s.count(needle)==1;s=s.replace(needle,'                        // sampler setup is charged after synchronized prefill')
    # End after terminal commitment AND required slot/state release. Target
    # verification, drafting, scheduling and rollback remain inside the interval.
    for indent in ('                ','                    '):
        needle=indent+'slot.release();\n\n'+indent+'return;'
        # Select terminal branches only by the print_timings/send_final sequence.
        full=indent+'slot.print_timings();\n'+indent+'send_final_response(slot);\n'+needle
        if full in s:
            new=indent+'const int hs_count = slot.stats.n_gen;\n'+indent+'const int hs_terminal = result.tok;\n'+indent+'llama_synchronize(ctx_tgt);\n'+indent+'if (ctx_dft) llama_synchronize(ctx_dft);\n'+indent+'slot.print_timings();\n'+indent+'send_final_response(slot);\n'+indent+'slot.release();\n'+indent+'slot.hs_finish(hs_count, hs_terminal);\n\n'+indent+'return;'
            s=s.replace(full,new)
    assert s.count('slot.hs_finish(hs_count, hs_terminal);')==2
    file.write_text(s,encoding='utf-8',newline='\n')
    STUDY.mkdir(parents=True,exist_ok=True)
    patch=''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='a/tools/server/server-context.cpp',tofile='b/tools/server/server-context.cpp'))
    (STUDY/'timer.patch').write_text(patch,encoding='utf-8',newline='\n')
    clifile=src/'tools/cli/cli.cpp'
    clioriginal=clifile.read_text(encoding='utf-8')
    climodified=clioriginal.replace('    cli_context ctx_cli(params);', '''    // The in-process frontend must initialize its static host clock/backend
    // before calling the parameter-overload server entry point. Frozen external
    // CUDA backend DLLs have their own ggml-base clock state; initialize it too.
    llama_backend_init();
    HMODULE hs_base = LoadLibraryW(L"ggml-base.dll");
    if (!hs_base) return 4;
    auto hs_init_clock = (void (*)()) GetProcAddress(hs_base, "ggml_time_init");
    if (!hs_init_clock) return 5;
    hs_init_clock();
    cli_context ctx_cli(params);''')
    clifile.write_text(climodified,encoding='utf-8',newline='\n')
    patch+=''.join(difflib.unified_diff(clioriginal.splitlines(True),climodified.splitlines(True),fromfile='a/tools/cli/cli.cpp',tofile='b/tools/cli/cli.cpp'))
    (STUDY/'timer.patch').write_text(patch,encoding='utf-8',newline='\n')
    cmfile=src/'ggml/src/CMakeLists.txt'
    cmoriginal=cmfile.read_text(encoding='utf-8')
    cmmodified=cmoriginal.replace('message(FATAL_ERROR "GGML_BACKEND_DL requires BUILD_SHARED_LIBS")',
        'message(WARNING "HeteroSpec isolated timer: static frontend loads frozen external backend")')
    cmfile.write_text(cmmodified,encoding='utf-8',newline='\n')
    patch+=''.join(difflib.unified_diff(cmoriginal.splitlines(True),cmmodified.splitlines(True),fromfile='a/ggml/src/CMakeLists.txt',tofile='b/ggml/src/CMakeLists.txt'))
    (STUDY/'timer.patch').write_text(patch,encoding='utf-8',newline='\n')
    cmake='D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe'
    zig='D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/ziglang/zig.exe'
    command=[cmake,'-S',str(src),'-B',str(build),'-G','Ninja',
      '-DCMAKE_MAKE_PROGRAM=D:/HeteroSpec-PC/.venv-analysis/Scripts/ninja.exe',
      '-DCMAKE_C_COMPILER='+zig,'-DCMAKE_C_COMPILER_ARG1=cc',
      '-DCMAKE_CXX_COMPILER='+zig,'-DCMAKE_CXX_COMPILER_ARG1=c++',
      '-DCMAKE_AR=D:/HeteroSpec-PC/scripts/debug/cuda_divergence/zig-ar.cmd',
      '-DCMAKE_RANLIB=D:/HeteroSpec-PC/scripts/debug/cuda_divergence/zig-ranlib.cmd',
      '-DCMAKE_BUILD_TYPE=Release','-DBUILD_SHARED_LIBS=OFF','-DGGML_BACKEND_DL=ON',
      '-DGGML_CPU=OFF','-DGGML_CUDA=OFF','-DLLAMA_SUBPROCESS=OFF','-DLLAMA_BUILD_APP=OFF',
      '-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_MTMD=OFF',
      '-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_UI=OFF','-DLLAMA_USE_PREBUILT_UI=OFF',
      '-DLLAMA_BUILD_NUMBER=10839','-DLLAMA_BUILD_COMMIT=0cae43063', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
    subprocess.run(command,check=True)
    subprocess.run([cmake,'--build',str(build),'--target','llama-cli','-j','4'],check=True)
    # Reuse CUDA and CPU backend distribution only. New core/front-end DLLs are
    # individually identified and require fresh direct-ID qualification.
    old=Path('D:/HeteroSpec-PC/tools/llama-b10839')
    for name in ('ggml-cuda.dll','cublas64_12.dll','cublasLt64_12.dll','cudart64_12.dll','libomp.dll'):
        shutil.copyfile(old/name,build/'bin'/name)
    for name in ('ggml-base.dll','ggml.dll'):
        shutil.copyfile(old/name,build/'bin'/name)
    for f in old.glob('ggml-cpu-*.dll'):shutil.copyfile(f,build/'bin'/f.name)
    identity={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (build/'bin').iterdir() if f.suffix in ('.exe','.dll')}
    record={'source_tar_sha256':hashlib.sha256(a.source_tar.read_bytes()).hexdigest(),
      'upstream_commit':'0cae43063cf15170e91a2ff4d034da0ecef4a1b2','patch_sha256':hashlib.sha256(patch.encode()).hexdigest(),
      'configure_command':command,'compiler_sha256':hashlib.sha256(Path(zig).read_bytes()).hexdigest(),
      'binaries':identity,'binary_dir':str(build/'bin'),
      'source_files':{f.relative_to(src).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()},
      'eligibility':'engineering build; NOT qualified by historical v2'}
    (STUDY/'timer_build_manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':main()
