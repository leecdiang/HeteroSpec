"""Compile a zero-forward observer against immutable source-built Linux archives.

Creates a separate admission-only supervisor extension. Old files and references
are read-only; no inference job is accepted by this new entrypoint.
"""
from pathlib import Path
import argparse, json, shlex, shutil, subprocess, sys

def build(baseline,runtime,out):
    sys.path.insert(0,str(runtime));from common import need,read,save,sha,command
    need(not out.exists(),'Fresh admission build');out.mkdir(parents=True)
    old=baseline/'build-R-01';b=read(old/'BUILD.json');deps=read(old/'DEPENDENCIES.json')
    need(b['cuda'] and b['dependency_closure_complete'] and deps['cuda_translation_units']>0,'Complete actual CUDA source build')
    for name,h in deps['files'].items():need(sha(name)==h,'Original compiled dependency changed: '+name)
    source=Path(__file__).parent/'native/admit.cpp';unit=next(x for x in read(old/'native/compile_commands.json') if x['file'].endswith('/native/reference.cpp'))
    args=shlex.split(unit['command']);old_obj=args[args.index('-o')+1];args[args.index('-o')+1]=str(out/'admit.o');args[args.index('-c')+1]=str(source)
    args+=['-MMD','-MF',str(out/'admit.d')];command(args,out/'compile',cwd=old/'native')
    raw=subprocess.check_output(['ninja','-C',str(old/'native'),'-t','commands','transfer-worker'],text=True).splitlines()[-1]
    link=shlex.split(raw);link=link[link.index('&&')+1:link.index('&&',link.index('&&')+1)]
    link=[str(out/'admit.o') if x==old_obj else x for x in link];link[link.index('-o')+1]=str(out/'admit')
    link=[('-Wl,-Map='+str(out/'admit.map')) if x.startswith('-Wl,-Map=') else x for x in link];command(link,out/'link',cwd=old/'native')
    names=dict(deps['files']);raw=(out/'admit.d').read_text().replace('\\\n',' ').split(':',1)[1].split()
    for name in raw:
        path=Path(name);path=path if path.is_absolute() else old/'native'/path;names[str(path.resolve())]=sha(path)
    for p in (out/'admit.o',out/'admit.map',out/'compile/command.json',out/'link/command.json',source):names[str(p.resolve())]=sha(p)
    save(out/'DEPENDENCIES.json',{**deps,'files':names,'qualified_archive_build_sha256':sha(old/'BUILD.json')})
    save(out/'BUILD.json',{**b,'role':'admission','reference_source_is_pristine':False,'numerical_archives_pristine_reference_build':True,
        'executable':str(out/'admit'),'executable_sha256':sha(out/'admit'),'dependency_closure_sha256':sha(out/'DEPENDENCIES.json'),
        'status':'BUILT_ZERO_FORWARD_ONLY_NOT_NUMERICALLY_QUALIFIED','numerical_archive_reuse':True,'source_sha256':sha(source),
        'qualified_linux_successor':'592abdfe9267fd97ecbde18cd0ee9a1bfc319e20'})
    print('ZERO_FORWARD_ADMISSION_BUILT',sha(out/'admit'),flush=True)

def supervise(runtime,out,manifest):
    sys.path.insert(0,str(runtime));from common import need,read,save,sha
    need(not out.exists(),'New isolated supervisor runtime');out.mkdir()
    shutil.copy2(runtime/'common.py',out/'common.py');pins=read(runtime/'pins.json')
    pins['models']['Qwen14B']={'target':manifest['target']['sha256'],'draft':manifest['draft']['sha256']};save(out/'pins.json',pins)
    source=(runtime/'host.py').read_text();anchor="    config=read(config_path);build=read(build_path);job=read(job_path);out=Path(out).resolve()"
    need(source.count(anchor)==1,'Pinned supervisor entry anchor')
    source=source.replace(anchor,anchor+"\n    need(phase=='admission' and build.get('role')=='admission' and job.get('zero_forward') is True and job.get('inputs')==[], 'This isolated runtime accepts only zero-forward admission; no reference or inference jobs')",1)
    anchor="    if build['role']!='reference':";need(source.count(anchor)==1,'Independent reference guard anchor')
    source=source.replace(anchor,"    if build['role']!='reference' and phase!='admission':",1)
    anchor="            if 'inputs' in job:";need(source.count(anchor)==1,'Input clock anchor')
    source=source.replace(anchor,"            if 'inputs' in job and job['inputs']:",1)
    (out/'admission_host.py').write_text(source)
    save(out/'SUPERVISOR_PORT.json',dict(base_commit='592abdfe9267fd97ecbde18cd0ee9a1bfc319e20',base_host_sha256=sha(runtime/'host.py'),
        admission_host_sha256=sha(out/'admission_host.py'),changes=['Admission-only role/phase/empty-input guard','Exact Qwen14B identity added from PR198 model manifest','No R required for a zero-forward-only entrypoint','No request-result clocks fabricated for zero inputs'],
        foreign_process_lock_environment_and_reserves_unchanged=True,old_reference_not_used_as_14B_oracle=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--supervisor',type=Path,required=True);a=p.parse_args()
    manifest=json.loads((Path(__file__).parent/'models.json').read_text());build(a.baseline.resolve(),a.runtime.resolve(),a.out.resolve());supervise(a.runtime.resolve(),a.supervisor.resolve(),manifest)
