"""Offline CPU harness compile. Copies only explicit CPU dependencies."""
import argparse, pathlib, shutil, subprocess, time
from common import ROOT, load, save, sha, modules

def main():
    p=argparse.ArgumentParser();p.add_argument('--old',type=pathlib.Path,required=True)
    p.add_argument('--cmake',default='cmake');a=p.parse_args();before=modules()
    host=ROOT/'_host';inc=host/'include';inc.mkdir(parents=True,exist_ok=True)
    helper=a.old/'native/local_attention.h';shutil.copy2(helper,inc/helper.name)
    pr=a.old/'_host/pr97/dependencies';build=host/'build';logs=[]
    cmds=[[a.cmake,'-S',str(ROOT/'native'),'-B',str(build),'-G','Visual Studio 17 2022','-A','x64',
           '-DPINNED='+str(pr/'pinned-source'),'-DHELPER='+str(inc),
           '-DBASE_LIB='+str(pr/'pinned-build/ggml/src/Release/ggml-base.lib')],
          [a.cmake,'--build',str(build),'--config','Release','--target','representation-cpu']]
    ok=True
    for cmd in cmds:
        t=time.time();r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
        logs.append(dict(argv=cmd,returncode=r.returncode,elapsed_s=time.time()-t,stdout=r.stdout,stderr=r.stderr))
        if r.returncode:ok=False;break
    if ok:
        for name in ['ggml-base.dll','ggml-cpu.dll']:
            shutil.copy2(a.old/'_host/build/Release'/name,build/'Release'/name)
    n=len(list(ROOT.glob('BUILD_*.json')))
    files=list((build/'Release').glob('*.exe'))+list((build/'Release').glob('*.dll')) if ok else []
    save(ROOT/f'BUILD_{n:02d}.json',dict(ok=ok,helper_sha256=sha(helper),logs=logs,
         executable_dependencies=[dict(name=f.name,sha256=sha(f),bytes=f.stat().st_size) for f in files],
         modules_before=before,modules_after=modules(),gpu_starts=0))
    for x in logs:print(x['stdout'][-4000:],x['stderr'][-1000:])
    raise SystemExit(0 if ok else 1)

if __name__=='__main__':main()
