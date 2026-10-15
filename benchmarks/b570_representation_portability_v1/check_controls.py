"""Checker revision regression, without executing another attention fixture."""
from common import ROOT, modules, save, sha
from conditions import evaluate, example

def main():
    before=modules();rows=[]
    for field,value in [('hk',7),('q',3),('q_offset',36),('q_nb',[4,0,512,32768]),
                        ('mask_nb',[4,516,16384,16384]),('k_nb',[2,256,1,1]),
                        ('k_buffer_bytes',2),('v_buffer_bytes',2),('mask_buffer_bytes',2),
                        ('mask_nonempty',False),('phase','UNKNOWN'),('role','UNKNOWN'),('state_provenance',''),('version','other')]:
        x=example();x[field]=value;r=evaluate(x);assert r['errors'],field
        rows.append(dict(field=field,value=value,errors=r['errors']))
    x=example();x['backend_dll_sha256']='unknown';r=evaluate(x)
    assert not r['errors'] and all(y['vulkan_mul_mat_support'] is None for y in r['representations'].values())
    role=[]
    for name in ('target','draft'):
        for phase in ('PREFILL','VERIFY'):
            x=example(1);x.update(role=name,phase=phase);r=evaluate(x)
            expected=name=='target' and phase!='PREFILL'
            assert r['representations']['PQ']['static_legal']==expected
            role.append(dict(role=name,phase=phase,PQ_admitted=expected))
    assert evaluate(example())['representations']['QB']['vulkan_mul_mat_support'] is False
    save(ROOT/'CHECKER_TESTS.json',dict(rejection_cases=rows,role_cases=role,unknown_backend_not_inferred=True,
         example=evaluate(example()),checker_sha256=sha(ROOT/'conditions.py'),
         revision=1,reason='Require explicitly declared K/V/mask buffer and backend version conditions; deny phase/role-incompatible bindings. This tightens static checker only after source review; frozen numerical harness/fixtures unchanged.',
         independent_holdout_claim_for_checker_revision=False,
         modules_before=before,modules_after=modules(),new_attention_fixtures=0,gpu_starts=0))
    print(dict(rejection_cases=len(rows),role_cases=len(role),unknown_backend=True,new_attention_fixtures=0))

if __name__=='__main__':main()
