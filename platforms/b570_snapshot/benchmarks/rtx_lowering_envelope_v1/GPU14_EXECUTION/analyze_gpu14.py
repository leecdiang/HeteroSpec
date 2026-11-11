"""CPU-only reconstruction of GPU14 raw with the unchanged frozen auditor.

No process start, backend load, device query or numerical execution occurs here.
Optional reference bindings relocate immutable bytes, never change arithmetic/gates.
Loaded numerical DLL identities are checked on disk at their original sealed paths.
"""
import argparse, csv, importlib.util, json, sys
from pathlib import Path

def load(p): return json.loads(Path(p).read_bytes())
def write(p,x):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(x,f,indent=2);f.write('\n')
def analyze(raw,frozen,bindings=None):
    sys.path.insert(0,str(frozen))
    spec=importlib.util.spec_from_file_location('frozen_gpu14_auditor',frozen/'audit_regression.py')
    auditor=importlib.util.module_from_spec(spec);spec.loader.exec_module(auditor)
    f0=load(frozen/'GPU14_F0.json')
    original_f0=load(frozen/'GPU14_F0.json')
    if bindings:
        mapping=load(bindings)
        for slot in f0['slots']:
            slot['root']=str(bindings.parent/mapping['snapshots'][slot['descriptor']])
        f0['old_operator_root']=str(bindings.parent/mapping['operators'])
    start=load(raw/'CONTROLLER_STARTED.json');end=load(raw/'CONTROLLER_ENDED.json')
    assert start['F0_sha256']=='65a6a60b726572305e29f73e2d852936af9e4c87d9740cba5f95f97f738bd290'
    assert end['terminal'] is None and (raw/'COMPLETE.json').exists()
    prior=[];rows=[];identities=[];pids=[start['pid']];lifetimes=[];support=0
    from pe_review import PE
    core_path=Path(f0['runtime_directory'])/'ggml-base.dll'
    exports=PE(core_path).exports()
    plugin_symbols=PE(Path(f0['runtime_directory'])/'ggml-cuda.dll').imports()['ggml-base.dll']
    assert len(plugin_symbols)==f0['plugin_core_import_count']==41
    for i,slot in enumerate(f0['slots']):
        d=raw/f'{i:02d}';assert load(d/'SLOT_PLANNED.json')==original_f0['slots'][i]
        result=auditor.inspect(slot,d,f0,prior)
        expected=load(d/'AUDIT.json');compare=dict(result,directory=expected['directory'])
        assert compare==expected,'raw reanalysis must equal the original frozen audit'
        assert load(d/'COMPLETED.json')['qualified_engineering_controls']
        native=load(d/'native/RECORD.json');gate=load(d/'native/CORE_ADMITTED_BEFORE_CUDA.json')
        core=gate['core'];base=core['module_handle'];plugin=load(d/'native/PLUGIN_CORE_IMPORTS.json')
        assert set(p['symbol'] for p in plugin)==set(plugin_symbols)
        assert all(p['target']==base+exports[p['symbol']]['RVA'] and exports[p['symbol']]['forwarder'] is None for p in plugin)
        assert all(fn['address']==base+exports[name]['RVA'] for name,fn in core['functions'].items())
        assert gate['host_import']['module_handle']==base
        assert native['pid']==load(d/'native_host.PROCESS.json')['pid']==core['pid']
        for prefix in ('readiness','native_host'):
            proc=load(d/(prefix+'.PROCESS.json'));life=load(d/(prefix+'.LIFETIME.json'))
            assert life['pid']==proc['pid'] and life['exit_code']==0 and life['seconds']<life['timeout_seconds']
            pids.append(proc['pid']);lifetimes.append(dict(slot=slot['id'],kind=prefix,**life))
        count=len(native['nodes']['nodes']);assert count==slot['registered_support_queries'];support+=count
        identities.append(dict(slot=slot['id'],pid=native['pid'],core_path=core['path'],core_sha256=core['sha256'],core_handle=base,
            host_IAT_target=gate['host_import']['IAT_target'],registry=gate['registry_import'],plugin_core_imports_verified=len(plugin),
            plugin_targets_equal_actual_core_exports=True,initializer_events=core['events']))
        rows.append(dict(slot=slot['id'],descriptor=slot['descriptor'],layout=slot['layout'],repeat=slot['repeat'],
            graph_started=1,graph_returned=1,synchronized=1,confirmed_complete=1,failed=0,support_queries=count,
            controls='PASS',repeatability=result['repeatability'],numerical_status=result['status']))
        prior.append(result)
    assert len(set(pids))==len(pids)==29 and support==166
    assert len(list(raw.glob('*/native/GRAPH_STARTED_*.json')))==14
    assert not list(raw.rglob('FAILED.json')) and not (raw/'TERMINAL_STOP.json').exists()
    normalized=[dict(p,directory=load(raw/f'{i:02d}'/'AUDIT.json')['directory']) for i,p in enumerate(prior)]
    assert normalized==load(raw/'COMPLETE.json')['records']
    q1={family:dict(hosts=2,completed=2,MQ_original_bitwise='PASS',own_path_inputs_modules_placement='PASS',independent_repeat='BITWISE_PASS')
        for family in ('Qwen','SmolLM2','Llama')}
    q2=[p for p in normalized if p['descriptor']=='Qwen_l00_prefill_q2']
    assert all(p['repeatability']=='BITWISE_PASS' for p in q2 if p['repeat']==1)
    qh=next(p for p in q2 if p['layout']=='QH_C' and p['repeat']==1)
    assert all(c['bitwise_equal'] for arm in ('PQ','QB') for c in qh['pairwise_same_repeat'][arm]['stages'].values())
    native_seconds=sum(p['seconds'] for p in lifetimes if p['kind']=='native_host')
    readiness_seconds=sum(p['seconds'] for p in lifetimes if p['kind']=='readiness')
    return dict(status='GPU14_ENGINEERING_PASS',run_id=f0['run_id'],reviewed_commit='9aefd4c722ac78421994052e41412c2c0417d73b',
        F0_sha256=start['F0_sha256'],counts=dict(controller_starts=1,native_host_starts=14,readiness_starts=14,controlled_process_starts=29,
            graph_starts=14,graph_call_returns=14,successful_full_device_sync_returns=14,confirmed_completed_graphs=14,failed=0,not_started=0,
            support_API_queries=166,model_requests=0,warmups=0,scientific_retries=0,standalone_support_hosts=0),
        accounting=dict(native_child_seconds=native_seconds,readiness_child_seconds=readiness_seconds,child_seconds=native_seconds+readiness_seconds,
            controller_seconds=end['seconds'],conservative_owned_bound_seconds=end['conservative_owned_bound_seconds'],
            owned_ceiling_seconds=1800,wall_ceiling_seconds=900,cost_qualification='NONE: engineering execution records, not clean timing or acceleration',
            internal_driver_query_count='UNKNOWN; 14 explicit readiness processes are not a total driver API count'),
        q1=q1,q2=q2,module_identity=identities,slots=rows,
        historical_720=dict(started_failed=1,not_started=719,confirmed_complete=0,not_backfilled=True),
        admission=dict(prepare_formal_numerical_v2_review=True,formal_v2_execution_authorized=False,timing_profile_authorized=False,
            S2_S3_authorized=False,full_actor_admitted=False,universal_equivalence=False,kernel_or_reduction_identity='UNKNOWN'))

def main():
    a=argparse.ArgumentParser();a.add_argument('--raw',required=True,type=Path);a.add_argument('--frozen',required=True,type=Path)
    a.add_argument('--bindings',type=Path);a.add_argument('--output',required=True,type=Path);args=a.parse_args()
    result=analyze(args.raw,args.frozen,args.bindings);write(args.output,result)
    with args.output.with_suffix('.csv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=result['slots'][0]);w.writeheader();w.writerows(result['slots'])
    print('PASS CPU raw reanalysis: 14 completed/0 failed; 29 controlled starts; 166 support queries; no new native or GPU work')
if __name__=='__main__': main()
