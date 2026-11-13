"""One continuation of charged416 after proven pre-native refusal. Never refunds."""
import os,sys,json,time,hashlib,datetime as dt,ctypes as C,importlib.util
from pathlib import Path
root=Path(__file__).resolve().parent
sys.stdout=(root/'ADMIN3.bootstrap.log').open('x',buffering=1,encoding='utf8');sys.stderr=sys.stdout
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('phase4',root/'runner_v5.py');w=r.w;proof=module('proof',root/'continuation_proof_v2.py')
python=(root.parent/'rtx223-e08/python311/python.exe').resolve();w.need(Path(sys.executable).resolve()==python and C.windll.shell32.IsUserAnAdmin(),'wrong interpreter/identity')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
contract=json.loads((root/'CONTRACT.json').read_bytes());end=dt.datetime.fromisoformat(contract['window'][1]).timestamp();w.need(time.time()+120<end,'expired window')
policy=json.loads((root/'IDLE_CONTINUATION_POLICY.json').read_bytes())
w.need(r.r.runner_context()==policy['runner_context'],'different administrator identity')
state=Path('D:/HeteroSpec-PC/rtx223-e11-u-contract');lease=w.DeviceLock(state/'runner.lease','RTX223-E11-UCONTRACT-Runner');lease.acquire()
path=state/'family.jsonl';prefix=path.read_bytes();w.need(hashlib.sha256(prefix).hexdigest()==policy['prefix_sha256'] and len(prefix)==policy['prefix_bytes'],'do not rewrite or reset prior ledger')
attempt_path=state/'timing-001/attempt.jsonl';w.need(sha(attempt_path)==policy['failed_attempt_sha256'],'failure proof drift')
qual=Path(policy['qualification_result']);w.need(sha(qual)==policy['qualification_result_sha256'],'qualified result drift')
w.need(sha(state/'timing-002/attempt.jsonl')==policy['second_failed_attempt_sha256'],'second failed proof drift')
audit=proof.audit([json.loads(x) for x in prefix.splitlines()],[json.loads(x) for x in attempt_path.read_bytes().splitlines()],json.loads(qual.read_bytes()),sha(root/'CONTRACT.json'))
w.need(audit==policy['audit'],'continuation proof mismatch')
journal=path.open('ab',buffering=0)
def event(**v):
 raw=(json.dumps(dict(utc=w.utc(),**v))+'\n').encode();w.need(journal.write(raw)==len(raw),'short journal write');os.fsync(journal.fileno())
queue=root/'admin-queue-idle';seen=set();claimed=False;cpu_started=False
event(kind='IDLE_CONTINUATION_READY',pid=os.getpid(),creation_filetime=w.process_creation(),limit=500,total_reserved=430,additional_reserved=0,prefix_sha256=policy['prefix_sha256'],contract_sha256=sha(root/'CONTRACT.json'))
try:
 while time.time()<end and not (root/'ADMIN3_STOP').exists():
  pending=sorted(p for p in queue.glob('*.json') if p.name not in seen)
  if not pending:time.sleep(.2);continue
  reqpath=pending[0];seen.add(reqpath.name);req=json.loads(reqpath.read_bytes());script=Path(req['script']).resolve(strict=True)
  w.need(script.is_relative_to(root) and script.suffix=='.py' and sha(script)==req['sha256'],'unbound continuation entry')
  kind=req['kind'];w.need(req['reservation']==0,'no new reservations and no refunds')
  if kind=='NUMERICAL_CONTINUATION':
   w.need(reqpath.name=='009-timing-idle.json' and req.get('reservation_ref')=='003-timing.json' and not claimed,'one timing continuation only')
   smoke=json.loads((root/'CPU_SMOKE_PASS_V5.json').read_bytes());w.need(smoke['pass'] and smoke['runner_context']==r.r.runner_context() and smoke['source_sha256']==sha(root/'runner_v5.py'),'fresh same-identity CPU admission')
   module('idle',root/'idle_admission.py').wait(root,r.ob,event,end,root/'ADMIN3_STOP')
   claimed=True;hard=120
   event(kind='IDLE_CONTINUATION_CLAIMED',request=reqpath.name,existing_reservation=416,additional_reserved=0,total_reserved=430,previous_explicit_permits=0,native_limit=392,maximum_family_actual=400,script=str(script),sha256=req['sha256'])
  else:
   w.need(kind=='CPU_ONLY' and reqpath.name in ('008-cpu-readmit.json','010-cleanup.json'),'unapproved continuation request')
   if reqpath.name=='008-cpu-readmit.json':w.need(not cpu_started and not claimed,'CPU admission order');cpu_started=True
   hard=30;event(kind='IDLE_CONTINUATION_CPU_TASK',request=reqpath.name,additional_reserved=0,total_reserved=430,script=str(script),sha256=req['sha256'])
  w.need(time.time()+hard<end,'phase outside window')
  job=w.AtomicJob();lim=w.EXTENDED_LIMIT();lim.BasicLimitInformation.LimitFlags=0x2000|0x100|0x8;lim.BasicLimitInformation.ActiveProcessLimit=2;lim.ProcessMemoryLimit=2*1024**3;w.checked(w.SetJob(job.job,9,C.byref(lim),C.sizeof(lim)),'outer containment unchanged')
  output=bytearray();error=bytearray();status='UNKNOWN';start=time.monotonic()
  try:
   env={k:v for k,v in os.environ.items() if not k.startswith(('CUDA_','GGML_','HS_'))};job.create([python,'-I','-B','-S',script],root,env);job.resume()
   while job.exit_code() is None and time.monotonic()-start<hard and time.time()<end:
    for fd,dest in ((job.output,output),(job.error,error)):
     part=job.read(fd)
     if part:dest.extend(part)
    w.need(len(output)+len(error)<=16*1024**2,'outer log cap');time.sleep(.02)
   if job.exit_code() is None:job.kill()
   w.Wait(job.process,1000);code=job.exit_code();status='COMPLETE' if code==0 else 'FAILED'
   for fd,dest in ((job.output,output),(job.error,error)):
    part=job.read(fd)
    if part:dest.extend(part)
   event(kind='IDLE_CONTINUATION_TASK_EXIT',request=reqpath.name,status=status,exit_code=code,wall_seconds=time.monotonic()-start,owned_exit_confirmed=job.active()==0)
  except BaseException as ex:job.kill();event(kind='IDLE_CONTINUATION_TASK_ERROR',request=reqpath.name,error=str(ex))
  finally:
   job.close();(queue/(reqpath.stem+'.stdout.log')).write_bytes(output);(queue/(reqpath.stem+'.stderr.log')).write_bytes(error)
   with (queue/(reqpath.stem+'.result')).open('x',encoding='utf8') as f:json.dump(dict(status=status),f)
finally:
 event(kind='IDLE_CONTINUATION_STOPPED',total_reserved=430,additional_reserved=0,claimed=claimed);journal.close();lease.close()
