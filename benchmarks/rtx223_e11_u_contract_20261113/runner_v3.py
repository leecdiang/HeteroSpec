"""Fresh e11 independent-contract phase gate; old helper implementations are immutable dependencies."""
import os,sys,json,time,datetime as dt,hashlib,ctypes as C,importlib.util,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'rtx223-e08'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('e08_helpers',OLD/'attempt-006/runner.py');w=r.win;ob=module('e11_observation',HERE/'observation.py');need=w.need
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def run(plan_path):
 plan=json.loads(Path(plan_path).read_bytes());phase=plan['phase'];need(phase in ('CPU','qualification','timing'),'phase')
 contract=json.loads((HERE/'CONTRACT.json').read_bytes());end=dt.datetime.fromisoformat(contract['window'][1]).timestamp();need(time.time()+120<end,'current window expired')
 state=Path(plan['receipt_dir']);state.mkdir(exist_ok=False);log=r.Journal(state,dict(scope='E11_U_CONTRACT',phase=phase,reservation=plan['app_launch_reservation'],contract_sha256=sha(HERE/'CONTRACT.json')))
 pins=r.Pins();job=observer=guard=lock=None;success=False;absent=False;error=None
 try:
  cp=subprocess.run(['C:/Program Files/PowerShell/7/pwsh.exe','-NoProfile','-NonInteractive','-File',str(HERE/'Collect-Host.ps1'),'-destination',str(state/'HOST.private.json')],capture_output=True,timeout=20,creationflags=0x08000000)
  (state/'host.stderr').write_bytes(cp.stderr);need(cp.returncode==0,'current task/service/process conflict')
  for row in plan['controller_inputs']:pins.pin(row)
  dep=json.loads((HERE/'DEPLOYMENT.json').read_bytes());stage=json.loads((HERE/'STAGING_V3.json').read_bytes())
  for row in [*dep['modules'].values(),*dep['candidates'],*stage['files']]:pins.pin(row)
  lineage=json.loads((HERE/'PARENT_REUSE_VERIFIED.json').read_bytes());pins.pin(dict(path=lineage['model']['path'],sha256=lineage['model']['sha256']))
  for row in lineage['operands']:pins.pin(dict(path=row['preserved'],sha256=row['sha256']))
  py=json.loads((OLD/'build/PYTHON_INPUTS.json').read_bytes());r.verify_python_members(py)
  for row in py['files']:pins.pin(row)
  need(not any(p.exists() for p in r.LEGACY),'existing experiment marker; preserve it')
  lock=w.DeviceLock(Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock'),r.UUID,r.LEGACY[1:]);lock.acquire()
  log.record(dict(kind='LIVE_HOST',process_count=r.live_check(),runner_context=r.runner_context(),old_thread_confirmation='historical, not a current snapshot',window_end=contract['window'][1]))
  if phase!='CPU':
   smoke=json.loads((HERE/'CPU_SMOKE_PASS.json').read_bytes());need(smoke['pass'] and smoke['runner_context']==r.runner_context() and smoke['source_sha256']==sha(HERE/'runner_v3.py'),'missing same-identity CPU admission')
  output=Path(plan['output_dir']);output.mkdir(exist_ok=False)
  manifest=dep['modules'].copy();exe=Path(plan['argv'][0]);manifest[exe.name.lower()]=dict(path=str(exe),sha256=sha(exe))
  policy=dict(device_uuid=r.UUID,output_dir=str(output),manifest=manifest,candidates=dep['candidates'],executable_name=exe.name.lower(),required_loaded=[] if phase=='CPU' else ['nvcuda.dll'])
  if phase=='CPU':
   class CPUObserver(ob.Observer):
    def start(self):
     self.etw=ob.open_pinned(self.by_name['observation.dll']['path']);self.begin=ob.function(self.etw,'hs_trace_start',ob.W.DWORD);self.bind_trace=ob.function(self.etw,'hs_trace_bind',ob.W.DWORD,ob.W.DWORD);self.read_trace=ob.function(self.etw,'hs_trace_next',ob.W.DWORD,C.POINTER(ob.TraceRecord),ob.W.DWORD);self.end_trace=ob.function(self.etw,'hs_trace_stop',ob.W.DWORD,C.POINTER(ob.W.DWORD));self.health=ob.function(self.etw,'hs_trace_health',ob.W.DWORD);self.session=True;need(self.begin()==0,'CPU ETW start')
    def _watermarks(self):pass
    def checkpoint(self,stage):
     if stage=='METER':time.sleep(2)
     self.poll()
    def finish(self):
     lost=(ob.W.DWORD*3)();rc=self.end_trace(lost);self.session=False;self._events();need(rc==0 and not any(lost) and self.counts[1]==self.counts[2]==1,'CPU ETW endpoints/loss');log.record(dict(kind='CPU_ETW_COMPLETE',counts=self.counts,lost=list(lost),loaded=list(self.loaded)));return dict(valid=True)
   observer=CPUObserver(policy,log.record)
  else:observer=ob.Observer(policy,log.record)
  job=w.AtomicJob();guard=r.Deadline(job,119,109,until=end)
  env=dict(SystemRoot='C:/Windows',WINDIR='C:/Windows',TEMP=str(output),TMP=str(output),LOCALAPPDATA=stage['profile'],PATH=str(exe.parent)+';C:/Windows/System32',CUDA_VISIBLE_DEVICES=r.UUID,HS_B_DEADLINE_TICK=str(w.GetTickCount64()+(80000 if phase=='CPU' else 109000)))
  observer.start();job.create(plan['argv'],exe.parent,env,r.PACKAGE);observer.bind(job.pid,job.creation)
  log.record(dict(kind='OWNED_SUSPENDED',pid=job.pid,creation_filetime=job.creation,active=job.active(),active_limit=1,commit_limit=2*1024**3,kill_on_close=True,package=r.PACKAGE))
  w.verify_package_restrictions(job,r.PACKAGE,r.protected_models(),[Path(x['path']) for x in stage['files']]);log.record(dict(kind='PROTECTED_MODEL_ACCESS_DENIED',paths=len(r.protected_models()),original_ACL_changes=0,new_model_loads=0))
  job.resume()
  if phase=='CPU':r.Protocol(job,observer,guard,log,state,r.LEGACY[1:]).run('cpu-fake')
  else:
   buffer=b'';outbytes=errbytes=0;granted=False
   with (state/'native.stdout').open('xb') as outf,(state/'native.stderr').open('xb') as errf:
    while job.exit_code() is None:
     guard.check(True);observer.poll();need(not any(p.exists() for p in r.LEGACY[1:]),'legacy marker appeared')
     need(sum(x.stat().st_size for x in output.rglob('*') if x.is_file())<=32*1024**2,'result byte cap')
     for fd,dest,kind in [(job.output,outf,'out'),(job.error,errf,'err')]:
      part=job.read(fd)
      if part:
       if kind=='out':outbytes+=len(part);buffer+=part
       else:errbytes+=len(part)
       need(outbytes<=8*1024**2 and errbytes<=8*1024**2,'native log cap');need(dest.write(part)==len(part),'native log short write');dest.flush()
     while b'\n' in buffer:
      line,buffer=buffer.split(b'\n',1);line=line.rstrip(b'\r')
      if line.startswith(b'READY '):
       need(line==b'READY EXECUTE' and not granted,'unexpected/repeated grant');guard.check();observer.checkpoint('EXECUTE');log.record(dict(kind='PERMIT',stage='EXECUTE'));need(os.write(job.input,b'GO EXECUTE\n')==11,'grant short write');granted=True
     time.sleep(.01)
    for fd,dest in [(job.output,outf),(job.error,errf)]:
     part=job.read(fd)
     if part:need(dest.write(part)==len(part),'terminal short write')
     dest.flush();os.fsync(dest.fileno())
   need(granted,'native execution was not granted');native_exit=job.exit_code()
   while job.active():guard.check(True);time.sleep(.01)
  observer.finish()
  if phase!='CPU':
   need(native_exit==0,'native result failed/incomplete;full ETW drain attempted first')
   result=json.loads((output/'result.json').read_bytes());need(result['status']=='PASS_E11_TWO_CONTRACTS' and result['explicit_prelaunch_charged']<=plan['app_launch_reservation'],'invalid native final receipt')
   if phase=='timing':need(len(result['paired_timings'])==48 and len(result['post_batch_bitwise'])==48 and all(x['activation_exact'] and x['output_exact'] for x in result['post_batch_bitwise']),'post-batch validity incomplete')
  success=True
 except BaseException as ex:error=str(ex);print('FAILED',error,flush=True)
 finally:
  try:
   if job:
    if not success:job.kill()
    absent=job.active()==0 if not job.process else w.Wait(job.process,1000)==0 and job.active()==0
    log.record(dict(kind='EXIT',code=job.exit_code() if job.process else None,confirmed=absent))
   else:absent=True
   if observer:observer.close()
  except BaseException as ex:error=(error or '')+'; cleanup '+str(ex);success=False
  finally:
   if guard:guard.close()
   if job:job.close()
   if lock:lock.close()
   pins.close();outcome='PASS' if success and absent else 'FAIL' if absent else 'UNKNOWN';log.record(dict(kind=outcome,failure=error,owned_process_exit_confirmed=absent,physical_launches=None,implicit_contexts=None),terminal=True);log.close()
 need(outcome=='PASS','phase '+outcome+' '+str(error))
 if phase=='CPU':
  result=dict(**{'pass':True},runner_context=r.runner_context(),source_sha256=sha(HERE/'runner_v3.py'),receipt_sha256=sha(state/'attempt.jsonl'),observed_utc=w.utc(),model_loads=0,CUDA_initializations=0,numerical_DLL_loads=0)
  with (HERE/'CPU_SMOKE_PASS.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
 print('PASS',phase,flush=True)
if __name__=='__main__':run(sys.argv[1])
