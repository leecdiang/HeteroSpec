"""CPU-reviewed F0 candidate only. This file cannot authorize or execute native collection."""
from pathlib import Path
from pinned_sources import *

def create():
 plan=read(ROOT/'PLAN.json');asset=read(ROOT/'ASSET_RECEIPT.json');bindings=[];seen=set()
 def bind(p,scope,pin=None):
  p=Path(p);name=str(p.resolve())
  if name in seen:return
  seen.add(name);size=p.stat().st_size;h=sha(p);require(pin is None or (size==pin['bytes'] and h==pin['sha256']),'candidate binding does not match frozen baseline');bindings.append({'path':name,'bytes':size,'sha256':h,'scope':scope})
 for p in sorted(ROOT.rglob('*')):
  if p.is_file() and p.name not in ('F0_CANDIDATE.json','F0_READBACK.json'):bind(p,'V2_CPU_SOURCE_PLAN_REGISTRY_ACTUAL_REQUEST_AUDIT')
 for p in REFS['source_modules'].values():bind(p['path'],'PINNED_EXTERNAL_SOURCE')
 for pin in read(ROOT/'ANALYSIS_RUNTIME.json')['bindings']:bind(pin['path'],'CPU_ANALYSIS_RUNTIME',pin)
 for p in asset['bindings']:bind(p['path'],'EXTERNAL_FROZEN_ACTOR_MODEL_RUNTIME',p)
 for c in plan['cells']:
  for pin in (c['mixture_spec'],c['initial_logits_spec']):bind(pin['path'],'EXTERNAL_FIXED_PR103_INPUT',pin)
 receipt=read(ROOT/'SUBPACKAGE_RECEIPT.json');bind(receipt['archive_path'],'LOCAL_PRIVATE_SELECTED_NUMERIC_SUBPACKAGE',{'bytes':receipt['archive_bytes'],'sha256':receipt['archive_sha256']})
 original=read(Path(REFS['old_run'])/'F0.json');f={'schema':2,'status':'CPU_REVIEWED_CANDIDATE_NOT_EXECUTION_AUTHORIZATION','new_native_authorized':False,'author_budget_approval':'PENDING','new_execution_F0_approval':'PENDING','study_namespace':'b570-decision-frontier-v2','candidate_run_NOT_CREATED':REFS['candidate_run'],'fixed_baselines':{k:REFS[k] for k in ('fixed_PR105','old_F0','PR103','PR103_registration','PR101')},'bindings':bindings,'semantic_admission_receipt_sha256':sha(ROOT/'ADMISSION_RECEIPT.json'),'actual_requests_sha256':sha(ROOT/'ACTUAL_REQUESTS.json'),'actual_request_summaries_sha256':sha(ROOT/'ACTUAL_REQUEST_SUMMARIES.json'),'registry_sha256':sha(ROOT/'REGISTRY.json'),'plan_sha256':sha(ROOT/'PLAN.json'),'code_sha256':{p.name:sha(p) for p in ROOT.glob('*.py')},'source_identity_pins':REFS['source_modules'],'driver_identity':asset['driver_identity'],'driver_module_pins':original['driver_module_pins'],'scientific_design':'same four tasks/two recipients/seven states/endpoints/cuts/order and numerical recipe as fixed v1 plan; no donor resampling','requested_new_budget':{'starts':168,'stage_counts':[16,32,40,80],'owned_seconds':21600,'new_output_bytes':4*1024**3,'extra_probes':0,'warmups':0,'retries':0},'old_v1_retained_cost':{'starts':1,'processes':1,'target_decode_calls':127,'owned_seconds':12.437999999994645,'qualified_scientific_comparisons':0,'unstarted_slots':167},'combined_if_author_approves_new_v2':{'starts_max':169,'owned_seconds_max':21612.438},'counts_heavy_contract':'counts memory.json; heavy trace.json + exact planned full captures; native source/import/reserialization/endpoint gate retained','execution_prerequisites':['EXPLICIT_AUTHOR_APPROVAL_NEW_BUDGET_AND_NEW_EXECUTION_F0','authenticated new execution F0 byte readback plus semantic checks','fresh workers no native probes/warmups/retries','actual loaded model/worker/DLL/driver/recipe/offload/memory gate','only-owned PID watchdog for21600s and4GiB gate','actual admitted object directly sent; no registry reread','all anchor controls must qualify before subsets'],'remote_subset_delivery':'REMOTE_PENDING','independent_machine':'NOT_PERFORMED'};write(ROOT/'F0_CANDIDATE.json',f);print('CPU_F0_CANDIDATE',len(bindings),'NO_NATIVE_AUTHORIZATION')
if __name__=='__main__':create()
