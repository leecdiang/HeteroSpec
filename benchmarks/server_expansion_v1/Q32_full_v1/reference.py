"""First model-specific32B scalar reference; no candidate execution here."""
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
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def prepare(a):
 r,w=a.root,a.work;w.mkdir(mode=0o700);runtime=w/'runtime';shutil.copytree(r/'m2-runtime-03',runtime)
 p=runtime/'host.py';s=p.read_text();old="inherited['requests']+sum(r['requests'] for r in reserved)+req<=2048 and inherited['rows']+sum(r['rows'] for r in reserved)+rows<=8000000";assert s.count(old)==1
 s=s.replace(old,"inherited['requests']+sum(r['requests'] for r in reserved)+req<=512 and inherited['rows']+sum(r['rows'] for r in reserved)+rows<=2000000",1);p.write_text(s)
 pins=read(runtime/'pins.json');pins['models']['Qwen32B']=dict(target='efd971561896866f0e910cce52761ca77b1b138090c7f15fe284676d57d1f689',draft='9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031');(runtime/'pins.json').write_text(json.dumps(pins,indent=2)+'\n')
 prior=r/'q32-diagnostic-run-01/ledger.jsonl';xs=[json.loads(s)for s in prior.read_text().splitlines()];res=[x for x in xs if x['event']=='RESERVE'];assert sum(x['requests']for x in res)==2 and sum(x['rows']for x in res)==128
 save(w/'INHERITED_ACCOUNTING.json',dict(requests=2,rows=128,ledgers=[dict(path=str(prior),sha256=sha(prior))],scope='Q32 original diagnostic plus explicit full32B user continuation;8B M2 ledger unchanged'))
 cfg=read(r/'q32-diagnostic-run-01/config.private.json');cfg.update(work_root=str(w),allocation_id='explicit-user-full32B-continuation-20261109',disk_reserve_bytes=100*1024**3,reference_freeze=None,reference_freeze_sha256=None);save(w/'config.private.json',cfg)
 src=r/'run-01/build-R-01/BUILD.json';build=read(src);assert build['reference_source_is_pristine']and build['role']=='reference'and sha(build['executable'])==build['executable_sha256']
 old=read(r/'q32-diagnostic-run-01/short_forward-JOB.json');base={k:old[k]for k in ('family','target_model','target_sha256','n_ctx','threads')};assert base['target_sha256']==pins['models']['Qwen32B']['target']
 selection=read(r/'m2-run-03/ROOT_SELECTION.json');jobs=[]
 for repeat in range(2):
  inputs=[]
  for i,key in enumerate(selection['roots']):
   x=dict(selection['inputs'][key]);x.update(family='Qwen32B',origin_role='EXPOSED_M2_DEPLOYMENT_MIGRATION',cap=128,prompt_tokens=len(x['prompt_ids']),prompt_ids_sha256=hashlib.sha256(json.dumps(x['prompt_ids'],separators=(',',':')).encode()).hexdigest())
   inputs.append(dict(name=f'root-{i}',input=x,capture=True,state_positions=list(range(len(x['prompt_ids']),len(x['prompt_ids'])+128))))
  job=dict(base,inputs=inputs);p=w/'reference/jobs'/f'R-repeat-{repeat}.json';save(p,job);jobs.append(dict(name=f'R-repeat-{repeat}',job=str(p),job_sha256=sha(p),requests=4,rows=sum(2*len(x['input']['prompt_ids'])+16*128 for x in inputs)))
 save(w/'REFERENCE_PLAN.private.json',dict(jobs=jobs,roots=selection['roots'],source_build=str(src),source_build_sha256=sha(src)))
 sys.path.insert(0,str(runtime));import native_checks
 structure=native_checks.gguf_structure(base['target_model']);assert structure['layers']==64 and structure['K_elements']==structure['V_elements']==1024
 profile=native_checks.profile(base['target_model'],base['target_sha256'],r/'run-01/stage-03/sources/reference/src/llama-kv-cache.cpp',structure)
 save(w/'MODEL_STRUCTURE.json',structure);save(w/'STATE_PROFILE.json',profile)
 public=dict(schema='heterospec.q32.full-reference-admission.v1',prepared_utc=stamp(),scope='Explicit user full32B continuation; independent Q32 ledger, not a PR197 budget reset',inherited_requests=2,inherited_reserved_rows=128,request_ceiling=512,row_ceiling=2000000,
  reference_jobs=[{**x,'job':Path(x['job']).name}for x in jobs],source_build_sha256=sha(src),reference_executable_sha256=build['executable_sha256'],reference_kind='Pristine fixed Linux CUDA UB1/reserve1, C1024,F16,noFA,threads2',target_sha256=base['target_sha256'],target_bytes=Path(base['target_model']).stat().st_size,
  roots=selection['roots'],structure=structure,profile_sha256=sha(w/'STATE_PROFILE.json'),minimum_GPU_reserve_bytes=cfg['gpu_reserve_bytes'],disk_reserve_bytes=cfg['disk_reserve_bytes'],GPU='Previously assigned GPU1 UUID private; GPU0 protected',CPU_native=[32,33],worker_timeout_s=900,
  ordering='No candidate forward before own reference freeze; CPU builds may precede qualification. Old8B oracles never used as32B outputs.',candidate_status='NOT_QUALIFIED',timing='Not admitted before full numerical/lifecycle/physical gates; new starts stop05:00 and archive by08:00 Asia/Shanghai2026-11-10')
 save(w/'REFERENCE_ADMISSION_PUBLIC.json',public);save(w/'SOURCE_FREEZE.private.json',{p.name:sha(p)for p in Path(__file__).parent.iterdir()if p.is_file()});print(json.dumps(dict(prepared=True,new_reference_requests=8,inherited=2)),flush=True)
def execute(a):
 r,w=a.root,a.work;src=Path(__file__).parent;runtime=w/'runtime';sys.path.insert(0,str(runtime));import host,freeze,native_checks
 proof=read(w/'PUBLIC_ADMISSION_BINDING.json');assert proof['passed']and proof['admission_sha256']==sha(w/'REFERENCE_ADMISSION_PUBLIC.json')
 plan=read(w/'REFERENCE_PLAN.private.json');profile=read(w/'STATE_PROFILE.json');_,parser=native_checks.legacy_readers(r/'repository-01');cutoff=datetime.datetime(2026,11,9,21,0,tzinfo=datetime.timezone.utc)
 (w/'reference/control').mkdir(parents=True)
 with(w/'reference/control/guard.stdout.log').open('xb')as so,(w/'reference/control/guard.stderr.log').open('xb')as se:
  guard=subprocess.Popen(['taskset','-c','36',sys.executable,'-B',str(src/'resource_guard.py'),'--work',str(w)],stdout=so,stderr=se,stdin=subprocess.DEVNULL,start_new_session=True)
 for _ in range(30):
  if(w/'RESOURCE_GUARD_LATEST.private.json').exists():break
  assert guard.poll()is None;time.sleep(.5)
 try:
  with(r/'STUDY_SCHEDULING.lock').open('a+')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   for job in plan['jobs']:
    assert not(w/'PAUSE.json').exists();g=read(w/'RESOURCE_GUARD_LATEST.private.json');assert time.time()-g['epoch']<20 and not g['events'];assert(cutoff-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>=960
    for n,h in read(w/'SOURCE_FREEZE.private.json').items():assert sha(src/n)==h
    assert sha(job['job'])==job['job_sha256']and sha(plan['source_build'])==plan['source_build_sha256']
    host.run(w/'config.private.json',Path(plan['source_build']),Path(job['job']),w/'reference/runs'/job['name'],'reference');print('Q32_REFERENCE_NATIVE_COMPLETE',job['name'],flush=True)
  aroot=w/'reference/runs/R-repeat-0/native';broot=w/'reference/runs/R-repeat-1/native';pairs=[];active=[]
  for i in range(4):
   x=read(plan['jobs'][0]['job'])['inputs'][i]['input'];left=aroot/f'root-{i}';right=broot/f'root-{i}';ep=read(left/'receipt.json');other=read(right/'receipt.json');assert ep['ids']==other['ids']and ep['eog']==other['eog']and ep['terminal_kind']==other['terminal_kind']
   for pos in range(len(x['prompt_ids']),len(x['prompt_ids'])+len(ep['ids'])):
    aa=left/'captures'/str(pos);bb=right/'captures'/str(pos)
    for kind,n in [('full_requested_logits','frontier.f32'),('active_sequence_serialized','sequence.bin')]:
     ah=sha(aa/n);bh=sha(bb/n);pairs.append(dict(kind=kind,equal=ah==bh,reference=str(aa/n),candidate=str(bb/n),reference_sha256=ah,candidate_sha256=bh))
    result=native_checks.state_pair(aa/'sequence.bin',bb/'sequence.bin',pos,parser,profile);assert result['equal'];active.append(dict(root=i,position=pos,**result))
   for pos in (len(x['prompt_ids']),len(x['prompt_ids'])+len(ep['ids'])-1):
    aa=left/'captures'/str(pos)/'frontier.f32';bb=right/'captures'/str(pos)/'frontier.f32';pairs.append(dict(kind='frontier',equal=sha(aa)==sha(bb),reference=str(aa),candidate=str(bb),reference_sha256=sha(aa),candidate_sha256=sha(bb)))
  assert all(x['equal']for x in pairs)
  evidence=w/'reference/REFERENCE_REPEAT.json';save(evidence,dict(mode='reference_repeat',passed=True,pairs=pairs,active_KV=active,scope='Own32B pristine Linux R repeat, all requested vectors and all active64-layer states'))
  freeze.reference(Path(plan['source_build']),evidence,w/'reference/REFERENCE_FREEZE.json')
  cfg=read(w/'config.private.json');cfg.update(reference_freeze=str(w/'reference/REFERENCE_FREEZE.json'),reference_freeze_sha256=sha(w/'reference/REFERENCE_FREEZE.json'));save(w/'config-reference-frozen.private.json',cfg)
  save(w/'reference/COMPLETE.json',dict(passed=True,utc=stamp(),new_reference_requests=8,own_R_frozen=True,numerical_candidate_qualified=False));print('Q32_INDEPENDENT_R_FROZEN',flush=True)
 except BaseException as e:
  save(w/'reference/FAILURE.json',dict(error=str(e),traceback=traceback.format_exc(),utc=stamp(),automatic_native_retry=False));raise
 finally:
  (w/'GUARD_DONE').touch(exist_ok=False)
  try:guard.wait(timeout=20)
  except subprocess.TimeoutExpired:pass
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--prepare',action='store_true');a=p.parse_args()
 if a.prepare:prepare(a)
 else:execute(a)
if __name__=='__main__':main()
