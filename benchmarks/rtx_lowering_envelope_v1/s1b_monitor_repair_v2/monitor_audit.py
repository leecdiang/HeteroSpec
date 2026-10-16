"""CPU replay of exact sample bytes; no new runtime samples can be fabricated."""
from pathlib import Path
from common import load,sha
from monitor_contract import Window,decode_sample,MAX_MONITOR_INTERVAL_NS
from clock_source import require_clock

def verify(prefix,contract,cpu_fixture=False):
    prefix=Path(prefix);p=lambda suffix:prefix.with_suffix('.'+suffix)
    c=load(p('MONITOR_CONFIG.json'));r=load(p('MONITOR.json'));life=load(p('LIFETIME.json'));proc=load(p('PROCESS.json'));watch=load(p('WATCHDOG_PROCESS.json'))
    assert (c['run_id'],c['execution_id'])==(contract['run_id'],contract['execution_id'])
    assert c['CPU_fixture_only']==cpu_fixture
    if not cpu_fixture:assert not c['test_hooks_enabled']
    assert r['config_sha256']==sha(p('MONITOR_CONFIG.json')) and r['watchdog_decision']=='PASS'
    assert r['target_pid']==proc['pid']==c['target_pid'] and r['watchdog_pid']==watch['pid']==life['watchdog_pid']
    ready=load(p('MONITOR_READY.json'))
    assert ready['config_sha256']==r['config_sha256'] and ready['pid']==watch['pid']
    assert ready['monotonic_ns']>=c['armed_ns']
    assert watch['script_sha256']==contract['watchdog_sha256'] and watch['python_sha256']==contract['python']['sha256']
    assert r['clock']==ready['clock']==require_clock()
    w=Window(c['armed_ns']);previous=c['config_token_sha256'];sequence=0;discarded=0
    for line in p('MONITOR_SAMPLES.jsonl').read_bytes().splitlines(keepends=True):
        assert line.endswith(b'\n');row,previous=decode_sample(line,previous,c);assert row['sequence']==sequence;sequence+=1
        if row['monotonic_ns']>r['exit_observed_monotonic_ns']:discarded+=1;continue
        w.sample(row['monotonic_ns'])
    w.close(r['exit_observed_monotonic_ns'])
    for k in ['sample_count','interval_count','missing_sample_count','observed_max_interval_ns','observed_max_coverage_gap_ns']:assert w.report()[k]==r[k],k
    assert r['sample_chain_tail']==previous and discarded==r['post_exit_samples_discarded']
    assert r['observed_max_interval_ns']<=MAX_MONITOR_INTERVAL_NS and r['observed_max_coverage_gap_ns']<=MAX_MONITOR_INTERVAL_NS and r['missing_sample_count']==0
    assert life['native_exit_observed_monotonic_ns']==r['exit_observed_monotonic_ns'] and life['native_runtime_seconds']>=0 and life['post_exit_audit_seconds']>=0
    return r
