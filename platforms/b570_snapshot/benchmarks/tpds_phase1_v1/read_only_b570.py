"""Recompute the delivered B570 result without model access or native processes."""
from pathlib import Path
import hashlib,json,math,ntpath,os,sqlite3,sys
_casefiles={}
_hashes={}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 p=Path(p);s=p.stat();key=(str(p.resolve()),s.st_size,s.st_mtime_ns)
 if key not in _hashes:
  with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
  after=p.stat();assert (s.st_size,s.st_mtime_ns)==(after.st_size,after.st_mtime_ns);_hashes[key]=h
 return _hashes[key]
def mapped(root,value):
 text=str(value).replace('\\','/');marker='/b570-phase1-20261107-v2/'
 if marker in text:text=text.split(marker,1)[1]
 elif '/benchmarks/' in text:text='repro/repository/benchmarks/'+text.split('/benchmarks/',1)[1]
 elif ntpath.isabs(text):raise AssertionError(('external prerequisite',value))
 p=(root/text).resolve();assert p.is_relative_to(root.resolve()),('outside evidence',value)
 if not p.exists():
  if str(root) not in _casefiles:_casefiles[str(root)]={x.relative_to(root).as_posix().lower():x for x in root.rglob('*') if x.is_file()}
  lookup=_casefiles[str(root)];name=p.relative_to(root).as_posix().lower()
  if name in lookup:p=lookup[name]
  elif name+'.pack.json' in lookup:p=Path(str(lookup[name+'.pack.json'])[:-len('.pack.json')])
 return p
def state_hash(p):
 if p.is_file():return sha(p)
 return read(str(p)+'.pack.json')['raw_sha256']
def recompute(root):
 root=Path(root).resolve();sys.path.insert(0,str(Path(__file__).resolve().parent))
 from receipts import normalize_receipt
 from analyze import analyze_structural
 plan=read(root/'SCHEDULE.json');saved=read(root/'FORMAL_RECORDS.json');records=[]
 for z,record in zip(plan,saved,strict=True):
  assert z['slot_id']==record['slot_id']
  n=int(z['slot_id'].rsplit('-',1)[1]);p=root/'runs'/f'formal-v2-{n//2:03d}'/(str(n%2)+'.json');r=read(p)
  assert r['capture_heavy'] is False and r['prefill_ms']==0 and r['head']==z['head'] and r['final_position_max']==z['head']+z['width']-1
  check=normalize_receipt(p,z['slot_id'],record['reference_id'],True,window='append_after_valid_state',coordinate=z);assert check==record;records.append(check)
 analysis=analyze_structural(plan,records);assert analysis==read(root/'STRUCTURAL_ANALYSIS.json')
 vectors=states=0
 for check in read(root/'QUALIFICATION.json')['checks']:
  p=mapped(root,check['receipt']);ref=mapped(root,check['reference']);r=read(p);nv=check['required_rows']
  for suffix in ('.initial.bin','.final.bin'):assert state_hash(Path(str(p)+suffix))==state_hash(Path(str(ref)+suffix));states+=1
  for j in range(nv):assert sha(str(p)+f'.row{j}.f32')==sha(str(ref)+f'.row{j}.f32');vectors+=1
  if check['kind']=='producer':assert sha(str(p)+'.initial.f32')==sha(str(ref)+'.initial.f32');vectors+=1
  assert r['observed_copied_rows']==nv and int(check['micrographs'][0]['head'])==r['head']
  assert sum(int(m['rows']) for m in check['micrographs'])==r['width']
 # Canonical old R bridge and independent repeated R_d' are checked again.
 for cap in (1024,4096):
  for i,c in enumerate(read(root/f'REFERENCES_C{cap}.json')['checks']):
   a=mapped(root,c['reference']);b=a.with_name(str(2*i+1)+'.json');width=read(a)['width']
   for suffix in ('.initial.bin','.final.bin'):assert state_hash(Path(str(a)+suffix))==state_hash(Path(str(b)+suffix))
   for j in range(width if width<=4 else 1):assert sha(str(a)+f'.row{j}.f32')==sha(str(b)+f'.row{j}.f32')
   if cap==1024:
    for repeat in (0,1):
     old=read(root/'runs/canonical-C1024'/(str(2*i+repeat)+'.json'))['prefixes']
     assert state_hash(mapped(root,old[0]['sequence']))==state_hash(Path(str(a)+'.initial.bin')) and state_hash(mapped(root,old[-1]['sequence']))==state_hash(Path(str(a)+'.final.bin'))
     for j in range(width if width<=4 else 1):assert sha(mapped(root,old[j+1 if width<=4 else width]['frontier']))==sha(str(a)+f'.row{j}.f32')
 for cap in (1024,4096):
  for i in range(3):
   ref=root/'runs'/f'ordinary-native02-C{cap}-R'/(str(i)+'.json');a=read(ref)
   assert a['materialized_output_tokens']==len(a['ids'])-1 and a['pending_id']==a['ids'][-1]
   assert a['terminal_kind']==('EOG' if i==1 else 'CAP')
   for method in ('S','L'):
    p=root/'runs'/f'ordinary-native02-C{cap}-{method}'/(str(i)+'.json');r=read(p);assert (r['ids'],r['eog'])==(a['ids'],a['eog'])
    assert state_hash(Path(str(p)+'.ordinary-final.bin'))==state_hash(Path(str(ref)+'.ordinary-final.bin'))
    for j in range(len(a['ids'])):assert sha(str(p)+f'.ordinary-row{j}.f32')==sha(str(ref)+f'.ordinary-row{j}.f32');vectors+=1
 for cap in (1024,4096):
  for method in ('R','S','L'):
   folder=root/'runs'/f'clean-native02-C{cap}-{method}'
   for i in (0,1):assert set(read(folder/(str(i)+'.json'))['append_observer_calls'].values())=={0}
   if cap==1024:assert set(read(folder/'2.json')['append_observer_calls'].values())=={1}
 for c in read(root/'CLEAN_BUILD_QUALIFIED.json')['checks']:
  p=mapped(root,c['receipt']);ref=next(z for z in read(root/f"REFERENCES_C{c['capacity']}.json")['checks'] if z['key']==f"C{c['capacity']}-q4-crossing")['reference'];ref=mapped(root,ref)
  for suffix in ('.initial.bin','.final.bin'):assert state_hash(Path(str(p)+suffix))==state_hash(Path(str(ref)+suffix));states+=1
  for j in range(4):assert sha(str(p)+f'.row{j}.f32')==sha(str(ref)+f'.row{j}.f32');vectors+=1
 # Retain and independently observe the rejected development runtime result.
 ref=root/'runs/reference-C1024/0.json.row0.f32';failed=root/'runs/qual-native01-C1024-S/0.json.row0.f32';assert sha(ref)!=sha(failed)
 db=sqlite3.connect('file:'+str(root/'ledger.sqlite').replace('\\','/')+'?mode=ro',uri=True)
 columns=[x[1] for x in db.execute('pragma table_info(attempts)')];attempts=[dict(zip(columns,x)) for x in db.execute('select * from attempts order by id')];db.close()
 requests=sum(x['requests'] for x in attempts);rows=sum(x['token_rows'] for x in attempts);assert requests<=1024 and rows<=2500000
 native=owned=provision=0.;module_checks=0
 for x in attempts:
  unit=root/'units'/x['id'];s=read(unit/'SUPERVISOR.json');r=read(unit/'RESERVATION.json');assert all(r[k]==x[k] for k in ('requests','token_rows','operators'))
  assert s['cleanup_verified'] and s['job_accounting']['active_processes']==0 and s['assigned_before_resume'];native+=s['charged_seconds'];owned+=read(unit/'RECEIPT.json')['owned_seconds'];provision+=s['provisioning_to_ready_seconds'];module_checks+=len(s['loaded_module_hashes'])
  if x['id'].startswith('formal-v2-'):
   argv=s['argv'];cap=int(argv[3]);method=argv[4];expected=read(root/'CLEAN_MODULE_SETS.json')[f'{cap}-{method}'];actual={ntpath.normcase(ntpath.normpath(z['path'])):z['sha256'] for z in s['loaded_module_hashes']};assert actual==expected
 details=read(root/'FORMAL_COST_DETAILS.json');assert len(details)==216
 cost=dict(reserved_requests=requests,reserved_row_upper_bounds=rows,reserved_operators=sum(x['operators'] for x in attempts),native_units=len(attempts),all_worker_cleanup_verified=True,native_charged_seconds=native,owned_worker_seconds=owned,provisioning_to_ready_seconds=provision,overlapping_clocks_do_not_add=True,complete_process_cost_includes_response_IO=True,native_service_until_receipt_assembly_s=sum(x['service_ms']/1000 for x in details),append_measured_s=sum(x['append_ms']/1000 for x in details if x['slot']['kind']=='measurement'),append_warmup_s=sum(x['append_ms']/1000 for x in details if x['slot']['kind']=='warmup'),preparation_all216_s=sum(x['preparation_ms']/1000 for x in details),import_and_read_all216_s=sum(x['state_import_and_read_ms']/1000 for x in details),reset_all216_s=sum(x['reset_ms']/1000 for x in details),cost_coverage=dict(expected_requests=216,present_requests=216,measured_append=216,measured_preparation=216,measured_native_service_envelope=216,complete=True),device_kernel_seconds=None,plan_mask_concat_extraction_split_seconds=None,response_IO_per_request_seconds=None,initial_unmetered_CPU_seconds=None,draft_decode=dict(status='NOT_EXECUTED',seconds=None),draft_idle_provisioning_split_seconds=None)
 cost['caller_batch_assembly_and_release_seconds']=None;cost['complete_service_per_request_seconds']=None
 builds={p.relative_to(root).as_posix():read(p) for p in sorted(root.rglob('*.log.cost.json'))};cost['build_command_receipts']=builds;cost['build_command_wall_observed_sum_s']=sum(z['wall_seconds'] for z in builds.values());cost['build_cost_scope']='Recorded configure/compile command envelopes; driver envelopes overlap and are not added'
 frozen=read(root/'BUILD_FREEZE.json');local=external=0
 for f in frozen['files'].values():
  try:p=mapped(root,f['path'])
  except AssertionError:external+=1;continue
  assert p.is_file() and p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],f['path'];local+=1
 return dict(status='READ_ONLY_NUMERICAL_STATE_SLOT_COST_RECOMPUTATION_PASS',model_forwards=0,performance_slots=216,measurements=108,warmups=108,required_full_vectors_rechecked=vectors,serialized_active_states_rechecked=states,coordinate_count=len(analysis['coordinates']),actual_module_records=module_checks,build_inputs=dict(delivered_and_rehashed=local,external_toolchain_system_prerequisites=external,complete_frozen_inputs=len(frozen['files'])),costs=cost,analysis=analysis,retained_failure_observed=True,build_freeze_sha256=sha(root/'BUILD_FREEZE.json'),formal_freeze_sha256=sha(root/'FORMAL_FREEZE.json'))
if __name__=='__main__':
 root=Path(sys.argv[1]).resolve();result=recompute(root)
 if len(sys.argv)>2:
  with Path(sys.argv[2]).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('analysis',)},indent=2))
