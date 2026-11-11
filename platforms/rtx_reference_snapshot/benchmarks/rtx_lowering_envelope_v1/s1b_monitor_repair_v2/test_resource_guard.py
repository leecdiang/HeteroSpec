"""Pure/real Windows CPU proofs that stale resource-guard state cannot qualify."""
import sys,threading,time
from common import V,load,save,sha,pin,env
from resource_guard import ResourceGuard
from strict_lifecycle import StrictChild

def main():
    out=V/'cpu_raw/resource_guard';out.mkdir(exist_ok=False);rows=[];calls=[]
    g=ResourceGuard(lambda:calls.append('actual_resources'),lambda:calls.append('deadline'))
    g();g();assert calls==['actual_resources','deadline']*2
    rows.append(dict(case='every_call_actual_resources_before_deadline',status='PASS'))
    def bad():raise RuntimeError('actual resource check failed')
    failed=False
    try:ResourceGuard(bad,lambda:calls.append('incorrect_accept'))()
    except RuntimeError:failed=True
    assert failed and 'incorrect_accept' not in calls;rows.append(dict(case='actual_resource_failure_cannot_qualify',status='PASS'))
    f=load(V/'F0.json');contract=f['monitor_contract']|dict(CPU_fixture_only=True);count=[0]
    def stall_resources():
        if 'collect' in threading.current_thread().name:
            count[0]+=1
            if count[0]==3:time.sleep(1.3)
    prefix=out/'real_resource_stall';error=None
    try:StrictChild(f['console_helper'],contract).run([sys.executable,'-B','-c','import time;time.sleep(4)'],prefix,6,env(''),128*1024**2,guard=ResourceGuard(stall_resources,lambda:None))
    except Exception as e:error=repr(e)
    r=load(prefix.with_suffix('.MONITOR.json'))
    assert error and r['watchdog_decision']=='FAIL' and r['missing_sample_count']>=1 and r['observed_max_coverage_gap_ns']>1_000_000_000
    rows.append(dict(case='real_Windows_resource_guard_stall_independent_watchdog',status='PASS',observed_max_interval_ns=r['observed_max_interval_ns'],interval_count=r['interval_count'],missing_sample_count=r['missing_sample_count'],watchdog_decision=r['watchdog_decision'],observed_max_coverage_gap_ns=r['observed_max_coverage_gap_ns'],error=error))
    save(V/'CPU_RESOURCE_GUARD_TESTS.json',dict(status='PASS',test_count=len(rows),cases=rows,GPU_queries=0,CUDA_loads=0,graph_calls=0))
    print('PASS actual-resource guard',len(rows),'checks;GPU0')
if __name__=='__main__':main()
