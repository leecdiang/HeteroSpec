from common95 import *
import shutil
assert not (PUB/'F0A.json').exists() and not (LOCAL/'ledger').exists()
src=LOCAL/'native/source';build=LOCAL/'native/build';asset=Path('D:/HeteroSpec-PC');cmake=asset/'.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe'
evidence=PUB/'CPU_BUILD_ATTEMPTS/v02';evidence.mkdir(parents=True)
for p in [LOCAL/'native/build-resumed.log',LOCAL/'build-resumed.stderr.log']:shutil.copyfile(p,evidence/p.name)
p=src/'CMakeLists.txt';s=p.read_text(encoding='utf-8');needle='target_include_directories(querylayout-replay PRIVATE ${CMAKE_SOURCE_DIR}/vendor/nlohmann)';assert s.count(needle)==1;p.write_text(s.replace(needle,'target_include_directories(querylayout-replay PRIVATE ${CMAKE_SOURCE_DIR}/common)'),encoding='utf-8',newline='\n')
status('BUILDING_REPLAY_HELPER',new_forwards=0)
cmd=[str(cmake),'--build',str(build),'--target','llama-server','querylayout-replay','-j','4'];log=LOCAL/'native/build-final.log'
with log.open('xb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0,log
for name,h in read(PUB/'ANCESTRY_RESTORE.json')['numerical_DLL_sha256'].items():
    shutil.copyfile(asset/'tools/llama-b10839'/name,build/'bin'/name);assert sha(build/'bin'/name)==h
before=read(PUB/'PARENT_NATIVE_SOURCE_HASHES.json');after={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file()}
for p in [PUB/'NATIVE_SOURCE_HASHES.json',PUB/'NATIVE_PATCH.json']:
    shutil.copyfile(p,evidence/p.name);assert p.resolve().parent==PUB.resolve();p.unlink()
save(PUB/'NATIVE_SOURCE_HASHES.json',after)
save(PUB/'NATIVE_PATCH.json',dict(changed_files={n:h for n,h in after.items() if before.get(n)!=h},parent_head=PARENT_HEAD,numerical_backend_source_changed=False,declared_changes=['Phase-scoped historical PQ subgraphs for admitted Qwen3/Llama graphs','GS whole-target physical microbatch1, unchanged caller/output reservation and draft','Diagnostic-only native QK/softmax/AV input/output readbacks','Actual graph reuse rejection trace only in heavy diagnostic mode'],CPU_failed_builds_preserved=['CPU_BUILD_ATTEMPTS/v01','CPU_BUILD_ATTEMPTS/v02'],no_new_forwards=True))
save(PUB/'NATIVE_BUILD.json',dict(status='BUILT_NOT_GPU_QUALIFIED',utc=now(),source_inventory_sha256=sha(PUB/'NATIVE_SOURCE_HASHES.json'),server_sha256=sha(build/'bin/llama-server.exe'),replay_sha256=sha(build/'bin/querylayout-replay.exe'),compiler_sha256=sha(asset/'.venv-analysis/Lib/site-packages/ziglang/zig.exe'),cmake_sha256=sha(cmake),numerical_DLL_sha256=read(PUB/'ANCESTRY_RESTORE.json')['numerical_DLL_sha256'],attempts=[dict(command=cmd,returncode=r.returncode,log_sha256=sha(log))]))
save(PUB/'PROFILER_ADMISSION.json',dict(utc=now(),nsys=shutil.which('nsys'),ncu=shutil.which('ncu'),nvcc=shutil.which('nvcc'),paid_profiling_enabled=False,diagnostic_fallback='Actual native node/backend buffer dispatch and standalone CUDA0 graph return status; kernel symbol/grid/block/algorithm UNKNOWN without independent kernel-level trace. No reduction scheduling claim from node names.',source_backend_DLL_unchanged=True))
status('ISOLATED_NATIVE_BUILT',new_forwards=0)
