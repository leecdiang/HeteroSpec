"""Fresh real-DLL CPU tests only, constrained by the new Job Object ledger."""
import copy,ctypes,hashlib,json,os,subprocess,sys
from pathlib import Path
from pe_review import PE
R=Path(__file__).resolve().parent;B=R.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2);f.write('\n')
def audit(record,shared=True):
    assert record['admitted'] and record['mode']=='positive'
    order=record['call_sequence'];assert order.index('owned_DLL_initializer_returned')<order.index('DLL_us_returned') and order.index('host_ggml_init_call')<order.index('host_ggml_init_returned')
    core=record['core_gate'];assert core['ready'] and core['events'].count('dll_initializer_returned')==1
    assert core['events'].index('owned_exports_resolved')<core['events'].index('dll_initializer_returned')
    assert core['events'].count('duplicate_request_no_export_call')==1 and core['events'].count('test_only_real_export_reinitialized')==1
    assert all(f['owner_path']==core['path'] for f in core['functions'].values())
    if shared:
        assert all(x['owner_path']==core['path'] and x['IAT_target']==core['functions'][name]['address'] for name,x in record['host_core_binding'].items())
    assert all(a<=b for a,b in zip(record['readings_us'],record['readings_us'][1:]))
    assert record['after_wrapper_repeat_us']>=record['before_repeat_us'] and record['after_actual_export_repeat_us']>=record['after_wrapper_repeat_us']
    delta=record['last_us']-record['first_us'];assert delta>0 and .8*record['QPC_elapsed_us']<=delta<=1.2*record['QPC_elapsed_us']+2000
    b=record['ms_bracket'];assert b['lower_us']-1000<=1000*b['ms']<=b['upper_us']+1000
    for field in ('modules_before','modules_after_cpu_core_load','modules_end'):
        assert not any(any(x in Path(n).name.lower() for x in ('cuda','vulkan','cublas','nvapi','cupti')) for n in record[field])
    assert record['GPU_plugin_loads']==record['device_queries']==record['graph_computes']==record['model_requests']==0
def main():
    assert json.loads((R/'CPU_DEPENDENCY_ADMISSION.json').read_bytes())['status']=='ADMITTED_FOR_CPU_TIMER_AND_METADATA_ONLY'
    f0=json.loads((B/'registration/S1_F0.json').read_bytes());runtime=Path(f0['runtime_directory']);core=runtime/'ggml-base.dll'
    for name,digest in f0['numerical_DLLs'].items():assert sha(runtime/name)==digest
    # Real candidate import tables must refer only to pinned core/registry and
    # Windows system libraries; never directly import a GPU plugin or driver.
    binaries={name:PE(R/name) for name in ('cpu_static.exe','cpu_shared.exe','lowering113_repair.exe')}
    for name,pe in binaries.items():
        assert not any(any(x in dll.lower() for x in ('cuda','vulkan','cublas','nvcuda')) for dll in pe.imports())
    assert 'ggml_init' in binaries['cpu_shared.exe'].imports()['ggml-base.dll']
    assert 'ggml_backend_load' in binaries['lowering113_repair.exe'].imports()['ggml.dll']
    assert not any('ggml' in n.lower() for n in binaries['cpu_static.exe'].imports())
    tests=[('positive_A'+str(i),'cpu_shared.exe','positive') for i in range(3)]+[(name,'cpu_static.exe',name) for name in ('wrong_module','missing_export','host_only','missing_init','wrong_order')]
    save(R/'CPU_TEST_PLAN_final.json',dict(tests=tests,exact_core=str(core),core_sha256=sha(core),binaries={n:sha(R/n) for n in binaries},GPU_starts=0))
    (R/'cpu_results_final').mkdir(exist_ok=False)
    env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','CUDA_','LLAMA_ARG_'))};env['PATH']=str(runtime)+os.pathsep+env.get('PATH','')
    records=[]
    for label,exe,mode in tests:
        output=R/'cpu_results_final'/(label+'.json')
        command=[sys.executable,'-B',str(R/'run_cpu.py'),'--label',label,'--parallel-bound','1',str(R/exe),mode,str(core),f0['numerical_DLLs']['ggml-base.dll'],str(output)]
        result=subprocess.run(command,env=env,capture_output=True)
        save(R/'cpu_results_final'/(label+'.controller.json'),dict(command=command,exit_code=result.returncode,stdout=result.stdout.decode(errors='replace'),stderr=result.stderr.decode(errors='replace')))
        assert result.returncode==0,label
        record=json.loads(output.read_bytes());records.append(record)
        if mode=='positive':audit(record)
        else:assert record['admitted'] is False and record['expected_rejection']
    negatives=[]
    for name in ('duplicate_initializer','missing_initializer','wrong_function_owner','missing_clock_evidence'):
        altered=copy.deepcopy(records[0])
        if name=='duplicate_initializer':altered['core_gate']['events'].append('dll_initializer_returned')
        if name=='missing_initializer':altered['core_gate']['events'].remove('dll_initializer_returned')
        if name=='wrong_function_owner':altered['core_gate']['functions']['ggml_time_init']['owner_path']='wrong module'
        if name=='missing_clock_evidence':del altered['readings_us']
        rejected=False
        try:audit(altered)
        except (AssertionError,KeyError):rejected=True
        assert rejected;negatives.append(dict(case=name,rejected=True,scope='Auditor corruption negative of real native receipt; not a mocked DLL positive test'))
    save(R/'CPU_TIMER_TESTS_final.json',dict(status='PASS',real_fresh_DLL_processes=len(records),shared_positive_processes=3,actual_negative_processes=5,auditor_negative_cases=negatives,
          positive_PIDs=[r['pid'] for r in records[:3]],core_sha256=sha(core),modules_and_functions='Actual native loader, export owner and IAT receipts per process',
          host_and_DLL_versions=[dict(host=r['host_version'],host_commit=r['host_commit'],DLL=r['core_version'],DLL_commit=r['core_commit']) for r in records[:3]],
          graph_computes=0,device_queries=0,GPU_plugin_loads=0,model_requests=0))
    print('PASS:3 fresh shared-core real timer regressions,5 real native negatives,4 raw-auditor negatives; zero GPU starts')
if __name__=='__main__':main()
