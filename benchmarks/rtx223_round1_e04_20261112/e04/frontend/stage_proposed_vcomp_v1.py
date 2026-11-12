from pathlib import Path
import hashlib,json,shutil,datetime
from pe_identity_v2 import inspect
HERE=Path(__file__).resolve().parent
source=Path('C:/Windows/System32/vcomp140.dll');target=HERE/'expected-modules-v1/vcomp140.dll'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before=sha(source)
if target.exists():raise RuntimeError('do not overwrite staged module')
shutil.copy2(source,target)
if sha(source)!=before or sha(target)!=before:raise RuntimeError('proposed source or copy changed')
value={'schema':'heterospec.e04.proposed-module-identity.v1','classification':'PROPOSED_NEW_MODULE_IDENTITY_NOT_NATIVE_QUALIFIED','module':'vcomp140.dll','source':str(source),'staged':str(target),'sha256':before,'bytes':target.stat().st_size,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'PE':inspect(target),'reason':'pinned ggml-base.dll imports vcomp140.dll; prior contract audit has no VCOMP hash and old worker directories do not contain it','prior_loaded_module_identity':'UNKNOWN_NOT_RECORDED','exact_prior_contract_equivalence':'NOT_ESTABLISHED','same_proposal_for_arms':['A','B','C'],'native_release':'BLOCKED','normal_numeric_DLL_loads':0,'GPU_launches':0,'model_requests':0}
with (HERE/'expected-modules-v1/PROPOSED_VCOMP_IDENTITY.json').open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,indent=2)
print(json.dumps({'status':value['classification'],'sha256':before,'imports':value['PE']['imports'],'delay_imports':value['PE']['delay_imports'],'DLL_loads':0}))
