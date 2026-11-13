"""Ephemeral C1-only controller. Durable415-family budget, no security/ACL changes."""
import os,sys,json,time,hashlib,datetime as dt,ctypes as C,importlib.util
from pathlib import Path
root=Path(__file__).resolve().parent
sys.stdout=(root/'ADMIN.bootstrap.log').open('x',buffering=1,encoding='utf8');sys.stderr=sys.stdout
sp=importlib.util.spec_from_file_location('phase',root/'runner.py');r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r);w=r.w
python=(root.parent/'rtx223-e08/python311/python.exe').resolve();w.need(Path(sys.executable).resolve()==python,'wrong interpreter')
contract=json.loads((root/'CONTRACT.json').read_bytes());end=dt.datetime.fromisoformat(contract['window'][1]).timestamp();w.need(time.time()+120<end,'expired window')
state=Path('D:/HeteroSpec-PC/rtx223-e09-c1');state.mkdir(exist_ok=True)
lease=w.DeviceLock(state/'runner.lease','RTX223-E09-C1-Runner');lease.acquire()
journal=(state/'family.jsonl').open('xb',buffering=0)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def event(**v):
 raw=(json.dumps(dict(utc=w.utc(),**v))+'\n').encode();w.need(journal.write(raw)==len(raw),'family short write');os.fsync(journal.fileno())
queue=root/'admin-queue';queue.mkdir(exist_ok=True);seen=set();reserved=0
event(kind='READY',pid=os.getpid(),creation_filetime=w.process_creation(),contract_sha256=sha(root/'CONTRACT.json'),limit=415,end=contract['window'][1])
try:
 while time.time()<end and not (root/'ADMIN_STOP').exists():
  pending=sorted(p for p in queue.glob('*.json') if p.name not in seen)
  if not pending:time.sleep(.2);continue
  path=pending[0];seen.add(path.name);req=json.loads(path.read_bytes());script=Path(req['script']).resolve(strict=True)
  w.need(script.is_relative_to(root) and script.suffix=='.py' and sha(script)==req['sha256'],'unbound C1 entry')
  n=req['reservation'];kind=req['kind'];w.need(type(n)is int and n>=0 and reserved+n<=415 and kind in ('CPU_ONLY','NUMERICAL'),'family budget/kind')
  w.need((kind=='CPU_ONLY' and n==0) or (kind=='NUMERICAL' and n in (14,355) and req.get('counter_audit') is True),'unapproved phase reservation')
  hard=120 if kind=='NUMERICAL' else 30;w.need(time.time()+hard<end,'phase outside current window')
  reserved+=n;event(kind='RESERVED_BEFORE_TASK',request=path.name,reserved=n,total=reserved,script=str(script),sha256=req['sha256'])
  job=w.AtomicJob();lim=w.EXTENDED_LIMIT();lim.BasicLimitInformation.LimitFlags=0x2000|0x100|0x8;lim.BasicLimitInformation.ActiveProcessLimit=2;lim.ProcessMemoryLimit=2*1024**3;w.checked(w.SetJob(job.job,9,C.byref(lim),C.sizeof(lim)),'outer Job containment')
  output=bytearray();error=bytearray();status='UNKNOWN';start=time.monotonic()
  try:
   env={k:v for k,v in os.environ.items() if not k.startswith(('CUDA_','GGML_','HS_'))}
   job.create([python,'-I','-B','-S',script],root,env);job.resume()
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
   event(kind='TASK_EXIT',request=path.name,status=status,exit_code=code,wall_seconds=time.monotonic()-start,owned_exit_confirmed=job.active()==0)
  except BaseException as ex:job.kill();event(kind='TASK_ERROR',request=path.name,error=str(ex))
  finally:
   job.close();(queue/(path.stem+'.stdout.log')).write_bytes(output);(queue/(path.stem+'.stderr.log')).write_bytes(error)
   with (queue/(path.stem+'.result')).open('x',encoding='utf8') as f:json.dump(dict(status=status),f)
finally:event(kind='STOPPED',reserved=reserved);journal.close();lease.close()
