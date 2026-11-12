"""Identity receipt checks with independent expected bindings; never admits GPU work."""
from pathlib import Path
import hashlib

class BindingRefusal(ValueError):pass
def need(ok,message):
    if not ok:raise BindingRefusal(message)
def check_identity(expected,receipt):
    required={'arm','linked_graph_core','graph_policy','exe_sha256','job_sha256','runtime_directory','modules','runtime_metadata','provider_scope'}
    need(set(expected)==required,'independent complete identity contract required')
    arm=expected['arm'];need(arm in ('A','B','C'),'bad frozen arm')
    need(expected['linked_graph_core']==('loop4' if arm=='A' else 'packed'),'frozen core/arm mismatch')
    need(expected['graph_policy']=='disabled_for_all_arms_draft_and_reference','common graph policy missing')
    for field in ('arm','linked_graph_core','graph_policy','exe_sha256','job_sha256'):
        need(receipt.get(field)==expected[field],'bound field mismatch: '+field)
    need(receipt.get('actual_numeric_route_observed') is False,'identity observation cannot certify an executed numeric route')
    kind=receipt.get('observation_kind');scope=expected['provider_scope']
    need(kind in ('OFFLINE_PE','CPU_STANDIN_LOAD','NUMERICAL_METADATA_LOAD'),'unknown identity observation kind')
    if scope=='CPU_STANDIN':need(kind=='CPU_STANDIN_LOAD','CPU stand-in cannot masquerade as numerical DLL observation')
    else:need(scope=='NUMERICAL_RUNTIME' and kind!='CPU_STANDIN_LOAD','numerical runtime requires numerical/offline evidence kind')
    need(receipt.get('runtime_metadata')==expected['runtime_metadata'],'runtime metadata differs from frozen provider')
    if scope=='NUMERICAL_RUNTIME':need(expected['runtime_metadata'].get('schema')=='heterospec.e03.cuda-runtime.v1','not numerical runtime metadata')
    modules=receipt.get('modules');need(isinstance(modules,dict) and set(modules)==set(expected['modules']),'missing/extra module identity')
    directory=Path(expected['runtime_directory']).resolve()
    for name,binding in expected['modules'].items():
        path=Path(binding['path']).resolve();observed=modules[name]
        need(path.parent==directory and path.name.lower()==name.lower(),'frozen module leaves isolated directory')
        need(Path(observed['path']).resolve()==path,'old or foreign numerical DLL resolved')
        need(observed['sha256']==binding['sha256']==hashlib.sha256(path.read_bytes()).hexdigest(),'loaded-path disk hash mismatch')
    return {'identity_check':'PASS','observation_kind':kind,'provider_scope':scope,
            'numeric_DLL_load_claimed':kind=='NUMERICAL_METADATA_LOAD',
            'actual_numeric_DLL_loaded':None if kind=='NUMERICAL_METADATA_LOAD' else False,
            'OS_load_attestation':'NOT_INDEPENDENTLY_VERIFIED_BY_THIS_OFFLINE_READER',
            'actual_numeric_route_observed':False,'native_qualification':'NOT_RUN',
            'complete_vector_state_qualification':'NOT_RUN','performance_admitted':False,
            'GPU_admission':'BLOCKED_NO_AUTHENTICATED_PARENT_OR_PHYSICAL_LAUNCH_COVERAGE'}
