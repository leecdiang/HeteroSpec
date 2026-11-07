"""CPU-only budget construction and impact review; never imports a backend."""
import difflib
from pathlib import Path
from common import V,RUN,load,save,sha,pin

OLD=Path('D:/hs113-bridge/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v1')
def main():
    plan=load(V/'PLAN.json');prior=load(OLD/'PLAN.json')
    assert plan['descriptors']==prior['descriptors']
    # Fields that must differ solely to isolate the new experiment.
    changed={'run_id','cas_root','native_output'}
    for a,b in zip(plan['numerical_slots'],prior['numerical_slots']):
        assert {k:v for k,v in a.items() if k not in changed}=={k:v for k,v in b.items() if k not in changed}
    unchanged=['native_formal.cpp','hs113_graph.h','core_gate.h','analyzer.py','raw_math.py','bounded.py','lifecycle.py','libggml.dll.a','libggml-base.dll.a']
    for name in unchanged:assert (V/name).read_bytes()==(OLD/name).read_bytes(),name
    gate_old=(OLD/'formal_gate.h').read_bytes()
    assert (V/'formal_gate.h').read_bytes()==gate_old.replace(b'pr113-s1a-bridge-v1',RUN.encode()).replace(b'S1A_BRIDGE_V1',b'S1A_BRIDGE_V2')
    identity=load(OLD/'F0.json');budget=load(OLD/'BUDGET_FINAL.json');initial=load(V/'BUDGET.json')
    for key in ['snapshot_input_logical_bytes','unique_input_bytes','complete_immutable_reference_unique_bytes','all240_outputs_no_dedup_bytes','first_mutant_input_readback_reserve_bytes']:
        assert budget['storage'][key]==initial['storage'][key]
    assert budget['counts']['maximum_all_controlled_and_helper_process_starts']==966
    assert budget['counts']['total_support_API_queries']==5418
    budget['registration_run_id']=RUN
    budget['basis']['readiness_attempts_under_new_policy']='A unchanged5%; no cooldown, extra query, inherited starts or budget reuse'
    budget['basis']['per_slot_OS_conflict_inventory']='CPU-only, included in stage wall; preserves all existing child limits'
    budget['CPU_delivery_accounting_scope']='Frozen offline jobs use exact process receipts; ordinary Git/interactive tools have separately reported elapsed wall and are not globally process-accounted.'
    save(V/'BUDGET_FINAL.json',budget)
    diff=''.join(difflib.unified_diff((OLD/'formal_gate.h').read_text().splitlines(True),(V/'formal_gate.h').read_text().splitlines(True),fromfile='closed_v1/formal_gate.h',tofile='new_v2/formal_gate.h'))
    save(V/'IMPLEMENTATION_REVIEW.json',dict(status='PASS_CPU_IMPACT_REVIEW',closed_run_immutable=True,
        byte_identical=unchanged,native_gate_diff=diff,arithmetic_changes=0,numerical_DLL_changes=0,
        snapshot_contexts_identical=24,input_selection='Original preregistered profile_coordinates() exactly unchanged',
        candidate='QH_C fixed; QH_D fixed contrast',numerical_tolerances_unchanged=True,
        old_executable=pin(OLD/'lowering113_formal.exe'),new_executable=pin(V/'lowering113_formal.exe'),
        support_inheritance='NEW_CENSUS_REQUIRED_NO_TRANSFER',reason='New executable hash, admission gate run/stage and wires/F0; no new query has occurred',
        new_census_graphs=120,new_census_support_queries=1806,new_numerical_graphs=240,new_numerical_support_queries=3612,
        original_numerical_DLLs=identity['numerical_DLLs'],new_GPU_activity=0))
    print('PASS identical24 contexts/graph arithmetic and budget; new census REQUIRED')
if __name__=='__main__':main()
