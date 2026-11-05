"""Retain capacity stop, all attempts and portable driver inputs; no model run."""
from host import *
import re,sqlite3
def prepare():
 history=ROOT/'historical';history.mkdir()
 for role,name in [('shared-01','candidate'),('original-final','original')]:
  shutil.copyfile(OLD/role/'FILES.json',history/(name+'-FILES.json'))
  shutil.copyfile(OLD/role/'kit/b570_producer_consumer_boundary_v1/native/boundary.cpp',history/(name+'-boundary.cpp'))
 shutil.copyfile(OLD/'FREEZE.json',history/'FREEZE.json')
 smol=Path('C:/hs/jsa-b570-run-v1');models=read(smol/'MODEL_CHOICE.json')['models']
 smol_pins=[]
 for role,f in models.items():
  p=Path(f['path']);assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256']
  smol_pins.append(dict(role=role,path=str(p),bytes=f['bytes'],sha256=f['sha256']))
 bindings=read(smol/'BINARY_BINDINGS.json')
 for name,pin in bindings.items():
  if name.startswith('bin/original/'):assert sha(smol/name)==pin['sha256']
 write(ROOT/'SMOL_INSPECTION.json',dict(models=smol_pins,model_choice_sha256=sha(smol/'MODEL_CHOICE.json'),original_runtime_manifest_sha256=sha(smol/'BINARY_BINDINGS.json'),original_source_sha256=sha(smol/'source/pr63-original-front/native.cpp'),draft_prefill='whole prompt in one observer.decode call at native.cpp:221',lifecycle='resident reset loop; distinct from PR165 fresh contexts',status='AVAILABLE_SEPARATELY_REFERENCED_INSPECTED_NOT_EXECUTED',disposition='Qwen lane closes at its mandatory C1U1 capacity failure. No secondary Smol campaign opened; the B570 protocol explicitly permits stopping. No model download, new reference substitution or relabeled Qwen pass.'))
 portable=ROOT/'portable';portable.mkdir()
 for label,api,libs in [('original',ORACLE/'clean-source2/llama.cpp-0cae43063cf15170e91a2ff4d034da0ecef4a1b2',ORACLE/'build'),('candidate',OLD/'source-01',OLD/'build-01')]:
  dest=portable/'api'/label
  for sub in ('include','ggml/include','vendor/nlohmann'):shutil.copytree(api/sub,dest/sub)
  for rel in ('runtime/src/Release/llama.lib','runtime/ggml/src/Release/ggml.lib','runtime/ggml/src/Release/ggml-base.lib'):
   out=portable/'libs'/label/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(libs/rel,out)
 repro=ROOT/'repro';shutil.copytree(HERE,repro/'host',ignore=shutil.ignore_patterns('__pycache__','evidence'))
 shutil.copytree(TOOLKIT,repro/'toolkit',ignore=shutil.ignore_patterns('__pycache__'))
 write(ROOT/'GATE_DISPOSITION.json',dict(utc=utc(),status='G0_QWEN_C1024_RESOURCE_BLOCKED',required_baseline='C1U1',mandatory_controls=['M','C1U1','C4U1'],compiled_arms=['R','C1U1','C4U1','C4U2','C4U4'],roster_not_pruned_for_performance=True,inputs_screened_by_output_or_performance=0,new_input_outputs=0,old_reference_bridge='NOT_RUN_GATED_BY_DUAL_CONTEXT_ADMISSION',trained_model_qualification='NOT_RUN_GATED_BY_C1U1_RESOURCE_FAILURE',pilot='NOT_RUN_GATED',confirmation='NOT_RUN_GATED',default_confirmation_requests=600,confirmation_slots_materialized=0,optional_wide_arms='BUILT; NOT_RUN_GATED; no numerical/performance exclusion claimed',smol='INSPECTED; no secondary campaign opened',scientific_stop_rule='protocols/B570.md: if M/C1U1 cannot run safely, close Qwen lane; separately referenced Smol or stop',no_capacity_context_or_residency_change=True))
def audit(root):
 root=Path(root);auth=read(root/'AUTHENTICATION.json');rows=[];owned=0
 history=root/'historical'
 assert sha(history/'candidate-boundary.cpp')==auth['worker_sha256']
 assert sha(history/'FREEZE.json')==auth['inherited_freeze_sha256']
 for unit in sorted((root/'units').iterdir()):
  sup=read(unit/'SUPERVISOR.json');n=read(unit/'native/result.json');receipt=read(unit/'RECEIPT.json')
  assert sup['assigned_before_resume'] and sup['cleanup_verified'] and sup['job_accounting']['active_processes']==0
  assert n['requests']==[] and n['status']=='STOPPED_FIRST_FAILURE' and receipt['success'] is False
  role=unit.name.removeprefix('admit-');manifest=read(root/role/'FILES.json')
  assert sha(root/role/'FILES.json')==sup['manifest_sha256']
  observed={Path(x['path']).name.lower():x['sha256'] for x in sup['loaded_module_hashes']}
  original=read(history/('original-FILES.json' if role.startswith('R') else 'candidate-FILES.json'))
  old={Path(f['path']).name.lower():f['sha256'] for f in original['files']}
  for f in manifest['files']:
   p=root/role/'build/bin/Release'/Path(f['path']).name
   assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256']
   if p.suffix.lower()=='.dll':assert observed[p.name.lower()]==f['sha256']==old[p.name.lower()]
  text=(unit/'SUPERVISOR.stderr.log').read_text(encoding='utf-8',errors='replace')
  budgets=[dict(zip(('heap','physical','budget','usage','signed_remaining'),map(int,m))) for m in re.findall(r'HS_BUDGET heap=(\d+) physical=(\d+) budget=(\d+) usage=(\d+) signed_remaining=(-?\d+)',text)]
  for b in budgets:assert b['budget']<=b['physical'] and b['signed_remaining']==b['budget']-b['usage']
  if role.endswith('budget01'):assert budgets and budgets[-1]['signed_remaining']<0 and n['error']=='128 MiB device reserve'
  owned+=receipt['owned_seconds'];rows.append(dict(unit=unit.name,phase='zero_forward_admission',status=n['status'],error=n['error'],budgets=budgets,owned_seconds=receipt['owned_seconds'],native_requests=0,cleanup=True))
 assert len(rows)==3
 cleanup=read(root/'CLEANUP_PROOF.json');assert cleanup['status']=='ACTUAL_DESCENDANT_CLEANUP_PASS'
 for c in cleanup['cases']:assert c['accounting']['active_processes']==0 and 2<=c['accounting']['total_processes']<=4
 db=sqlite3.connect(root/'ledger.sqlite');ledger=db.execute('select id,requests,token_rows,operators,status from attempts order by id').fetchall();db.close()
 assert len(ledger)==3 and all(x[1:4]==(0,0,0) and x[4]=='FAILED' for x in ledger)
 costs=[]
 for p in sorted(root.glob('*/*.log.cost.json')):costs.append(dict(path=p.relative_to(root).as_posix(),**read(p)))
 return dict(status='CAPACITY_FAILURE_AND_CLEANUP_RECONSTRUCTED',original_numerical_dlls_unchanged=True,zero_forward_attempts=rows,native_admission_owned_seconds=owned,decoded_model_requests=0,decoded_token_rows=0,operator_replays=0,ledger=ledger,build_costs=costs,build_wall_seconds=sum(x['wall_seconds'] for x in costs),qualification_pilot_and_confirmation_not_run=True,qualification_or_performance_claim=False,gate=read(root/'GATE_DISPOSITION.json'))
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 else:print(json.dumps(audit(sys.argv[2]),indent=2))
