"""One immutable attempt per frozen coordinate; failures remain results."""
import gzip
import hashlib
import json
from pathlib import Path
import time
import traceback
import checker
from model import simulate
from prepare import ROOT,save,sha

def main():
    f0=json.loads((ROOT/'CPU_F0.json').read_bytes())
    for name,h in f0['files'].items():assert sha(ROOT/name)==h,('source/input drift',name)
    for name,h in f0['runtime'].items():assert sha(name)==h,('runtime drift',name)
    assert (ROOT/'AUTHENTICATED_CPU_F0_BYTES.json').read_bytes()==(ROOT/'CPU_F0.json').read_bytes()
    remote=json.loads((ROOT/'AUTHENTICATED_CPU_F0.json').read_bytes());assert remote['sha256']==sha(ROOT/'CPU_F0.json')
    plan=json.loads((ROOT/'PLAN.json').read_bytes());resources={r['id']:r for r in plan['resources']}
    formal=ROOT/'formal';formal.mkdir(exist_ok=False);failures=[]
    save(formal/'STARTED.json',dict(epoch=time.time(),F0_sha256=sha(ROOT/'CPU_F0.json'),authenticated_commit=remote['commit'],cells=len(plan['cells'])))
    for i,cell in enumerate(plan['cells']):
        assert i<1024
        d=formal/f'{i:04d}';d.mkdir(exist_ok=False);save(d/'CELL_STARTED.json',dict(index=i,epoch=time.time(),**cell))
        start=time.perf_counter();path=ROOT/'inputs'/(cell['workload']+'.json');before=sha(path)
        try:
            w=json.loads(path.read_bytes());r=resources[cell['resource']];result=simulate(w,r,cell['mapping'])
            trace=result.pop('trace')
            with gzip.open(d/'trace.jsonl.gz','xt',encoding='utf-8') as f:
                for event in trace:f.write(json.dumps(event,sort_keys=True,separators=(',',':'))+'\n')
            save(d/'OUTPUT.json',result)
            check=checker.validate(w,r,trace,result['output']);assert sha(path)==before
            save(d/'CELL_RESULT.json',dict(status='PASS',**cell,index=i,input_sha256=before,output_sha256=sha(d/'OUTPUT.json'),
                 trace_sha256=sha(d/'trace.jsonl.gz'),events=len(trace),checker=check,CPU_host_seconds=time.perf_counter()-start))
        except Exception as exc:
            failures.append(i);save(d/'CELL_RESULT.json',dict(status='FAIL',**cell,index=i,error=repr(exc),traceback=traceback.format_exc(),CPU_host_seconds=time.perf_counter()-start))
        if i%50==0:print(json.dumps(dict(completed=i+1,failures=len(failures))),flush=True)
    save(formal/'COMPLETE.json',dict(epoch=time.time(),attempts=len(plan['cells']),passed=len(plan['cells'])-len(failures),failures=failures))
    print(json.dumps(dict(attempts=len(plan['cells']),failed=failures)))
if __name__=='__main__':main()
