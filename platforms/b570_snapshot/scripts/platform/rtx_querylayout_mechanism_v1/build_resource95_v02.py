"""Resource-only PQ graph capacity correction. No GPU invocations or numerical patch."""
from common95 import *
from freeze95 import archive,split
import shutil,difflib
src=LOCAL/'native-repair/source';build=LOCAL/'native-repair/build';original=LOCAL/'native/source'
assert not (LOCAL/'RESULT_PR.json').exists()
assert not list((LOCAL/'runs').rglob('FAILED_FORMAL_RETRY.json'))
shutil.copytree(original,src)
path=src/'src/llama-context.cpp';text=path.read_text(encoding='utf-8');before=text
start=text.index('uint32_t llama_context::graph_max_nodes(');end=text.index('\nllm_graph_result *',start)
block=text[start:end];assert block.count('    return res;')==1
block=block.replace('    return res;','    // PQ materializes up to four attention subgraphs; reserve metadata capacity only.\n    return hs_scope::layout95() == 1 ? 4 * res : res;')
text=text[:start]+block+text[end:];path.write_text(text,encoding='utf-8',newline='\n')
inventory={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file()};old=read(PUB/'NATIVE_SOURCE_HASHES.json')
changed=[n for n in inventory if old[n]!=inventory[n]];assert changed==['src/llama-context.cpp']
save(PUB/'NATIVE_SOURCE_HASHES_V02.json',inventory)
save(PUB/'RESOURCE_CORRECTION.json',dict(utc=now(),reason='PQ metadata allocation abort before any PQ engineering panel or formal slot in SmolLM2/Llama',changed_source=changed,patch=''.join(difflib.unified_diff(before.splitlines(True),text.splitlines(True),fromfile='v01/src/llama-context.cpp',tofile='v02/src/llama-context.cpp')),capacity_factor=4,bound_from_predeclared_max_q=4,numerical_graph_operations_changed=False,numerical_backend_DLLs_changed=False,models_precision_mask_k_panel_unchanged=True,affected_runtime_arms=['SmolLM2/M_PQ','SmolLM2/C_PQ','Llama/M_PQ','Llama/C_PQ'],failed_warm_slots_never_retried=True,formal_slots_already_started=96,no_formal_retries=True))
asset=Path('D:/HeteroSpec-PC');zig=asset/'.venv-analysis/Lib/site-packages/ziglang/zig.exe';cmake=asset/'.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe'
cmd=[str(cmake),'-S',str(src),'-B',str(build),'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(asset/'.venv-analysis/Scripts/ninja.exe'),'-DCMAKE_C_COMPILER='+str(zig),'-DCMAKE_C_COMPILER_ARG1=cc','-DCMAKE_CXX_COMPILER='+str(zig),'-DCMAKE_CXX_COMPILER_ARG1=c++','-DCMAKE_AR='+str(asset/'scripts/debug/cuda_divergence/zig-ar.cmd'),'-DCMAKE_RANLIB='+str(asset/'scripts/debug/cuda_divergence/zig-ranlib.cmd'),'-DCMAKE_BUILD_TYPE=Release','-DBUILD_SHARED_LIBS=OFF','-DGGML_BACKEND_DL=ON','-DGGML_CPU=OFF','-DGGML_CUDA=OFF','-DLLAMA_SUBPROCESS=OFF','-DLLAMA_BUILD_APP=OFF','-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_MTMD=OFF','-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_UI=OFF','-DLLAMA_USE_PREBUILT_UI=OFF','-DLLAMA_BUILD_NUMBER=10839','-DLLAMA_BUILD_COMMIT=0cae43063','-DCMAKE_EXE_LINKER_FLAGS=-lpsapi','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
attempts=[];status('CPU_BUILD_RESOURCE_CORRECTION',new_forwards=0,formal_retained=96)
for name,c in [('configure',cmd),('build',[str(cmake),'--build',str(build),'--target','llama-server','-j','4'])]:
    log=LOCAL/'native-repair'/('build-'+name+'.log')
    with log.open('xb') as f:r=subprocess.run(c,stdout=f,stderr=subprocess.STDOUT)
    attempts.append(dict(command=c,returncode=r.returncode,log_sha256=sha(log)));assert r.returncode==0,(name,log)
server=LOCAL/'native/build/bin/llama-server-pq-metadata4.exe';shutil.copyfile(build/'bin/llama-server.exe',server)
oldbuild=read(PUB/'NATIVE_BUILD.json')
save(PUB/'NATIVE_BUILD_V02.json',dict(status='BUILT_NOT_GPU_QUALIFIED',utc=now(),source_inventory_sha256=sha(PUB/'NATIVE_SOURCE_HASHES_V02.json'),server_sha256=sha(server),server_path=str(server),replay_sha256=oldbuild['replay_sha256'],compiler_sha256=sha(zig),cmake_sha256=sha(cmake),numerical_DLL_sha256=oldbuild['numerical_DLL_sha256'],attempts=attempts,scope='PQ in SmolLM2/Llama only; original binary remains authority for every other arm'))
files={'native/source/'+p.relative_to(src).as_posix():p for p in src.rglob('*') if p.is_file()}
files['native/bin/llama-server-pq-metadata4.exe']=server
for p in (LOCAL/'native-repair').glob('*.log'):files['native/'+p.name]=p
pkg=LOCAL/'SOURCE_RUNTIME_V02.zip';info=archive(pkg,files);parts=split(pkg,'SOURCE_RUNTIME_V02');save(PUB/'SOURCE_RUNTIME_MANIFEST_V02.json',dict(**info,parts=parts,format='ordered binary ZIP slices',inherits_original_pinned_numerical_runtime=True))
status('RESOURCE_CORRECTION_BUILT_NOT_GPU_QUALIFIED',formal_retained=96,new_forwards=0)
