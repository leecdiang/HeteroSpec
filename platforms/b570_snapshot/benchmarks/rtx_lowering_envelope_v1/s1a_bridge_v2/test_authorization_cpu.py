"""Exercise the real approval gate with explicitly synthetic CPU-only files."""
import copy,hashlib
from pathlib import Path
import run_bridge as R
from common import V,RUN,save,load,sha

def main():
    work=V/'cpu_tests/approval';work.mkdir(parents=True,exist_ok=False)
    checks=[];realV=R.V
    for label in ['valid_new_census','old_census','old_numerical','wrong_run','wrong_F0',
                  'message_changed','missing_author','unauthenticated','remote_bytes_drift','wrong_stage']:
        d=work/label;d.mkdir();save(d/'F0.json',dict(CPU_fixture_only=True))
        (d/'REMOTE_F0_BYTES.json').write_bytes((d/'F0.json').read_bytes())
        auth=dict(authenticated_remote_bytes=True,sha256=sha(d/'F0.json'))
        a=dict(stage='BRIDGE_V2_CENSUS_ONLY',F0_sha256=sha(d/'F0.json'),run_id=RUN,
               author_message='CPU_FIXTURE_ONLY_NOT_ACTUAL_AUTHOR_APPROVAL',
               author_message_sha256=hashlib.sha256(b'CPU_FIXTURE_ONLY_NOT_ACTUAL_AUTHOR_APPROVAL').hexdigest())
        if label=='old_census':a['stage']='BRIDGE_CENSUS_ONLY'
        if label=='old_numerical':a['stage']='BRIDGE_NUMERICAL_EXACT'
        if label=='wrong_run':a['run_id']='pr113-s1a-bridge-v1'
        if label=='wrong_F0':a['F0_sha256']='0'*64
        if label=='message_changed':a['author_message']+=' changed'
        if label=='missing_author':a['author_message']=''
        if label=='unauthenticated':auth['authenticated_remote_bytes']=False
        if label=='remote_bytes_drift':(d/'REMOTE_F0_BYTES.json').write_bytes(b'{}')
        if label=='wrong_stage':a['stage']='BRIDGE_V2_NUMERICAL_EXACT'
        save(d/'AUTHENTICATED_F0.json',auth);R.V=d;error=None
        try:R.approval_gate('census',d/'F0.json',a)
        except (AssertionError,KeyError) as exc:error=repr(exc)
        finally:R.V=realV
        assert (error is None)==(label=='valid_new_census'),label
        checks.append(dict(case=label,expected_accept=error is None,error=error))
    save(V/'CPU_AUTHORIZATION_TESTS.json',dict(status='PASS',cases=checks,
        actual_authorization_created=False,production_gate_used=True,GPU_queries=0,CUDA_loads=0,graph_computes=0))
    print('PASS new stage gate and9 negative authorization/remote-byte cases; no GPU authority created')
if __name__=='__main__':main()
