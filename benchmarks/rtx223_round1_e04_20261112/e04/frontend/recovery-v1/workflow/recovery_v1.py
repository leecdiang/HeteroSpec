"""Additive conservative recovery; reuse completed frozen loop4, build missing packed once."""
from pathlib import Path
import argparse,json,shutil,datetime
from input_freeze import ReadFreeze,need,sha,snapshot,verify,verify_manifest_identity
import input_freeze as freeze_module
import dep_witness_v3 as dep_module
from dep_witness_v3 import parse_dependency,resolved_cpu
import closure_witness_v1 as witness_module
import link_witness as archive_module
from closure_witness_v1 import analyze
import frozen_build_v4 as recipe_module

HERE=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx223-round1-resume-20261112-e04/e04/frontend').resolve()
ORIGINAL=HERE/'run-v4';RECOVERY=HERE/'recovery-v1'
def put(path,value):
    with Path(path).open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,indent=2)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def tree_members(recipe):
    return {str(p.resolve()):sha(p) for k in ('toolchain','source','dependencies') for p in Path(recipe[k]).rglob('*') if p.is_file()}|{str(p.resolve()):sha(p) for p in (ORIGINAL/'workflow').rglob('*') if p.is_file()}
def direct_objects(info):return [arg for arg in info['link'] if Path(arg).is_absolute() and Path(arg).suffix.casefold()=='.obj']
def attest(core,recipe,compile_folder,link_folder):
    info=recipe['cores'][core];source=Path(recipe['source'])/'entry.cpp'
    deps=parse_dependency(Path(info['object']).parent/'worker.d',info['object'],source)
    need(deps==info['prescan_dependencies'],'actual header set differs: '+core)
    need(resolved_cpu((compile_folder/(core+'-compile.stderr.log')).read_text(encoding='utf8'))==info['effective_CPU'],'actual CPU differs: '+core)
    c=json.loads((compile_folder/(core+'-compile.json')).read_bytes());l=json.loads((link_folder/(core+'-link.json')).read_bytes())
    need(c['returncode']==0 and c['argv']==info['compile'],'compile invocation mismatch')
    need(l['returncode']==0 and l['argv']==info['link'],'link invocation mismatch')
    trace=(link_folder/(core+'-link.stdout.log')).read_text(encoding='utf8')+(link_folder/(core+'-link.stderr.log')).read_text(encoding='utf8')
    mapping=(Path(info['object']).parent/'worker.map').read_text(encoding='utf8')
    witness=analyze(trace,info['archives'],direct_objects(info),mapping)
    return {'core':core,'exe':info['exe'],'exe_sha256':sha(info['exe']),'object':snapshot([Path(info['object'])])[0],'actual_dependencies':deps,'actual_dependency_file_sha256':sha(Path(info['object']).parent/'worker.d'),'actual_CPU':info['effective_CPU'],'whole_archive_witness':witness,'codegen_and_link_passed':True}
def prepare():
    RECOVERY.mkdir(exist_ok=False);workflow=RECOVERY/'workflow';workflow.mkdir()
    original=json.loads((ORIGINAL/'FREEZE.json').read_bytes());verify(original['entries'])
    recipe=json.loads((ORIGINAL/'RECIPE.json').read_bytes());need(tree_members(recipe)==original['tree_membership'],'original codegen input closure changed')
    loop4=attest('loop4',recipe,ORIGINAL,ORIGINAL)
    put(RECOVERY/'LOOP4_OFFLINE_PRECHECK.json',loop4)
    source_files=[HERE/'recovery_v1.py',HERE/'closure_witness_v1.py',ORIGINAL/'workflow/input_freeze.py',ORIGINAL/'workflow/dep_witness_v3.py',ORIGINAL/'workflow/link_witness.py',ORIGINAL/'workflow/frozen_build_v4.py']
    for path in source_files:shutil.copy2(path,workflow/path.name)
    extras=[ORIGINAL/'FREEZE.json',ORIGINAL/'loop4-compile.json',ORIGINAL/'loop4-compile.stdout.log',ORIGINAL/'loop4-compile.stderr.log',ORIGINAL/'loop4-link.json',ORIGINAL/'loop4-link.stdout.log',ORIGINAL/'loop4-link.stderr.log',ORIGINAL/'build/loop4/worker.obj',ORIGINAL/'build/loop4/worker.d',ORIGINAL/'build/loop4/worker.map',ORIGINAL/'build/loop4/bin/worker.exe',RECOVERY/'LOOP4_OFFLINE_PRECHECK.json',*workflow.iterdir()]
    entries=original['entries']+snapshot(extras)
    put(RECOVERY/'PREPARED.json',{'schema':'heterospec.e04.frontend-recovery-prepared.v1','entries':entries,'original_tree_membership':original['tree_membership'],'original_freeze_sha256':sha(ORIGINAL/'FREEZE.json'),'original_recipe_sha256':sha(ORIGINAL/'RECIPE.json'),'loop4_codegen_repeated':False,'packed_codegen_started':False,'witness_policy':'complete frozen archive containers; exact duplicate-member occurrence NOT_ATTESTED','workflow_files':{str(p):sha(p) for p in workflow.iterdir()},'OS_DLLs_and_Python_runtime_attested':False})
    print(json.dumps({'prepared_sha256':sha(RECOVERY/'PREPARED.json'),'next':'run staged recovery_v1.py build --prepared-sha','GPU_launches':0}))
def build(expected):
    workflow=RECOVERY/'workflow';need(Path(__file__).resolve()==workflow/'recovery_v1.py','execute staged recovery controller')
    for module,name in ((freeze_module,'input_freeze.py'),(dep_module,'dep_witness_v3.py'),(witness_module,'closure_witness_v1.py'),(archive_module,'link_witness.py'),(recipe_module,'frozen_build_v4.py')):need(Path(module.__file__).resolve()==workflow/name,'active workflow import mismatch')
    prepared=verify_manifest_identity(RECOVERY/'PREPARED.json',expected);recipe=json.loads((ORIGINAL/'RECIPE.json').read_bytes())
    need(tree_members(recipe)==prepared['original_tree_membership'],'original membership changed before recovery')
    need(all(sha(p)==h for p,h in prepared['workflow_files'].items()),'recovery workflow changed')
    freeze={'schema':'heterospec.e04.frontend-recovery-freeze.v1','entries':prepared['entries']+snapshot([RECOVERY/'PREPARED.json']),'prepared_sha256':expected,'pre_packed_codegen':True,'started_utc':utc(),'lock_scope':'own e04 complete sources, compiler/resources, headers, archive containers, recovery controller, existing loop4 evidence','original_v4_inputs_modified':False,'new_packed_outputs_use_original_frozen_recipe_paths':True}
    put(RECOVERY/'FREEZE.json',freeze)
    with ReadFreeze(freeze['entries']+[{'path':str(RECOVERY/'FREEZE.json'),'sha256':sha(RECOVERY/'FREEZE.json')}]) as held:
        locked_utc=utc();loop4=attest('loop4',recipe,ORIGINAL,ORIGINAL);put(RECOVERY/'loop4-WHOLE_ARCHIVE_WITNESS.json',loop4['whole_archive_witness'])
        info=recipe['cores']['packed'];recipe_module.run_record('packed-compile',info['compile'],ORIGINAL,recipe['environment'],RECOVERY)
        actual_deps=parse_dependency(Path(info['object']).parent/'worker.d',info['object'],Path(recipe['source'])/'entry.cpp');need(actual_deps==info['prescan_dependencies'],'packed actual header mismatch')
        need(resolved_cpu((RECOVERY/'packed-compile.stderr.log').read_text(encoding='utf8'))==info['effective_CPU'],'packed CPU mismatch')
        obj=snapshot([Path(info['object'])])[0];held.add(obj)
        recipe_module.run_record('packed-link',info['link'],ORIGINAL,recipe['environment'],RECOVERY)
        packed=attest('packed',recipe,RECOVERY,RECOVERY);put(RECOVERY/'packed-WHOLE_ARCHIVE_WITNESS.json',packed['whole_archive_witness'])
        verify(freeze['entries']);verify([obj]);need(tree_members(recipe)==prepared['original_tree_membership'],'input membership changed during recovery')
        put(RECOVERY/'POSTFREEZE.json',{'entries_rehashed':len(freeze['entries']),'same_membership_hashes_and_mtimes':True,'packed_object':obj,'locks_held_through_packed_codegen_link_and_final_verification':True,'locked_utc':locked_utc,'verified_utc':utc(),'loop4_original_lock_session':'separate v4 ReadFreeze held throughout its successful compile/link, released on narrow witness failure; retained inputs and outputs revalidated under recovery lock','uninterrupted_dual_core_lock_session':False})
    for output in (loop4,packed):output.pop('whole_archive_witness')
    result={'schema':'heterospec.e04.frontend-bound-build.v1','status':'PASS_FROZEN_BUILD_NOT_NATIVE_QUALIFIED','outputs':[loop4,packed],'original_freeze_sha256':prepared['original_freeze_sha256'],'recovery_freeze_sha256':sha(RECOVERY/'FREEZE.json'),'postfreeze_sha256':sha(RECOVERY/'POSTFREEZE.json'),'recipe_sha256':sha(ORIGINAL/'RECIPE.json'),'whole_archive_input_closure':'PASS','exact_selected_duplicate_member_occurrence':'NOT_ATTESTED','original_narrow_witness_failure_retained':str(HERE/'BUILD_v4.log'),'loop4_codegen_repeated':False,'separate_per_core_lock_sessions':True,'GPU_launches':0,'model_requests':0,'CUDA_DLL_loads':0,'worker_EXE_runs':0,'native_gate':'BLOCKED'}
    put(RECOVERY/'BUILD.json',result);print(json.dumps({'status':result['status'],'cores':[x['core'] for x in result['outputs']],'GPU_launches':0}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=('prepare','build'));a.add_argument('--prepared-sha');v=a.parse_args()
    if v.action=='prepare':prepare()
    else:build(v.prepared_sha)
