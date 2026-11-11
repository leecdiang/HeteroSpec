"""Resume only missing slots after a resource stop; never replace a measurement."""
from develop import *

def resume(family,arm):
    source=ROOT/'runs'/f'{family}-{arm}-development'
    assert json.loads((source/'failure.json').read_bytes())['error']=="AssertionError('live resource limit')"
    original=json.loads((source/'job.json').read_bytes());completed=[];missing=[];gap=False
    for one in original['inputs']:
        exists=(source/'native'/one['name']/'receipt.json').exists()
        if not exists:gap=True;missing.append(one)
        else:assert not gap;completed.append(one)
    assert completed and missing and all(not r['capture'] for r in missing)
    # Reconstruct the same input/reset/decode history without duplicating offline
    # exports. Every completed measurement remains selected from the first job.
    recovery=[dict(one,name='recovery-'+one['name'],capture=False) for one in completed]+missing
    payload={k:v for k,v in original.items() if k not in MODELS[family]};payload['inputs']=recovery
    plan=dict(failed_attempt=str(source),completed_slots=[r['name'] for r in completed],missing_slots=[r['name'] for r in missing],completed_measurements_never_replaced=True,recovery_history_performed_but_never_used_as_performance_samples=True,selection_uses_receipt_existence_only=True,source_binary_unchanged=True)
    design=ROOT/f'{family}-{arm}-STORAGE-RESUME-DESIGN.json'
    if not design.exists():put(design,plan)
    else:assert json.loads(design.read_bytes())==plan
    reserve=json.loads((source/'launch.json').read_bytes())['reservation']
    out=finished(f'{family}-{arm}-storage-recovery',VERSIONS[arm.split('-')[0]],family,payload,reserve)
    for one in completed:
        a=json.loads((source/'native'/one['name']/'receipt.json').read_bytes())
        b=json.loads((out/'native'/('recovery-'+one['name'])/'receipt.json').read_bytes())
        assert a['endpoint']==b['endpoint'],'recovery history endpoint differs'
    view=ROOT/'resumed-views'/f'{family}-{arm}';(view/'native').mkdir(parents=True,exist_ok=True)
    for name in ('binding.json','job.json'):
        if (view/name).exists():assert sha(view/name)==sha(source/name)
        else:os.link(source/name,view/name)
    for one in original['inputs']:
        base=source if one in completed else out
        src=base/'native'/one['name'];dst=view/'native'/one['name']
        if dst.exists():
            assert {p.relative_to(src):sha(p) for p in src.rglob('*') if p.is_file()}=={p.relative_to(dst):sha(p) for p in dst.rglob('*') if p.is_file()}
        else:shutil.copytree(src,dst,copy_function=os.link)
    a=json.loads((source/'native/result.json').read_bytes());b=json.loads((out/'native/result.json').read_bytes());meta=dict(a)
    meta['status']='COMPOSITE_VIEW_NOT_A_NATIVE_ATTEMPT';meta['requests']=[dict(name=one['name'],record=one['name']+'/receipt.json') for one in original['inputs']]
    for k in ('model_load_s','pool_setup_s'):meta[k]=a[k]+b[k]
    first=json.loads((source/'native'/completed[0]['name']/'receipt.json').read_bytes())
    meta['resident_initial_plan_compile_s']=first['first_call_plan_s']+b['resident_initial_plan_compile_s']
    meta['initial_plan_clock_basis']='Original first-ever target-call clock plus recovery native result; partial native result omits its final summary field.'
    meta['storage_recovery']=dict(plan,recovery_attempt=str(out),all_setup_and_recovery_service_charged=True)
    put(view/'native/result.json',meta);put(ROOT/f'{family}-{arm}-STORAGE-RESUME.json',dict(plan,view=str(view),recovery_attempt=str(out)))
    dedup();print('Retained first completed slots and resumed only',plan['missing_slots'],flush=True)

if __name__=='__main__':resume('Smol','SIMPLE-D1')
