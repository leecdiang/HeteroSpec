"""Integration revision1: supply the omitted frozen memory-budget header only."""
import argparse, pathlib, shutil, subprocess, time, zipfile
from common import ROOT, load, save, sha, modules

def main():
    p=argparse.ArgumentParser();p.add_argument('--old',type=pathlib.Path,required=True);p.add_argument('--cmake',default='cmake');a=p.parse_args();before=modules()
    first=load(ROOT/'host/ACTOR_BUILD.json');assert first['success'] is False
    assert 'native_memory_budget.h' in first['logs'][-1]['stdout']
    host=ROOT/'host_outputs/actor';source=a.old/'native/native_memory_budget.h';shutil.copy2(source,host/source.name)
    cmd=[a.cmake,'--build',str(host/'build'),'--config','Release','--target','b570-qh-worker','--parallel','4']
    start=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');print(r.stdout[-3500:])
    archive=ROOT/'host/ACTOR_SOURCE_FIXED.zip';sources=[]
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(host.rglob('*')):
            if f.is_file() and 'build' not in f.relative_to(host).parts:
                name=f.relative_to(host).as_posix();z.write(f,name);sources.append(dict(path=name,bytes=f.stat().st_size,sha256=sha(f)))
    save(ROOT/'host/ACTOR_REPAIR_01.json',dict(revision=1,scope='Missing inherited header include only; no graph/transaction/arithmetic change',
         header_source=str(source),header_sha256=sha(source),success=r.returncode==0,returncode=r.returncode,elapsed_s=time.monotonic()-start,
         argv=cmd,stdout=r.stdout,stderr=r.stderr,sources=sources,source_capsule_sha256=sha(archive),
         binaries=[dict(name=f.name,sha256=sha(f)) for f in (host/'build/Release').glob('*') if f.suffix in ('.exe','.dll')],
         model_processes=0,model_requests=0,GPU_starts=0,executable_launched=False,modules_before=before,modules_after=modules()))
    raise SystemExit(r.returncode)

if __name__=='__main__':main()
