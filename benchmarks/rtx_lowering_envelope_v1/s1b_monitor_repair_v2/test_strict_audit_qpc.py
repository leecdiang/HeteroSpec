"""Independent replay negatives and real watchdog-death CPU fixture."""
import copy,shutil,sys
from pathlib import Path
from common import V,load,save,pin,sha,env
from monitor_audit import verify
from strict_lifecycle import StrictChild
from monitor_contract import MAX_MONITOR_INTERVAL_NS

def main():
    out=V/'cpu_raw/strict_audit_qpc';out.mkdir(exist_ok=False);rows=[]
    contract=dict(run_id='pr116-s1b-cost-v1',execution_id='pr116-s1b-exact-r2',max_monitor_interval_ns=MAX_MONITOR_INTERVAL_NS,watchdog_path=str(V/'monitor_worker.py'),watchdog_sha256=sha(V/'monitor_worker.py'),python=pin(sys.executable),CPU_fixture_only=True)
    source=V/'cpu_raw/monitor_qpc/normal50ms'
    def case(name,mutate=None,good=False):
        d=out/name;d.mkdir();prefix=d/'host'
        for p in source.parent.glob(source.name+'.*'):
            shutil.copyfile(p,prefix.with_suffix(p.name[len(source.name):]))
        if mutate:mutate(prefix)
        error=None;r=None
        try:r=verify(prefix,contract,cpu_fixture=True)
        except Exception as e:error=repr(e)
        assert (error is None)==good,(name,error)
        rows.append(dict(case=name,accepted=error is None,expected_accept=good,error=error,observed_max_interval_ns=r['observed_max_interval_ns'] if r else None,interval_count=r['interval_count'] if r else None,missing_sample_count=r['missing_sample_count'] if r else None,watchdog_decision='PASS' if r else 'REJECT',identity_decision='PASS' if r else 'REJECT',exact_Census_byte_decision='N/A monitor evidence'))
    def change(prefix,suffix,fn):
        p=prefix.with_suffix('.'+suffix);data=load(p);fn(data);p.write_text(__import__('json').dumps(data),encoding='utf-8')
    case('exact_monitor_evidence',good=True)
    case('alter_sample_bytes',lambda p:p.with_suffix('.MONITOR_SAMPLES.jsonl').write_bytes(p.with_suffix('.MONITOR_SAMPLES.jsonl').read_bytes().replace(b'resource_valid":true',b'resource_valid":false',1)))
    case('truncated_sample',lambda p:p.with_suffix('.MONITOR_SAMPLES.jsonl').write_bytes(p.with_suffix('.MONITOR_SAMPLES.jsonl').read_bytes()[:-1]))
    case('missing_samples',lambda p:p.with_suffix('.MONITOR_SAMPLES.jsonl').unlink())
    case('wrong_run_id',lambda p:change(p,'MONITOR_CONFIG.json',lambda d:d.update(run_id=contract['execution_id'])))
    case('wrong_execution_id',lambda p:change(p,'MONITOR_CONFIG.json',lambda d:d.update(execution_id=contract['run_id'])))
    case('false_maximum',lambda p:change(p,'MONITOR.json',lambda d:d.update(observed_max_interval_ns=0)))
    case('false_missing_count',lambda p:change(p,'MONITOR.json',lambda d:d.update(missing_sample_count=1)))
    case('false_watchdog_PID',lambda p:change(p,'MONITOR.json',lambda d:d.update(watchdog_pid=1)))
    case('wrong_watchdog_source',lambda p:change(p,'WATCHDOG_PROCESS.json',lambda d:d.update(script_sha256='0'*64)))
    case('missing_watchdog_ready',lambda p:p.with_suffix('.MONITOR_READY.json').unlink())
    case('watchdog_failure_not_qualified',lambda p:change(p,'MONITOR.json',lambda d:d.update(watchdog_decision='FAIL')))
    prefix=out/'watchdog_crash';error=None
    try:StrictChild(load(V.parent/'s1b_exact_repair_v1/F0.json')['console_helper'],contract).run([sys.executable,'-B','-c','import time;time.sleep(4)'],prefix,6,env(''),128*1024**2,cpu_hooks=dict(kill_watchdog_after=2))
    except Exception as e:error=repr(e)
    assert error and load(prefix.with_suffix('.LIFETIME.json'))['error']
    assert not prefix.with_suffix('.MONITOR.json').exists(),'no fabricated terminal qualification'
    rows.append(dict(case='real_Windows_watchdog_crash_fail_closed',expected_accept=False,accepted=False,error=error,observed_max_interval_ns=None,interval_count=None,missing_sample_count=1,watchdog_decision='REJECT_NO_TERMINAL_RECEIPT',identity_decision='CPU fixture identity',exact_Census_byte_decision='N/A'))
    save(V/'CPU_QPC_STRICT_AUDIT_TESTS.json',dict(status='PASS',test_count=len(rows),cases=rows,GPU_queries=0,CUDA_loads=0,graph_calls=0))
    print('PASS',len(rows),'independent monitor audit / watchdog death tests;GPU0')
if __name__=='__main__':main()
