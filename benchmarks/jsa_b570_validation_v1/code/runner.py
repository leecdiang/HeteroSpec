"""Bounded four-path executor. No automatic scientific retries or candidate edits."""
import os,sys,json,time,hashlib,subprocess,threading,queue,ctypes,re,traceback
from pathlib import Path
from datetime import datetime,timezone
R=Path('C:/hs/jsa-b570-run-v1');REPO=Path('C:/hs/jsa-b570-v1')
def now():return datetime.now(timezone.utc).isoformat()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8');os.replace(tmp,p)
def event(kind,**kw):
 with (R/'LEDGER.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(dict(utc=now(),event=kind,**kw))+'\n');f.flush();os.fsync(f.fileno())
def identity(pid):
 k=ctypes.WinDLL('kernel32');k.OpenProcess.restype=ctypes.c_void_p;k.GetProcessTimes.argtypes=[ctypes.c_void_p]*5;k.CloseHandle.argtypes=[ctypes.c_void_p]
 h=k.OpenProcess(0x1000,0,pid)
 if not h:return None
 try:
  t=[ctypes.c_ulonglong() for _ in range(4)];return str(t[0].value) if k.GetProcessTimes(h,*map(ctypes.byref,t)) else None
 finally:k.CloseHandle(h)
def budget():
 ev=[json.loads(s) for s in (R/'LEDGER.jsonl').read_text(encoding='utf8').splitlines()] if (R/'LEDGER.jsonl').exists() else []
 starts=[e for e in ev if e['event']=='REQUEST_START'];warm=sum(e['warm'] for e in starts);eng=sum(not e['warm'] and e['stage']!='D' for e in starts);formal=sum(not e['warm'] and e['stage']=='D' for e in starts)
 sessions=[load(p) for p in (R/'sessions').glob('*/SESSION_CLOSE.json')];engs=sum(s['active_seconds'] for s in sessions if s['stage']!='D');forms=sum(s['active_seconds'] for s in sessions if s['stage']=='D')
 return dict(engineering=eng,formal=formal,warm=warm,total=len(starts),engineering_active_seconds=engs,formal_active_seconds=forms,auxiliary_decodes=0)
def stopped():return (R/'STOP').exists()
def parse_endpoint(x,family):
 meta=load(R/('QWEN_RUNTIME.json' if family=='Qwen' else 'TOKENIZATION_BINDINGS.json'));v=meta['vocab_tokens'];es=set(meta['runtime_eog_ids']);ids=x['ids'];flags=x['eog']
 assert len(ids)==len(flags)>0 and all(type(i)==int and 0<=i<v for i in ids)
 assert all(type(b)==bool for b in flags) and flags==[i in es for i in ids]
 n=min(128,next((i+1 for i,b in enumerate(flags) if b),len(ids)));assert flags[n-1] or n==128
 return dict(ids=ids[:n],eog=flags[:n],reason='EOG' if flags[n-1] else 'CAP',raw_suffix=len(ids)-n)
PROGRAMS={'R':('original','b570-closeout-target.exe',False,128,True),'N':('original','b570-closeout-native.exe',True,1,False),'M':('candidate','b570-candidate-target.exe',False,1,True),'C':('candidate','b570-candidate-native.exe',True,1,True)}
class Session:
 def __init__(self,spec):
  self.spec=spec;self.name=spec['session'];self.dir=R/'sessions'/self.name;self.dir.mkdir(parents=True,exist_ok=False);self.start=time.perf_counter();self.closed=False;self.p=None
  self.family=spec['family'];self.stage=spec['stage'];self.arm=spec['arm'];folder,exe,native,ub,plain=PROGRAMS[self.arm];self.native=native;self.exe=R/'bin'/folder/exe
  if stopped():raise RuntimeError('MANUAL_STOP')
  b=budget();assert b['engineering_active_seconds']<28800 and b['formal_active_seconds']<28800 and b['engineering_active_seconds']+b['formal_active_seconds']<57600
  bindings=load(R/'BINARY_BINDINGS.json')
  for p in self.exe.parent.glob('*'):
   if p.suffix in ['.exe','.dll']:assert sha(p)==bindings[p.relative_to(R).as_posix()]['sha256']
  env={k:os.environ[k] for k in ['SystemRoot','WINDIR','TEMP','TMP','PATH','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'] if k in os.environ}
  env.update(HS_PREFILL_OUTPUT=str(self.dir/'initial.json'),HS_PREFILL_UB='128')
  if not spec['capture']:env['HS_TRACE_OFF']='1'
  if plain:env['HS_NO_TRANSFER']='1'
  available=subprocess.check_output([str(self.exe),'--list-devices'],text=True,encoding='utf8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
  devices=re.findall(r'(Vulkan\d+): Intel\(R\) Arc\(TM\) B570 Graphics',available);assert len(devices)==1;device=devices[0]
  save(self.dir/'DEVICE_PREFLIGHT.json',dict(utc=now(),selected_device=device,available=available,model_forwards=0))
  models=load(R/('QWEN_MODELS.json' if self.family=='Qwen' else 'MODEL_CHOICE.json'))['models']
  for role,model in models.items():assert sha(model['path'])==model['sha256'],role+' model identity'
  inventory=json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',"@{device=@(Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion);processes=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match 'b570|llama|ToDesk|forza'} | Select-Object ProcessId,Name,CommandLine)} | ConvertTo-Json -Depth 4 -Compress"],text=True,encoding='utf8'))
  assert not any(re.search(r'b570|llama',x['Name'],re.I) for x in inventory['processes']),'OTHER_MODEL_GPU_SESSION'
  assert next(x['DriverVersion'] for x in inventory['device'] if x['Name']=='Intel(R) Arc(TM) B570 Graphics')=='32.0.101.9034','DRIVER_IDENTITY_CHANGE'
  save(self.dir/'ENVIRONMENT.json',dict(utc=now(),**inventory,temperature='UNAVAILABLE_NO_PINNED_READOUT',frequency='UNAVAILABLE_NO_PINNED_READOUT',policy='Record interference; never change desktop apps or power configuration.'))
  cmd=[str(self.exe),'--model',models['target']['path'],'--device',device,'--n-gpu-layers','all','--fit','off','--ctx-size','1024','--batch-size','512','--ubatch-size',str(ub),'--flash-attn','off','--n-predict',str(127 if native else 128),'--temp','0','--top-k','0','--top-p','1','--min-p','0','--seed','123','--threads','10','--threads-batch','10','--log-verbosity','3']
  if native:cmd+=['--spec-type','draft-simple','--spec-draft-model',models['draft']['path'],'--spec-draft-device',device,'--spec-draft-ngl','all','--spec-draft-n-max','2','--spec-draft-n-min','0','--spec-draft-threads','10','--spec-draft-threads-batch','10']
  else:cmd+=['--no-warmup','--reasoning','off','--simple-io','--no-conversation']
  self.err=(self.dir/'stderr.log').open('w',encoding='utf8');self.out=(self.dir/'stdout.log').open('w',encoding='utf8');self.q=queue.Queue()
  self.p=subprocess.Popen(cmd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,text=True,encoding='utf8',errors='replace',bufsize=1,creationflags=subprocess.CREATE_NO_WINDOW)
  self.pid_identity=identity(self.p.pid);assert self.pid_identity
  event('SESSION_START',session=self.name,stage=self.stage,pid=self.p.pid,creation_identity=self.pid_identity)
  save(self.dir/'SESSION.json',dict(utc=now(),command=cmd,environment={k:v for k,v in env.items() if k.startswith('HS_')},pid=self.p.pid,creation_identity=self.pid_identity,spec=spec,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()))
  def pump():
   for line in self.p.stdout:self.out.write(line);self.out.flush();self.q.put(line.strip())
   self.q.put(None)
  threading.Thread(target=pump,daemon=True).start()
  try:
   while self.wait(300)!='HS_READY':pass
   log=(self.dir/'stderr.log').read_text(encoding='utf8',errors='replace')
   assert f'using device {device} (Intel(R) Arc(TM) B570 Graphics)' in log
   counts=re.findall(r'offloaded (\d+)/(\d+) layers to GPU',log);assert len(counts)==(2 if native else 1) and all(a==b for a,b in counts)
   expected=load(R/('QWEN_RUNTIME.json' if self.family=='Qwen' else 'TOKENIZATION_BINDINGS.json'))['offload_layers']
   assert list(map(lambda x:int(x[0]),counts))==([expected['target'],expected['draft']] if native else [expected['target']])
   ps=f"(Get-Process -Id {self.p.pid}).Modules | Select-Object FileName,ModuleName | ConvertTo-Json -Compress"
   modules=json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',ps],text=True,encoding='utf8'))
   actual=[dict(x,sha256=sha(x['FileName'])) for x in modules if x['ModuleName'].lower().startswith(('llama','ggml','b570'))]
   for x in actual:
    assert Path(x['FileName']).resolve().is_relative_to(self.exe.parent.resolve()),x
   save(self.dir/'MODULES.json',dict(actual=actual,offload_counts=counts,all_layers_on_B570=True))
   self.load_seconds=time.perf_counter()-self.start
   save(self.dir/'SESSION_LOAD.json',dict(utc=now(),seconds=self.load_seconds,implicit_forwards=0,implicit_warmup_disabled_by_frozen_source=True))
  except BaseException:self.close();raise
 def wait(self,timeout=600):
  deadline=time.perf_counter()+timeout
  while time.perf_counter()<deadline:
   if stopped():raise RuntimeError('MANUAL_STOP')
   b=budget();live=time.perf_counter()-self.start
   assert b['engineering_active_seconds']+(live if self.stage!='D' else 0)<28800 and b['formal_active_seconds']+(live if self.stage=='D' else 0)<28800 and b['engineering_active_seconds']+b['formal_active_seconds']+live<57600,'ACTIVE_GPU_BUDGET'
   try:
    line=self.q.get(timeout=1)
    if line is None:raise RuntimeError('Frontend exited '+str(self.p.poll())+' '+self.name)
    return line
   except queue.Empty:pass
  raise TimeoutError('Owned frontend timeout')
 def request(self,req):
  unit=req['unit'];warm=req['warm'];b=budget();assert b['total']<704
  if warm:assert b['warm']<64
  if not warm:assert b['formal']<384 if self.stage=='D' else b['engineering']<256
  if stopped():raise RuntimeError('MANUAL_STOP')
  folder=R/'raw'/hashlib.sha256(unit.encode()).hexdigest()[:24];folder.mkdir(parents=True,exist_ok=False)
  inp=load(R/req['input_file'])[req['input_index']];out=folder/'capture.json';payload=dict(request_id=unit,prompt_ids=inp['prompt_ids'],output=str(out),task=inp['id'])
  save(folder/'START.json',dict(utc=now(),unit=unit,payload=payload,spec=self.spec,input_sha256=hashlib.sha256(json.dumps(inp,sort_keys=True).encode()).hexdigest(),warm=warm,runner_sha256=sha(__file__)))
  event('REQUEST_START',unit=unit,stage=self.stage,session=self.name,warm=warm,arm=self.arm,task=inp['id'],family=self.family)
  start=time.perf_counter_ns()
  try:
   self.p.stdin.write(json.dumps(payload)+'\n');self.p.stdin.flush()
   while True:
    line=self.wait()
    if line.startswith('HS_RESULT '):metrics=json.loads(line[10:]);break
   assert metrics['request_id']==unit
   raw=load(out);diskmetrics=load(str(out)+'.metrics.json');assert metrics==diskmetrics and raw['prompt_ids']==inp['prompt_ids']
   ep=parse_endpoint(raw,self.family);assert metrics['raw_count']==len(raw['ids'])
   assert metrics['reset_target']['min']==metrics['reset_target']['max']==-1
   if self.native:assert metrics['reset_draft']['min']==metrics['reset_draft']['max']==-1
   host=(time.perf_counter_ns()-start)/1e9
   receipt=dict(unit=unit,task=inp['id'],arm=self.arm,stage=self.stage,family=self.family,round=self.spec['round'],capture=self.spec['capture'],warm=warm,session=self.name,host_seconds=host,endpoint=ep,metrics=metrics,raw_ids=raw['ids'],raw_eog=raw['eog'],source_epoch=load(self.dir/'SESSION.json')['source_commit'],files={p.relative_to(R).as_posix():sha(p) for p in folder.iterdir() if p.is_file()})
   save(folder/'RESULT.json',receipt);event('REQUEST_COMPLETE',unit=unit,stage=self.stage,warm=warm,host_seconds=host)
   save(R/'STATUS.json',dict(utc=now(),stage=self.stage,current_session=self.name,last_complete=unit,budget=budget()));print('COMPLETE',unit,round(host,3),flush=True)
   return receipt
  except BaseException as e:save(folder/'FAILURE.json',dict(utc=now(),error=repr(e)));event('REQUEST_FAILURE',unit=unit,error=repr(e));raise
 def close(self):
  if self.closed:return
  self.closed=True;begin=time.perf_counter()
  if self.p and self.p.poll() is None:
   try:self.p.stdin.close();self.p.wait(timeout=20)
   except (subprocess.TimeoutExpired,OSError):
    if identity(self.p.pid)==self.pid_identity:self.p.kill();self.p.wait(timeout=10)
  if hasattr(self,'err'):self.err.close();self.out.close()
  save(self.dir/'SESSION_CLOSE.json',dict(utc=now(),stage=self.stage,active_seconds=time.perf_counter()-self.start,cleanup_seconds=time.perf_counter()-begin,exit_code=self.p.poll() if self.p else None))
def run(stage):
 if stage!='A':
  assert load(R/'REMOTE_FREEZE_RECEIPT.json')['status']=='PASS';assert load(R/'A_VERIFICATION.json')['status']=='PASS'
  for rel,x in load(R/'F0.json')['frozen_files'].items():
   assert sha(R/rel)==x['sha256'],rel
   if rel.startswith('code/'):assert sha(REPO/'benchmarks/jsa_b570_validation_v1'/rel)==x['sha256'],rel+' current source'
  events=[json.loads(s) for s in (R/'LEDGER.jsonl').read_text(encoding='utf8').splitlines()]
  first=next(e for e in events if e['event']=='SESSION_START');assert (datetime.now(timezone.utc)-datetime.fromisoformat(first['utc'])).total_seconds()<7*86400,'CALENDAR_BUDGET'
 schedule=load(R/'REQUEST_SCHEDULE.json')[stage]
 for spec in schedule:
  if (R/'sessions'/spec['session']).exists():
   # No replay of a session, including partial/failed requests.
   assert all((R/'raw'/hashlib.sha256(q['unit'].encode()).hexdigest()[:24]/'RESULT.json').exists() for q in spec['requests']),'PARTIAL_ALREADY_STARTED_NO_RETRY'
   continue
  s=Session(spec)
  try:
   for q in spec['requests']:s.request(q)
  finally:s.close()
 save(R/(stage+'_EXECUTION.json'),dict(status='COMPLETE',utc=now(),budget=budget()))
if __name__=='__main__':
 lock=R/'LOCK.json'
 if lock.exists():
  l=load(lock);assert identity(l['pid'])!=l['identity'],'Live study controller'
  lock.rename(R/('LOCK.stale-'+str(time.time_ns())+'.json'))
 save(lock,dict(pid=os.getpid(),identity=identity(os.getpid()),utc=now()))
 try:run(sys.argv[1])
 except BaseException:save(R/('CONTROLLER_FAILURE-'+str(time.time_ns())+'.json'),dict(utc=now(),traceback=traceback.format_exc()));raise
 finally:lock.unlink(missing_ok=True)
