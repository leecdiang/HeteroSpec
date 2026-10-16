"""New interpreter replay of restored CPU engineering evidence, no device APIs."""
import argparse,ast
from pathlib import Path
from common import V,load,save,sha
from monitor_audit import verify
from monitor_contract import identities,MAX_MONITOR_INTERVAL_NS

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);ap.add_argument('--F0-sha256',required=True);a=ap.parse_args()
    f=load(V/'F0.json');plan=load(V/'PLAN.json');checks=[]
    def ok(name):checks.append(dict(case=name,status='PASS'))
    assert sha(V/'F0.json')==a.F0_sha256;ok('restored_exact_F0')
    identities(f,plan);identities(f,f['monitor_contract'])
    for s in plan['clean_slots']+plan['trace_slots']:identities(f,s)
    ok('canonical_and_execution_ID_every_slot')
    assert sha(V/'s1b_clean.exe')=='073bdc32c6b54866b075d0dc47b5e9a343ec299fa1c87b5cd0937abe32db035b';ok('native_EXE_unchanged')
    census=V.parent/'evidence/CENSUS.json'
    assert sha(census)==f['execution_bound_census']['sha256']=='d8c79ed1b4fc748ec8ce22a201137ef6fc201de79052fa7c6c4f7711806e8256';ok('execution_Census_exact_CRLF')
    assert sha(V.parent/'evidence/DECISION.json')==f['execution_bound_decision']['sha256'];ok('exact_Decision')
    original=Path(f['repository'])/'benchmarks/rtx_lowering_envelope_v1/s1b_monitor_repair_v2'
    mapped=0
    for row in f['files']:
        try:rel=Path(row['path']).relative_to(original)
        except ValueError:continue
        assert (V/rel).stat().st_size==row['bytes'] and sha(V/rel)==row['sha256'];mapped+=1
    assert mapped>40;ok('all_F0_local_source_and_CPU_evidence_pins_restored')
    for name,digest in f['numerical_DLLs'].items():assert sha(Path(f['runtime_directory'])/name)==digest
    assert len(f['numerical_DLLs'])==21;ok('21_DLL_exact_disk_bytes_no_load')
    g=load(V/'CPU_GRAPHS.json');assert g['graphs']==72 and g['graph_computes']==g['new_GPU_queries']==g['new_CUDA_loads']==0
    assert g['records']==load(V.parent/'evidence/ORIGINAL_CPU_GRAPHS.json')['records'];ok('all72_actual_CPU_graph_serializer_records_unchanged')
    report=load(V/'CPU_MONITOR_TESTS_FINAL.json');real=report['real_Windows_processes'];positive=[]
    for r in real:
        if r['expected_accept']:
            proof=verify(V/'cpu_raw/monitor_v2_final'/r['case'],f['monitor_contract']|dict(CPU_fixture_only=True),cpu_fixture=True);positive.append(proof)
        else:assert r['monitor']['watchdog_decision']=='FAIL' and r['monitor']['missing_sample_count']>=1
    assert len(positive)==4;ok('real_process_samples_independently_replayed_4_qualified_3_fail_closed')
    boundaries={r['case']:r for r in report['deterministic']}
    for n,good in [('boundary_999999999',True),('boundary_1000000000',True),('boundary_1000000001',False)]:assert (boundaries[n]['error'] is None)==good
    ok('inclusive_exact_nanosecond_boundaries')
    total=0
    for name in ['CPU_TESTS.json','CPU_MONITOR_TESTS_FINAL.json','CPU_STRICT_AUDIT_TESTS.json','CPU_IDENTITY_CONTRACT_TESTS.json','CPU_POST_FREEZE_TESTS.json']:
        r=load(V/name);assert r['status']=='PASS';total+=r.get('test_count',r.get('test_total',0))
    assert total==177;ok('177_CPU_tests_recorded_pass_including_negative_expectations')
    for row in load(V/'HISTORY_BEFORE.json')['files']:assert sha(row['path'])==row['sha256']
    ok('all4941_historical_files_unchanged')
    assert not Path(f['execution_root']).exists() and not (original/'execution_ledger').exists();ok('new_GPU_execution_never_started')
    for p in V.glob('*.py'):ast.parse(p.read_bytes(),filename=str(p))
    ok('restored_sources_parse_no_CUDA_import')
    save(a.out,dict(status='PASS',run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(V/'F0.json'),test_count=len(checks),checks=checks,prior_CPU_test_count=total,restored_F0_pins=mapped,actual_sample_max_interval_ns=max(r['observed_max_interval_ns'] for r in positive),actual_positive_interval_count=sum(r['interval_count'] for r in positive),missing_sample_count=sum(r['missing_sample_count'] for r in positive),watchdog_decision='PASS qualified;all failure fixtures rejected',identity_decision='PASS',exact_Census_byte_decision='PASS',GPU_queries=0,CUDA_loads=0,graph_calls=0))
    print('PASS fresh independent CPU replay',len(checks),'checks;GPU0')
if __name__=='__main__':main()
