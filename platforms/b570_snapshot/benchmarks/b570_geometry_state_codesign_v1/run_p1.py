"""Authorized P1 launcher only. No work on import; refuses absent exact F0 authorization."""
from __future__ import annotations
import argparse,ctypes,hashlib,json,os,queue,subprocess,threading,time,uuid
from pathlib import Path
from protocol import read_json,digest,file_sha,validate_plan,require,encode
from host_request import admit,readback
from evidence_adapter import adapt
ROOT=Path(__file__).resolve().parent
RUN=ROOT/'_host/run'
LIMITS=dict(process_attempts=80,request_starts=80,operator_starts=0,owned_seconds=7200,new_bytes=4*1024**3,process_timeout_seconds=300,minimum_disk_free_bytes=10*1024**3,minimum_available_RAM_bytes=2*1024**3,maximum_owned_working_set_bytes=12*1024**3,safety_poll_seconds=.1,minimum_B570_signed_headroom_bytes=536870912)
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(encode(x));f.flush();os.fsync(f.fileno())
def journal(x):
 RUN.mkdir(parents=True,exist_ok=True)
 with (RUN/'LEDGER.jsonl').open('ab',buffering=0) as f:f.write(encode(dict(epoch=time.time(),**x)));os.fsync(f.fileno())
def ledger():return [json.loads(s) for s in (RUN/'LEDGER.jsonl').read_text().splitlines()] if (RUN/'LEDGER.jsonl').exists() else []
def owned_seconds():
 rows=ledger();closed={r['slot']:r['owned_seconds'] for r in rows if r['event']=='PROCESS_CLOSED'}
 return sum(closed.get(r['slot'],time.time()-r['epoch']) for r in rows if r['event']=='PROCESS_ATTEMPT')
def bytes_used():return sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
def pin_gate(runtime,f0):
 for row in f0['source_files']:
  require(file_sha(ROOT/row['path'])==row['sha256'],'source changed: '+row['path'])
 for role in runtime['roles'].values():
  for x in role['modules']+role['files']:require(file_sha(Path(x['path']))==x['sha256'],'runtime bytes changed')
 for x in runtime['models'].values():require(file_sha(Path(x['path']))==x['sha256'],'model bytes changed')
 for x in runtime['driver_files']:require(file_sha(Path(x['path']))==x['sha256'],'driver bytes changed')

def modules(pid):
 from ctypes import wintypes as W
 k=ctypes.WinDLL('kernel32',use_last_error=True);ps=ctypes.WinDLL('psapi',use_last_error=True)
 k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
 ps.EnumProcessModulesEx.argtypes=[W.HANDLE,ctypes.POINTER(W.HMODULE),W.DWORD,ctypes.POINTER(W.DWORD),W.DWORD]
 ps.GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
 k.CloseHandle.argtypes=[W.HANDLE]
 h=k.OpenProcess(0x410,False,pid);require(bool(h),'owned PID unavailable');a=(W.HMODULE*4096)();n=W.DWORD()
 try:
  require(ps.EnumProcessModulesEx(h,a,ctypes.sizeof(a),ctypes.byref(n),3)!=0,'module list unavailable');rows=[]
  for handle in a[:n.value//ctypes.sizeof(W.HMODULE)]:
   s=ctypes.create_unicode_buffer(32768);require(ps.GetModuleFileNameExW(h,handle,s,len(s))>0,'module path');p=Path(s.value);rows.append(dict(name=p.name,path=str(p),sha256=file_sha(p),bytes=p.stat().st_size))
  return rows
 finally:k.CloseHandle(h)
def memory_status(pid):
 from ctypes import wintypes as W
 class M(ctypes.Structure):_fields_=[('length',W.DWORD),('load',W.DWORD)]+[(n,ctypes.c_ulonglong) for n in ('total','available','page','page_available','virtual','virtual_available','extended')]
 class P(ctypes.Structure):_fields_=[('cb',W.DWORD),('faults',W.DWORD)]+[(n,ctypes.c_size_t) for n in ('peak_ws','ws','peak_pool_p','pool_p','peak_pool_np','pool_np','page','peak_page','private')]
 k=ctypes.WinDLL('kernel32',use_last_error=True);ps=ctypes.WinDLL('psapi',use_last_error=True);k.OpenProcess.restype=W.HANDLE;k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.CloseHandle.argtypes=[W.HANDLE];ps.GetProcessMemoryInfo.argtypes=[W.HANDLE,ctypes.POINTER(P),W.DWORD]
 m=M();m.length=ctypes.sizeof(m);require(k.GlobalMemoryStatusEx(ctypes.byref(m))!=0,'RAM sample unavailable');h=k.OpenProcess(0x410,False,pid);require(h,'owned process RAM handle');p=P();p.cb=ctypes.sizeof(p)
 try:require(ps.GetProcessMemoryInfo(h,ctypes.byref(p),p.cb)!=0,'owned RAM sample unavailable')
 finally:k.CloseHandle(h)
 return dict(available=m.available,owned_working_set=p.ws)


def busy_gate():
 import csv,io
 out=subprocess.run([str(Path(os.environ.get('WINDIR','C:/Windows'))/'System32/tasklist.exe'),'/FO','CSV','/NH'],capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
 rows=list(csv.reader(io.StringIO(out.stdout.decode('mbcs'))));active=[dict(name=r[0],pid=int(r[1])) for r in rows if len(r)>1 and any(n in r[0].lower() for n in ('b570','llama','operator-replay'))]
 require(not active,'Other native experiment owns the host: '+str(active))
 return dict(status='NO_OTHER_KNOWN_NATIVE_WORKER',sampled_epoch=time.time(),unknown_other_GPU_consumers='NOT_ESTABLISHED_BY_PROCESS_NAMES')
def native_lifetime(p):
 from ctypes import wintypes as W
 class FT(ctypes.Structure):_fields_=[('low',W.DWORD),('high',W.DWORD)]
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetProcessTimes.argtypes=[W.HANDLE,ctypes.POINTER(FT),ctypes.POINTER(FT),ctypes.POINTER(FT),ctypes.POINTER(FT)]
 created,exited,kernel,user=FT(),FT(),FT(),FT()
 require(k.GetProcessTimes(W.HANDLE(int(p._handle)),ctypes.byref(created),ctypes.byref(exited),ctypes.byref(kernel),ctypes.byref(user))!=0,'native lifetime timestamps unavailable')
 value=lambda x:(x.high<<32)|x.low
 return dict(created_FILETIME_100ns=value(created),exited_FILETIME_100ns=value(exited),native_owned_seconds=(value(exited)-value(created))/1e7)

def stage_gate(plan,index,records):
 slot=plan['slots'][index];refs={}
 for s in plan['slots'][:index]:
  if s['arm']=='R' and s['slot'] in records:refs.setdefault(s['task'],[]).append(records[s['slot']]['endpoint'])
 if index>=8:
  require(len(refs)==4 and all(len(v)==2 and v[0]==v[1] for v in refs.values()),'R stability control failed')
 if index>=12:
  for s in plan['slots'][8:12]:require(records[s['slot']]['endpoint']==refs[s['task']][0],'R_SHADOW counts failed')
 if index>=16:
  for s in plan['slots'][12:16]:require(records[s['slot']]['endpoint']==refs[s['task']][0],'R_SHADOW observer failed')
 # Valid treatment/reference differences remain counterexamples. Observer differences stop.
 if slot['mode']=='diagnostic' and slot['arm']!='R_SHADOW':
  require(any(s['task']==slot['task'] and s['arm']==slot['arm'] and s['mode']=='counts' and s['slot'] in records for s in plan['slots'][:index]),'missing matching counts receipt')

class Worker:
 def __init__(self,a,runtime):self.a=a;self.runtime=runtime;self.p=None;self.lines=[];self.errors=[];self.events=[];self.q=queue.Queue();self.stop=threading.Event();self.watch_error=[];self.closed=False
 def start(self):
  rows=ledger();require(not any(r.get('slot')==self.a.slot and r['event']=='PROCESS_ATTEMPT' for r in rows),'slot was already attempted')
  require(sum(r['event']=='PROCESS_ATTEMPT' for r in rows)<80 and owned_seconds()<7200 and bytes_used()<LIMITS['new_bytes'],'phase budget')
  self.d=RUN/self.a.slot;self.d.mkdir(parents=True,exist_ok=False);save(self.d/'LAUNCH.json',readback(self.a));self.begin=time.monotonic();self.start_epoch=time.time();self.life_id=uuid.uuid4().hex
  # Durable before-start reservation remains charged even if Popen/model load fails.
  journal(dict(event='PROCESS_ATTEMPT',slot=self.a.slot,lifecycle_id=self.life_id,argv=list(self.a.argv),request_sha256=self.a.request_sha256))
  env=os.environ.copy()
  for k in list(env):
   if k.startswith('VK_') or k.startswith('GGML_VK_') or k.startswith('LLAMA_'):env.pop(k)
  try:
   self.p=subprocess.Popen(self.a.argv,cwd=Path(self.a.argv[0]).parent,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,bufsize=0,creationflags=subprocess.CREATE_NO_WINDOW)
   journal(dict(event='OWNED_PID',slot=self.a.slot,pid=self.p.pid,lifecycle_id=self.life_id))
   def output(stream,path,parse):
    with path.open('xb',buffering=0) as f:
     for line in iter(stream.readline,b''):
      f.write(line)
      if parse:
       try:
        x=json.loads(line);self.events.append(x);self.q.put(x)
        if x.get('event') in ('FORWARD_START','FORWARD_RETURN'):journal(dict(event=x['event'],slot=self.a.slot,native=x))
       except Exception as e:self.q.put(dict(event='PARSE_ERROR',reason=str(e)))
    if parse:self.q.put(dict(event='EOF'))
   self.threads=[threading.Thread(target=output,args=(self.p.stdout,self.d/'stdout.jsonl',True),daemon=True),threading.Thread(target=output,args=(self.p.stderr,self.d/'stderr.log',False),daemon=True)]
   for t in self.threads:t.start()
   def watch():
    import shutil
    try:
     while not self.stop.wait(LIMITS['safety_poll_seconds']):
      if self.p.poll() is not None:return
      m=memory_status(self.p.pid);sample=dict(epoch=time.time(),**m,disk_free=shutil.disk_usage(RUN).free,output_bytes=bytes_used(),owned_seconds=owned_seconds())
      with (self.d/'SAFETY.jsonl').open('ab') as f:f.write(encode(sample))
      require(time.monotonic()-self.begin<LIMITS['process_timeout_seconds'],'owned timeout')
      require(sample['owned_seconds']<7200 and sample['output_bytes']<LIMITS['new_bytes'],'global budget')
      require(sample['disk_free']>=LIMITS['minimum_disk_free_bytes'] and m['available']>=LIMITS['minimum_available_RAM_bytes'] and m['owned_working_set']<=LIMITS['maximum_owned_working_set_bytes'],'disk/RAM gate')
    except BaseException as e:
     self.watch_error.append(str(e));journal(dict(event='WATCHDOG_STOP',slot=self.a.slot,pid=self.p.pid,reason=str(e)));self.p.kill()
   self.watcher=threading.Thread(target=watch,daemon=True);self.watcher.start();ready=self.wait('READY');require(ready['pid']==self.p.pid and ready['forward_calls']==0,'ready identity')
   actual=modules(self.p.pid);loaded={x['name'].lower():x for x in actual}
   for pin in self.runtime['roles'][self.a.runtime_role]['modules']:
    x=loaded.get(pin['name'].lower());require(x and x['sha256']==pin['sha256'] and Path(x['path']).resolve()==Path(pin['path']).resolve(),'wrong loaded module')
   driver={str(Path(x['path']).resolve()).casefold():x for x in self.runtime['driver_files']}
   for x in actual:
    key=str(Path(x['path']).resolve()).casefold()
    if key in driver:require(x['sha256']==driver[key]['sha256'],'loaded driver drift')
    if x['name'].lower() in ('igvk64.dll','vulkan-1.dll'):require(key in driver,'unregistered Vulkan driver')
   require(not any('api_dump' in x['name'].lower() for x in actual),'API observer loaded')
   weights=[e for e in self.events if e['event']=='WEIGHT_MAP'];require(len(weights)==(2 if self.a.effective_k else 1),'role placement count');require(all(w['all_weights_Vulkan0'] for w in weights),'CPU model placement')
   text=(self.d/'stderr.log').read_text(encoding='utf-8',errors='replace');kv=[l for l in text.splitlines() if 'KV buffer size' in l];require(len(kv)==len(weights) and all('Vulkan0' in l and 'CPU' not in l for l in kv),'KV placement')
   save(self.d/'IDENTITY.json',dict(pid=self.p.pid,modules=actual,all_target_weights_offloaded=weights[0]['all_weights_Vulkan0'],no_draft_offload_violation=all(w['all_weights_Vulkan0'] for w in weights),weights=weights,kv_lines=kv,argv=list(self.a.argv),physical_residency='UNKNOWN'))
   self.p.stdin.write(b'{"op":"CHECK"}\n');self.p.stdin.flush();self.wait('CHECK_OK')
  except BaseException:self.close();raise
 def wait(self,event):
  end=self.begin+LIMITS['process_timeout_seconds']
  while True:
   x=self.q.get(timeout=max(.01,end-time.monotonic()))
   if x['event']==event:return x
   if x['event'] in ('ERROR','EOF','PARSE_ERROR'):raise RuntimeError(x)
   require(not self.watch_error,'watchdog gate')
 def request(self):
  require(sum(r['event']=='REQUEST_START' for r in ledger())<80,'request budget')
  (self.d/'REQUEST.wire').write_bytes(self.a.wire);save(self.d/'REQUEST.json',self.a.request)
  journal(dict(event='REQUEST_START',slot=self.a.slot,pid=self.p.pid,wire_sha256=self.a.wire_sha256))
  self.a.send(self.p.stdin);result=self.wait('RESULT');save(self.d/'RESULT.json',result);self.wait('PERSISTED');return result
 def close(self):
  if self.closed:return
  self.closed=True
  if not hasattr(self,'begin'):return
  if self.p:
   try:
    self.p.stdin.close();self.p.wait(timeout=max(.1,min(30,300-(time.monotonic()-self.begin))))
   except Exception:self.p.kill();self.p.wait()
   self.stop.set()
   for t in self.threads:t.join(timeout=5)
   self.watcher.join(timeout=5)
  life=dict(pid=self.p.pid if self.p else None,returncode=self.p.returncode if self.p else None,closed=True,owned_seconds=time.monotonic()-self.begin,lifecycle_id=self.life_id,watchdog_failures=self.watch_error)
  life['native_process_times']=native_lifetime(self.p) if self.p else None
  save(self.d/'LIFECYCLE.json',life);journal(dict(event='PROCESS_CLOSED',slot=self.a.slot,**life))

def authorize(f0,approval,receipt):
 require(f0['status']=='P0_COMPLETE_PENDING_AUTHOR_CONFIRMATION','F0 not admitted')
 require(approval['author_confirmed'] is True and approval['phase']=='P1' and approval['F0_sha256']==digest(f0) and approval['budget']==f0['budget'],'exact author authorization absent')
 require(isinstance(approval['authorization_source'],str) and approval['authorization_source'],'missing author evidence')
 require(receipt['F0_sha256']==digest(f0) and receipt['status']=='PASS_REMOTE_BYTE_READBACK' and len(receipt['commit'])==40,'remote F0 not authenticated')

def main():
 p=argparse.ArgumentParser();p.add_argument('--author-approval',type=Path,required=True);args=p.parse_args()
 f0=read_json(ROOT/'p0/F0_EXECUTION.json');authorize(f0,read_json(args.author_approval),read_json(ROOT/'p0/REMOTE_READBACK.json'))
 plan=read_json(ROOT/'p0/PLAN_P1.json');runtime=read_json(ROOT/'p0/RUNTIME.json');validate_plan(plan);require(digest(plan)==f0['plan_sha256'] and digest(runtime)==f0['runtime_sha256'],'plan/runtime drift');pin_gate(runtime,f0)
 require(not ledger(),'fresh P1 only; attempted slots require audited explicit recovery, never automatic replay')
 admissions=[admit(s,next(c for c in plan['panel'] if c['id']==s['task']),runtime) for s in plan['slots']]
 require([readback(a) for a in admissions]==read_json(ROOT/'p0/WIRES_P1.json'),'wire or launch drift')
 records={};error=None
 try:
  for i,(s,a) in enumerate(zip(plan['slots'],admissions)):
   stage_gate(plan,i,records);busy_gate();pin_gate(runtime,f0);w=Worker(a,runtime)
   try:w.start();w.request()
   finally:w.close()
   require(w.p.returncode==0 and not w.watch_error,'native lifecycle failed')
   rec=adapt(w.d,s,runtime,digest(runtime));save(w.d/'NORMALIZED.json',rec);records[s['slot']]=rec
   if s['mode']=='diagnostic' and s['arm']!='R_SHADOW':
    counts=next(x for x in plan['slots'] if x['task']==s['task'] and x['arm']==s['arm'] and x['mode']=='counts');require(rec['endpoint']==records[counts['slot']]['endpoint'],'observer endpoint failure')
   journal(dict(event='AUDIT_COMPLETED',slot=s['slot'],record_sha256=digest(rec)))
 except BaseException as e:error=str(e);raise
 finally:
  rows=ledger();attempted={r['slot'] for r in rows if r['event']=='PROCESS_ATTEMPT'}
  save(RUN/'CLOSEOUT.json',dict(status='STOPPED' if error else 'COMPLETED',error=error,process_attempts=len(attempted),request_starts=sum(r['event']=='REQUEST_START' for r in rows),forward_starts_observed=sum(r['event']=='FORWARD_START' for r in rows),original_R_successful_forwards=sum(records[s['slot']]['work']['target_continuation_callers']+1 for s in plan['slots'] if s['arm']=='R' and s['slot'] in records),operator_starts=0,owned_seconds=owned_seconds(),new_bytes=bytes_used(),unstarted=[{k:s[k] for k in ('slot','task','arm','session','mode')} for s in plan['slots'] if s['slot'] not in attempted],performance_aggregate='WITHHELD',automatic_P2=False))
if __name__=='__main__':main()
