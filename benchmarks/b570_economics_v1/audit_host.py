"""Read-only reconstruction of this finite B570 study and its immutable PR187 bank.

Set HS_ECON_ROOT and HS_ECON_PR187 to delivered/restored roots. No native work,
model loading, reference substitution or host-path fallback is performed here.
"""
from evidence_host import *
from costs import decompose,economic_identity,scan_saved
import collections,sqlite3,re,math

_file_hashes={}
def checked_file(value,expected=None):
 p=native_path(value);st=p.stat();key=(str(p),st.st_size,st.st_mtime_ns)
 if key not in _file_hashes:_file_hashes[key]=sha(p)
 if expected is not None:assert _file_hashes[key]==expected,(str(p),expected)
 return _file_hashes[key]

def units_and_costs():
 db=sqlite3.connect('file:'+str(ROOT/'ledger.sqlite').replace('\\','/')+'?mode=ro',uri=True)
 try:ledger=[dict(zip(('unit','requests','token_rows','operators','status','code'),r)) for r in db.execute('select id,requests,token_rows,operators,status,code from attempts order by id')]
 finally:db.close()
 assert all(x['status'] in ('COMPLETE','FAILED','EXPECTED_FAILURE_VERIFIED') for x in ledger)
 totals={k:sum(x[k] for x in ledger) for k in LIMITS};assert all(totals[k]<=LIMITS[k] for k in LIMITS)
 byid={x['unit']:x for x in ledger};rows=[]
 for unit in sorted((ROOT/'units').iterdir()):
  if not unit.is_dir():continue
  reservation=read(unit/'RESERVATION.json');entry=byid[unit.name]
  assert all(reservation[k]==entry[k] for k in LIMITS)
  if not (unit/'SUPERVISOR.json').exists():
   p=read(unit/'PRELAUNCH_REJECTION.json');assert entry['status']=='FAILED' and p['status']=='PRELAUNCH_ENV_REJECTION_NO_NATIVE_PROCESS' and p['native_forwards']==0 and p['native_workers_absent']
   rows.append(dict(unit=unit.name,requests_reserved=entry['requests'],rows_reserved=entry['token_rows'],status='PRELAUNCH_REJECTED',native_seconds=0,owned_seconds=None,provisioning_to_ready_seconds=None,actual_forwards=0))
   continue
  s=read(unit/'SUPERVISOR.json');receipt=read(unit/'RECEIPT.json')
  assert s['assigned_before_resume'] and s['cleanup_verified'] and s['job_accounting']['active_processes']==0
  assert s['limit_seconds']==900 and s['progress_bound_seconds']==180 and s['ram_reserve_bytes']==2*1024**3 and s['job_memory_limit_bytes']==16*1024**3
  assert s['minimum_available_ram_bytes']>=s['ram_reserve_bytes']
  cmd=read(unit/'COMMAND.json');manifest=native_path(cmd[cmd.index('--manifest')+1]);assert sha(manifest)==s['manifest_sha256']
  files=read(manifest)['files'];expected={PureWindowsPath(x['path']).name.lower():x['sha256'] for x in files}
  for x in files:assert native_path(x['path']).stat().st_size==x['bytes'];checked_file(x['path'],x['sha256'])
  observed={PureWindowsPath(x['path']).name.lower():x['sha256'] for x in s['loaded_module_hashes']}
  required={'llama.dll','llama-common.dll','ggml.dll','ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll'}
  assert required<=observed.keys() and all(observed[k]==expected[k] for k in required)
  assert receipt['success']==(s['status']=='complete')==(entry['status']=='COMPLETE')
  text=(unit/'SUPERVISOR.stderr.log').read_text(errors='replace');budgets=[]
  for match in re.finditer(r'HS_BUDGET heap=(\d+) physical=(\d+) budget=(\d+) usage=(\d+) signed_remaining=(-?\d+)',text):
   heap,physical,budget,usage,remaining=map(int,match.groups());assert remaining==budget-usage and 0<budget<=physical and remaining>=128*1024**2
   budgets.append(remaining)
  bridge=None
  if not budgets:
   assert unit.name.startswith('forced-') and read(manifest)['source_manifest_sha256']==read(OLD_CAMPAIGN/'FREEZE.json')['forced_reference_manifest_sha256']
   bridge=next(x for x in read(ROOT/'REFERENCE_RESOURCE_BRIDGE.json')['results'] if x['original_unit']==unit.name)
   assert bridge['all_equal'] and bridge['minimum_signed_GPU_reserve_bytes']>=128*1024**2
  rows.append(dict(unit=unit.name,status=s['status'],requests_reserved=entry['requests'],rows_reserved=entry['token_rows'],native_seconds=s['charged_seconds'],owned_seconds=receipt['owned_seconds'],provisioning_to_ready_seconds=s['provisioning_to_ready_seconds'],poll_seconds=s['poll_seconds'],supervisor_sha256=s['supervisor_source_sha256'],minimum_signed_GPU_reserve_bytes=min(budgets) if budgets else None,missing_original_budget_observation_not_invented=not budgets,resource_observer_bridge_unit=bridge['resource_observer_unit'] if bridge else None,cleanup=True))
 stages={}
 for x in rows:
  name=x['unit'];stage='original-R-forced' if name.startswith('forced-') else 'original-R-resource-observer' if name.startswith('resource-ref01-') else 'A1-qualification' if name.startswith('a1-qual-') else 'A1-timing' if name.startswith(('a1-time-','a1-sync-')) else 'known-mechanism' if name.startswith('known-') else 'cap1-contract' if name.startswith('cap1-') else 'k3-protocol' if name.startswith('protocol-') else '-'.join(name.split('-')[:2])
  z=stages.setdefault(stage,dict(requests_reserved=0,rows_reserved=0,native_seconds=0,owned_seconds=0,provisioning_seconds=0,unmetered_provisioning_units=0))
  for k in ('requests_reserved','rows_reserved','native_seconds','owned_seconds'):z[k]+=x[k] or 0
  if x['provisioning_to_ready_seconds'] is None:z['unmetered_provisioning_units']+=1
  else:z['provisioning_seconds']+=x['provisioning_to_ready_seconds']
 assert totals['requests']==sum(x['requests_reserved'] for x in rows)
 assert totals['token_rows']==sum(x['rows_reserved'] for x in rows)
 streams=[read(p) for p in sorted((ROOT/'runs').glob('*/STREAM_STORAGE.json'))]
 assert all(x['thread_stopped'] and not x['error'] for x in streams)
 commands={}
 for p in sorted(ROOT.rglob('*.cost.json')):
  if 'repro' in p.relative_to(ROOT).parts:continue
  v=read(p)
  if 'wall_seconds' in v:commands.setdefault(sha(p),dict(path=str(p.relative_to(ROOT)),**v))
 return dict(reserved=totals,ceilings=LIMITS,by_stage=stages,units=rows,ledger=ledger,native_seconds=sum(x['native_seconds'] for x in rows),owned_worker_seconds=sum(x['owned_seconds'] or 0 for x in rows),streamed_storage=dict(units=len(streams),packing_seconds=sum(x['packing_seconds'] for x in streams),post_native_drain_seconds=sum(x.get('post_native_drain_seconds',0) for x in streams),overlaps_native_not_additive=True),retained_command_receipts=list(commands.values()),sum_of_retained_command_wall_seconds_including_nested=sum(x['wall_seconds'] for x in commands.values()),driver_receipts={p.name:read(p) for p in sorted((ROOT/'driver-costs').glob('*.json'))},failed_reservations=[x for x in ledger if x['status']=='FAILED'],no_refunds=True,old_reserved_unchanged=dict(requests=1706,token_rows=1804796,operators=0),device_kernel_times=None,unmetered_engineering_CPU_time=None,clocks_are_not_additive=True)

def qualification(row,arm,heavy,off=None,cap1=False,known=False):
 old,ref=bank(row['group'],row['index']);a=read(heavy/'1.json')
 if not known:
  expected=dict(old,ids=old['ids'][:1],eog=old['eog'][:1]) if cap1 else old
  contract=boundaries(a,expected,arm)
  assert (a['ids'],a['eog'])==(expected['ids'],expected['eog'])
 else:contract=None
 vals=a['full_target_vectors'];states=a['committed_states'];assert vals and states
 for x in vals:
  raw=native_path(x['path']).read_bytes();assert len(raw)==49152*4 and np.isfinite(np.frombuffer(raw,dtype='<f4')).all()
  assert raw==native_path(ref[tuple(x['prefix'])]['frontier']).read_bytes()
 for x in states:assert state_equal(x,ref[tuple(x['prefix'])])
 if off is not None:
  b=read(off/'1.json');assert (a['ids'],a['eog'])==(b['ids'],b['eog']) and state_equal(states[-1],b['committed_states'][-1])
 return dict(vectors=len(vals),states=len(states),contract=contract)

def qualifications():
 inputs=read(ROOT/'EXPOSED_INPUTS.json')['inputs'];rows=[]
 for stage,methods in (('a1',('mode0','mode1','mode2')),('resident',('R',)),('parallel',('S','L'))):
  for i,r in enumerate(inputs):
   for method in methods:
    for arm in ('M','H1','C4U4')+(() if stage=='a1' else ('C4U1',)):
     key=f'a1-qual-r{i}-{arm}-m{method[-1]}' if stage=='a1' else f'{stage}-qual-r{i}-{method}-{arm}'
     h=ROOT/'runs'/(key+'-heavy');o=ROOT/'runs'/(key+'-off');q=qualification(r,arm,h,o)
     saved=read(h/'QUALIFICATION.json');assert q['vectors']==saved['conditional_vectors']==saved['equal_vectors'] and q['states']==saved['committed_states']==saved['equal_states']
     rows.append(dict(stage=stage,root=i,method=method,arm=arm,**q))
 for z in read(ROOT/'CAP1_RESULTS.json')['results']:
  key=f"cap1-{z['stage']}-{z['method']}-{z['arm']}";q=qualification(inputs[0],z['arm'],ROOT/'runs'/(key+'-heavy'),ROOT/'runs'/(key+'-off'),cap1=True)
  rows.append(dict(stage='cap1',method=z['method'],arm=z['arm'],**q))
 for z in read(ROOT/'K3_PROTOCOL_RESULTS.json')['results']:
  key='protocol-k3-'+z['method'];q=qualification(inputs[0],'H1',ROOT/'runs'/(key+'-heavy'),ROOT/'runs'/(key+'-off'))
  assert z['first_rejections']>0 and z['later_rejections']>0
  rows.append(dict(stage='k3-protocol-only',method=z['method'],**q))
 for z in read(ROOT/'KNOWN_PROBE_RESULTS.json')['results']:
  key='known-'+z['method']+'-'+z['case'];q=qualification(inputs[0],'M',ROOT/'runs'/key,known=True)
  rows.append(dict(stage='known-mechanism-only',method=z['method'],case=z['case'],**q))
 return dict(rows=rows,vectors=sum(x['vectors'] for x in rows),states=sum(x['states'] for x in rows),all_equal=True,independent_roots=4,original_R_unchanged=True)

def pilot(stage):
 result=read(ROOT/(stage.upper()+'_PILOT.json'));groups={};samples={};inputs=read(ROOT/'EXPOSED_INPUTS.json')['inputs']
 assert len(result['records'])==(64 if stage=='resident' else 128)
 for x in result['records']:
  j=0 if x['kind']=='warmup' else 1;folder=ROOT/'runs'/x['name'];p=folder/f'{j}.json.metrics.json'
  assert sha(p)==x['metrics_sha256'] and read(p)['service_ms']/1000==x['service_s']
  a=read(folder/f'{j}.json');old,_=bank(inputs[x['root']]['group'],inputs[x['root']]['index'])
  assert (a['prompt_ids'],a['ids'],a['eog'])==(old['prompt_ids'],old['ids'],old['eog'])
  key=x['method']+'_'+x['arm'];g=groups.setdefault(key,dict(measure=0.,warmup=0.,measurements=0,warmups=0,proposed=0,accepted=0))
  samples.setdefault(key,dict(measure=[],warmup=[]))[x['kind']].append(x['service_s']);g['measurements' if j else 'warmups']+=1
  if j:g['proposed']+=x['drafted'];g['accepted']+=x['accepted']
 # Match the decision's builtin sum, including Python 3.12 compensated float
 # summation; sequential += differs by one ulp on two retained arm totals.
 for key,g in groups.items():
  for kind in ('measure','warmup'):g[kind]=sum(samples[key][kind])
 assert all(x['measurements']==x['warmups']==8 for x in groups.values())
 return groups

def known_work():
 rows=[];cases=read(ROOT/'KNOWN_PROBE_PLAN.json')['cases'];prompt=len(read(ROOT/'EXPOSED_INPUTS.json')['inputs'][0]['prompt_ids'])
 for method in ('S','L'):
  for case in cases:
   key='known-'+method+'-'+case['name'];folder=ROOT/'runs'/key;request=read(folder/'JOBS.json')[1]
   extra=len(request.get('after_rollback',[]));actual=prompt+len(case['prelude'])+len(case['known_suffix'])+extra
   cost=read(folder/'1.json.cost.json');assert cost['caller_rows']==actual
   lines=(ROOT/'units'/key/'SUPERVISOR.stderr.log').read_text(errors='replace').splitlines();micro=[]
   for line in lines:
    if line.startswith('ECON_MICRO '):micro.append({k:int(v) if k not in ('ctx','kv') else v for k,v in (x.split('=',1) for x in line.split()[2:])})
   occupied=[x for x in micro if x['ub']==case['width']]
   # Includes warm and heavy request. Prelude capacity128 is excluded.
   assert sum(x['rows'] for x in occupied)==2*(len(case['known_suffix'])+extra)
   rows.append(dict(method=method,case=case['name'],actual_decoded_rows_per_request=actual,post_rollback_rows_per_request=extra,occupied=occupied,includes_warmup=True,natural_performance=False))
 return rows

def draft_observations():
 rows=[]
 for i in range(4):
  scalar=read(ROOT/'runs'/f'resident-qual-r{i}-R-H1-heavy/1.json')['draft_prefill_vectors'][0]['path'];baseline=native_path(scalar).read_bytes()
  for method in ('S','L'):
   for arm in ('H1','C4U4','C4U1'):
    capture=read(ROOT/'runs'/f'parallel-qual-r{i}-{method}-{arm}-heavy/1.json');path=capture['draft_prefill_vectors'][0]['path'];raw=native_path(path).read_bytes()
    prior=read(ROOT/'runs'/f'resident-qual-r{i}-R-{arm}-heavy/1.json')['draft_prefill_vectors'][0]['path'];old=native_path(prior).read_bytes()
    x=np.frombuffer(raw,dtype='<f4');y=np.frombuffer(baseline,dtype='<f4');assert x.size==y.size==49152 and np.isfinite(x).all()
    rows.append(dict(root=i,method=method,arm=arm,draft_frontier_equal_resident_same_arm=raw==old,draft_frontier_equal_resident_H1=raw==baseline,max_absolute_difference_from_H1=float(np.max(np.abs(x-y))),candidate_draft_values_never_used_to_filter=True))
 return rows

def reference_resource_bridge():
 proof=read(ROOT/'REFERENCE_RESOURCE_BRIDGE.json');vectors=states=0
 assert proof['status']=='ORIGINAL_R_RESOURCE_OBSERVER_BYTE_EXACT_BRIDGE_PASS' and proof['original_reference_data_not_replaced'] and proof['natural_performance_samples']==0
 for r in proof['results']:
  a=read(ROOT/'runs'/r['original_unit']/'0.json');b=read(ROOT/'runs'/r['resource_observer_unit']/'0.json')
  assert not a['candidate_values_received'] and not b['candidate_values_received'] and a['prompt_ids']==b['prompt_ids']
  assert [x['prefix'] for x in a['prefixes']]==[x['prefix'] for x in b['prefixes']]
  for x,y in zip(a['prefixes'],b['prefixes']):
   assert native_path(x['frontier']).read_bytes()==native_path(y['frontier']).read_bytes();vectors+=1
   if 'sequence' in x:assert state_equal(x,y);states+=1
 assert (vectors,states)==(proof['full_vectors'],proof['states'])
 return proof

def audit():
 assert not LOCK.exists(),'Read-only reconstruction requires quiescent native workers'
 pins=read(ROOT/'HOST_BINDINGS.json');assert pins['reference_changed'] is False and pins['reference_producer_ub']==128 and pins['reference_outer_batch']==512
 assert sha(OLD_CAMPAIGN/'FREEZE.json')==pins['pr187_freeze_sha256'] and sha(OLD_CAMPAIGN/'RECORDS.json')==pins['pr187_records_sha256']
 for f in pins['original_files']:checked_file(f['path'],f['sha256'])
 a0=scan_saved(OLD_CAMPAIGN,OSMOL/'cohort/PANEL.json');assert a0==read(ROOT/'a0/saved-costs.json') and a0['model_forwards']==0 and a0['slots']==864
 costs=units_and_costs();resource=reference_resource_bridge()
 missing={x['unit'] for x in costs['units'] if x.get('missing_original_budget_observation_not_invented')}
 assert missing=={x['original_unit'] for x in resource['results']}
 observed={x['unit']:x for x in costs['units']}
 for x in resource['results']:assert observed[x['resource_observer_unit']]['minimum_signed_GPU_reserve_bytes']==x['minimum_signed_GPU_reserve_bytes']
 q=qualifications()
 decision=read(ROOT/'DEVELOPMENT_DECISION.json');p=pilot('parallel');assert all(p[m+'_'+a]['measure']==decision['complete_clean_service_totals_s'][m+'_'+{'M':'M','H1':'D1','C4U4':'D4','C4U1':'C4U1'}[a]] for m in ('S','L') for a in ('M','H1','C4U4','C4U1'))
 return dict(status='COMPLETE_NATIVE_EXPOSED_ECONOMICS_RECONSTRUCTION',a0=dict(slots=a0['slots'],model_forwards=0,summary=a0['summary']),qualification=q,resident_pilot=pilot('resident'),parallel_pilot=p,known_work=known_work(),draft_observations=draft_observations(),reference_resource_bridge=resource,decision=decision,costs=costs,fresh_natural_confirmation_started=False,external_native_replication=False,prior_release_dependency='b570-decisive-recovery-v2-evidence-20261105',weights_needed_for_read_only_recompute=False)

if __name__=='__main__':print(json.dumps(audit(),indent=2))
