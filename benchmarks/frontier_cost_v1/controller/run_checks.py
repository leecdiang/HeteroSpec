"""Save meaningful controller checks and host-only method overhead; no inference."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import statistics
import sys
from time import perf_counter_ns
import unittest
from causal_policy import Snapshot,Price,SyntheticStage,SyntheticModel,CausalController

HERE=Path(__file__).resolve().parent


def overhead():
    snapshot=Snapshot('synthetic','synthetic_initial',tuple(range(7)),0,7,96)
    stages=[]
    for at in range(8):
        for width in range(1,9-at):
            prices={f'reject:{j}':Price(100+7*width,0,0,'synthetic_reject') for j in range(at+1,min(at+width,7)+1)}
            prices['continue' if at+width<8 else 'bonus']=Price(100+7*width,0,int(at+width==8),'synthetic_frontier')
            stages.append(SyntheticStage(at,width,prices))
    model=SyntheticModel('synthetic','synthetic_initial',10000,5,tuple(stages),{(v,'none'):Price(5,0,0,'synthetic_stop') for v in range(1,8)})
    values={}
    for name in ('model_recursion','runtime_abstention'):
        controller=CausalController(overhead_limit_nanoseconds=1_000_000_000);durations=[]
        for _ in range(200):
            began=perf_counter_ns()
            result=controller.decide_model(snapshot,model) if name=='model_recursion' else controller.decide_runtime(snapshot)
            durations.append(perf_counter_ns()-began)
        ordered=sorted(durations)
        values[name]={'calls':len(durations),'mean_nanoseconds':statistics.mean(durations),'median_nanoseconds':statistics.median(durations),
                      'p95_nanoseconds':ordered[189],'maximum_nanoseconds':max(durations),'all_nanoseconds':durations}
    return {'scope':'External CPU Python call boundary INCLUDING final policy accounting/return; same-process repeats, first call retained; excludes feature/state construction, receipt admission, GPU synchronization and runtime adapter. Internal watchdog spans are not total controller cost.',
            'performance_claim':False,'GPU_cost_calibration':False,'platform':platform.platform(),'python':sys.version,'measurements':values}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():raise ValueError('fresh output required')
    a.output.mkdir(parents=True);capture=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_causal_policy.py')
    result=unittest.TextTestRunner(stream=capture,verbosity=2).run(suite)
    (a.output/'tests.log').write_text(capture.getvalue())
    timing=overhead();(a.output/'OVERHEAD.json').write_text(json.dumps(timing,indent=2)+'\n')
    report={'status':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'scope':'Synthetic model properties and runtime abstention only. No native/model/GPU execution.',
            'source_sha256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ('causal_policy.py','cost_admission_v2.py','test_causal_policy.py','run_checks.py')},
            'model_requests':0,'GPU_requests':0,'new_stage_costs':0,
            'controller_overhead':{k:{a:b for a,b in v.items() if a!='all_nanoseconds'} for k,v in timing['measurements'].items()},
            'overhead_scope':timing['scope'],'overhead_may_not_be_used_as_GPU_cost':True}
    (a.output/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if not result.wasSuccessful():raise SystemExit(1)


if __name__=='__main__':main()
