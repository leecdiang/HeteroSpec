"""Offline native wire/phase integration; never invokes a model process."""
import argparse, difflib, pathlib, shutil, subprocess, time, zipfile
from common import ROOT, load, save, sha, modules

def main():
    p=argparse.ArgumentParser();p.add_argument('--old',type=pathlib.Path,required=True);p.add_argument('--cmake',default='cmake');a=p.parse_args();before=modules()
    host=ROOT/'host_outputs/actor';host.mkdir(exist_ok=False);src=host/'source';shutil.copytree(a.old/'_host/source',src)
    shutil.copy2(ROOT/'native/query_head.h',src/'query_head.h');shutil.copy2(ROOT/'native/host/actor_attention.h',src/'local_attention.h')
    context=src/'llama-context.cpp';text=context.read_text(encoding='utf-8');oldtext=text
    assert text.count('layout<0||layout>2')==1;text=text.replace('layout<0||layout>2','layout<0||layout>4||layout==2');context.write_text(text,encoding='utf-8',newline='\n')
    (ROOT/'host/ACTOR_CONTEXT.diff').write_text(''.join(difflib.unified_diff(oldtext.splitlines(True),text.splitlines(True),fromfile='PR109/llama-context.cpp',tofile='PR112/llama-context.cpp')),encoding='utf-8')
    original=(a.old/'native/worker.cpp').read_text(encoding='utf-8');worker=original.replace('108','112')
    needle='layout112=="QB"?2:-1';assert worker.count(needle)==1
    worker=worker.replace(needle,'layout112=="QH_C"?3:layout112=="QH_D"?4:-1')
    needle='heavy()?json(5):json(nullptr)';assert worker.count(needle)==1;worker=worker.replace(needle,'json(100)')
    (host/'worker.cpp').write_text(worker,encoding='utf-8',newline='\n')
    shutil.copy2(a.old/'native/transaction_contract.h',host/'transaction_contract.h')
    shutil.copy2(a.old/'native/native_memory_budget.h',host/'native_memory_budget.h')
    (ROOT/'host/ACTOR_WORKER.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),worker.splitlines(True),fromfile='PR109/worker.cpp',tofile='PR112/worker.cpp')),encoding='utf-8')
    cm=host/'cmake';cm.mkdir();shutil.copy2(ROOT/'native/host/actor.CMakeLists.txt',cm/'CMakeLists.txt')
    dep=a.old/'_host/pr97/dependencies';logs=[]
    for cmd in [[a.cmake,'-S',str(cm),'-B',str(host/'build'),'-G','Visual Studio 17 2022','-A','x64','-DACTOR_SOURCE='+str(src),'-DACTOR_WORKER='+str(host/'worker.cpp'),'-DACTOR_HEADERS='+str(host),'-DPINNED='+str(dep/'pinned-source'),'-DLIB='+str(dep/'pinned-build/ggml/src/Release')],
                [a.cmake,'--build',str(host/'build'),'--config','Release','--parallel','4']]:
        start=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');logs.append(dict(argv=cmd,returncode=r.returncode,elapsed_s=time.monotonic()-start,stdout=r.stdout,stderr=r.stderr));print(r.stdout[-2500:])
        if r.returncode:break
    success=all(x['returncode']==0 for x in logs)
    sources=[dict(path=f.relative_to(host).as_posix(),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(host.rglob('*')) if f.is_file() and 'build' not in f.relative_to(host).parts]
    archive=ROOT/'host/ACTOR_SOURCE_CAPSULE.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for f in sources:z.write(host/f['path'],f['path'])
    save(ROOT/'host/ACTOR_BUILD.json',dict(success=success,logs=logs,sources=sources,source_capsule_sha256=sha(archive),
         binaries=[dict(name=f.name,sha256=sha(f)) for f in (host/'build/Release').glob('*') if f.suffix in ('.exe','.dll')],
         integration_scope='Actual recovered k1 actor and phase/graph library compiled; normalized112 wire, explicit QH_C/QH_D, accurate new periodic100ms declaration. No runtime/model admission.',
         preserved='pending/bonus/reconciliation, independent target/draft schedules, original q1 chain, graph cache parameter checks, dtype/sampler/model unchanged',
         S2_requires_S1_selected_variant_and_separate_F0=True,executable_launched=False,new_model_processes=0,new_model_requests=0,GPU_starts=0,modules_before=before,modules_after=modules()))
    raise SystemExit(0 if success else 1)

if __name__=='__main__':main()
