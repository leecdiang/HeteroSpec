from common98 import *
OLD=ROOT.parent/'b570-phasebinding-boundary-v1'
shutil.copytree(OLD/'dependencies/pinned-source',ROOT/'dependencies/pinned-source')
for n in ['ggml','ggml-base']:shutil.copy2(OLD/'dependencies/pinned-build/ggml/src/Release'/(n+'.lib'),ROOT/'build/Release'/(n+'.lib'))
p=ROOT/'native/CMakeLists.txt';s=p.read_text();s=s.replace((OLD/'dependencies/pinned-source').as_posix(),chr(36)+'{CMAKE_SOURCE_DIR}/../dependencies/pinned-source').replace((OLD/'build/Release/llama-b570-memory.lib').as_posix(),chr(36)+'{CMAKE_SOURCE_DIR}/../build/Release/llama-b570-memory.lib').replace(chr(36)+'{PINNED_BUILD}/ggml/src/Release/ggml.lib',chr(36)+'{CMAKE_SOURCE_DIR}/../build/Release/ggml.lib').replace(chr(36)+'{PINNED_BUILD}/ggml/src/Release/ggml-base.lib',chr(36)+'{CMAKE_SOURCE_DIR}/../build/Release/ggml-base.lib');p.write_text(s,encoding='utf8',newline='\n')
shutil.copy2(OLD/'baseline/pr92_restore/RESULTS.json',ROOT/'baseline/PR92_QUALIFICATION.json')
for name in ['llama-kv-cache.cpp','llama-context.cpp','llama-memory.cpp','llama-kv-cache.h','llama-kv-cells.h']:
 q=OLD/'baseline/pr92_restore/native/candidate-src'/name
 if q.exists():shutil.copy2(q,ROOT/'baseline'/name)
hist=load(ROOT/'baseline/HISTORICAL_SELECTED.json');sources=[]
for r in hist:
 p=OLD/'baseline/pr92_restore'/r['raw_path'].replace(chr(92),'/');q=ROOT/'baseline'/r['raw_path'].replace(chr(92),'/');q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);sources.append(dict(path=str(q.relative_to(ROOT)).replace(chr(92),'/'),sha256=sha(q)))
save(ROOT/'baseline/HISTORICAL_NATIVE_PINS.json',sources)
import py_compile
py_compile.compile(str(ROOT/'code/controller98.py'),doraise=True)
# Reconfigure portable identical-byte headers/import libs before freezing.
check_step('PORTABLE_CONFIGURE',['C:/Program Files/CMake/bin/cmake.exe','-S',str(ROOT/'native'),'-B',str(ROOT/'build-host64'),'-DCMAKE_TRY_COMPILE_CONFIGURATION=Release'])
check_step('PORTABLE_BUILD',['C:/Program Files/CMake/bin/cmake.exe','--build',str(ROOT/'build-host64'),'--config','Release','--parallel','4'])
shutil.copy2(ROOT/'build-host64/Release/b570-boundary-worker.exe',ROOT/'build/Release/b570-boundary-worker.exe')
pin=load(ROOT/'NATIVE_BUILD.json');pin['worker_sha256']=sha(ROOT/'build/Release/b570-boundary-worker.exe');pin['portable_source_imports']=True;save(ROOT/'NATIVE_BUILD.json',pin)
files=[p for folder in ['code','native','dependencies','build/Release','baseline'] for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
files.extend(ROOT/n for n in ['COUNTER_SEMANTICS.json','INPUTS.json','PLAN.json','PROTOCOL.md','README.md','ASSET_PREFLIGHT.json','NATIVE_BUILD.json','ENVIRONMENT_FAILURES.json'])
pins=[dict(path=str(p.relative_to(ROOT)).replace(chr(92),'/'),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]
f=dict(parent_head='5a66653bd0ce413d4eb9aef3a4501b93c138071b',plan_sha256=digest(load(ROOT/'PLAN.json')),inputs_file_sha256=sha(ROOT/'INPUTS.json'),runtime_files=pins,forward_calls_before_seal=0,utc=now())
save(ROOT/'F0A.json',f)
with zipfile.ZipFile(ROOT/'F0A_SOURCE.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files+[ROOT/'F0A.json']:z.write(p,str(p.relative_to(ROOT)).replace(chr(92),'/'))
save(ROOT/'F0A_CAPSULE.json',dict(bytes=(ROOT/'F0A_SOURCE.zip').stat().st_size,sha256=sha(ROOT/'F0A_SOURCE.zip'),files=len(files)+1,scope='All frozen actor/source/runtime/numericalDLL/input/baseline bytes; no GGUF weights',utc=now()))
print('F0A_SEALED',len(files)+1,(ROOT/'F0A_SOURCE.zip').stat().st_size,flush=True)
