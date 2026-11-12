"""Bind final artifacts and static PE import names; never initialize a numerical DLL."""
from pathlib import Path
import datetime,hashlib,json,shutil
from pe_identity_v2 import inspect
from stage_modules_v1 import is_system
from input_freeze import ReadFreeze,snapshot,verify
from finalize_artifacts import volume
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'expected-modules-v1'
EXPECTED='2307f64f1f1f4d0bb4aba42e6f6793a29579c2af031e4dbadac77811096ae8ad'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
    if not v:raise RuntimeError(m)
def put(p,j):
    with Path(p).open('x',encoding='utf8',newline='\n') as f:json.dump(j,f,indent=2)
def main():
    source=ROOT/'runtime/link-v3/bin/ggml-cuda.dll';link_path=ROOT/'runtime/link-v3/BUILD.json';compile_path=ROOT/'runtime/build-v2/BUILD.json'
    link=json.loads(link_path.read_bytes());comp=json.loads(compile_path.read_bytes())
    need(link['DLL_sha256']==EXPECTED==sha(source),'native output identity differs')
    need(Path(link['DLL_path']).resolve()==source.resolve() and link['link_returncode']==0 and not link['input_posthash_changes'],'native final link receipt mismatch')
    need(link['fresh_e04_v2_compiled_objects']==145 and link['e03_objects']==link['failed_v1_objects']==0 and link['uninterrupted_compile_link_freeze'] is False,'native compile/link-session contract differs')
    need(comp['fresh_translation_units']==145 and comp['compile_failures']==comp['reused_objects']==0 and comp['dependency_closure']=='PASS','native fresh compile closure did not pass')
    target=OUT/'ggml-cuda.dll';need(not target.exists(),'do not overwrite staged numerical DLL');shutil.copy2(source,target);need(sha(source)==EXPECTED==sha(target),'numeric copy changed')
    staged=json.loads((OUT/'STAGED_DEPENDENCIES.json').read_bytes());proposed=json.loads((OUT/'PROPOSED_VCOMP_IDENTITY.json').read_bytes())
    paths={name:Path(v['path']) for name,v in staged['modules'].items()};paths['vcomp140.dll']=Path(proposed['staged']);paths['ggml-cuda.dll']=target
    expected={name:v['sha256'] for name,v in staged['modules'].items()};expected.update({'vcomp140.dll':proposed['sha256'],'ggml-cuda.dll':EXPECTED})
    need({p.name.casefold() for p in OUT.glob('*.dll')}==set(paths),'unlisted DLL in isolated directory')
    entries=snapshot(paths.values());need(all(sha(p)==expected[n] for n,p in paths.items()),'staged dependency identity changed')
    with ReadFreeze(entries):
        pe={name:inspect(path) for name,path in paths.items()};external=set();missing=[];symbols=[];forwarders=[]
        for name,record in pe.items():
            for kind,key in (('direct','import_symbols'),('delay','delay_import_symbols')):
                for dep,imports in record[key].items():
                    dep=dep.casefold()
                    if is_system(dep):external.add(dep);continue
                    if dep not in pe:missing.append({'from':name,'module':dep,'kind':kind});continue
                    provided=pe[dep]['exports'];ordinals={v['ordinal'] for v in provided.values()}
                    for imported in imports:
                        if isinstance(imported,dict):found=imported['ordinal'] in ordinals
                        else:found=imported in provided
                        symbols.append({'from':name,'to':dep,'kind':kind,'symbol':imported,'export_present':found})
                        if not found:missing.append({'from':name,'module':dep,'symbol':imported,'kind':kind})
                        if isinstance(imported,str) and imported in provided and provided[imported]['forwarder']:forwarders.append({'from':dep,'symbol':imported,'target':provided[imported]['forwarder']})
        verify(entries)
        closure={'schema':'heterospec.e04.isolated-module-disk-closure.v2','status':'PASS_STATIC_PE_NAME_CLOSURE_NATIVE_UNQUALIFIED' if not missing else 'FAIL_STATIC_PE_NAME_CLOSURE','directory':str(OUT),'modules':{n:{'path':str(paths[n]),'bytes':r['bytes'],'sha256':r['sha256'],'imports':r['imports'],'delay_imports':r['delay_imports'],'TLS_directory_present':r['TLS_directory_present'],'provenance':staged['modules'].get(n,{}).get('prior_contract_identity',proposed['classification'] if n=='vcomp140.dll' else 'NEW_FRESH_NUMERICAL_BINARY_NOT_NATIVE_QUALIFIED')} for n,r in pe.items()},'non_system_symbol_checks':symbols,'missing':missing,'forwarded_imports_not_executed':forwarders,'external_system_and_API_set_imports':sorted(external),'same_directory_and_module_policy_for_arms':['A','B','C'],'prior_contract_pin_scope':'base/cudart/cublas/Lt match both previous exact loop4/packed pins; MSVC matches old entry disk only; VCOMP prior identity UNKNOWN','VCOMP_classification':proposed['classification'],'semantic_ABI_and_numerical_compatibility':'NOT_RUN; PE name match is insufficient','dynamic_driver_plugin_API_set_resolution':'NOT_RUN','actually_loaded_modules':None,'expected_modules_are_disk_bindings_only':True,'runtime_ready_or_native_admission':'NOT_CLAIMED; NATIVE_BLOCKED','normal_numeric_DLL_loads':0,'GPU_launches':0,'model_requests':0,'volume':volume(OUT),'pre_and_posthash_equal_under_own_read_locks':True}
        put(OUT/'MODULE_CLOSURE_v2.json',closure)
    need(not missing,'incomplete import/export disk closure; receipt retained')
    host_path=HERE/'HOST_ARTIFACTS_v4.json';host=json.loads(host_path.read_bytes());need(all(sha(p['path'])==p['sha256'] for p in host['PEs']),'frontend EXE changed before binding')
    manifests=[HERE/'SOURCE_IDENTITY_v4.json',HERE/'recovery-v1/BUILD.json',HERE/'recovery-v1/FREEZE.json',HERE/'recovery-v1/POSTFREEZE.json',host_path,compile_path,ROOT/'runtime/build-v2/COMPILE_RECEIPTS.json',ROOT/'runtime/build-v2/DEPENDENCY_CLOSURE.json',ROOT/'e04/freeze/v2/FREEZE.json',link_path,ROOT/'e04/freeze/link-v3/FREEZE.json',OUT/'STAGED_DEPENDENCIES.json',OUT/'PROPOSED_VCOMP_IDENTITY.json',OUT/'MODULE_CLOSURE_v2.json']
    value={'schema':'heterospec.e04.frontend-numeric-artifact-binding.v2','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'binding_kind':'EXTERNAL_DISK_ARTIFACT_ONLY','bound_manifests':{str(p):sha(p) for p in manifests},'frontends':[{k:p[k] for k in ('core','path','sha256')} for p in host['PEs']],'numeric_DLL':{'source':str(source),'staged':str(target),'sha256':EXPECTED,'bytes':target.stat().st_size},'module_directory':str(OUT),'module_closure_sha256':sha(OUT/'MODULE_CLOSURE_v2.json'),'compile_link_provenance':{'frontend':'separate successful loop4 v4 and packed recovery-v1 lock sessions','numerical':'145 fresh v2 TUs+actual header closure PASS; failed v2 link retained; separate frozen link-v3 PASS','uninterrupted_compile_link_freeze':False,'e03_objects_reused_in_numeric_DLL':0},'prior_VCOMP_identity':'UNKNOWN; proposed module not same-contract qualified','source_toolchain_binding_is_not_runtime_qualification':True,'native_release':'BLOCKED','expected_loaded_module_policy_for_arms':['A','B','C'],'actually_loaded_modules':None,'numeric_DLL_OS_load':'NOT_RUN','metadata_selector_budget_exports_called':'NOT_RUN','A_B_C_route_selection':'NOT_RUN','native_qualification':'NOT_RUN','GPU_launches':0,'model_requests':0,'target_draft_rows':0,'native_GPU_seconds':0,'worker_EXE_runs':0,'compiler_output_DLL_hash_not_embedded_in_frontend':True,'artifact_assembler_sources':{str(p):sha(p) for p in (Path(__file__),HERE/'pe_identity_v2.py',HERE/'stage_modules_v1.py',HERE/'stage_proposed_vcomp_v1.py')}}
    put(HERE/'DEPLOYMENT_BINDING_v1.json',value)
    print(json.dumps({'status':'PASS_DISK_BINDING_NOT_NATIVE_QUALIFIED','modules':len(paths),'non_system_import_symbol_checks':len(symbols),'normal_numeric_DLL_loads':0,'native_release':'BLOCKED'}))
if __name__=='__main__':main()
