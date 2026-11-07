"""Run the fixed exposed-root qualification; never a formal timing panel."""
from qualify_rtx import *

def finish():
    proofs=sorted(ROOT.glob('*v2-*-QUALIFICATION.json'))
    assert len(proofs)==21 and all(read(p)['passed'] for p in proofs)
    put(ROOT/'NATIVE_QUALIFICATION_COMPLETE.json',dict(version=VERSION,proofs=[dict(path=str(p),sha256=sha(p)) for p in proofs],passed=True,full_original_requested_vectors=True,finite_active_KV_boundaries=True,real_target_only_four_combinations=True,matched_M_and_D4=True,formal_timing_requests=0))
    inherited=[]
    for p in sorted((P190/'runs').glob('*teacher*')):
        if (p/'COMPLETE.json').exists():inherited.append(dict(path=str(p),binding_sha256=sha(p/'binding.json'),actual_work=read(p/'COMPLETE.json')['actual_work']))
    put(ROOT/'INHERITED_REFERENCE_COSTS.json',dict(original_R_unchanged=True,only_same_reference_prefix_evidence_reused=True,PR190_unified_costs_sha256=sha(HERE.parent/'rtx_phase_plan_v1/host_evidence/UNIFIED_COSTS.json'),original_reference_teachers=inherited,PR186_canonical_prefix_costs='Original immutable replay bank and parent ledger, not new free work or pooled timing',new_native_work_in='ledger.sqlite',historical_performance_not_pooled=True))
    print('All actual native finite qualifications complete',flush=True)

def main():
    for family in ('Qwen','Smol'):
        for arm in ARMS:natural(family,arm)
    for arm in ARMS:natural('Qwen',arm,target_only=True)
    natural('Qwen','L_P',draft=True)
    finish()

if __name__=='__main__':
    if '--finish' in sys.argv:finish()
    else:main()
