"""Read-only reconstruction, using delivered bytes with no original-host fallback.

Invoke as: python RESTORED/repro/recovery/smol_audit.py RESTORED
"""
import os,sys
if __name__=='__main__':os.environ['HS_DECISIVE_ROOT']=sys.argv[1]
from smol_verify import *
from smol_forced import check as historical_check
from smol_timing import register
from smol_population import recompute as population_recompute
from analyze import analyze
import re,sqlite3

def local(value):
 parts=PureWindowsPath(str(value)).parts
 assert 'b570-decisive-20261105' in parts,'External raw path in audit'
 p=ROOT.joinpath(*parts[parts.index('b570-decisive-20261105')+1:])
 assert ROOT.resolve() in p.resolve().parents
 return p

def inspect_units(parent,kind):
 rows=[]
 for unit in sorted(parent.iterdir()):
  if not unit.is_dir():continue
  p=unit/'SUPERVISOR.json';assert p.exists(),unit
  s=read(p);receipt=read(unit/'RECEIPT.json');assert s['cleanup_verified'] and s['job_accounting']['active_processes']==0 and s['assigned_before_resume']
  assert s['status'] in ('complete','failed') and receipt['success']==(s['status']=='complete')
  m=local(read(unit/'COMMAND.json')[read(unit/'COMMAND.json').index('--manifest')+1])
  assert sha(m)==s['manifest_sha256']
  expected={}
  for f in read(m)['files']:
   path=local(f['path']);assert path.stat().st_size==f['bytes'] and sha(path)==f['sha256']
   expected[PureWindowsPath(f['path']).name.lower()]=f['sha256']
  observed={PureWindowsPath(f['path']).name.lower():f['sha256'] for f in s['loaded_module_hashes']}
  assert all(observed[k]==v for k,v in expected.items() if k.endswith('.dll') and k in observed)
  if kind=='smol' and unit.name.startswith('campaign02-') and s['status']=='complete':
   required={'llama.dll','llama-common.dll','ggml.dll','ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll'}
   assert required<=observed.keys() and all(observed[k]==expected[k] for k in required)
  row=dict(unit=unit.name,status=s['status'],requests_reserved=read(unit/'RESERVATION.json')['requests'],rows_reserved=read(unit/'RESERVATION.json')['token_rows'],owned_seconds=receipt['owned_seconds'],native_seconds=s['charged_seconds'],supervisor_source_sha256=s.get('supervisor_source_sha256'),provisioning_to_ready_seconds=s.get('provisioning_to_ready_seconds'),provisioning_observation_resolution_seconds=s.get('poll_seconds'),cleanup=True)
  if kind=='qwen':
   n=read(unit/'native/result.json');assert n['status']=='STOPPED_FIRST_FAILURE' and not n['requests'] and not receipt['success'] and row['requests_reserved']==0
   logs='\n'.join(x.read_text(errors='replace') for x in unit.glob('SUPERVISOR.*.log'))
   budgets=[]
   for match in re.finditer(r'HS_BUDGET heap=(\d+) physical=(\d+) budget=(\d+) usage=(\d+) signed_remaining=(-?\d+)',logs):
    heap,total,budget,usage,remaining=map(int,match.groups());assert remaining==budget-usage and 0<budget<=total
    budgets.append(dict(heap=heap,physical=total,budget=budget,usage=usage,signed_remaining=remaining))
   row.update(error=n.get('error'),budget_observations=budgets,forwards=0)
  rows.append(row)
 return rows

def audit():
 assert ROOT.is_dir() and SROOT.is_dir() and not LOCK.exists(),'Native work must be quiescent'
 qwen=inspect_units(ROOT/'units','qwen');smol=inspect_units(SROOT/'units','smol')
 assert len(qwen)==5 and all(x['status']=='failed' for x in qwen)
 pin=read(SROOT/'AUTHENTICATION.json');historical=read(SROOT/'provenance/BINARY_BINDINGS.json')
 for name,item in historical.items():
  if name.startswith('bin/original/'):assert sha(SROOT/'original-runtime'/PureWindowsPath(name).name)==item['sha256']
 profile=read(SROOT/'STATE_PROFILE.json')
 assert profile['writer_sha256']==sha(SROOT/'provenance/src/llama-kv-cache.cpp') and profile['layer_map_source_sha256']==sha(SROOT/'provenance/src/llama-hparams.h') and profile['target_model_sha256']==pin['models'][0]['sha256']
 r=read(SROOT/'old-R-0-capture.json');gold=read(SROOT/'historical/original-R-0-capture.json');assert r==gold
 observed=read(SROOT/'observer-R-0-capture.json');assert all(r[k]==observed[k] for k in ('prompt_ids','ids','eog','commits'))
 h=historical_check(False);assert h==read(SROOT/'QUALIFICATION-0.json') and h['status']=='FINITE_NATIVE_CAPTURE_MATCH'
 a=read(SROOT/'qual02-0-heavy-capture.json')['committed_states'][-1];b=read(SROOT/'qual02-0-off-capture.json')['committed_states'][-1];assert state_equal(a,b)
 old_native=read(SROOT/'old-N-k1-0-capture.json');assert old_native['ids']==r['ids'] and old_native['eog']==r['eog'] and old_native['commits'][0]['scores']!=r['commits'][0]['scores']
 qualifications=[]
 for group,count in (('development',4),('test',12)):
  prefix='dev' if group=='development' else 'test'
  for index in range(count):
   path=SROOT/EPOCH/f'{prefix}-{index}-QUALIFICATION.json'
   if not path.exists():continue
   actual=check(group,index,False);assert actual==read(path);qualifications.append(dict(group=group,index=index,report=actual))
 selected=read(SROOT/'cohort/PANEL.json');extra=read(SROOT/'cohort/EXPOSURE_SUPPLEMENT.json')
 roots={x['root_id'] for group in ('development','test') for x in selected[group]}
 assert len(roots)==16 and not roots&set(extra['additional_authenticated_roots']) and not roots&set(selected['excluded_roots'])
 population=population_recompute();assert population==read(SROOT/'cohort/POPULATION_RECOMPUTATION.json')
 ledger=sqlite3.connect('file:'+str(ROOT/'ledger.sqlite').replace('\\','/')+'?mode=ro',uri=True)
 try:
  from common import digest
  assert ledger.execute("select v from meta where k='limits'").fetchone()[0]==digest(LIMITS)
  reservations=[dict(zip(('unit','status','requests','token_rows','operators'),x)) for x in ledger.execute('select id,status,requests,token_rows,operators from attempts order by id')]
 finally:ledger.close()
 assert not any(x['status'] not in ('COMPLETE','FAILED') for x in reservations)
 totals={k:sum(x[k] for x in reservations) for k in LIMITS};assert all(totals[k]<=LIMITS[k] for k in LIMITS)
 assert totals['requests']==sum(x['requests_reserved'] for x in qwen+smol) and totals['token_rows']==sum(x['rows_reserved'] for x in qwen+smol)
 pilot=None;pp=SROOT/EPOCH/'PILOT.json'
 if pp.exists():
  pilot=read(pp);assert len(pilot['records'])==48 and pilot['measurements']==pilot['warmups']==24 and {x['arm'] for x in pilot['records']}==set(ARMS)
  for x in pilot['records']:
   index=next(i for i,r in enumerate(selected['development']) if r['root_id']==x['root_id']);j=0 if x['kind']=='warmup' else 1
   path=SROOT/EPOCH/'runs'/f"pilot-{index}-{x['arm']}"/(str(j)+'.json.metrics.json');assert sha(path)==x['metrics_sha256'] and read(path)['service_ms']/1000==x['service_s']
 main=None;mechanisms={};boundaries={};post_panel=None;rp=SROOT/EPOCH/'RECORDS.json'
 if rp.exists():
  register();records=read(rp);main=analyze(selected,'b570-smol-draft',records);assert main==read(SROOT/EPOCH/'ANALYSIS.json')
  expected=read(SROOT/'cohort/SCHEDULE.json')['slots'];assert len(expected)==len(records['records'])==864 and len([x for x in qualifications if x['group']=='test'])==12
  for x in records['records']:
   ix=next(i for i,r in enumerate(selected['test']) if r['id']==x['input_id']);j=0 if x['kind']=='warmup' else 1
   folder=SROOT/EPOCH/'runs'/f"main-s{x['session']}-r{ix}-{x['arm']}";path=folder/(str(j)+'.json.metrics.json');raw=read(folder/(str(j)+'.json'));ref=read(SROOT/EPOCH/'runs'/f'test-{ix}-oldR/0.json')
   assert sha(path)==x['metrics_sha256'] and read(path)['service_ms']/1000==x['service_s'] and (raw['ids'],raw['eog'])==(ref['ids'],ref['eog'])
  frozen=read(SROOT/EPOCH/'FREEZE.json');published=read(SROOT/EPOCH/'PUBLISHED_FREEZE.json')
  assert published['freeze_sha256']==sha(SROOT/EPOCH/'FREEZE.json') and published['remote_readback_equal']
  for proof in frozen['source_proofs']:assert sha(ROOT/proof['snapshot'])==proof['sha256']
  for path,hsh in frozen['native_source_proofs'].items():assert sha(ROOT/path)==hsh
  for name,hsh in frozen['data_proofs'].items():assert sha(SROOT/'cohort'/name)==hsh
  for arm,hsh in frozen['binary_manifest_sha256'].items():assert sha(SROOT/EPOCH/arm/'FILES.json')==hsh
  supervisor_pin=next(x['sha256'] for x in frozen['source_proofs'] if PureWindowsPath(x['path']).name=='supervisor.py')
  assert all(x['supervisor_source_sha256']==supervisor_pin for x in smol if x['unit'].startswith(('campaign02-test-','campaign02-main-')))
  # Post-timing reader checks add no model requests or measurement slots.
  from smol_mechanism import mechanism
  from smol_boundaries import campaign as boundary_campaign
  for group,count in (('development',4),('test',12)):
   mechanisms[group]=json.loads(json.dumps(dict(roots=[mechanism(group,i) for i in range(count)])))
   boundaries[group]=boundary_campaign(group)
   assert mechanisms[group]==read(SROOT/EPOCH/('MECHANISM-'+group+'.json'))
   assert boundaries[group]==read(SROOT/EPOCH/('BOUNDARIES-'+group+'.json'))
  post_panel=read(SROOT/EPOCH/'POST_PANEL_SOURCE_BINDING.json')
  assert post_panel['freeze_sha256']==sha(SROOT/EPOCH/'FREEZE.json') and post_panel['records_sha256']==sha(rp) and post_panel['analysis_sha256']==sha(SROOT/EPOCH/'ANALYSIS.json')
 # Cost ledgers are additive across every epoch. Coordinator elapsed times include
 # child time and are disclosed separately, never added to native totals twice.
 costs=dict(reserved=totals,ceilings=LIMITS,native_process_seconds=sum(x['native_seconds'] for x in qwen+smol),owned_worker_seconds=sum(x['owned_seconds'] for x in qwen+smol),failed_native_units=[x['unit'] for x in qwen+smol if x['status']=='failed'],model_requests_include_failed_warm_and_forced=True,operator_replays=totals['operators'],initial_CPU_preparation_and_early_packing_not_separately_metered=True,all_initial_v1_costs_retained=True)
 costs['post_timing_mechanism_boundary_aggregation_not_separately_wall_metered']=True
 stages={}
 for row in qwen+smol:
  phase='qwen-zero-forward' if row in qwen else 'confirmation' if row['unit'].startswith('campaign02-main-') else 'pilot' if row['unit'].startswith('campaign02-pilot-') else 'offline-test-qualification' if row['unit'].startswith('campaign02-test-') else 'offline-development-qualification'
  stage=stages.setdefault(phase,dict(requests_reserved=0,rows_reserved=0,owned_seconds=0,native_seconds=0,observed_provisioning_seconds=0,provisioning_units_not_separately_metered=0))
  for key in ('requests_reserved','rows_reserved','owned_seconds','native_seconds'):stage[key]+=row[key]
  if row['provisioning_to_ready_seconds'] is None:stage['provisioning_units_not_separately_metered']+=1
  else:stage['observed_provisioning_seconds']+=row['provisioning_to_ready_seconds']
 costs['by_stage']=stages
 builds={}
 for p in sorted(ROOT.rglob('*.cost.json')):
  if 'repro' in p.relative_to(ROOT).parts or 'source-freeze' in p.parts:continue
  v=read(p)
  if 'wall_seconds' in v:builds.setdefault(sha(p),v)
 costs['retained_build_command_seconds']=sum(builds[h]['wall_seconds'] for h in sorted(builds));costs['retained_build_commands']=len(builds)
 costs['CPU_coordinator_receipts_are_inclusive_not_additive']=True
 costs['initial_v1_delivery']=read(HERE/'evidence/DELIVERY_COSTS.json')
 streams=[read(p) for p in sorted((SROOT/EPOCH/'runs').glob('*/STREAM_STORAGE.json'))]
 assert all(x['thread_stopped'] and not x['error'] for x in streams)
 costs['streamed_storage']=dict(units=len(streams),packing_wall_seconds=sum(x['packing_seconds'] for x in streams),post_native_drain_seconds=sum(x.get('post_native_drain_seconds',0) for x in streams),overlaps_native_not_additive=True)
 return dict(status='COMPLETE_RESTORED_SECONDARY_PANEL' if main else 'PARTIAL_NATIVE_RECOVERY_RECONSTRUCTED',qwen_status='G0_MANDATORY_CONTROL_CAPACITY_FAILURE_RETAINED',qwen_attempts=qwen,historical_Smol=h,population=population,qualifications=qualifications,pilot=pilot,main_analysis=main,mechanisms=mechanisms,boundaries=boundaries,post_panel_source_binding=post_panel,costs=costs,all_native_units=qwen+smol,raw='Full vectors plus byte-exact reconstructible sequence states; failed raw attempts retained; no weights',external_native_replication=False)

if __name__=='__main__':print(json.dumps(audit(),indent=2))
