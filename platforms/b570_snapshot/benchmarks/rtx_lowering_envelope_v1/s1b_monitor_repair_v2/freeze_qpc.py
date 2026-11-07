"""Finalize actual QPC clock qualification; preserve all superseded CPU evidence."""
import datetime
from common import V,load,save,sha,pin
from clock_source import require_clock

def main():
    # Independent restore uses the final QPC fixtures, not the old coarse-clock candidates.
    s=(V/'fresh_check.py').read_text()
    replace={'CPU_TESTS.json':'CPU_QPC_TESTS.json','CPU_MONITOR_TESTS_FINAL':'CPU_QPC_MONITOR_TESTS','CPU_STRICT_AUDIT_TESTS':'CPU_QPC_STRICT_AUDIT_TESTS','CPU_POST_FREEZE_TESTS':'CPU_QPC_POST_ACTUAL_CLOCK_TESTS','CPU_RESOURCE_GUARD_TESTS':'CPU_QPC_RESOURCE_GUARD_TESTS',"'CPU_GRAPHS.json'":"'CPU_QPC_GRAPHS.json'",'cpu_raw/monitor_v2_final':'cpu_raw/monitor_qpc',"'CPU_QPC_RESOURCE_GUARD_TESTS.json']":"'CPU_QPC_RESOURCE_GUARD_TESTS.json','CPU_QPC_CLOCK_SOURCE_TESTS.json']",'total==180':'total==186','180_CPU_tests':'186_CPU_tests'}
    for a,b in replace.items():s=s.replace(a,b)
    s=s.replace("f=load(V/'F0.json');plan=load(V/'PLAN.json');checks=[]","f=load(V/'F0.json');plan=load(V/'PLAN.json');checks=[]")
    s=s.replace("assert sha(V/'F0.json')==a.F0_sha256;ok('restored_exact_F0')","assert sha(V/'F0.json')==a.F0_sha256;ok('restored_exact_F0')\n    from clock_source import require_clock\n    assert require_clock()==f['monitor_contract']['actual_clock'];ok('actual_QPC_monotonic_100ns_clock_verified')")
    (V/'fresh_check_qpc.py').write_text(s,encoding='utf-8')
    s=(V/'publish_cpu.py').read_text().replace('delivery/raw','delivery/cpu-qpc').replace('cpu_raw/publication','cpu_raw/publication_qpc').replace('hs116-s1b-exact-r2-cpu-fresh','hs116-s1b-exact-r2-cpu-qpc-fresh').replace('fresh_check.py','fresh_check_qpc.py')
    s=s.replace("['cpu_raw','preparation_candidates','ledger']","['cpu_raw','cpu_tests','preparation_candidates','ledger']")
    s=s.replace("if folder=='cpu_raw' and 'publication' in p.relative_to(V/folder).parts:continue","if folder=='cpu_raw' and any(x.startswith('publication') for x in p.relative_to(V/folder).parts):continue")
    (V/'publish_cpu_qpc.py').write_text(s,encoding='utf-8')
    d=V/'preparation_candidates/actual_QPC_revision';d.mkdir(exist_ok=False);f=load(V/'F0.json')
    for n in ['F0.json','AUTHENTICATED_F0.json','REMOTE_F0_BYTES.json','CENSUS_EXACT_AUTHENTICATED.json','REMOTE_ARCHIVE_VERIFIED.json','CPU_CAPSULE_PACKAGED.json','FRESH_CPU_AUDIT.json']:(V/n).rename(d/n)
    f.update(registration_revision=4,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),repair_source_parent_commit='f0939e2c1d6c3302c4d341a54e7ca7f68d7ba216',superseded_CPU_candidate=pin(d/'F0.json'),superseded_CPU_remote_verification=pin(d/'REMOTE_ARCHIVE_VERIFIED.json'))
    f['monitor_contract'].update(clock='time.perf_counter_ns;verified Windows QueryPerformanceCounter',actual_clock=require_clock(),watchdog_sha256=sha(V/'monitor_worker.py'),coarse_monotonic_ns_not_used=True)
    reports=['CPU_QPC_TESTS.json','CPU_QPC_MONITOR_TESTS.json','CPU_QPC_STRICT_AUDIT_TESTS.json','CPU_IDENTITY_CONTRACT_TESTS.json','CPU_QPC_POST_ACTUAL_CLOCK_TESTS.json','CPU_QPC_RESOURCE_GUARD_TESTS.json','CPU_QPC_CLOCK_SOURCE_TESTS.json']
    assert sum(load(V/n).get('test_count',load(V/n).get('test_total',0)) for n in reports)==186
    f['CPU_tests']={n:pin(V/n) for n in reports};f['CPU_tests']['PRE_FREEZE_IDENTITY.json']=pin(V/'PRE_FREEZE_IDENTITY.json')
    f['CPU_candidate_correction']='Earlier monotonic_ns clock was GetTickCount64,not QPC; earlier labels superseded. Final actual QPC source,high-resolution process tests and independent replay required. No GPU attempt ever started.'
    files={r['path']:r for r in f['files']}
    for p in list(V.iterdir())+list(d.iterdir()):
        if p.is_file() and p.suffix in {'.py','.h','.cpp','.exe','.json','.md'} and p.name!='F0.json':files[str(p)]=pin(p)
    files[str(d/'F0.json')]=pin(d/'F0.json')
    f['files']=sorted(files.values(),key=lambda r:r['path']);f['source_roles']={p.name:sha(p) for p in V.iterdir() if p.suffix in {'.py','.h','.cpp'}}
    save(V/'F0.json',f);print('FINAL QPC F0',sha(V/'F0.json'),'186CPU tests;no GPU execution')
if __name__=='__main__':main()
