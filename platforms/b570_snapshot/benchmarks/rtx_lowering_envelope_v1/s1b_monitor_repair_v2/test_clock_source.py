"""Verify actual frozen runtime clock and reject unsuitable clock providers."""
import types,time
from common import V,save
import clock_source as C

def main():
    actual=C.require_clock();old=vars(time.get_clock_info('monotonic'));a=C.clock_ns();b=C.clock_ns();assert b>=a
    rows=[dict(case='real_frozen_QPC_monotonic_100ns_source',status='PASS')]
    fn=time.get_clock_info
    for name,updates in [('GetTickCount64_rejected',dict(implementation='GetTickCount64()')),('nonmonotonic_rejected',dict(monotonic=False)),('adjustable_rejected',dict(adjustable=True)),('resolution_drift_rejected',dict(resolution=.015625))]:
        fake={k:v for k,v in actual.items() if k in ['implementation','monotonic','adjustable','resolution']}|updates
        error=None
        try:
            time.get_clock_info=lambda name:types.SimpleNamespace(**fake)
            try:C.require_clock()
            except Exception as e:error=repr(e)
        finally:time.get_clock_info=fn
        assert error;rows.append(dict(case=name,status='PASS',expected_reject=True,error=error))
    for name in ['strict_lifecycle.py','monitor_worker.py']:
        s=(V/name).read_text();assert 'time.monotonic_ns()' not in s and 'clock_ns()' in s and 'require_clock()' in s
    rows.append(dict(case='sampler_and_independent_watchdog_share_verified_QPC',status='PASS'))
    save(V/'CPU_QPC_CLOCK_SOURCE_TESTS.json',dict(status='PASS',test_count=len(rows),cases=rows,actual_clock=actual,not_used_clock=old,prior_QPC_label_was_incorrect=True,prior_candidates_preserved=True,GPU_queries=0,CUDA_loads=0,graph_calls=0))
    print('PASS actual QPC clock and',len(rows),'clock source tests;GPU0')
if __name__=='__main__':main()
