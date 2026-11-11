"""Compile a no-forward POSIX vocabulary/roundtrip helper with pristine archives."""
from pathlib import Path
import argparse, shlex, subprocess, sys

def main():
    p=argparse.ArgumentParser()
    for key in ('baseline','runtime','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(a.runtime.resolve()));from common import need,read,save,sha,command
    old=a.baseline.resolve()/'build-R-01';out=a.out.resolve();need(not out.exists(),'Fresh vocabulary build');out.mkdir(parents=True)
    b=read(old/'BUILD.json');deps=read(old/'DEPENDENCIES.json')
    for name,h in deps['files'].items():need(sha(name)==h,'Pristine dependency changed: '+name)
    source=Path(__file__).parent/'native/vocabulary.cpp';unit=next(x for x in read(old/'native/compile_commands.json') if x['file'].endswith('/native/reference.cpp'))
    args=shlex.split(unit['command']);old_obj=args[args.index('-o')+1];args[args.index('-o')+1]=str(out/'vocabulary.o');args[args.index('-c')+1]=str(source)
    args+=['-MMD','-MF',str(out/'vocabulary.d')];command(args,out/'compile',cwd=old/'native')
    raw=subprocess.check_output(['ninja','-C',str(old/'native'),'-t','commands','transfer-worker'],text=True).splitlines()[-1]
    link=shlex.split(raw);link=link[link.index('&&')+1:link.index('&&',link.index('&&')+1)]
    link=[str(out/'vocabulary.o') if x==old_obj else x for x in link];link[link.index('-o')+1]=str(out/'vocabulary')
    link=[('-Wl,-Map='+str(out/'vocabulary.map')) if x.startswith('-Wl,-Map=') else x for x in link];command(link,out/'link',cwd=old/'native')
    files=dict(deps['files'])
    for name in (out/'vocabulary.d').read_text().replace('\\\n',' ').split(':',1)[1].split():
        path=Path(name);path=path if path.is_absolute() else old/'native'/path;files[str(path.resolve())]=sha(path)
    for path in (source,out/'vocabulary.o',out/'vocabulary.map',out/'compile/command.json',out/'link/command.json'):files[str(path.resolve())]=sha(path)
    save(out/'DEPENDENCIES.json',{**deps,'files':files})
    save(out/'BUILD.json',dict(role='vocabulary_only_not_reference',executable=str(out/'vocabulary'),executable_sha256=sha(out/'vocabulary'),
        original_pristine_build_sha256=sha(old/'BUILD.json'),source_sha256=sha(source),dependency_closure_sha256=sha(out/'DEPENDENCIES.json'),
        max_model_forwards=0,max_context_creations=0,reference_qualification=False))
    print('VOCABULARY_ONLY_BUILT',sha(out/'vocabulary'),flush=True)

if __name__=='__main__':main()
