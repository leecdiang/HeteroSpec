"""Additional heavy-only projection graph observer; same qualified archives.

The formal binaries are not replaced. Their cap8-output clean requests serve as
a bridge to this observer's full vectors/states. Verification remains k3/q4 with
reserve4; generation cap8 is a short diagnostic, not M2 or q8 verification.
"""
from pathlib import Path
import argparse, json, shlex, shutil, sys

def main():
    p=argparse.ArgumentParser()
    for key in ('builds','out','runtime'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.runtime.resolve()));from common import need,read,save,sha,inventory,command
    old=a.builds.resolve();out=a.out.resolve();need(not out.exists(),'Fresh observer build epoch');out.mkdir(parents=True)
    frontend=out/'frontend';shutil.copytree(old/'frontend',frontend);path=frontend/'worker.cpp';text=path.read_text()
    anchor='if(name.rfind("kq",0)!=0&&name.rfind("hs_",0)!=0)return false;'
    need(text.count(anchor)==1,'Exact qualified observer anchor')
    text=text.replace(anchor,'if(name.rfind("kq",0)!=0&&name.rfind("hs_",0)!=0&&t->op!=GGML_OP_MUL_MAT)return false;',1);path.write_text(text)
    for role in ('loop4','packed'):
        before=old/role;dest=out/role;dest.mkdir();b=read(before/'BUILD.json');deps=read(before/'DEPENDENCIES.json')
        for name,h in deps['files'].items():need(sha(name)==h,'Qualified compiler dependency changed: '+name)
        def argv(phase):
            r=read(before/phase/'command.json');args=[x.replace(str(old/'frontend'),str(frontend)).replace(str(before),str(dest)) for x in r['argv']];return args,r['cwd']
        for phase in ('compile','link'):
            args,cwd=argv(phase);command(args,dest/phase,cwd=cwd)
        names=dict(deps['files']);raw=(dest/'frontend.d').read_text().replace('\\\n',' ').split(':',1)[1].split();cwd=Path(read(before/'compile/command.json')['cwd'])
        for name in raw:
            file=Path(name);file=file if file.is_absolute() else cwd/file;names[str(file.resolve())]=sha(file)
        for file in [dest/'frontend.o',dest/'transfer-worker.map',*frontend.rglob('*'),dest/'compile/command.json',dest/'link/command.json']:
            if file.is_file():names[str(file.resolve())]=sha(file)
        save(dest/'DEPENDENCIES.json',{**deps,'files':names,'observer_only_change':'Heavy callback admits every actual MUL_MAT GPU graph node'})
        exe=dest/'transfer-worker';save(dest/'BUILD.json',{**b,'executable':str(exe),'executable_sha256':sha(exe),'dependency_closure_sha256':sha(dest/'DEPENDENCIES.json'),
            'status':'PROJECTION_OBSERVER_ONLY_NOT_FORMAL_EXECUTABLE','formal_build_sha256':sha(before/'BUILD.json'),'frontend':inventory(frontend)})
        print('PROJECTION_OBSERVER_BUILT',role,sha(exe),flush=True)
    save(out/'BUILD_COMPLETE.json',dict(passed=True,numerical_archives_unchanged=True,frontend_change='One observer filter, active only in heavy captures',formal_binaries_replaced=False))

if __name__=='__main__':main()
