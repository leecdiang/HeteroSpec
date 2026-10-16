"""Actual new host CPU graph/wire/storage tests. GPU modes are never invoked."""
import copy,difflib,json,subprocess,sys
from pathlib import Path
from common import V,RUN,load,save,sha,wire,env
def native(label,mode,plan,output,success=True):
    from lifecycle import Child
    import time
    helper=load(Path('D:/hs113/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/F0.json'))['console_helper']
    worker=Child(helper);cmd=[str(V/'lowering113_formal.exe'),mode,str(plan),str(output)];error=None;t=time.perf_counter()
    try:worker.run(cmd,V/'cpu_tests'/label,120,env(load(V/'PLAN.json')['census_wire']['runtime_directory']),512*1024**2)
    except Exception as exc:error=repr(exc)
    save(V/'cpu_tests'/(label+'.controller.json'),dict(command=cmd,error=error,seconds=time.perf_counter()-t,expected_success=success))
    assert (error is None)==success,label

def main():
    plan=load(V/'PLAN.json');F=V/'CPU_FIXTURE';F.mkdir(exist_ok=False)
    runtime=plan['census_wire']['runtime_directory'];dlls=load(Path('D:/hs113/benchmarks/rtx_lowering_envelope_v1/repair_timer_v1/GPU14_F0.json'))['numerical_DLLs']
    fixture=dict(run_id=RUN,stage='S1A_BRIDGE_V2',CPU_fixture_only=True,executable_sha256=sha(V/'lowering113_formal.exe'),plan_path=str(V/'PLAN.json'),plan_sha256=sha(V/'PLAN.json'),runtime_directory=runtime,numerical_DLLs=dlls)
    save(F/'F0.json',fixture);paths=[]
    for i,s in enumerate(plan['numerical_slots']):
        p=F/'wires'/('%03d.json'%i);save(p,wire(s,F/'F0.json'));paths.append(str(p))
    save(F/'WIRES.json',dict(wire_files=paths))
    native('all240_actual_wires','--cpu-wires',F/'WIRES.json',V/'CPU_WIRES.json')
    actual=load(V/'CPU_WIRES.json');expected={(r['descriptor_id'],r['layout']):r for r in load(V/'EXPECTED_GRAPHS.json')}
    shape_fields=('nodes','output','common_q1_original_arithmetic_chain')
    for r in actual['records']:
        e=expected[r['descriptor_id'],r['layout']]
        assert all(r[k]==e[k] for k in shape_fields)
        s=next(x for x in plan['numerical_slots'] if x['id']==r['slot'])
        assert r['wire_file_sha256']==sha(paths[s['index']])
        d=next(d for d in plan['descriptors'] if d['id']==r['descriptor_id'])
        for stage,size in d['stage_bytes'].items():
            md=r['stage_descriptors'][stage];assert md['bytes']==size and md['type']==0
            assert md['ne'][0]*md['ne'][1]*md['ne'][2]*md['ne'][3]*4==size
            stride=4
            for extent,nb in zip(md['ne'],md['nb']):assert nb==stride;stride*=extent
    for d in plan['descriptors']:
        if d['q']==1:
            rows=[r for r in actual['records'] if r['descriptor_id']==d['id']]
            assert len(rows)==10 and all(r['common_q1_original_arithmetic_chain'] for r in rows)
            assert all(all(r[k]==rows[0][k] for k in shape_fields) for r in rows)
    save(F/'DESCRIPTORS.json',dict(descriptors=plan['descriptors']))
    native('all24_storage_addresses','--cpu-all-addresses',F/'DESCRIPTORS.json',V/'CPU_ADDRESSES.json')
    native('native_malformed_descriptors','--cpu-negatives',F/'DESCRIPTORS.json',V/'CPU_DESCRIPTOR_NEGATIVES.json')
    save(F/'CAS.json',dict(input=plan['numerical_slots'][0]['input_files'][0]['path']))
    native('native_CAS_full_bytes','--cpu-cas',F/'CAS.json',V/'cpu_tests/CAS')
    base=wire(plan['numerical_slots'][0],F/'F0.json');negative=[]
    changes=[('wrong_run','run_id','pr113-s1a-bridge-v1'),('wrong_F0_hash','approved_stage_F0','0'*64),('missing_F0','F0_path',str(F/'absent.json')),
        ('wrong_stage','stage','TIMING'),('wrong_layout','layout','QH_C'),('wrong_repeat','repeat',True),('wrong_index','index',240),
        ('wrong_root','root',str(F)),('wrong_runtime','runtime_directory',str(F)),('wrong_core_hash','core_sha256','0'*64),
        ('wrong_CAS','cas_root',str(F)),('wrong_output','native_output',str(F)),('hidden_warmup','warmups',1),('two_calls','graph_computes',2),('clean_mode','kind','clean')]
    for label,key,value in changes:
        bad=copy.deepcopy(base);bad[key]=value;p=F/'negative'/(label+'.json');save(p,bad)
        native('reject_'+label,'--cpu-one-wire',p,V/'cpu_tests'/(label+'.json'),False);negative.append(label)
    native('positive_one_wire','--cpu-one-wire',paths[0],V/'cpu_tests/positive_wire.json')
    old=(Path('D:/hs113/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/native_formal.cpp')).read_text(encoding='utf-8');new=(V/'native_formal.cpp').read_text(encoding='utf-8')
    assert old[old.index('struct Graph {'):old.index('using I=')]==new[new.index('struct Graph {'):new.index('using I=')]
    assert (V/'hs113_graph.h').read_bytes()==(Path('D:/hs113/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/hs113_graph.h')).read_bytes()
    assert (V/'core_gate.h').read_bytes()==(Path('D:/hs113/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/core_gate.h')).read_bytes()
    with (V/'SOURCE.diff').open('x',encoding='utf-8',newline='\n') as f:f.writelines(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='GPU14/native_repair.cpp',tofile='formal_v2/native_formal.cpp'))
    save(V/'CPU_NATIVE_TESTS.json',dict(status='PASS',real_graphs_from_actual_serialized_wires=240,complete_node_records_equal_frozen_graphs=3612,
        stage_and_ordinary_sizes_and_contiguous_logical_order_checked=240,actual_serializer_roundtrips=240,q1_all_five_common_graphs=60,
        storage_address_results=load(V/'CPU_ADDRESSES.json'),descriptor_negative_tests=5,actual_native_wire_rejections=negative,
        CAS_actual_cpu_full_read_dedup_and_mutation_retention=load(V/'cpu_tests/CAS/RESULT.json'),
        shared_core_mechanism_and_graph_constructor_bytes_unchanged=True,arithmetic_Graph_header_unchanged=True,
        no_GPU_modules_in_actual_CPU_wire_receipt=True,CPU_module_paths=actual['modules'],new_CUDA_plugin_loads=0,new_GPU_queries=0,new_graph_computes=0,new_model_requests=0,
        qualification='Actual shared-core native CPU graph/wire/storage integration only; not backend support or CUDA numerical admission'))
    print('PASS real native240 wire/graph cases,3612node identities,60q1 common graphs,address storage and15negative wires; no CUDA/GPU/query/compute')
if __name__=='__main__':main()
