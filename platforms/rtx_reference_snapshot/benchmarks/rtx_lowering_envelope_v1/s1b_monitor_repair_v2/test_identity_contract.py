"""Real CRLF artifact, canonical identity and minimum-stop CPU regressions."""
import copy,hashlib,json
from pathlib import Path
from common import V,load,save,pin,sha
from exact_binding import admit
from identified_state import IdentifiedState

def main():
    out=V/'cpu_raw/identity_contract';out.mkdir(exist_ok=False);rows=[]
    raw=Path('D:/hs116-s1b-cost-v1/census/native/CENSUS.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='d8c79ed1b4fc748ec8ce22a201137ef6fc201de79052fa7c6c4f7711806e8256'
    c=out/'CENSUS.json';c.write_bytes(raw);decision=Path('D:/hs116-s1b-cost-v1/CENSUS_DECISION.json')
    f=dict(run_id='pr116-s1b-cost-v1',execution_id='pr116-s1b-exact-r2',execution_bound_census=pin(c),execution_bound_decision=pin(decision));fp=out/'F0.json';save(fp,f)
    a=dict(run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(fp),census_sha256=sha(c),decision_sha256=sha(decision))
    def test(name,fn,good=False):
        error=None
        try:fn()
        except Exception as e:error=repr(e)
        assert (error is None)==good,(name,error)
        rows.append(dict(case=name,expected_accept=good,accepted=error is None,error=error,observed_max_interval_ns=None,interval_count=0,missing_sample_count=0,watchdog_decision='NOT_STARTED_CPU_ADMISSION',identity_decision='PASS' if not error else 'REJECT',exact_Census_byte_decision='PASS' if not error else 'REJECT'))
    test('canonical_exact_native_Census',lambda:admit(f,a,fp),True)
    test('execution_id_in_run_id',lambda:admit(f,a|dict(run_id=a['execution_id']),fp))
    test('swapped_fields',lambda:admit(f,a|dict(run_id=a['execution_id'],execution_id=a['run_id']),fp))
    test('missing_execution_id',lambda:admit(f,{k:v for k,v in a.items() if k!='execution_id'},fp))
    test('obsolete_registration_alias',lambda:admit(f,a|dict(registration_id=a['execution_id']),fp))
    test('wrong_execution_id',lambda:admit(f,a|dict(execution_id='pr116-s1b-exact-r1'),fp))
    test('F0_hash_mismatch',lambda:admit(f,a|dict(F0_sha256='0'*64),fp))
    test('wrong_Census_hash',lambda:admit(f,a|dict(census_sha256='0'*64),fp))
    def change(data):
        c.write_bytes(data)
        try:admit(f,a,fp)
        finally:c.write_bytes(raw)
    lf=raw.replace(b'\r\n',b'\n');assert json.loads(lf)==json.loads(raw) and lf!=raw
    test('real_LF_semantic_equivalent_rejected',lambda:change(lf))
    test('real_JSON_reserialized_rejected',lambda:change(json.dumps(json.loads(raw)).encode()))
    test('real_truncated_Census',lambda:change(raw[:-1]))
    test('real_one_byte_mutation',lambda:change(bytes([raw[0]^1])+raw[1:]))
    def missing():
        c.rename(out/'preserved')
        try:admit(f,a,fp)
        finally:(out/'preserved').rename(c)
    test('real_missing_Census',missing)
    copied=out/'byte_copy';copied.write_bytes(raw);ff=f|dict(execution_bound_census=pin(copied));ffp=out/'copy_F0.json';save(ffp,ff)
    test('real_byte_for_byte_copy',lambda:admit(ff,a|dict(F0_sha256=sha(ffp)),ffp),True)
    root=out/'state';root.mkdir();s=IdentifiedState(root,'CLEAN0',f['run_id'],f['execution_id']);s.reserve_start(dict(id='completed_slot'),100,80);s.native_start(123);s.complete()
    def budgetstop():s.reserve_start(dict(id='next_slot'),79,80)
    test('budget_before_next_does_not_fail_completed_slot',budgetstop)
    s.minimum_stop('CPU fixture budget stop');s.finish('INCOMPLETE_STOPPED');stop=load(root/'CLEAN0_MINIMUM_STOP.json')
    assert stop['completed']==1 and stop['current'] is None and stop['run_id']==f['run_id'] and stop['execution_id']==f['execution_id']
    test('durable_stop_two_identities_no_retroactive_failure',lambda:None,True)
    save(V/'CPU_IDENTITY_CONTRACT_TESTS.json',dict(status='PASS',test_count=len(rows),cases=rows,authorization_binds='exact bytes consumed by the execution entry',GPU_queries=0,CUDA_loads=0,graph_calls=0))
    print('PASS',len(rows),'canonical/exact native Census/minimum-stop tests;GPU0')
if __name__=='__main__':main()
