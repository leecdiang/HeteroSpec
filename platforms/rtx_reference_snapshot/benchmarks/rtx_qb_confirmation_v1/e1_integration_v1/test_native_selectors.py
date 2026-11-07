"""Compile and execute a CPU-only test of the actual integrated capture header."""
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiment as e
def main():
    root=Path('D:/hs104-e1-v1');source=root/'native/source';out=root/'CPU-tests';out.mkdir(exist_ok=False)
    zig=Path('D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/ziglang/zig.exe')
    exe=out/'selectors.exe';cpp=Path(__file__).with_suffix('.cpp')
    cmd=[str(zig),'c++','-std=c++17','-O1',str(cpp),'-I'+str(source/'common'),'-I'+str(source/'ggml/include'),
         '-I'+str(source/'include'),'-I'+str(source/'vendor/nlohmann/..'),'-lpsapi','-o',str(exe)]
    attempts=[]
    for label,args in [('compile',cmd),('run',[str(exe)])]:
        start=time.perf_counter();r=subprocess.run(args,capture_output=True,timeout=120)
        (out/(label+'.stdout.log')).write_bytes(r.stdout);(out/(label+'.stderr.log')).write_bytes(r.stderr)
        row=dict(label=label,command=args,seconds=time.perf_counter()-start,exit_code=r.returncode,new_model_operator_starts=0)
        attempts.append(row);e.save(out/(label+'.json'),row)
        e.require(r.returncode==0,'CPU-only actual selector test failed')
    e.save(out/'RESULT.json',dict(status='PASS',attempts=attempts,executable=e.pin(exe),actual_header=e.pin(source/'common/capture95.h'),GPU_initialized=False))
    print('Actual generated native header CPU test PASS')
if __name__=='__main__':main()
