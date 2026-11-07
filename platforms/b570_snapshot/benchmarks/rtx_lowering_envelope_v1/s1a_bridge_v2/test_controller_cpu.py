"""Run the production controller flow with explicit CPU-only transport fixtures.

No synthetic envelope is admitted as CUDA evidence. Native/analysis dependencies
are replaced only in this test process; deployed run_bridge has no fixture flag.
"""
import sys,tempfile,time
from pathlib import Path
import run_bridge as R
from bounded import State as RealState
from common import V,load,save,sha

def main():
    out=V/'cpu_tests/controller_v4';out.mkdir(parents=True,exist_ok=False);real=time.perf_counter;results=[]
    for case in ('next_budget','started_failure','readiness_failure'):
        work=out/case;work.mkdir();root=work/'raw';root.mkdir();(root/'cas').mkdir()
        offset=[0.];slots=[dict(id='CPU_FIXTURE_SLOT_'+str(i),index=i,descriptor='fixture',layout='MQ',repeat=0,q=1,graph_computes=1,native_output=str(root/'numerical'/('%03d'%i)/'native')) for i in range(2)]
        old=load(Path('D:/hs113/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/F0.json'))
        f0=dict(executable='CPU_TRANSPORT_FIXTURE_ONLY.exe',execution_root=str(root),runtime_directory=old['runtime_directory'],console_helper=old['console_helper'],
            budget=dict(stages=dict(numerical=dict(wall_seconds=150)),limits=dict(minimum_volume_free_before_start_bytes=0,minimum_volume_free_during_stage_bytes=0,controller_commit_bytes=512*1024**2,
                finalization_reserve_seconds=5,qualification_reserve_seconds=5,native_process_commit_bytes=256*1024**2,raw_root_bytes=32*1024**2,numeric_producer_reservation_bytes=1024**2,
                numeric_nonCAS_bytes_per_slot=262144,single_blob_bytes=16*1024**2)))
        save(work/'F0.json',f0);save(work/'PLAN.json',dict(numerical_slots=slots));save(work/'REFERENCE_INDEX.json',{});save(work/'CPU_GRAPH_EXPECTED.json',[dict(descriptor_id='fixture',layout='MQ')]);save(work/'approval.json',dict(prospective_24_context_amendment_accepted=True,census_sha256='fixture',decision_sha256='fixture'))
        save(root/'CENSUS_AUTHENTICATED.json',dict(authenticated_remote_bytes=True,F0_sha256=sha(work/'F0.json'),census_sha256='fixture',decision_sha256='fixture'))
        save(root/'CENSUS_DECISION.json',dict(numerical_admitted=True,denied_slots=[]));save(root/'CENSUS_ENDED.json',dict(status='COMPLETE'))
        class State(RealState):
            def __init__(self,*args):super().__init__(*args,clock=lambda:real()+offset[0])
        class CPUWorker:
            def __init__(self,*args):pass
            def terminate(self):pass
            def run(self,command,prefix,*args,on_start,**kwargs):
                on_start(111);p=Path(prefix);p.mkdir();save(p/'RECORD.json',dict(modules=[]))
                if case=='started_failure':raise RuntimeError('CPU_FAKE_NATIVE_FAILURE')
                offset[0]=90
        def ready(*args,**kwargs):
            if case=='readiness_failure':raise RuntimeError('CPU_FAKE_READINESS_FAILURE')
        R.V=work;R.State=State;R.Child=CPUWorker;R.check=lambda *args:None;R.owned_conflicts=lambda *args:None;R.approval_gate=lambda *args:None
        R.readiness=ready;R.module_inventory=lambda *args:[]
        R.analyzer.inspect=lambda *args,**kwargs:dict(process_identity=[111,222])
        original_sha=R.sha
        R.sha=lambda p:'fixture' if Path(p).name in ('CENSUS.json','CENSUS_DECISION.json') else sha(p)
        original_argv=sys.argv;sys.argv=['run_bridge.py','--stage','numerical','--approval',str(work/'approval.json')]
        error=None
        try:R.main()
        except RuntimeError as exc:error=repr(exc)
        finally:sys.argv=original_argv;R.sha=original_sha
        assert error;end=load(root/'NUMERICAL_ENDED.json');first=root/'numerical/000'
        if case=='next_budget':
            assert end['completed']==1 and end['current'] is None and (first/'COMPLETED.json').exists() and not (first/'FAILED.json').exists()
            assert not (root/'numerical/001').exists()
        else:
            assert end['completed']==0 and end['native_started']==int(case=='started_failure') and (first/'FAILED.json').exists()
        assert (root/'NUMERICAL_MINIMUM_STOP.json').exists() and not (root/'ANALYSIS.json').exists()
        results.append(dict(case=case,status='PASS',actual_controller_flow=True,CPU_transport_fixture=True,ended=end))
    save(V/'CPU_CONTROLLER_TESTS_final_v2.json',dict(status='PASS',cases=results,GPU_queries=0,CUDA_loads=0,graph_computes=0))
    print('PASS3 production-controller CPU fixture flows:completion/budget,started failure,readiness failure;offline analysis absent')
if __name__=='__main__':main()
