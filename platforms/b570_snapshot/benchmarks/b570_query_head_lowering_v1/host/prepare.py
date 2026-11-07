"""Read-only old-asset qualification, offline build and delivered small tests."""
import argparse, io, json, pathlib, shutil, subprocess, sys, time, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, load, save, sha, modules
sys.path.insert(0,str(ROOT))
import core, plan

def main():
    p=argparse.ArgumentParser();p.add_argument('--old',type=pathlib.Path,required=True)
    p.add_argument('--pr111',type=pathlib.Path,required=True);p.add_argument('--source',type=pathlib.Path,required=True)
    p.add_argument('--cmake',default='cmake');a=p.parse_args();before=modules();out=ROOT/'host';host=ROOT/'host_outputs';host.mkdir(exist_ok=True)
    oldbinding=load(a.pr111/'SOURCE_BINDINGS.json');source=[]
    for x in oldbinding['backend_sources']:
        if x['status']=='MATCH':
            f=a.source/x['path'];assert sha(f)==x['expected'];source.append(x)
    for x in oldbinding['dlls']:assert sha(a.old/'_host/build/Release'/x['name'])==x['actual']
    assert sha(a.old/'p0/F0_EXECUTION.json')==oldbinding['F0_sha256']
    for name in ('native/local_attention.h','native/graph_contract_cpu.cpp','native/graph_numeric_cpu.cpp'):
        expected=next(x['sha256'] for x in oldbinding['native'] if x['path']==name);assert sha(a.old/name)==expected
    stream=io.StringIO();teststart=time.monotonic()
    tests=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(tests)
    save(out/'HOST_TOY_TESTS.json',dict(tests=result.testsRun,success=result.wasSuccessful(),log=stream.getvalue(),elapsed_s=time.monotonic()-teststart,scope='SMALL_SYNTHETIC_NOT_GGML',modules_before=before,modules_after=modules()))
    assert result.wasSuccessful()
    dep=a.old/'_host/pr97/dependencies';build=ROOT/'build';cmake=[a.cmake,'-S',str(ROOT/'native/host'),'-B',str(build),'-G','Visual Studio 17 2022','-A','x64','-DPINNED='+str(dep/'pinned-source'),'-DBASE_LIB='+str(dep/'pinned-build/ggml/src/Release/ggml-base.lib')]
    logs=[];ok=True
    for cmd in [cmake,[a.cmake,'--build',str(build),'--config','Release']]:
        start=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
        logs.append(dict(argv=cmd,returncode=r.returncode,elapsed_s=time.monotonic()-start,stdout=r.stdout,stderr=r.stderr));print(r.stdout[-3500:])
        if r.returncode:ok=False;break
    n=len(list(out.glob('HOST_BUILD_*.json')))
    save(out/f'HOST_BUILD_{n:02d}.json',dict(success=ok,logs=logs,modules=modules(),real_include=str(dep/'pinned-source/ggml/include'),mock_include_excluded_from_real=True))
    if not ok:raise SystemExit(1)
    for name in ('ggml-base.dll','ggml-cpu.dll'):shutil.copy2(a.old/'_host/build/Release'/name,build/'Release'/name)
    r=subprocess.run([str(build/'Release/qh-descriptor.exe')],capture_output=True,text=True)
    save(out/'HOST_DESCRIPTOR_TESTS.json',dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,executable_sha256=sha(build/'Release/qh-descriptor.exe'),scope='DESCRIPTOR_MOCK_ONLY_NO_NUMERICAL_GGML'))
    assert r.returncode==0 and 'cases=48' in r.stdout
    save(out/'HOST_SOURCE_BINDINGS.json',dict(PR112='7864716787fabb17cb613ed7125c180736c133ef',PR111='9fafc4ba49119f1c52e1606d295bd0b9a55a06d1',PR109='039a24bf61374042e0dc9f3a3619ea40b218a5ad',old_binding_sha256=sha(a.pr111/'SOURCE_BINDINGS.json'),backend_source=source,dlls=oldbinding['dlls'],F0_unchanged=oldbinding['F0_sha256'],original_R=load(a.old/'p0/RUNTIME.json')['runtimes']['old'] if 'runtimes' in load(a.old/'p0/RUNTIME.json') else 'Original R hash retained in pinned RUNTIME.json',runtime_manifest_sha256=sha(a.old/'p0/RUNTIME.json'),numerical_harness_sha256=sha(build/'Release/qh-real.exe'),harness_sources={str(f.relative_to(ROOT)):sha(f) for f in (ROOT/'native/host').glob('*') if f.is_file()},modules_before=before,modules_after=modules(),new_GPU_starts=0,new_model_processes=0))
    save(out/'HOST_S0_CELLS.json',plan.cpu_cells())
    print(dict(toy_methods=result.testsRun,descriptor_cases=48,real_compile=True,GPU=0))

if __name__=='__main__':main()
