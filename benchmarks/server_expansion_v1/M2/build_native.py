"""Relink a new observer frontend to the exact qualified Linux numerical archives.

The original full CUDA source builds and their complete dependency closure are
verified, retained and referenced. This is not a new arithmetic implementation.
Neither the original binaries nor their source/dependency files are written.
"""
from pathlib import Path
import argparse, json, os, shlex, shutil, subprocess, sys

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.runtime));from common import need,read,save,sha,inventory,verify_tree,command
    w=a.baseline.resolve();out=a.out.resolve();need(not out.exists(),'Fresh M1 build epoch required');out.mkdir(parents=True)
    lock=read(w/'stage-04/SOURCE_LOCK.json');verify_tree(w/'stage-04/frontend',lock['frontend'])
    frontend=out/'frontend';shutil.copytree(w/'stage-04/frontend',frontend)
    from transform import transform
    transform(frontend)
    shutil.copy2(Path(__file__).parent/'native/tapes.hpp',frontend/'m2_tapes.hpp')
    shutil.copy2(Path(__file__).parent/'native/capability.hpp',frontend/'m1_capability.hpp')
    path=frontend/'entry.cpp';text=path.read_text();text=text.replace('static json module_inventory()', '#include "m1_capability.hpp"\nstatic json module_inventory()',1)
    marker='        phase1_profiling=job.value("profile",false);'
    need(text.count(marker)==1,'Exact qualified frontend insertion point')
    text=text.replace(marker,'        m1_capability(job,pool,t,d,spec,root,result);\n'+marker,1);path.write_text(text)
    for role in ('loop4','packed'):
        old=w/f'build-{role}-01';b=read(old/'BUILD.json');deps=read(old/'DEPENDENCIES.json')
        need(sha(b['executable'])==b['executable_sha256'],'Original qualified executable changed')
        need(b['dependency_closure_complete'] and deps['cuda_translation_units']>0,'Complete actual numerical source build required')
        for name,h in deps['files'].items():need(sha(name)==h,'Original compiled dependency changed: '+name)
        verify_tree(w/'stage-04/sources'/role,lock['sources'][role])
        dest=out/role;dest.mkdir();obj=dest/'frontend.o';exe=dest/'transfer-worker';linkmap=dest/'transfer-worker.map'
        unit=next(x for x in read(old/'native/compile_commands.json') if x['file']==str(w/'stage-04/frontend/entry.cpp'))
        args=shlex.split(unit['command']);args=[x.replace(str(w/'stage-04/frontend'),str(frontend)) for x in args]
        args[args.index('-o')+1]=str(obj);args+=['-MMD','-MF',str(dest/'frontend.d'),'-DM1_PROJECTION="'+role+'"']
        command(args,dest/'compile',cwd=old/'native')
        raw=subprocess.check_output(['ninja','-C',str(old/'native'),'-t','commands','transfer-worker'],text=True).splitlines()[-1]
        link=shlex.split(raw);link=link[link.index('&&')+1:link.index('&&',link.index('&&')+1)]
        old_obj=unit.get('output') or shlex.split(unit['command'])[shlex.split(unit['command']).index('-o')+1]
        link=[str(obj) if x==old_obj else x for x in link];link[link.index('-o')+1]=str(exe)
        link=[('-Wl,-Map='+str(linkmap)) if x.startswith('-Wl,-Map=') else x for x in link]
        command(link,dest/'link',cwd=old/'native')
        names=dict(deps['files']);newdeps=(dest/'frontend.d').read_text().replace('\\\n',' ').split(':',1)[1].split()
        for name in newdeps:
            file=Path(name);file=file if file.is_absolute() else old/'native'/file;names[str(file.resolve())]=sha(file)
        for file in [obj,linkmap,*frontend.rglob('*'),dest/'compile/command.json',dest/'link/command.json']:
            if file.is_file():names[str(file.resolve())]=sha(file)
        save(dest/'DEPENDENCIES.json',{**deps,'files':names,'qualified_archive_reuse':True,'original_build':str(old/'BUILD.json'),'original_build_sha256':sha(old/'BUILD.json')})
        save(dest/'BUILD.json',{**b,'executable':str(exe),'executable_sha256':sha(exe),'dependency_closure_sha256':sha(dest/'DEPENDENCIES.json'),
            'status':'M1_OBSERVER_RELINK_NOT_YET_QUALIFIED','frontend':inventory(frontend),'original_build_sha256':sha(old/'BUILD.json'),
            'numerical_archives':'Read-only exact fully source-built qualified PR203 archives; M2 transaction/reservation/replay frontend changes, no CUDA or arithmetic edits',
            'native_capability_schema':'heterospec.m2.native-capability.v1'})
        print('M1_OBSERVER_BUILT',role,sha(exe),flush=True)
    save(out/'BUILD_COMPLETE.json',{'passed':True,'arithmetic_edits':False,'M2_transaction_and_reservation_edits':True,'originals_modified':False,'frontend':inventory(frontend)})

if __name__=='__main__':main()
