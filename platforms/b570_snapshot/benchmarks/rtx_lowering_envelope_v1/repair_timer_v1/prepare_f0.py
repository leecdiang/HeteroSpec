"""CPU preparation only. Never calls safety.query, backend or GPU executable modes."""
import difflib,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from pe_review import PE
R=Path(__file__).resolve().parent;B=R.parent
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2);f.write('\n')
def main():
    old=load(B/'registration/S1_F0.json');runtime=Path(old['runtime_directory']);mismatches=[]
    for p in old['files']:
        if sha(p['path'])!=p['sha256']:mismatches.append(p['path'])
    assert not mismatches
    # Compare every previously tracked experiment byte to the reviewed stop.
    tracked=subprocess.check_output(['git','ls-tree','-r','--name-only','dbf86fde1908e643d5c35ae4429cd720c37a6e4c','--','benchmarks/rtx_lowering_envelope_v1'],cwd=B.parents[1]).decode().splitlines()
    tracked_mismatch=[]
    for rel in tracked:
        data=subprocess.check_output(['git','show','dbf86fde1908e643d5c35ae4429cd720c37a6e4c:'+rel],cwd=B.parents[1]);path=B.parents[1]/rel
        if data!=path.read_bytes():tracked_mismatch.append(rel)
    assert not tracked_mismatch
    status=load(B/'S1_NUMERICAL/ANALYSIS.json');assert (status['numeric_hosts_started'],status['numeric_hosts_failed'],status['not_started_due_to_protocol_stop'],status['confirmed_completed_graphs'])==(1,1,719,0)
    starts=list(Path(old['execution_root']).rglob('BEFORE_START.json'));assert len(starts)==2
    save(R/'OLD_EVIDENCE_UNCHANGED.json',dict(status='PASS',old_F0_files_verified=len(old['files']),reviewed_tracked_files_verified=len(tracked),mismatches=[],
         old_numerical_started=1,old_numerical_failed=1,old_numerical_not_started=719,old_completed=0,old_S1_native_hosts=2,old_graph_start_charge=1,old_native_owned_seconds=status['S1_total_native_owned_seconds'],
         old_operator_sha256=sha(B/'native/build/bin/lowering113.exe'),old_selection_sha256=sha(B/'S1A/PREOUTPUT_SELECTION.json'),old_numerical_archive_sha256=sha(B/'S1_NUMERICAL/RAW_NUMERICAL_STOP.zip'),no_budget_transfer=True))
    # Actual release binary: CPU graph construction/ABI only, no backend calls.
    env=os.environ.copy();env['PATH']=str(runtime)+os.pathsep+env.get('PATH','')
    for label,mode,plan,output in [('release_registry','--cpu-registry',B/'DESCRIPTOR_PLAN.json',R/'CPU_REGISTRY_release.json'),('release_ABI','--cpu-core-abi',R/'CPU_ABI_PLAN.json',R/'CPU_ABI_release.json')]:
        argv=[sys.executable,'-B',str(R/'run_cpu.py'),'--label',label,'--parallel-bound','1',str(R/'lowering113_repair.exe'),mode,str(plan),str(output)]
        result=subprocess.run(argv,env=env,capture_output=True)
        save(R/(label+'.controller.json'),dict(command=argv,exit_code=result.returncode,stdout=result.stdout.decode(errors='replace'),stderr=result.stderr.decode(errors='replace')))
        assert result.returncode==0
    registry=load(R/'CPU_REGISTRY_release.json');expected=load(B/'CPU_ACCEPTED/SUPPORT_REGISTRY_S0.json')
    assert registry['records']==expected['records'] and registry['graphs']==1680 and registry['GPU_initializations']==registry['graph_computes']==0
    assert not any(any(x in Path(p).name.lower() for x in ('cuda','vulkan','cublas','nvapi','cupti')) for p in registry['modules'])
    source=(R/'native_repair.cpp').read_text();original=(B/'native113.cpp').read_text()
    assert source[source.index('struct Graph {'):source.index('using I=')]==original[original.index('struct Graph {'):original.index('using I=')]
    assert (R/'hs113_graph.h').read_bytes()==(B/'hs113_graph.h').read_bytes()
    # Exact audited link lines, not a claim based on the names of functions.
    logs=[load(p) for p in sorted((R/'ledger').glob('*-START.json'))];link=next(x['command'] for x in logs if x['command'][-1].endswith('lowering113_repair.exe') and '-O3' in x['command'])
    imports=PE(R/'lowering113_repair.exe').imports();assert 'ggml.dll' in imports and 'ggml-base.dll' in imports
    assert not any('ggml-base.a' in x or x.endswith('/ggml.a') for x in link)
    save(R/'RELEASE_IDENTITY.json',dict(operator_sha256=sha(R/'lowering113_repair.exe'),source_sha256=sha(R/'native_repair.cpp'),graph_header_sha256=sha(R/'hs113_graph.h'),
        route='A',exact_link_command=link,PE_imports=imports,full_1680_graph_records_equal=True,ABI_metadata_checks=load(R/'CPU_ABI_release.json')['tensor_checks'],
        graph_computes=0,CUDA_plugin_loads=0,device_queries=0))
    plan=load(B/'S1_PLAN.json');numeric=[p for p in plan['slots'] if p['kind']=='numeric'];full=load(B/'FULL_SNAPSHOTS.json')
    coordinates=[]
    for family in ('Qwen','SmolLM2','Llama'):
        coordinates.append(next(p for p in numeric if p['layout']=='MQ' and p['repeat']==0 and p['descriptor'].startswith(family+'_') and '_prefill_q1' in p['descriptor']))
    q2=next(p for p in numeric if p['layout']=='MQ' and p['repeat']==0 and p['descriptor'].startswith('Qwen_') and '_prefill_q2' in p['descriptor'])
    query_counts={(p['descriptor_id'],p['layout']):len(p['nodes']) for p in registry['records'] if p['stage_outputs']}
    slots=[]
    def append(p,layout,repeat,group):
        meta=load(Path(p['root'])/'snapshot.json');snapshot=next(s for s in full['contexts'] if s['context']['id']==p['descriptor'])
        files=[Path(p['root'])/'snapshot.json']+[Path(p['root'])/meta[role]['file'] for role in ('Q','K','V','mask')]
        slots.append(dict(id=f'gpu14/{len(slots):02d}/{p["descriptor"]}/{layout}/r{repeat}',group=group,descriptor=p['descriptor'],root=p['root'],layout=layout,repeat=repeat,old_index=snapshot['index'],
            graph_computes=1,warmups=0,registered_support_queries=query_counts[(p['descriptor'],layout)],
            input_files=[dict(path=str(f),bytes=f.stat().st_size,sha256=sha(f)) for f in files]))
    for p in coordinates:
        for repeat in (0,1):append(p,'MQ',repeat,'common_q1')
    for layout in ('MQ','PQ','QB','QH_C'):
        for repeat in (0,1):append(q2,layout,repeat,'q2_diagnostic')
    assert len(slots)==14
    files={p['path']:p for p in old['files']}
    for p in sorted(R.rglob('*')):
        if p.is_file() and p.name not in ('GPU14_F0.json','RAW_REPAIR.zip','RAW_REPAIR_MANIFEST.json'):
            files[str(p)]=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
    # Exclude live/current ledger logs; historical closed records remain pinned.
    for name in list(files):
        if '/ledger/' in name.replace('\\','/') and not Path(name).name.split('-')[0].isdigit():del files[name]
    f0=dict(schema=1,run_id='pr113-timer-gpu-regression-v1',review_base='dbf86fde1908e643d5c35ae4429cd720c37a6e4c',status='PREPARED_NOT_GPU_AUTHORIZED',
        route='A: new host imports byte-identical frozen core and registry DLLs; exact pointer/owner admission before explicit CUDA plugin load',
        execution_root='D:/hs113-timer-gpu14-v1',executable=str(R/'lowering113_repair.exe'),runtime_directory=str(runtime),numerical_DLLs=old['numerical_DLLs'],admission_policy=old['admission_policy'],
        selected_QH='QH_C',selection_policy='unchanged prior selection; never replace with QH_D after outcomes',old_operator_root='D:/hs104-authenticated-final-restore/E1/data/operators',
        plugin_core_import_count=len(PE(runtime/'ggml-cuda.dll').imports()['ggml-base.dll']),
        support_policy='No automatic whole-registry inheritance for the revised executable. Query every node of each actual14 graph once in its registered host. Full formal-v2 support admission needs later review/F0.',
        limits=dict(controller_process_starts=1,native_host_attempts=14,readiness_process_starts=14,explicit_nvidia_smi_queries=14,controlled_process_start_cap=29,
            graph_attempts=14,graph_computes_per_host=1,warmups=0,model_requests=0,standalone_support_hosts=0,support_API_queries=sum(s['registered_support_queries'] for s in slots),
            backend_load_API_calls=14,backend_init_by_name_API_calls=14,plugin_core_IAT_entries_per_host=41,
            internal_driver_query_count='UNKNOWN: do not equate14 explicit checkpoint queries with all driver/device enumeration internal calls',
            owned_child_seconds=1800,whole_controller_wall_seconds=900,accounting='conservative whole-controller wall times2; one synchronous child maximum, child descendants JobObject active limit1',
            per_native_host_seconds=60,per_readiness_seconds=10,per_host_bytes=12*1024**2,raw_root_bytes=192*1024**2,all_new_derived_bytes=1024**3),
        stop_rules=['All6 common-q1 controls, full inputs, own paths and repeatability pass before q2','Any native/readiness/interface/support/placement/input/control failure is terminal; retain first failure and all starts, no retry, replacement, alternate snapshot or layout',
                    'All outputs finite; MQ own path and inherited PQ/QB bitwise controls mandatory; ordinary restore matches own canonical AV',
                    'Two fresh repeats per coordinate/layout must agree bitwise','Finite q2 QH differences retained with exact bitwise/max-error/ULP, no tolerance tuning; fixed QH_C never changed','No timing/profile/model/panel-v2/S2/S3 automatic admission'],
        output_contract='Before/after graph markers, API return and all-device completion status, actual module paths and hashes, host/plugin real core-IAT ownership, complete Q/K/V/mask before/after bytes, canonical QK/softmax/AV and ordinary bytes, frozen own-path/q1/repeatability audits. Engineering IO intervals are not clean timing.',
        inherited_environment=dict(GGML_CUDA_DISABLE_GRAPHS='1',meaning='Identical to failed frozen run; not changed as timer fix'),files=list(files.values()),slots=slots)
    save(R/'GPU14_F0.json',f0)
    save(R/'GPU14_SELECTION.json',dict(selection_before_any_new_GPU_output=True,coordinates=[dict(id=s['id'],group=s['group'],descriptor=s['descriptor'],layout=s['layout'],repeat=s['repeat'],support_API_queries=s['registered_support_queries']) for s in slots],support_API_queries=f0['limits']['support_API_queries'],GPU_started=False))
    print(json.dumps(dict(status='CPU_REPAIR_PASS_GPU14_NOT_AUTHORIZED',operator_sha256=sha(R/'lowering113_repair.exe'),F0_sha256=sha(R/'GPU14_F0.json'),support_queries=f0['limits']['support_API_queries'],slots=[s['id'] for s in slots]),indent=2))
def load(p):return json.loads(Path(p).read_bytes())
if __name__=='__main__':main()
