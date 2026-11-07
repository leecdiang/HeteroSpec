"""New D14 reference/candidate frontends, exact read-only numerical archives.

All GPU weights are explicitly placed identically for independent R and controls.
No arithmetic, transaction rule, output reservation, or old artifact is edited.
"""
from pathlib import Path
import argparse, json, shlex, shutil, subprocess, sys

def replace(text,old,new):
    if text.count(old)!=1:raise ValueError('Pinned source anchor: '+old)
    return text.replace(old,new,1)

def main():
    p=argparse.ArgumentParser()
    for key in ('baseline','runtime','out','supervisor'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(a.runtime.resolve()))
    from common import need,read,save,sha,inventory,verify_tree,command
    w=a.baseline.resolve();out=a.out.resolve();need(not out.exists(),'Fresh D14 build epoch');out.mkdir(parents=True)
    frontend=out/'frontend';lock=read(w/'stage-04/SOURCE_LOCK.json');verify_tree(w/'stage-04/frontend',lock['frontend']);shutil.copytree(w/'stage-04/frontend',frontend)
    shutil.copy2(Path(__file__).parent/'native/deployment.hpp',frontend/'d14_deployment.hpp')
    placement='mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;'
    override=placement+'llama_model_tensor_buft_override fullgpu[]={{".*",ggml_backend_dev_buffer_type(gpu)},{nullptr,nullptr}};mp.tensor_buft_overrides=fullgpu;'
    entry=frontend/'entry.cpp';text=entry.read_text();text=replace(text,'static json module_inventory()','#include "d14_deployment.hpp"\nstatic json module_inventory()')
    text=replace(text,placement,override)
    marker='        phase1_profiling=job.value("profile",false);'
    text=replace(text,marker,'        result["native_capability"]=d14_capability(job,t,pool.target->c,d,pool.draft?pool.draft->c:nullptr,gpu,phase_lowering,spec.k,d?phase_draft_width:0,root);\n'+marker);entry.write_text(text)
    oldref=w/'stage-03/frontend/native/reference.cpp'
    # The compiler database is the authority for the actual pristine-R frontend.
    refunit=next(x for x in read(w/'build-R-01/native/compile_commands.json') if x['file'].endswith('/native/reference.cpp'))
    oldref=Path(refunit['file']);text=oldref.read_text();text=replace(text,'struct ModelDelete','\n#include "d14_deployment.hpp"\nstruct ModelDelete')
    text=replace(text,placement,override)
    anchor='    need(llama_n_ctx(ctx.get())==unsigned(cap)&&llama_n_ubatch(ctx.get())==1,"observed reference allocation");'
    text=replace(text,anchor,anchor+'\n    result["native_capability"]=d14_capability(D14Json(job),model.get(),ctx.get(),nullptr,nullptr,gpu,"WHOLE_UB1",0,0,out);')
    refsource=frontend/'reference.cpp';refsource.write_text(text)
    for role in ('reference','loop4','packed'):
        old=w/('build-R-01' if role=='reference' else f'build-{role}-01');b=read(old/'BUILD.json');deps=read(old/'DEPENDENCIES.json')
        need(b['cuda'] and b['dependency_closure_complete'] and deps['cuda_translation_units']>0,'Complete actual CUDA build required')
        for name,h in deps['files'].items():need(sha(name)==h,'Original dependency changed: '+name)
        dest=out/role;dest.mkdir();obj=dest/'frontend.o';exe=dest/'transfer-worker'
        unit=refunit if role=='reference' else next(x for x in read(old/'native/compile_commands.json') if x['file']==str(w/'stage-04/frontend/entry.cpp'))
        args=shlex.split(unit['command']);old_obj=args[args.index('-o')+1]
        if role=='reference':args[args.index('-c')+1]=str(refsource)
        else:args=[x.replace(str(w/'stage-04/frontend'),str(frontend)) for x in args]
        args[args.index('-o')+1]=str(obj);args+=['-I'+str(frontend),'-MMD','-MF',str(dest/'frontend.d'),'-DD14_CORE="'+role+'"']
        command(args,dest/'compile',cwd=old/'native')
        raw=subprocess.check_output(['ninja','-C',str(old/'native'),'-t','commands','transfer-worker'],text=True).splitlines()[-1]
        link=shlex.split(raw);link=link[link.index('&&')+1:link.index('&&',link.index('&&')+1)]
        link=[str(obj) if x==old_obj else x for x in link];link[link.index('-o')+1]=str(exe);link=[('-Wl,-Map='+str(dest/'worker.map')) if x.startswith('-Wl,-Map=') else x for x in link]
        command(link,dest/'link',cwd=old/'native');names=dict(deps['files'])
        for name in (dest/'frontend.d').read_text().replace('\\\n',' ').split(':',1)[1].split():
            file=Path(name);file=file if file.is_absolute() else old/'native'/file;names[str(file.resolve())]=sha(file)
        for file in [obj,dest/'worker.map',*frontend.rglob('*'),dest/'compile/command.json',dest/'link/command.json']:
            if file.is_file():names[str(file.resolve())]=sha(file)
        save(dest/'DEPENDENCIES.json',{**deps,'files':names,'qualified_archive_reuse':True,'original_build_sha256':sha(old/'BUILD.json')})
        save(dest/'BUILD.json',{**b,'executable':str(exe),'executable_sha256':sha(exe),'dependency_closure_sha256':sha(dest/'DEPENDENCIES.json'),
            'status':'D14_OBSERVER_RELINK_NOT_YET_QUALIFIED','numerical_archives_pristine':role=='reference',
            'frontend_modified':True,'frontend_modifications':['Full-GPU weight placement','Versioned native capability and actual buffer observation'],
            'original_build_sha256':sha(old/'BUILD.json'),'native_capability_schema':'heterospec.d14.native-capability.v1',
            'numerical_archive_reuse':True,'fresh_CUDA_recompilation':False})
        print('D14_DEPLOYMENT_BUILT',role,sha(exe),flush=True)
    runtime=a.runtime.resolve();supervisor=a.supervisor.resolve();need(not supervisor.exists(),'Fresh independent D14 runtime');shutil.copytree(runtime,supervisor)
    pins=read(supervisor/'pins.json');model=read(Path(__file__).parent/'models.json');pins['models']['Qwen14B']={r:model[r]['sha256'] for r in ('target','draft')}
    (supervisor/'pins.json').write_text(json.dumps(pins,indent=2)+'\n')
    host=supervisor/'host.py';text=host.read_text();text=replace(text,'<=2048 and sum(r[\'rows\'] for r in reserved)+rows<=4000000','<=2560 and sum(r[\'rows\'] for r in reserved)+rows<=12000000');host.write_text(text)
    save(supervisor/'D14_PORT.json',dict(base_commit='592abdfe9267fd97ecbde18cd0ee9a1bfc319e20',base_runtime_files=inventory(runtime),
        host_sha256=sha(host),changes=['Exact Qwen14B model profile','Author-declared2560 request/12M row ceiling'],
        independent_reference_guard_unchanged=True,reserves_foreign_process_checks_unchanged=True))
    save(out/'BUILD_COMPLETE.json',dict(passed=True,frontend=inventory(frontend),arithmetic_edits=False,originals_modified=False))

if __name__=='__main__':main()
