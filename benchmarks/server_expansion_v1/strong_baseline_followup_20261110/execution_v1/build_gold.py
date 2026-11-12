"""Link an operand oracle exclusively to the original pristine reference build."""
import argparse
from pathlib import Path
import shlex
import subprocess
from build_backend import command
from objects import archive_members
from support import fresh,need,read,sha


def build(root,out):
    out.mkdir();pristine=root/'run-01/build-R-01';native=pristine/'native'
    identity=read(pristine/'BUILD.json');need(identity['reference_source_is_pristine']is True,'Pristine source promise')
    need(sha(identity['executable'])==identity['executable_sha256'],'Original R ELF changed')
    deps=read(pristine/'DEPENDENCIES.json');verified=[]
    for name,digest in deps['files'].items():
        need(sha(name)==digest,'Pristine transitive input changed: '+name)
        verified.append(dict(path=name,sha256=digest))
    here=Path(__file__).parent;units=read(native/'compile_commands.json')
    unit=next(x for x in units if x['file'].endswith('/reference.cpp'))
    args=shlex.split(unit['command']);args[args.index('-o')+1]=str(out/'gold-worker.o')
    args[args.index('-c')+1]=str(here/'gold_worker.cpp')
    args+=['-I/usr/local/cuda-12.5/targets/x86_64-linux/include','-MD','-MF',str(out/'gold-worker.d')]
    command(out,'compile-gold-worker',args,native)
    unit=next(x for x in units if x['file'].endswith('/quantize.cu'))
    args=shlex.split(unit['command']);args[args.index('-o')+1]=str(out/'gold-quant.cu.o')
    args[args.index('-c')+1]=str(here/'gold_quant.cu')
    args+=['-I'+str(Path(unit['file']).parent),'-MD','-MF',str(out/'gold-quant.d')]
    command(out,'compile-gold-quant-glue',args,native)
    line=subprocess.check_output(['ninja','-t','commands','bin/transfer-worker'],cwd=native,text=True).splitlines()[-1]
    words=shlex.split(line);need(words[:2]==[':','&&']and words[-2:]==['&&',':'],'Pinned link shell form')
    link=[];archives=[]
    for a in words[2:-2]:
        if a=='CMakeFiles/transfer-worker.dir/native/reference.cpp.o':
            link.extend([str(out/'gold-worker.o'),str(out/'gold-quant.cu.o')])
        elif a=='bin/transfer-worker':link.append(str(out/'gold-worker'))
        elif a.startswith('-Wl,-Map='):link.append('-Wl,-Map='+str(out/'gold-worker.map'))
        elif a=='llama/src/libllama.a':continue
        else:
            link.append(a)
            if a.endswith('.a'):
                p=Path(a)if Path(a).is_absolute()else native/a
                archives.append(dict(path=str(p),sha256=sha(p),members=archive_members(p)))
    command(out,'link-gold-worker',link,native)
    need(all('/run-01/build-R-01/'in e['path']or e['path'].startswith('/usr/')for e in archives),
         'Candidate archive in gold linkage')
    fresh(out/'BUILD.json',dict(status='CPU_PRISTINE_GOLD_BUILT_NOT_NUMERICALLY_QUALIFIED',
        executable=str(out/'gold-worker'),executable_sha256=sha(out/'gold-worker'),
        source_R_build_sha256=sha(pristine/'BUILD.json'),transitive_dependency_proof_sha256=sha(pristine/'DEPENDENCIES.json'),
        independently_verified_pristine_inputs=verified,archives=archives,
        candidate_numerical_objects_linked=False,original_scalar_and_quantizer_objects_unchanged=True,
        new_glue_sources=[dict(path=str(here/name),sha256=sha(here/name))for name in ('gold_worker.cpp','gold_quant.cu')],
        native_model_requests_started=0))


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();need(not a.out.exists(),'Fresh gold build')
    try:build(a.root,a.out)
    except BaseException as e:
        if a.out.exists():fresh(a.out/'BUILD_FAILED.json',dict(status='CPU_GOLD_BUILD_FAILED',reason=str(e),native_model_requests_started=0))
        raise


if __name__=='__main__':main()
