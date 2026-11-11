from paths import *
import shutil
DATA=PR165/'historical/NATIVE_PANEL.json'
Q=read(PR165/'MODEL_PINS.json')['files']
S=Path('C:/hs/jsa-b570-run-v1/models')
sm=str(S/'SmolLM2-1.7B-Instruct-Q8_0.gguf');tiny=str(S/'SmolLM2-135M-Instruct-Q8_0.gguf')
MODELS={'qwen':tuple(x['path'] for x in Q),'smol':(sm,tiny),'tiny':(tiny,sm)}
MODELS['qwen_target']=MODELS['qwen']
def setup():
    ROOT.mkdir(exist_ok=True)
    if not (ROOT/'ASSETS.json').exists():
        pins=[]
        for f in set(p for m in MODELS.values() for p in m):
            p=Path(f);pins.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns))
        assert all(any(x['sha256']==y['sha256'] for y in pins) for x in Q)
        write(ROOT/'ASSETS.json',pins)
    if not (ROOT/'supervisor.py').exists():
        s=SUP.read_text(encoding='utf-8')
        key="    if a.capture:env['HS_STAGE_CAPTURE']"
        s=once(s,key,'''    task=json.loads(Path(a.argv[1]).read_text(encoding="utf-8")) if a.argv[1].endswith(".json") else {}
    if task.get("dispatch"):env["HS_PARALLEL_DISPATCH"]="1";env["HS_TRANSFER_TRACE"]="1"
    if task.get("profile"):env["GGML_VK_PERF_LOGGER"]="1"
'''+key)
        (ROOT/'supervisor.py').write_text(s,encoding='utf-8')
def driver(name,src,libs,candidate,worker=HERE/'worker.cpp'):
    dest=ROOT/name;dest.mkdir()
    shutil.copyfile(worker,dest/'worker.cpp');worker=dest/'worker.cpp'
    cm=f'''cmake_minimum_required(VERSION 3.20)
project(frontier_driver LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
add_executable(frontier "{worker.as_posix()}")
target_include_directories(frontier PRIVATE "{src.as_posix()}/include" "{src.as_posix()}/ggml/include" "{src.as_posix()}/vendor")
target_compile_definitions(frontier PRIVATE LLAMA_SHARED GGML_SHARED GGML_BACKEND_SHARED)
target_compile_options(frontier PRIVATE /fp:precise /O2 /W4 /utf-8)
target_link_libraries(frontier PRIVATE "{libs.as_posix()}/runtime/src/Release/llama.lib" "{libs.as_posix()}/runtime/ggml/src/Release/ggml.lib" "{libs.as_posix()}/runtime/ggml/src/Release/ggml-base.lib" bcrypt)
'''
    if candidate:cm+='target_compile_definitions(frontier PRIVATE CAND)\n'
    (dest/'CMakeLists.txt').write_text(cm,encoding='utf-8')
    command(['cmake','-S',dest,'-B',dest/'build','-G','Visual Studio 17 2022','-A','x64'],dest/'configure.log')
    command(['cmake','--build',dest/'build','--config','Release','--parallel','4'],dest/'compile.log')
    bin=dest/'build/Release'
    for dll in (libs/'bin/Release').glob('*.dll'):shutil.copyfile(dll,bin/dll.name)
    bind(name,bin)
def bind(name,bin,exe='frontier.exe'):
    files=[bin/exe,*sorted(bin.glob('*.dll'))];assert len(files)>=6
    write(ROOT/name/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in files]))
def run(name,role,job,*,timeout=1200,allow_failure=False,args=None):
    unit=ROOT/'units'/name
    if unit.exists():
        assert read(unit/'JOB.json')==job
        receipt=read(unit/'RECEIPT.json')
        if not receipt['success'] and not allow_failure:raise RuntimeError(name+': retained failure')
        return read(unit/'native/result.json') if (unit/'native/result.json').exists() else receipt
    for f in read(ROOT/'ASSETS.json'):
        st=Path(f['path']).stat();assert st.st_size==f['bytes'] and st.st_mtime_ns==f['mtime_ns']
    unit.mkdir(parents=True);write(unit/'JOB.json',job)
    manifest=ROOT/role/'FILES.json';files=read(manifest)['files']
    argv=[files[0]['path'],str(unit/'JOB.json'),str(unit/'native')] if args is None else [files[0]['path'],*args(unit)]
    sup_path=ROOT/'supervisor.py'
    if job.get('block_bytes'):
        tuned=ROOT/'allocation-supervisor.py'
        if not tuned.exists():
            s=sup_path.read_text(encoding='utf-8')
            key='    exe=Path(a.argv[0]).resolve()'
            s=once(s,key,'    cfg=json.loads(next(Path(v) for v in a.argv[1:] if Path(v).name=="JOB.json").read_text(encoding="utf-8"))\n    env["GGML_VK_SUBALLOCATION_BLOCK_SIZE"]=str(cfg["block_bytes"])\n'+key)
            tuned.write_text(s,encoding='utf-8')
        sup_path=tuned
    if job.get('device_local'):
        assert not job.get('block_bytes')
        tuned=ROOT/'device-local-supervisor.py'
        if not tuned.exists():
            s=sup_path.read_text(encoding='utf-8')
            key='    exe=Path(a.argv[0]).resolve()'
            tuned.write_text(once(s,key,'    env["GGML_VK_DISABLE_HOST_VISIBLE_VIDMEM"]="1"\n'+key),encoding='utf-8')
        sup_path=tuned
    cmd=[sys.executable,'-B',str(sup_path),'--manifest',str(manifest),'--receipt',str(unit/'SUPERVISOR.json'),'--limit',str(timeout),'--minimum-free-bytes',str(20*1024**3),*argv]
    write(unit/'COMMAND.json',cmd);write(LOCK,dict(pid=os.getpid(),unit=str(unit)))
    start=time.monotonic()
    try:
        with (unit/'host.log').open('x') as log:code=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+180).returncode
        sup=read(unit/'SUPERVISOR.json');assert sup['job_accounting']['active_processes']==0
        native=read(unit/'native/result.json') if (unit/'native/result.json').exists() else {'status':'NO_NATIVE_FOOTER'}
        loaded={Path(x['path']).name.lower():x['sha256'] for x in sup.get('loaded_module_hashes',[])}
        ok=code==0 and sup['status']=='complete' and all(loaded.get(Path(f['path']).name.lower())==f['sha256'] for f in files if f['path'].endswith('.dll'))
        write(unit/'RECEIPT.json',dict(success=ok,status=native['status'],owned_seconds=time.monotonic()-start,process_seconds=sup['charged_seconds'],cleanup=True,manifest_sha256=sha(manifest)))
        if not ok and not allow_failure:raise RuntimeError(name+': '+str(native.get('error',native['status'])))
        print('UNIT',name,native['status'],flush=True);return native
    finally:
        if (unit/'SUPERVISOR.json').is_file() and read(unit/'SUPERVISOR.json').get('job_accounting',{}).get('active_processes')==0:LOCK.unlink(missing_ok=True)
def job(family,C,slots,**extras):
    if family=='qwen_target':extras['target_only']=True
    t,d=MODELS[family];return dict(target=t,draft=d,context=C,cas=str(ROOT/'vectors'),slots=slots,**extras)
if __name__=='__main__':
    setup();role=sys.argv[1]
    if role.startswith('reference'):driver(role,OLD_LIB/'clean-source2/llama.cpp-0cae43063cf15170e91a2ff4d034da0ecef4a1b2',OLD_LIB/'build',False)
    else:driver(role,ROOT/'source-00',ROOT/'build-00',True)
