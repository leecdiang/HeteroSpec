"""New CPU fixtures/report names preserve all earlier GetTickCount64 candidates."""
from common import V

def main():
    for name in ['strict_lifecycle.py','monitor_worker.py']:
        p=V/name;s=p.read_text();s=s.replace('from monitor_contract import','from clock_source import clock_ns,require_clock\nfrom monitor_contract import',1)
        s=s.replace('time.monotonic_ns()','clock_ns()')
        if name=='strict_lifecycle.py':s=s.replace('self.contract=contract','require_clock()\n        self.contract=contract',1)
        else:
            s=s.replace("info=time.get_clock_info('monotonic');assert info.monotonic and not info.adjustable","info=require_clock()")
            s=s.replace('clock=vars(info)','clock=info')
        p.write_text(s,encoding='utf-8')
    replacements={
      'test_cpu.py':{'legacy_regression_r2':'legacy_regression_qpc',"'CPU_GRAPHS.json'":"'CPU_QPC_GRAPHS.json'",'CPU_LOOP_':'CPU_QPC_LOOP_','CPU_TEST_PROGRESS':'CPU_QPC_TEST_PROGRESS','CPU_TESTS.json':'CPU_QPC_TESTS.json','CPU_READINESS_TESTS':'CPU_QPC_READINESS_TESTS','CPU_BOUNDED_TESTS':'CPU_QPC_BOUNDED_TESTS','CPU_AUDIT_TESTS_FINAL':'CPU_QPC_AUDIT_TESTS','test_readiness_cpu.py':'test_readiness_cpu_qpc.py','test_bounded_cpu.py':'test_bounded_cpu_qpc.py','test_audit_cpu.py':'test_audit_cpu_qpc.py'},
      'test_readiness_cpu.py':{'CPU_READINESS_TESTS':'CPU_QPC_READINESS_TESTS'},
      'test_bounded_cpu.py':{'cpu_tests/bounded':'cpu_tests/qpc_bounded','CPU_BOUNDED_TESTS':'CPU_QPC_BOUNDED_TESTS'},
      'test_audit_cpu.py':{'cpu_tests/audit_fixture_final2':'cpu_tests/qpc_audit_fixture','CPU_AUDIT_TESTS_FINAL':'CPU_QPC_AUDIT_TESTS'},
      'test_monitor.py':{'cpu_raw/monitor_v2_final':'cpu_raw/monitor_qpc','CPU_MONITOR_TESTS_FINAL':'CPU_QPC_MONITOR_TESTS'},
      'test_strict_audit.py':{'cpu_raw/strict_audit':'cpu_raw/strict_audit_qpc','cpu_raw/monitor_v2_final':'cpu_raw/monitor_qpc','CPU_STRICT_AUDIT_TESTS':'CPU_QPC_STRICT_AUDIT_TESTS'},
      'test_resource_guard.py':{'cpu_raw/resource_guard':'cpu_raw/resource_guard_qpc','CPU_RESOURCE_GUARD_TESTS':'CPU_QPC_RESOURCE_GUARD_TESTS',"contract=f['monitor_contract']|dict(CPU_fixture_only=True)":"contract=f['monitor_contract']|dict(CPU_fixture_only=True,watchdog_sha256=sha(V/'monitor_worker.py'))"},
      'post_freeze_cpu.py':{'CPU_POST_FREEZE_TESTS':'CPU_QPC_POST_FREEZE_TESTS'}
    }
    for name,mapping in replacements.items():
        s=(V/name).read_text()
        for a,b in mapping.items():s=s.replace(a,b)
        target=V/(name[:-3]+'_qpc.py');assert not target.exists();target.write_text(s,encoding='utf-8')
    print('QPC sources and isolated CPU test outputs prepared;no device activity')
if __name__=='__main__':main()
