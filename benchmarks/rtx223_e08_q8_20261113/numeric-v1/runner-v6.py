"""One native child, zero capabilities, fixed UUID and independent durable phase receipts."""
import os,sys,json,hashlib,time,datetime as dt,subprocess,ctypes as C,importlib.util,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;E08=HERE.parent
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('bootstrap_bound',E08/'attempt-006/runner.py');w=r.win
ob=module('numeric_observer',HERE/'observation.py')
need=w.need
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def record(p):
 p=Path(p).resolve(strict=True);s=p.stat();return dict(path=str(p),sha256=sha(p),bytes=s.st_size,file_id=dict(volume=s.st_dev,inode=s.st_ino))

def run(plan_path):
 started=time.monotonic();plan=json.loads(Path(plan_path).read_bytes());phase=plan['phase']
 need(phase in ('CPU','capture','qualification','timing'),'unknown phase')
 need(time.time()+120<dt.datetime.fromisoformat('2026-11-13T08:00:00+08:00').timestamp(),'end window')
 root=Path(plan['receipt_dir']);root.mkdir(exist_ok=False)
 log=r.Journal(root,dict(scope='E08_NUMERIC_INDEPENDENT',phase=phase,reservation=plan['app_launch_reservation'],contract_sha=sha(HERE/'CONTRACT-v3.json')))
 success=False;absent=False;observer=None;job=None;guard=None;pins=r.Pins();lock=None;outcome='FAILED';error=None
 try:
  # Full-host task and service scan precedes native process creation. No termination.
  cp=subprocess.run(['C:/Program Files/PowerShell/7/pwsh.exe','-NoProfile','-NonInteractive','-File',str(HERE/'Collect-Host.ps1'),'-destination',str(root/'HOST.json')],capture_output=True,timeout=20,creationflags=0x08000000)
  (root/'host.stderr').write_bytes(cp.stderr);need(cp.returncode==0,'host dispatcher check failed')
  dep=json.loads((HERE/'DEPLOYMENT-v5.json').read_bytes());stage=json.loads((HERE/'STAGING-v5.json').read_bytes())
  for row in plan['controller_inputs']:pins.pin(row)
  for row in [*dep['modules'].values(),*dep['candidates']]:pins.pin(row)
  model=Path(stage['original_model']['path']);pins.pin(dict(path=str(model),sha256=stage['original_model']['sha256']))
  for row in stage['files']:pins.pin(row)
  # The dedicated interpreter and every importable input remain bound too.
  py=json.loads((E08/'build/PYTHON_INPUTS.json').read_bytes())
  for row in py['files']:pins.pin(row)
  need(not any(p.exists() for p in r.LEGACY),'legacy lock appeared')
  lock=w.DeviceLock(Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock'),r.UUID,r.LEGACY[1:]);lock.acquire()
  log.record(dict(kind='LIVE_HOST',process_count=r.live_check(),window_end='2026-11-13T08:00:00+08:00',old_thread_user_confirmation='historical only; current task+service+process checks refreshed'))
  output=Path(plan['output_dir']);output.mkdir(exist_ok=False)
  manifest=dep['modules'].copy();manifest[plan['executable_name']]=record(plan['argv'][0])
  policy=dict(device_uuid=r.UUID,output_dir=str(output),manifest=manifest,candidates=dep['candidates'],executable_name=plan['executable_name'],required_loaded=plan['required_loaded'])
  if phase=='CPU':
   class CPUObserver(ob.Observer):
    def start(self):
     self.etw=ob.open_pinned(self.by_name['observation.dll']['path']);self.begin=ob.function(self.etw,'hs_trace_start',ob.W.DWORD);self.bind_trace=ob.function(self.etw,'hs_trace_bind',ob.W.DWORD,ob.W.DWORD);self.read_trace=ob.function(self.etw,'hs_trace_next',ob.W.DWORD,C.POINTER(ob.TraceRecord),ob.W.DWORD);self.end_trace=ob.function(self.etw,'hs_trace_stop',ob.W.DWORD,C.POINTER(ob.W.DWORD));self.health=ob.function(self.etw,'hs_trace_health',ob.W.DWORD);self.session=True;need(self.begin()==0,'CPU ETW')
    def _watermarks(self):pass
    def checkpoint(self,stage):
     if stage=='METER':time.sleep(2)
     self.poll()
    def finish(self):
     lost=(ob.W.DWORD*3)();rc=self.end_trace(lost);self.session=False;self._events();need(rc==0 and not any(lost) and self.counts[1]==self.counts[2]==1,'CPU ETW drain');log.record(dict(kind='CPU_ETW_COMPLETE',counts=self.counts,losses=list(lost),loaded=list(self.loaded)));return dict(valid=True)
   observer=CPUObserver(policy,log.record)
  else:observer=ob.Observer(policy,log.record)
  job=w.AtomicJob();guard=r.Deadline(job,119,109)
  env={'SystemRoot':'C:/Windows','WINDIR':'C:/Windows','TEMP':str(output),'TMP':str(output),'LOCALAPPDATA':plan['profile'],'PATH':str(Path(plan['argv'][0]).parent)+';C:/Windows/System32','CUDA_VISIBLE_DEVICES':r.UUID,'HS_E08_LAUNCH_LOG':str(output/'launches.log'),'HS_E02_Q8_QUANT_CAPTURE':str(output/'quantized')}
  env['HS_B_DEADLINE_TICK']=str(w.GetTickCount64()+(80000 if phase=='CPU' else 109000))
  observer.start();job.create(plan['argv'],Path(plan['argv'][0]).parent,env,r.PACKAGE);observer.bind(job.pid,job.creation)
  log.record(dict(kind='OWNED_SUSPENDED',pid=job.pid,creation=job.creation,active=job.active(),active_limit=1,commit_limit=2*1024**3,kill_on_close=True,package=r.PACKAGE))
  w.verify_package_restrictions(job,r.PACKAGE,r.protected_models(),[Path(row['path']) for row in stage['files']]);log.record(dict(kind='MODEL_ACCESS',original_paths='DENIED',staged_one_frozen_model='READABLE',original_ACL_changes=0))
  job.resume()
  if phase=='CPU':r.Protocol(job,observer,guard,log,root,r.LEGACY[1:]).run('cpu-fake')
  else:
   buffer=b'';stdout=0;stderr=0;seen=[];expected=plan['gates']
   with (root/'native.stdout').open('xb') as outf,(root/'native.stderr').open('xb') as errf:
    while job.exit_code() is None:
     guard.check(True);need(not any(p.exists() for p in r.LEGACY[1:]),'legacy lock appeared');observer.poll()
     need(sum(p.stat().st_size for p in output.rglob('*') if p.is_file())<=32*1024**2,'output byte cap')
     part=job.read(job.error)
     if part:stderr+=len(part);need(stderr<=8*1024**2,'stderr cap');need(errf.write(part)==len(part),'stderr short write');errf.flush()
     part=job.read(job.output)
     if part:
      stdout+=len(part);need(stdout<=8*1024**2,'stdout cap');need(outf.write(part)==len(part),'stdout short write');outf.flush();buffer+=part
      while b'\n' in buffer:
       line,buffer=buffer.split(b'\n',1);line=line.rstrip(b'\r')
       need(len(line)<=1024**2,'line cap')
       if line.startswith(b'READY '):
        gate=line[6:].decode('ascii');need(len(seen)<len(expected) and gate==expected[len(seen)],'unexpected stage');guard.check(gate=='CLEANUP');observer.checkpoint(gate);log.record(dict(kind='PERMIT',stage=gate));command=('GO '+gate+'\n').encode();need(os.write(job.input,command)==len(command),'permit short write');seen.append(gate)
     time.sleep(.01)
    for fd,f in ((job.output,outf),(job.error,errf)):
     part=job.read(fd)
     if part:need(f.write(part)==len(part),'terminal log short write')
     f.flush();os.fsync(f.fileno())
   need(seen==expected and job.exit_code()==0,'native result not complete')
   while job.active():guard.check(True);time.sleep(.01)
  observation=observer.finish();need(observation['valid'],'observer receipt')
  if phase=='capture':
   need((output/'receipt.txt').is_file(),'capture missing receipt');need((output/'quantized/activation_q8_1.bin').stat().st_size==36864,'actual Q8 activation missing')
  elif phase in ('qualification','timing'):
   result=json.loads((output/'result.json').read_bytes());need(result['status']=='PASS_OPERATOR_ONLY' and result['explicit_prelaunch_charged']<=plan['app_launch_reservation'],'operator result failure')
  success=True
 except BaseException as ex:error=str(ex);print('FAILED',error,flush=True)
 finally:
  try:
   if job:
    if not success:job.kill()
    if job.process:
     absent=w.Wait(job.process,1000)==0 and job.active()==0
     log.record(dict(kind='EXIT',exit_code=job.exit_code(),active=job.active(),confirmed=absent))
    else:absent=job.active()==0
   else:absent=True
   if observer:observer.close()
  except BaseException as ex:error=(error or '')+'; cleanup '+str(ex);success=False
  finally:
   if guard:guard.close()
   if job:job.close()
   if lock:lock.close()
   pins.close()
   outcome='PASS' if success and absent else 'FAIL' if absent else 'UNKNOWN'
   log.record(dict(kind=outcome,failure=error,owned_process_exit_confirmed=absent,wall_seconds=time.monotonic()-started,physical_kernels=None,implicit_contexts=None),terminal=True);log.close()
 need(outcome=='PASS','phase '+outcome+' '+str(error));print('PASS',phase,flush=True)

if __name__=='__main__':run(sys.argv[1])
