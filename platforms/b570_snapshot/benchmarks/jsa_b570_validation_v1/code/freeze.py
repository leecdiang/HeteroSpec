import shutil,json,hashlib,time
from pathlib import Path
from prepare import R,REPO,PLAN,load,save,sha
from initialize import make_spec
assert load(R/'A_VERIFICATION.json')['status']=='PASS';assert load(R/'TOKENIZATION_BINDINGS.json')['status']=='PASS'
design=load(PLAN/'DESIGN.json');assert load(R/'EXPOSURE_AUDIT.json')['status']=='PASS'
schedule=load(R/'REQUEST_SCHEDULE.json');save('A_REQUEST_SCHEDULE.json',schedule['A'])
schedule['B']=[make_spec('B',a,k,False,'Smol','SMOL_DISCOVERY_INPUTS.json',range(12)) for k in [0,1] for a in ['R','N','M','C']]
schedule['B'] += [make_spec('B',a,k,k==3,'Smol','SMOL_DISCOVERY_INPUTS.json',range(4)) for k in [2,3] for a in ['R','N','M','C']]
schedule['D']=[]
for k,arms in enumerate(design['stages']['D_confirmation']['condition_order']):
 off=[0,6,12,18][k];indices=list(range(24))[off:]+list(range(24))[:off]
 for a in arms:schedule['D'].append(make_spec('D',a,k,False,'Smol','SMOL_CONFIRMATION_INPUTS.json',indices,warm=True))
assert sum(not q['warm'] for s in schedule['B'] for q in s['requests'])==128
assert len(schedule['D'])==16 and sum(not q['warm'] for s in schedule['D'] for q in s['requests'])==384
assert sum(q['warm'] for s in schedule['D'] for q in s['requests'])==16
save('REQUEST_SCHEDULE.json',schedule)
save('NATURAL_BRANCH_PLAN.json',dict(rule=design['stages']['C_optional_natural_cross'],selection='First at most two locked discovery tasks with R/N or R/C endpoint divergence, in locked order. No additional task search.',actual_checkpoint_interfaces='Inherited PR63/PR64 exact binaries expose prefill transfer or phase binding, but neither exposes naturally aligned N/C continuation checkpoint/resume. If triggered, UNSUPPORTED_NATURAL_RESTORATION; do not replace their paths with teacher-prefill or unqualified IO port. If no trigger, NO_TRIGGER.',checkpoint_auxiliary_decode_starts=0,donor_full_request_starts=0,new_generation_binary_changes=0))
public=REPO/'benchmarks/jsa_b570_validation_v1';shutil.copytree(public/'code',R/'code',dirs_exist_ok=True)
shutil.copytree(PLAN,R/'plan',dirs_exist_ok=True)
files={}
names=['MODEL_CHOICE.json','QWEN_MODELS.json','TOKENIZATION_BINDINGS.json','SMOL_DISCOVERY_INPUTS.json','SMOL_CONFIRMATION_INPUTS.json','REQUEST_SCHEDULE.json','EXPOSURE_AUDIT.json','EXPOSURE_CATALOG.json','BINARY_BINDINGS.json','SOURCE_BINDINGS.json','TIMER_BINDINGS.json','NATURAL_BRANCH_PLAN.json','A_HISTORY_BINDING_AMENDMENT.json','HISTORICAL_OWN_PATH.json']
for name in names:files[name]=dict(sha256=sha(R/name),bytes=(R/name).stat().st_size)
for folder in ['code','plan','remote']:
 for p in (R/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:files[p.relative_to(R).as_posix()]=dict(sha256=sha(p),bytes=p.stat().st_size)
save('F0.json',dict(schema='heterospec.jsa.b570.F0.v1',status='FROZEN_BEFORE_ANY_SMOL_FORWARD',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),plan_head='0a95a64805536323b0e8ae11784eaab150f91dcf',result_pr=82,frozen_files=files,models=load(R/'MODEL_CHOICE.json'),limits=design['limits'],confirmation_tasks=24,formal_requests=384,formal_warm=16,formal_sessions=16,engineering_requests=160,conditional_natural_plan='NATURAL_BRANCH_PLAN.json',auxiliary_decode_starts=0,implicit_forwards=0,first_smol_forward_utc=None))
for name in names+['F0.json','A_REQUEST_SCHEDULE.json','CONFIRMATION_RAW_INPUTS.json']:
 if name=='EXPOSURE_CATALOG.json':continue # bulky mechanical catalog remains CAS
 shutil.copyfile(R/name,public/name)
shutil.copytree(R/'remote',public/'remote',dirs_exist_ok=True)
print('F0 frozen before Smol; 160 engineering +384 formal +16 warm; all formal order locked',flush=True)
