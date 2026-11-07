"""Compile each staged graph/core variant with the historical Zig flags."""
from build_host import sha,put,ROOT
from pathlib import Path
import subprocess,time,shutil,json
FROZEN=Path('E:/tpds167/build01')
def main():
    for arm in ('graph_tiles','backend_loop4','packed'):
        out=Path('D:/rtx184-operator')/arm;out.mkdir(parents=True);(out/'core').mkdir();(out/'bin').mkdir()
        source=ROOT/'loop/native-arms'/arm
        for p in (FROZEN/'core').glob('*.cmd'):shutil.copy2(p,out/'core'/p.name)
        records=[]
        for phase in ('configure','core'):
            base=json.loads(sorted(FROZEN.glob(phase+'-*.json'))[-1].read_bytes())['argv']
            argv=[x.replace(str(FROZEN/'source'),str(source)).replace((FROZEN/'source').as_posix(),source.as_posix()).replace(str(FROZEN),str(out)).replace(FROZEN.as_posix(),out.as_posix()) for x in base]
            if '-j' in argv:argv[argv.index('-j')+1]='4'
            t=time.monotonic()
            with (out/(phase+'.log')).open('xb') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
            record=dict(argv=argv,code=r.returncode,seconds=time.monotonic()-t);put(out/(phase+'.json'),record);records.append(record);r.check_returncode()
        put(out/'CORE_BUILD.json',dict(arm=arm,source=str(source),core=sha(out/'core/src/libllama.a'),commands=records,status='CORE_COMPILED_CUDA_RUNTIME_AND_GPU_QUALIFICATION_PENDING'))
        print(arm,'core compiled',flush=True)
if __name__=='__main__':main()
