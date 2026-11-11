"""Stage C:16 charged first/follow-up target operations; no candidate edits."""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,json,os,shutil,subprocess,sys,time,traceback
sys.dont_write_bytecode=True
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x')as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
CELLS=[('loop4',248,'q4pair'),('loop4',248,'q8'),('loop4',252,'q8'),('loop4',252,'q4pair'),('packed',252,'q4pair'),('packed',252,'q8'),('packed',248,'q8'),('packed',248,'q4pair')]
def prepare(a):
 r,w=a.root,a.work;w.mkdir();b=r/'pr210-stage-b-20261109-05';builds=r/'pr210-stage-b-build-02'
 assert read(b/'COMPLETE.json')['passed']and len(read(b/'QUALIFIED.json')['cells'])==32
 proof=read(a.B_public_readback);assert proof['passed']and proof['anonymous_full_byte_readback']and proof['exact_diagnosis_reproduced']
 assert proof['commit']=='f0f53e1e3eceba96f61f472865491eef573048fa'
 save(w/'B_PUBLIC_READBACK_BOUND.json',proof)
 runtime=w/'runtime';shutil.copytree(b/'runtime',runtime);p=runtime/'host.py';s=p.read_text()
 old="req<=79,'Stage B ceiling, no stage transfer'";assert s.count(old)==1;s=s.replace(old,"req<=16,'Stage C ceiling includes every profile/primer/reference/failure'",1);p.write_text(s)
 ledgers=[];req=rows=0
 names=('run-01','m1-run-01','m2-run-01','m2-run-02','m2-run-03','pr210-stage-b-20261109-04','pr210-stage-b-20261109-05')
 for name in names:
  p=r/name/'ledger.jsonl';xs=[json.loads(s)for s in p.read_text().splitlines()];xs=[x for x in xs if x['event']=='RESERVE'];req+=sum(x['requests']for x in xs);rows+=sum(x['rows']for x in xs);ledgers.append(dict(path=str(p),sha256=sha(p)))
 assert(req,rows)==(1893,3049826),'Budget changed; stop before any GPU work'
 known={'run-01','m1-run-01','m2-run-01','m2-run-02','m2-run-03','d14-attribution-run-01','d14-run-01','d14-admission-01','q32-diagnostic-run-01','f-run-01','pr210-stage-b-20261109-04','pr210-stage-b-20261109-05'}
 assert not [p for p in r.glob('*/ledger.jsonl')if p.parent.name not in known],'Unknown native ledger requires review'
 save(w/'INHERITED_ACCOUNTING.json',dict(ledgers=ledgers,requests=req,rows=rows))
 cfg=read(b/'config.private.json');cfg.update(work_root=str(w),allocation_id='explicit-extended-server-window-20261109-stage-C');save(w/'config.private.json',cfg)
 freeze=read(b/'REFERENCE_DERIVED_FREEZE.json');payload={x['path']:x for x in freeze['files']}
 for f in freeze['files']:assert Path(f['path']).stat().st_size==f['bytes']and sha(f['path'])==f['sha256'],'Frozen B oracle changed'
 streams=freeze['streams'];base=read(b/'jobs/R-historical-replay-0.json');base={k:base[k]for k in ('family','target_model','target_sha256','n_ctx','threads')}
 plan=[]
 for i,(core,pos,execution)in enumerate(CELLS):
  name=f'C{i:02d}-{core}-{pos}-{execution}';initial=b/f'runs/R-trunk-0/native/trunk/captures/{pos}';oracle=b/'runs/R-trunk-0/native/trunk/captures'
  state=initial/'sequence.bin';front=initial/'frontier.f32';ids=streams['0'][pos:pos+8];expected=[payload[str(oracle/str(pos+j+1)/'frontier.f32')]['sha256']for j in range(8)]
  items=[dict(name=tag,position=pos,ids=ids,execution=execution,capture=False,state_path=str(state),state_sha256=payload[str(state)]['sha256'],frontier_path=str(front),frontier_sha256=payload[str(front)]['sha256'])for tag in ('first-use','follow-up')]
  job=dict(base,diagnostics=items,pause_file=str(w/'PAUSE.json'));p=w/'jobs'/(name+'.json');save(p,job)
  plan.append(dict(id=name,core=core,position=pos,execution=execution,job=str(p),job_sha256=sha(p),expected_output_sha256=expected,expected_module_map=read(b/f'runs/qualification-{core}-0/LOADED_MODULES.json')))
 save(w/'PLAN.private.json',plan)
 bindings=dict(B_qualification_sha256=sha(b/'QUALIFIED.json'),B_derived_oracle_freeze_sha256=sha(b/'REFERENCE_DERIVED_FREEZE.json'),original_R_freeze_sha256=cfg['reference_freeze_sha256'],host_adapter_sha256=sha(runtime/'host.py'),
   cores={core:dict(build_sha256=sha(builds/core/'BUILD.json'),executable_sha256=read(builds/core/'BUILD.json')['executable_sha256'])for core in ('loop4','packed')})
 save(w/'BINDINGS_PUBLIC.json',bindings)
 public=dict(schema='heterospec.pr210.stage-C.admission.v1',prepared_utc=now(),B_artifact_commit=proof['commit'],B_delivery_proof_commit='361fb4fc44be8f2c08c4ac91c4a6c36c3cb5832b',
   purpose='Separate first-use from follow-up host target-operation cost; no CUDA kernel profiling or live-service result',
   cells=[dict(id=x['id'],core=x['core'],position=x['position'],execution=x['execution'],job_sha256=x['job_sha256'])for x in plan],
   requests=dict(workers=8,first_use_profiles=8,follow_up_profiles=8,total=16,new_reference=0,extra_primers=0,failures_charged=True,ceiling=16),
   cumulative_before=dict(requests=req,reserved_rows=rows,request_ceiling=2048,row_ceiling=8000000),conservative_new_rows=4128,actual_expected_target_rows=128,draft_rows=0,
   eligibility_reuse='Exact B binaries/modules/config/model/oracle states and all32 full-vector/initial/final-active-KV proofs. No arithmetic, lifecycle, precision or output-policy edit. Every new clean operation still checks all8 independent-R output hashes, bounds, masks and actual physical counters. No new live EOG/cap/rollback claim.',
   controls='Fresh process per cell, two consecutive same-path operations. Identical scalar snapshot/frontier restored before each, outside primary timer. Both requests charged and reported; no hidden warmups. All cells retained. One follow-up observation is not a steady-state convergence proof.',
   profiling_scope='Existing host phase/planning/copy clocks and physical/graph counters; no new CUDA profiler. Instrumentation overhead not independently measured. Full process/load/restore cost retained separately.',
   shutdown=dict(new_worker_cutoff_BJT='2026-11-09T23:00:00+08:00',minimum_start_margin_s=960,worker_timeout_s=900,archive_boundary_BJT='2026-11-09T23:30:00+08:00'),
   resources='Previously assigned single GPU1 UUID private; GPU0 protected; native affinity32,33/two threads. Pause only assigned-GPU conflict, reserves or observed interference.',
   next='No automatic D/E or Q32. Candidate edits require measured removable hotspot and expected end-to-end contribution; otherwise stop and preserve negative diagnosis.')
 save(w/'ADMISSION_PUBLIC.json',public);save(w/'SOURCE_FREEZE.private.json',{p.name:sha(p)for p in Path(__file__).parent.iterdir()if p.is_file()})
 print(json.dumps(dict(prepared=True,requests=16,rows=4128)),flush=True)
def execute(a):
 r,w=a.root,a.work;b=r/'pr210-stage-b-20261109-05';builds=r/'pr210-stage-b-build-02';src=Path(__file__).parent
 sys.path.insert(0,str(w/'runtime'));import host
 proof=read(w/'PUBLIC_ADMISSION_BINDING.json');assert proof['passed']and proof['admission_sha256']==sha(w/'ADMISSION_PUBLIC.json')
 source=read(w/'SOURCE_FREEZE.private.json');plan=read(w/'PLAN.private.json');bindings=read(w/'BINDINGS_PUBLIC.json')
 cutoff=datetime.datetime.fromisoformat(read(w/'ADMISSION_PUBLIC.json')['shutdown']['new_worker_cutoff_BJT'])
 for n,h in source.items():assert sha(src/n)==h
 assert sha(b/'QUALIFIED.json')==bindings['B_qualification_sha256']and sha(b/'REFERENCE_DERIVED_FREEZE.json')==bindings['B_derived_oracle_freeze_sha256']
 assert sha(w/'runtime/host.py')==bindings['host_adapter_sha256']
 for f in read(b/'REFERENCE_DERIVED_FREEZE.json')['files']:assert sha(f['path'])==f['sha256']
 for core in ('loop4','packed'):assert sha(builds/core/'BUILD.json')==bindings['cores'][core]['build_sha256']
 (w/'control').mkdir()
 with(w/'control/guard.stdout.log').open('xb')as so,(w/'control/guard.stderr.log').open('xb')as se:
  guard=subprocess.Popen(['taskset','-c','34',sys.executable,'-B',str(src/'resource_guard.py'),'--work',str(w)],stdout=so,stderr=se,stdin=subprocess.DEVNULL,start_new_session=True)
 for _ in range(20):
  if(w/'RESOURCE_GUARD_LATEST.private.json').exists():break
  assert guard.poll()is None;time.sleep(.5)
 workers=[];observations=[];failure=None
 try:
  with(r/'STUDY_SCHEDULING.lock').open('a+')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   for cell in plan:
    assert not(w/'PAUSE.json').exists();g=read(w/'RESOURCE_GUARD_LATEST.private.json');assert time.time()-g['epoch']<20 and not g['events']
    assert(cutoff-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>=960,'Worker/archive window exhausted'
    for n,h in source.items():assert sha(src/n)==h
    p=Path(cell['job']);assert sha(p)==cell['job_sha256'];job=read(p);dest=w/'runs'/cell['id'];start=time.monotonic()
    host.run(w/'config.private.json',builds/cell['core']/'BUILD.json',p,dest,'development')
    meta=read(dest/'native/result.json');assert read(dest/'LOADED_MODULES.json')==cell['expected_module_map'],'Modules changed from qualified B'
    assert meta['draft_calls']==0 and meta['context']==dict(n_ctx=1024,n_batch=1024,n_ubatch=32,outputs_max=8,outputs_per_seq=8,flash_attention=False,type_k='f16',type_v='f16')
    worker=dict(id=cell['id'],core=cell['core'],position=cell['position'],execution=cell['execution'],adapter_inclusive_s=time.monotonic()-start,HOST=read(dest/'HOST.json'))
    workers.append(worker);save(w/'worker-records'/(cell['id']+'.json'),worker)
    pair=[]
    for item in job['diagnostics']:
     receipt=read(dest/'native'/item['name']/'receipt.json');width=8 if cell['execution']=='q8'else 4
     assert receipt['output_sha256']==cell['expected_output_sha256']and receipt['output_vectors']==8 and receipt['output_floats']==8*151936
     assert receipt['ids']==item['ids']and receipt['position']==cell['position']and receipt['execution']==cell['execution']
     assert receipt['physical_width_histogram']=={str(width):8//width}and len(receipt['executions'])==8//width
     assert receipt['final_bounds']==dict(min=0,max=cell['position']+7)
     assert receipt['online_state_imports']==receipt['online_state_exports']==receipt['online_heavy_captures']==0
     for j,e in enumerate(receipt['executions']):
      assert e['position']==cell['position']+j*width and e['width']==width and e['requested_rows']==list(range(width))and e['active_cells']==e['position']+width
      assert e['expected_extents']==[256 if p<256 else 512 for p in range(e['position'],e['position']+width)]and e['actual_attention_extent']==max(e['expected_extents'])
     record=dict(cell=cell['id'],core=cell['core'],position=cell['position'],execution=cell['execution'],tag=item['name'],receipt=receipt,all_eight_vectors_match_R=True,physical_passed=True)
     observations.append(record);pair.append(record);save(w/'checked'/(cell['id']+'-'+item['name']+'.json'),record)
    assert len(pair)==2;print('PROFILE_CELL_COMPLETE',cell['id'],flush=True)
  assert len(observations)==16
  summary=[]
  for cell in plan:
   xs=[x for x in observations if x['cell']==cell['id']];first=xs[0]['receipt'];follow=xs[1]['receipt'];summary.append(dict(cell=cell['id'],core=cell['core'],position=cell['position'],execution=cell['execution'],first_use_s=first['operation_s'],follow_up_s=follow['operation_s'],first_over_follow=first['operation_s']/follow['operation_s'],first_graphs=[first['graph_built'],first['graph_reused']],follow_graphs=[follow['graph_built'],follow['graph_reused']]))
  save(w/'RESULTS.json',dict(status='COMPLETE_16_REQUEST_HOST_PHASE_DIAGNOSTIC',scope='One first-use and one follow-up observation/cell, not a live-service or population result; no CUDA kernel profiler',summary=summary,observations=observations,workers=workers))
  save(w/'NATIVE_COMPLETE.json',dict(passed=True,utc=now(),requests=16,actual_target_rows=128,reference_requests=0,all_eight_vectors_passed=True,numerical_binaries_changed=False,next='No automatic D/E or32B'))
 except BaseException as e:
  failure=dict(status='STOPPED',utc=now(),error=str(e),traceback=traceback.format_exc(),native_retry=False);save(w/'FAILURE.json',failure)
 finally:
  (w/'GUARD_DONE').touch(exist_ok=False)
  try:guard.wait(timeout=20)
  except subprocess.TimeoutExpired:save(w/'OBSERVER_CLOSEOUT_ERROR.json',dict(reason='Observer did not exit; no new native admission'))
  (w/'closeout').mkdir()
  with(w/'closeout/collect.stdout.log').open('xb')as so,(w/'closeout/collect.stderr.log').open('xb')as se:
   result=subprocess.run(['taskset','-c','32','nice','-n','19',sys.executable,'-B',str(src/'collect.py'),'--root',str(r),'--work',str(w),'--source',str(src),'--out',str(w/'export-01')],stdout=so,stderr=se,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),timeout=900)
  save(w/'TERMINAL.json',dict(status='COMPLETE_LOCAL_ARCHIVE'if failure is None and result.returncode==0 else'STOPPED_DATA_RETAINED',utc=now(),native_complete=failure is None,archive_returncode=result.returncode,native_jobs_queued=0,public_upload='Pending connected authorized client',no_automatic_D_E_Q32=True))
 if failure:raise RuntimeError(failure['error'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--prepare',action='store_true');p.add_argument('--B-public-readback',dest='B_public_readback',type=Path);a=p.parse_args()
 if a.prepare:prepare(a)
 else:execute(a)
if __name__=='__main__':main()
