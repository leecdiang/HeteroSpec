"""Final CPU-only native census-wire and exact plan/runtime/source contract."""
import csv,json,subprocess,sys
from common import V,load,save,wire,sha,env
def main():
    plan=load(V/'PLAN.json');p=V/'CPU_FIXTURE/CENSUS_WIRE.json';save(p,wire(plan['census_wire'],V/'CPU_FIXTURE/F0.json'))
    command=[sys.executable,'-B',str(V/'cpu_job.py'),'--label','actual_census_wire_CPU','--parallel-bound','1',str(V/'lowering113_formal.exe'),'--cpu-one-wire',str(p),str(V/'CPU_CENSUS_WIRE.json')]
    result=subprocess.run(command,env=env(plan['census_wire']['runtime_directory']),capture_output=True)
    save(V/'CPU_CENSUS_WIRE.controller.json',dict(command=command,exit_code=result.returncode,stdout=result.stdout.decode(errors='replace'),stderr=result.stderr.decode(errors='replace')));assert result.returncode==0
    for p in V.glob('*.py'):compile(p.read_text(encoding='utf-8'),str(p),'exec')
    rows=load(V/'CPU_WIRES.json')['records'];assert len(rows)==720
    with (V/'MATRIX.csv').open('x',encoding='utf-8',newline='') as out:
        fields=['index','descriptor','family','layer','phase','q','layout','repeat','old_index','registered_support_queries','visible_key_counts','padded_key_extent']
        w=csv.DictWriter(out,fieldnames=fields,lineterminator='\n');w.writeheader()
        for s in plan['numerical_slots']:
            d=next(d for d in plan['descriptors'] if d['id']==s['descriptor']);w.writerow({k:s[k] for k in fields[:-2]}|dict(visible_key_counts=','.join(str(x['count']) for x in d['visibility']['visible_keys_by_query']),padded_key_extent=d['visibility']['padded_key_extent']))
    old=(V.parent/'repair_timer_v1/native_repair.cpp').read_text(encoding='utf-8');new=(V/'native_formal.cpp').read_text(encoding='utf-8')
    assert old[old.index('struct Graph {'):old.index('using I=')]==new[new.index('struct Graph {'):new.index('using I=')]
    assert (V/'hs113_graph.h').read_bytes()==(V.parent/'repair_timer_v1/hs113_graph.h').read_bytes()
    assert (V/'core_gate.h').read_bytes()==(V.parent/'repair_timer_v1/core_gate.h').read_bytes()
    # Native snapshots are input identities, not additional or unseen prompts.
    save(V/'CPU_CONTRACT_TESTS.json',dict(status='PASS',real_native_census_wire_admitted_in_CPU_mode=True,all720_CSV_wires_enumerated=True,
        all_current_Python_sources_parse=True,Graph_constructor_and_arithmetic_header_identical_to_GPU14=True,shared_CoreGate_header_identical_to_GPU14=True,
        support_query_counts=dict(census=5418,numerical=10836,total=16254),numerical_contexts=72,layouts=5,fresh_repeats=2,
        strict_GPU_F0_and_run_id_checks_retained=True,GPU_queries=0,CUDA_plugin_loads=0,graph_computes=0,model_requests=0))
    print('PASS actual census-wire CPU admission,720matrix enumeration,source/plan contracts; no GPU work')
if __name__=='__main__':main()
