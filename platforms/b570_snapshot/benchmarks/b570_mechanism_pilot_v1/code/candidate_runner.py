"""One owned resident Vulkan process; append-only attempts, resumable hashed units."""
import os,sys,json,time,hashlib,subprocess,threading,queue,uuid,ctypes,traceback
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(os.environ.get('HETEROSPEC_B570_STUDY_ROOT',Path(__file__).parent))
OLD=Path(os.environ.get('HETEROSPEC_B570_OLD_ROOT','C:/hs/b570-prefill-v1'))
ASSET=Path(os.environ.get('HETEROSPEC_ASSET_ROOT','C:/Users/DIANG/Documents/ChatGPT/HeteroSpec'))
BIN=ROOT/'candidate-build/Release'
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp')
 with tmp.open('w',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def event(kind,**kw):
 with (ROOT/'LEDGER.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'utc':now(),'event':kind,**kw})+'\n');f.flush();os.fsync(f.fileno())
def identity(pid):
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.restype=ctypes.c_void_p;k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]
 k.GetProcessTimes.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p];k.CloseHandle.argtypes=[ctypes.c_void_p]
 h=k.OpenProcess(0x1000,0,pid)
 if not h:return None
 try:
  t=[ctypes.c_ulonglong() for _ in range(4)]
  return str(t[0].value) if k.GetProcessTimes(h,*[ctypes.byref(x) for x in t]) else None
 finally:k.CloseHandle(h)
def endpoint(x,cap):
 ids=x['ids'];eog=x['eog'];assert len(ids)==len(eog)>0
 assert all(type(i)==int and 0<=i<151936 for i in ids) and all(type(b)==bool for b in eog)
 first=next((i+1 for i,b in enumerate(eog) if b),len(ids));n=min(cap,first)
 assert eog[n-1] or n==cap
 return {'ids':ids[:n],'eog':eog[:n],'reason':'EOG' if eog[n-1] else 'CAP','raw_suffix':len(ids)-n}
def equal(a,b):return all(a[k]==b[k] for k in ['ids','eog','reason'])
def source():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
def compatible_commit(commit):
 if commit==source():return True
 if (ROOT/'CONTINUATION_FREEZE.json').exists():
  f=read(ROOT/'CONTINUATION_FREEZE.json')
  if commit in f['allowed_inference_commits'] and all(sha(ROOT/n)==h for n,h in f['current_sources'].items()):return True
 if (ROOT/'DEVICE_RECOVERY_FREEZE.json').exists():
  f=read(ROOT/'DEVICE_RECOVERY_FREEZE.json')
  if commit in f['allowed_inference_commits'] and all(sha(ROOT/n)==h for n,h in f['current_sources'].items()):return True
 p=ROOT/'RECOVERY_AMENDMENT.json'
 if not p.exists():return False
 a=read(p)
 return commit in a['reusable_source_commits'] and all(sha(ROOT/f)==h for f,h in a['unchanged_numerical_assets'].items())
def legacy_stopped_unused():
 p=ROOT/('CONTINUATION_AMENDMENT.json' if (ROOT/'CONTINUATION_AMENDMENT.json').exists() else 'RECOVERY_AMENDMENT.json');s=read(p if p.exists() else ROOT/'STARTUP.json');return (ROOT/'STOP').exists() or False
def stopped():return (ROOT/'STOP').exists()
class Session:
 def __init__(self,name,config):
  if stopped():raise RuntimeError('Manual STOP before any new GPU service')
  self.name=name;self.config=config;self.dir=ROOT/'sessions'/name;self.dir.mkdir(parents=True,exist_ok=False)
  keys=['SystemRoot','WINDIR','TEMP','TMP','PATH','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE']
  env={k:os.environ[k] for k in keys if k in os.environ}
  env.update(HS_PREFILL_OUTPUT=str(self.dir/'initial.json'),HS_PREFILL_UB=str(config['prefill']))
  if not config.get('capture',False):env['HS_TRACE_OFF']='1'
  if config.get('matched'):env['HS_MATCHED_TARGET']='1'
  if config.get('plain'):env['HS_NO_TRANSFER']='1'
  native=config['native'];ub=config['ub'];k=config.get('k',2);cap=config.get('cap',128)
  available=subprocess.check_output([str(BIN/'b570-candidate-target.exe'),'--list-devices'],text=True,encoding='utf-8',errors='replace')
  import re
  devices=re.findall(r'(Vulkan\d+): Intel\(R\) Arc\(TM\) B570 Graphics',available)
  if len(devices)!=1:raise RuntimeError('Exactly one physical B570 required before loading: '+available)
  device=devices[0]
  save(self.dir/'DEVICE_PREFLIGHT.json',dict(utc=now(),selected_device=device,available=available,model_forwards=0))
  cmd=[str(BIN/('b570-candidate-native.exe' if native else 'b570-candidate-target.exe')),'--model',str(ASSET/'models/gguf/Qwen3-8B-Q8_0.gguf'),'--device',device,'--n-gpu-layers','all','--fit','off','--ctx-size','1024','--batch-size','512','--ubatch-size',str(ub),'--flash-attn','off','--n-predict',str(cap-1 if native else cap),'--temp','0','--top-k','0','--top-p','1','--min-p','0','--seed','123','--threads','10','--threads-batch','10','--log-verbosity','2','--no-warmup']
  if native:cmd+=['--spec-type','draft-simple','--spec-draft-model',str(ASSET/'models/gguf/Qwen3-0.6B-Q8_0.gguf'),'--spec-draft-device',device,'--spec-draft-ngl','all','--spec-draft-n-max',str(k),'--spec-draft-n-min','0','--spec-draft-threads','10','--spec-draft-threads-batch','10']
  else:cmd+=['--reasoning','off','--simple-io','--no-conversation']
  if native:cmd.remove('--no-warmup')
  cmd[cmd.index('--log-verbosity')+1]='3'
  self.err=(self.dir/'stderr.log').open('w',encoding='utf-8');self.out=(self.dir/'stdout.log').open('w',encoding='utf-8')
  start=time.perf_counter();self.p=subprocess.Popen(cmd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,text=True,encoding='utf-8',errors='replace',bufsize=1,creationflags=subprocess.CREATE_NO_WINDOW)
  save(self.dir/'SESSION.json',{'utc':now(),'command':cmd,'environment':{k:v for k,v in env.items() if k.startswith('HS_')},'pid':self.p.pid,'creation_identity':identity(self.p.pid),'source_commit':source(),'config':config})
  self.q=queue.Queue()
  def pump():
   for line in self.p.stdout:self.out.write(line);self.out.flush();self.q.put(line.strip())
   self.q.put(None)
  threading.Thread(target=pump,daemon=True).start()
  while True:
   line=self.wait(240)
   if line=='HS_READY':break
  self.err.flush()
  observed=(self.dir/'stderr.log').read_text(encoding='utf-8',errors='replace')
  if f'using device {device} (Intel(R) Arc(TM) B570 Graphics)' not in observed:
   self.close();raise RuntimeError('Actual model-load device is not preflight B570; zero request forwards')
  if 'offloaded 37/37 layers to GPU' not in observed or (native and 'offloaded 29/29 layers to GPU' not in observed):
   self.close();raise RuntimeError('Incomplete actual GPU offload')
  self.load_seconds=time.perf_counter()-start
  save(self.dir/'SESSION_LOAD.json',dict(utc=now(),model_and_context_load_seconds=self.load_seconds,scope="Excluded cold session initialization before HS_READY; explicit warm request follows"))
 def wait(self,timeout=300):
  begin=time.perf_counter()
  while time.perf_counter()-begin<timeout:
   if stopped():self.close();raise RuntimeError('Hard stop before new work')
   try:
    line=self.q.get(timeout=1)
    if line is None:
     try:code=self.p.wait(timeout=5)
     except subprocess.TimeoutExpired:code=self.p.poll()
     raise RuntimeError(f'Frontend exited {code}; {self.dir}')
    return line
   except queue.Empty:heartbeat(self.p.pid)
  self.close();raise TimeoutError('Owned frontend no result')
 def request(self,unit,inp,warm=False):
  if stopped():raise RuntimeError('Hard stop')
  short=hashlib.sha256(unit.encode()).hexdigest()[:20];folder=ROOT/'raw'/short
  if (folder/'RESULT.json').exists():
   r=read(folder/'RESULT.json');assert r['unit_id']==unit and r['config']==self.config and compatible_commit(r['source_commit'])
   for p,h in r['files'].items():assert sha(ROOT/p)==h
   return r
  folder.mkdir(parents=True,exist_ok=True)
  for previous in folder.glob('attempt-*'):
   if (previous/'INFRA_REJECTION.json').exists():continue
   capture=previous/'capture.json';metric=previous/'capture.json.metrics.json'
   if not capture.exists() or not metric.exists():continue
   try:
    saved_capture=read(capture);saved_metrics=read(metric);endpoint(saved_capture,self.config.get('cap',128))
    valid=saved_metrics.get('request_id')==unit and saved_metrics.get('raw_count')==len(saved_capture['ids'])
   except (ValueError,KeyError,AssertionError,TypeError):valid=False
   if valid:raise RuntimeError('Complete scientific payload exists without RESULT; independent CPU recovery required before resume, no new model request: '+str(previous))
  attempt=folder/('attempt-'+uuid.uuid4().hex);attempt.mkdir()
  req={'request_id':unit,'prompt_ids':inp['prompt_ids'],'output':str(attempt/'capture.json'),'task':inp['id']}
  if not warm and inp.get('checkpoint_window'):req['checkpoint_window']=inp['checkpoint_window']
  if inp.get('resume'):req['resume']=inp['resume']
  save(attempt/'START.json',{'utc':now(),'source_commit':source(),'unit_id':unit,'request':req,'config':self.config,'input_sha256':hashlib.sha256(json.dumps(inp,sort_keys=True).encode()).hexdigest(),'warm':warm,'session':self.name})
  events=[json.loads(s) for s in (ROOT/'LEDGER.jsonl').read_text().splitlines()] if (ROOT/'LEDGER.jsonl').exists() else []
  count=sum(e.get('event')=='REQUEST_START' and e.get('warm')==warm for e in events)
  if count>=(48 if warm else 312):raise RuntimeError('Request budget exhausted')
  event('REQUEST_START',unit_id=unit,session=self.name,warm=warm)
  start=time.perf_counter();self.p.stdin.write(json.dumps(req)+'\n');self.p.stdin.flush()
  try:
   while True:
    line=self.wait()
    if line.startswith('HS_RESULT '):metrics=json.loads(line[10:]);break
   assert metrics['request_id']==unit
   cap=read(attempt/'capture.json');assert cap['prompt_ids']==inp['prompt_ids']
   ep=endpoint(cap,self.config.get('cap',128))
   assert metrics['reset_target']['max']==-1 and metrics['reset_target']['min']==-1
   if self.config['native']:assert metrics['reset_draft']['max']==-1 and metrics['reset_draft']['min']==-1
   if cap['transfer']:
    t=cap['transfer'];assert t['kv_equal'] and t['source_unchanged'] and t['pending_id']==ep['ids'][0]
    assert t['before']==t['after']==t['source_after'];assert t['destination_ub']==self.config['ub']
   r={'unit_id':unit,'task':inp['id'],'session':self.name,'warm':warm,'config':self.config,'endpoint':ep,'metrics':metrics,'host_seconds':time.perf_counter()-start,'source_commit':source(),'files':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in attempt.rglob('*') if p.is_file()}}
   save(folder/'RESULT.json',r);event('REQUEST_COMPLETE',unit_id=unit,warm=warm,host_seconds=r['host_seconds']);return r
  except BaseException as e:
   save(attempt/'FAILURE.json',{'utc':now(),'error':repr(e),'code':self.p.poll()});event('REQUEST_INFRA_FAILURE',unit_id=unit,error=repr(e));raise
 def close(self):
  cleanup_start=time.perf_counter()
  if self.p.poll() is None:
   try:self.p.stdin.close();self.p.wait(timeout=20)
   except (subprocess.TimeoutExpired,OSError):self.p.kill();self.p.wait(timeout=10)
  self.err.close();self.out.close()
  save(self.dir/'SESSION_CLOSE.json',dict(utc=now(),process_exit_code=self.p.poll(),model_session_cleanup_seconds=time.perf_counter()-cleanup_start,scope="Excluded session teardown after last complete request; continuation context cleanup is inside whole-request timer"))
def heartbeat(worker=None):save(ROOT/'STATUS.json',{'utc':now(),'stage':STAGE,'controller_pid':os.getpid(),'creation_identity':identity(os.getpid()),'worker_pid':worker,'completed':sum(1 for _ in (ROOT/'raw').glob('*/RESULT.json'))})
STAGE='IDLE'
def run_sessions(stage,sessions):
 global STAGE;STAGE=stage
 if (ROOT/f'{stage}_SCHEDULE.json').exists():assert read(ROOT/f'{stage}_SCHEDULE.json')==sessions
 else:save(ROOT/f'{stage}_SCHEDULE.json',sessions)
 event('STAGE',stage=stage);results=[]
 for si,spec in enumerate(sessions):
  keys=[f'{stage}/{si}/{ri}/{inp["id"]}' for ri,inp in enumerate(spec['inputs'])]
  paths=[ROOT/'raw'/hashlib.sha256(k.encode()).hexdigest()[:20]/'RESULT.json' for k in keys]
  if all(p.exists() for p in paths):
   cached=[read(p) for p in paths]
   for key,r in zip(keys,cached):
    assert r['unit_id']==key and r['config']==spec['config'] and compatible_commit(r['source_commit'])
    for f,h in r['files'].items():assert sha(ROOT/f)==h
   results.extend(cached);event('SESSION_REUSED',stage=stage,session_index=si,requests=len(cached));continue
  session=Session(f'{stage}-{si:03d}-{uuid.uuid4().hex[:6]}',spec['config'])
  try:
   results.append(session.request(f'{stage}/{si}/WARM/{session.name}',spec['inputs'][0],True))
   for ri,inp in enumerate(spec['inputs']):results.append(session.request(f'{stage}/{si}/{ri}/{inp["id"]}',inp))
  finally:session.close()
  heartbeat()
 save(ROOT/f'{stage}_RESULTS.json',results);return results
def acquire():
 lock=ROOT/'LOCK.json'
 if lock.exists():
  l=read(lock)
  if identity(l['pid'])==l['creation_identity']:raise RuntimeError('Live controller already owns lock')
  lock.rename(ROOT/('LOCK.stale-'+uuid.uuid4().hex+'.json'))
 with lock.open('x',encoding='utf-8') as f:json.dump({'pid':os.getpid(),'creation_identity':identity(os.getpid()),'utc':now()},f)

def release():

 (ROOT/'LOCK.json').unlink(missing_ok=True)
def old_inputs():
 manifest=read(OLD/'artifacts/b570_prefill_diagnostic_v1/INPUTS.json')
 return [{'id':t,'prompt_ids':read(i['ids']),'formatted_prompt':Path(i['text']).read_text(encoding='utf-8')} for t,i in manifest.items()]
def g0():
 inputs=old_inputs();configs={'R':{'native':False,'prefill':128,'ub':128,'plain':True},'N0':{'native':True,'prefill':1,'ub':1,'k':2},'N1':{'native':True,'prefill':128,'ub':1,'k':2}}
 sessions=[{'config':dict(configs[c],capture=False),'inputs':inputs} for rep in range(2) for c in configs]
 results=run_sessions('G0',sessions);expected=read(OLD/'artifacts/b570_prefill_diagnostic_v1/evaluation/HISTORICAL_EXPECTED.json');fails=[]
 for r in results:
  if r['warm']:continue
  si=int(r['unit_id'].split('/')[1]);cond=list(configs)[si%3];historical='R' if cond=='N1' else cond
  ref=expected[f'{r["task"]}/{historical}/1'];ep=dict(ref,reason='EOG' if ref['endpoint']=='EOG' else 'CAP')
  if not equal(r['endpoint'],ep):fails.append({'unit_id':r['unit_id'],'task':r['task'],'condition':cond,'observed_length':len(r['endpoint']['ids']),'expected_length':len(ep['ids'])})
 bridge_tasks=[i for i in inputs if i['id'] in ['HumanEval/134','HumanEval/42','HumanEval/145','HumanEval/138','HumanEval/58']]
 bridgeconfigs=[{'native':False,'matched':True,'prefill':128,'ub':1,'capture':True},{'native':True,'k':2,'prefill':128,'ub':1,'capture':True}]
 br=run_sessions('G0_BRIDGE',[{'config':c,'inputs':bridge_tasks} for _ in range(2) for c in bridgeconfigs])
 for r in br:
  if r['warm']:continue
  ref=expected[f'{r["task"]}/R/1'];ep=dict(ref,reason='EOG' if ref['endpoint']=='EOG' else 'CAP')
  if not equal(r['endpoint'],ep):fails.append({'unit_id':r['unit_id'],'task':r['task'],'condition':'BRIDGE'})
 save(ROOT/'G0.json',{'status':'PASS' if not fails else 'BLOCKED_REFERENCE','requests':144,'bridge_requests':20,'warm':10,'failures':fails});print(read(ROOT/'G0.json'),flush=True)
if __name__=='__main__':
 acquire()
 try:
  if sys.argv[1]=='g0':g0()
  elif sys.argv[1]=='schedule':run_sessions(sys.argv[2],read(sys.argv[3]))
 except BaseException:
  save(ROOT/('CONTROLLER_FAILURE-'+uuid.uuid4().hex+'.json'),{'utc':now(),'traceback':traceback.format_exc()});raise
 finally:release()
