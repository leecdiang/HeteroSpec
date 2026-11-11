"""Deterministic boundary proofs + real Windows CPU-only owned processes."""
import copy,json,os,sys,time
from pathlib import Path
from common import V,load,save,sha,pin,env
from monitor_contract import Window,MAX_MONITOR_INTERVAL_NS,identities
from strict_lifecycle import StrictChild

def main():
    out=V/'cpu_raw/monitor_v2_final';out.mkdir(exist_ok=False);rows=[]
    def deterministic(name,times,close=None,check=None,good=True):
        window=Window(10);error=None
        try:
            for t in times:window.sample(t)
            if check is not None:window.check(check)
            if close is not None:window.close(close)
        except Exception as e:error=repr(e)
        report=dict(case=name,**window.report('PASS' if error is None else 'FAIL'),identity_decision='N/A pure interval',exact_Census_byte_decision='N/A pure interval',expected_accept=good,error=error)
        rows.append(report)
        assert (error is None)==good,report
    deterministic('normal_requested50ms_actual50ms',[10,50_000_010,100_000_010],close=120_000_010)
    deterministic('actual_interval_far_below1s',[10,1010,2010],close=3010)
    for gap,good in [(999_999_999,True),(1_000_000_000,True),(1_000_000_001,False)]:
        deterministic('boundary_'+str(gap),[10,10+gap],close=10+gap,good=good)
    deterministic('watchdog_age_at_exact_boundary',[10],check=1_000_000_010)
    deterministic('watchdog_missing_sample_over_boundary',[10],check=1_000_000_011,good=False)
    deterministic('no_samples_exit_is_not_a_sample',[],close=100,good=False)
    deterministic('backwards_timestamp',[10,9],good=False)
    deterministic('equal_timestamp_anomaly',[10,10],good=False)
    deterministic('EOF_does_not_create_sample',[],check=1_000_000_011,good=False)
    w=Window(10);w.sample(10);w.sample(100);w.close(150);before=w.report();w.check(20_000_000_000);assert w.report()==before
    rows.append(dict(case='slow_post_audit_cannot_change_closed_window',**w.report(),identity_decision='N/A',exact_Census_byte_decision='N/A'))
    f=dict(run_id='pr116-s1b-cost-v1',execution_id='pr116-s1b-exact-r2')
    for name,a,good in [('canonical_identity',f,True),('swapped_identity',dict(run_id=f['execution_id'],execution_id=f['run_id']),False),('wrong_execution',f|dict(execution_id='pr116-s1b-exact-r1'),False),('execution_in_run_id',f|dict(run_id=f['execution_id']),False)]:
        error=None
        try:identities(f,a)
        except ValueError as e:error=repr(e)
        assert (error is None)==good
        rows.append(dict(case=name,observed_max_interval_ns=None,interval_count=0,missing_sample_count=0,watchdog_decision='NOT_STARTED_CPU_IDENTITY_ONLY',identity_decision='PASS' if error is None else 'REJECT',exact_Census_byte_decision='N/A',expected_accept=good,error=error))
    old=load(V.parent/'s1b_exact_repair_v1/F0.json');contract=dict(f,max_monitor_interval_ns=MAX_MONITOR_INTERVAL_NS,watchdog_path=str(V/'monitor_worker.py'),watchdog_sha256=sha(V/'monitor_worker.py'),python=pin(sys.executable),CPU_fixture_only=True)
    real=[]
    scenarios=[('normal50ms','import time;time.sleep(.25)',{},True),
               ('monitor_sleep_stall','import time;time.sleep(4)',dict(stall_after=2,stall_seconds=1.3),False),
               ('monitor_crash','import time;time.sleep(4)',dict(crash_after=2),False),
               ('missing_all_samples','import time;time.sleep(4)',dict(crash_after=0),False),
               ('normal_exit_monitor_race','import time;time.sleep(.15)',dict(stall_after=1,stall_seconds=1.3),True),
               ('slow_post_exit_audit','import time;time.sleep(.15)',dict(post_audit_sleep=1.3),True),
               ('pipe_EOF_while_host_alive','import os,time;os.close(1);os.close(2);time.sleep(.25)',{},True)]
    for name,code,hooks,good in scenarios:
        prefix=out/name;worker=StrictChild(old['console_helper'],contract);error=None
        try:worker.run([sys.executable,'-B','-c',code],prefix,6,env(''),128*1024**2,cpu_hooks=hooks)
        except Exception as e:error=repr(e)
        mp=prefix.with_suffix('.MONITOR.json');record=load(mp) if mp.exists() else dict(watchdog_decision='NO_RESULT',missing_sample_count=1)
        life=load(prefix.with_suffix('.LIFETIME.json'))
        row=dict(case=name,expected_accept=good,error=error,monitor=record,lifetime=life)
        real.append(row);save(out/(name+'.TEST.json'),row)
        assert (error is None)==good,row
        assert record['watchdog_decision']==('PASS' if good else 'FAIL'),row
        assert record['watchdog_pid']!=record['target_pid'] and record['watchdog_pid']!=os.getpid()
        if good:
            from monitor_audit import verify
            verify(prefix,contract,cpu_fixture=True)
            assert record['missing_sample_count']==0 and record['observed_max_interval_ns']<=MAX_MONITOR_INTERVAL_NS and record['observed_max_coverage_gap_ns']<=MAX_MONITOR_INTERVAL_NS
            assert record['sample_count']>=1 and record['window_closed']
        else:assert record['missing_sample_count']>=1
        if name=='monitor_sleep_stall':assert record['observed_max_coverage_gap_ns']>MAX_MONITOR_INTERVAL_NS
        if name in ['slow_post_exit_audit','normal_exit_monitor_race']:
            assert life['native_runtime_seconds']<1 and life['post_exit_audit_seconds']>1
        if name=='normal_exit_monitor_race':assert record['sample_count']==1
    save(V/'CPU_MONITOR_TESTS_FINAL.json',dict(status='PASS',max_interval_ns=MAX_MONITOR_INTERVAL_NS,boundary_rule='<= inclusive; > fails',deterministic=rows,real_Windows_processes=real,test_count=len(rows)+len(real),GPU_queries=0,CUDA_loads=0,graph_computes=0,warmups=0))
    print('PASS strict interval/identity',len(rows),'deterministic +',len(real),'real Windows process scenarios;GPU0')

if __name__=='__main__':main()
