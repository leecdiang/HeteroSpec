"""Compile and stage S1 only; never launch the Vulkan executable."""
import argparse, pathlib, shutil, subprocess, time
from common import ROOT, load, save, sha, modules

def main():
    p=argparse.ArgumentParser();p.add_argument('--old',type=pathlib.Path,required=True);p.add_argument('--cmake',default='cmake');a=p.parse_args();before=modules()
    dep=a.old/'_host/pr97/dependencies';build=ROOT/'build';logs=[]
    for cmd in [[a.cmake,'-S',str(ROOT/'native/host'),'-B',str(build),'-G','Visual Studio 17 2022','-A','x64','-DPINNED='+str(dep/'pinned-source'),'-DBASE_LIB='+str(dep/'pinned-build/ggml/src/Release/ggml-base.lib')],
                [a.cmake,'--build',str(build),'--config','Release','--target','qh-vulkan']]:
        start=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');logs.append(dict(argv=cmd,returncode=r.returncode,elapsed_s=time.monotonic()-start,stdout=r.stdout,stderr=r.stderr));print(r.stdout[-4000:])
        if r.returncode:break
    ok=all(x['returncode']==0 for x in logs);index=len(list((ROOT/'host').glob('S1_OFFLINE_BUILD_*.json')))
    if ok:
        for name in ('ggml-base.dll','ggml-vulkan.dll'):shutil.copy2(a.old/'_host/build/Release'/name,build/'S1'/name)
    save(ROOT/f'host/S1_OFFLINE_BUILD_{index:02d}.json',dict(success=ok,logs=logs,
         staged=[dict(name=f.name,bytes=f.stat().st_size,sha256=sha(f)) for f in (build/'S1').glob('*') if f.suffix in ('.dll','.exe')],
         executable_launched=False,new_device_queries=0,new_GPU_starts=0,modules_before=before,modules_after=modules()))
    raise SystemExit(0 if ok else 1)

if __name__=='__main__':main()
