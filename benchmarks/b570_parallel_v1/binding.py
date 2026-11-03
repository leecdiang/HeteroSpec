"""Bind bytes actually loaded, including staged changes beyond the first source receipt."""
from experiment import *
def bind_source(role):
    src=ROOT/'source-00'
    files=['src/hs_reference_batching.hpp','src/query_head.h','src/llama-context.cpp','src/llama-graph.cpp','src/llama-kv-cache.cpp','src/llama-kv-cache.h','ggml/src/ggml-vulkan/ggml-vulkan.cpp',
           'ggml/src/ggml-vulkan/vulkan-shaders/mul_mat_vec_base.glsl','ggml/src/ggml-vulkan/vulkan-shaders/mul_mat_vec_p021.comp','ggml/src/ggml-vulkan/vulkan-shaders/mul_mat_vec_nc.comp']
    actual={f:sha(src/f) for f in files if (src/f).is_file()}
    common='src/hs_reference_batching.hpp'
    repo=HERE.parents[1]
    assert sha(repo/'src/reference_batching/reference_batching.hpp')==actual[common]=='7c1e2ee97e0af5b306ec9ba3cf7e2fb55c37749da07891f46cccd88041530809'
    cmd=['git','-c','gc.auto=0','-c','maintenance.auto=false','rev-parse','9c79594f679ea4aad1956d8a385fdf6a7352d892:src/reference_batching/reference_batching.hpp']
    assert subprocess.check_output(cmd,cwd=repo,text=True).strip()=='a0baff824a1b54fb3867845372939b9a97c11115'
    dest=ROOT/f'SOURCE_BINDING-{role}.json'
    put_once(dest,dict(parent='5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f',runtime=role,runtime_files=read(ROOT/role/'FILES.json'),worker_snapshot=sha(ROOT/role/'worker.cpp') if (ROOT/role/'worker.cpp').exists() else None,reference_runtime_files=read(ROOT/('reference-D' if role=='candidate-D' else 'reference-B')/'FILES.json'),
        compiled_source=actual,pr166_core_commit='abd36bea639bf814159ad68ab015bc983c5338b1',rtx_integrated_commit='9c79594f679ea4aad1956d8a385fdf6a7352d892',
        common_git_blob='a0baff824a1b54fb3867845372939b9a97c11115',cmake_cache_sha256=sha(ROOT/'build-00/CMakeCache.txt'),first_receipt=sha(ROOT/'SOURCE.json')))
if __name__=='__main__':bind_source(sys.argv[1])
