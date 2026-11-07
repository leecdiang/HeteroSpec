from common98 import *
import threading,queue,re,math,collections
PLAN=load(ROOT/'PLAN.json');CASES={c['id']:c for c in load(ROOT/'INPUTS.json')['cases']}
EXE=ROOT/'build/Release/b570-boundary-worker.exe'
def rows():return [json.loads(s) for s in (ROOT/'LEDGER.jsonl').read_text().splitlines()] if (ROOT/'LEDGER.jsonl').exists() else []
def owned():
 rr=rows();starts={x['block']:x for x in rr if x['event']=='WORKER_STARTED'};closes={x['block']:x for x in rr if x['event']=='WORKER_CLOSED'}
 return sum(closes[b]['owned_seconds'] if b in closes else time.time()-x['epoch'] for b,x in starts.items())
def charge(kind,slot):
 rr=rows();assert not any(x.get('slot')==slot and x['event'] in ['REQUEST_STARTED','PROBE_STARTED'] for x in rr),'No replay of started slot'
 counts=collections.Counter(x['kind'] for x in rr if x['event'] in ['REQUEST_STARTED','PROBE_STARTED'])
 limit={'P1A':21,'P1B':38,'P1C':18,'P0':16,'P2':40,'probe':8}
 assert counts[kind]<limit[kind] and sum(v for k,v in counts.items() if k!='probe')<200 and owned()<21600
 event(event='PROBE_STARTED' if kind=='probe' else 'REQUEST_STARTED',kind=kind,slot=slot,counts_before=dict(counts))
def source_gate():
 f=load(ROOT/'F0_BASE.json');remote=load(ROOT/'F0_AUTHENTICATED.json')
 assert remote['status']=='PASS_ACTUAL_AUTHENTICATED_GITHUB_BYTES' and remote['before_new_forward'] and len(remote['commit'])==40
 assert digest(PLAN)==f['plan_sha256'] and sha(ROOT/'INPUTS.json')==f['inputs_file_sha256']
 for x in f['runtime_files']:assert sha(ROOT/x['path'])==x['sha256'],('FROZEN_ACTOR_CHANGED',x['path'])
 assert load(ROOT/'ASSET_PREFLIGHT.json')['status']=='PASS'
 return remote['commit']
class Worker:
 def __init__(self,block,probe=False):
  self.block=block;self.name=block['name'];self.arm=block['arm'];self.cfg=PLAN['arms'][self.arm];self.probe=probe;self.closed=False;self.p=None;self.lines=[];self.errors=[];self.events=[];self.q=queue.Queue();self.freeze=source_gate()
  self.dir=ROOT/'raw'/self.name;self.dir.mkdir(parents=True,exist_ok=False)
  for role,path in [('target',TARGET),*([('draft',DRAFT)] if self.cfg['spec'] else [])]:
   pin=next(x for x in load(ROOT/'ASSET_PREFLIGHT.json')['models'] if x['role']==role);assert path.stat().st_size==pin['bytes'] and sha(path)==pin['sha256']
  if probe:charge('probe',self.name)
  self.argv=[str(EXE),'STANDARD_Q6',str(TARGET),str(DRAFT) if self.cfg['spec'] else 'NONE',str(self.cfg['ub']),self.cfg['mode'],'1',str(self.dir),'probe' if probe else 'resident','counts']
  env=os.environ.copy()
  if block.get('api_dump'):
   env.update(VK_INSTANCE_LAYERS='VK_LAYER_LUNARG_api_dump',VK_LAYER_PATH='C:/VulkanSDK/1.4.357.0/Bin',VK_LUNARG_API_DUMP_FILE='true',VK_LUNARG_API_DUMP_LOG_FILENAME=str(self.dir/'vulkan-api.txt'),VK_LUNARG_API_DUMP_DETAILED='true',VK_LUNARG_API_DUMP_FLUSH='false',VK_LUNARG_API_DUMP_SHOW_SHADER='false')
  save(self.dir/'COMMAND.json',dict(argv=self.argv,source_commit=self.freeze,block=block,env_overrides={k:v for k,v in env.items() if k.startswith('VK_')},hidden_warmups=0))
  self.begin=time.monotonic();self.epoch=time.time();event(event='WORKER_STARTED',block=self.name,epoch=self.epoch)
  try:
   self.p=subprocess.Popen(self.argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=EXE.parent,env=env,bufsize=0,creationflags=subprocess.CREATE_NO_WINDOW)
   event(event='OWNED_PID',block=self.name,pid=self.p.pid)
   def out():
    for b in iter(self.p.stdout.readline,b''):
     self.lines.append(b)
     try:x=json.loads(b);self.events.append(x);self.q.put(x)
     except Exception as e:self.q.put(dict(event='PARSE_ERROR',reason=str(e)))
    self.q.put(dict(event='EOF',returncode=self.p.wait()))
   def err():
    for b in iter(self.p.stderr.readline,b''):self.errors.append(b)
   self.threads=[threading.Thread(target=out,daemon=True),threading.Thread(target=err,daemon=True)]
   for t in self.threads:t.start()
   self.ready=self.wait('READY',300);assert self.ready['pid']==self.p.pid and self.ready['forward_calls']==0
   self.identity()
   self.watch_stop=threading.Event()
   def watchdog():
    while not self.watch_stop.wait(.5):
     p=self.dir/'vulkan-api.txt'
     if owned()>=21598 or p.exists() and p.stat().st_size>PLAN['limits']['api_dump_bytes']:
      save(self.dir/'WATCHDOG_STOP.json',dict(owned_seconds=owned(),api_bytes=p.stat().st_size if p.exists() else 0,utc=now(),only_owned_pid=self.p.pid));self.p.kill();return
   self.watch=threading.Thread(target=watchdog,daemon=True);self.watch.start()
  except BaseException:
   self.close(True);raise
 def wait(self,name,timeout=240):
  end=time.monotonic()+timeout
  while True:
   x=self.q.get(timeout=max(.01,end-time.monotonic()))
   if x['event']==name:return x
   if x['event'] in ['ERROR','EOF','PARSE_ERROR']:raise RuntimeError(x)
   if time.monotonic()>end:raise TimeoutError(name)
 def send(self,x):self.p.stdin.write((json.dumps(x,separators=(',',':'))+'\n').encode());self.p.stdin.flush()
 def memory(self,samples):
  assert samples
  for m in samples:
   assert m['pid']==self.p.pid and m['vendor_id']==0x8086 and m['device_id']==0xE20C and m['adapter_luid_valid']
   hs=[h for h in m['heaps'] if h['device_local']]
   assert len(hs)==1 and hs[0]['index']==0 and hs[0]['physical_size_bytes']==10563354624
   assert m['device_local_headroom_bytes']==int(hs[0]['budget_bytes'])-int(hs[0]['usage_bytes'])>=536870912
 def identity(self):
  command='[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); @(Get-Process -Id '+str(self.p.pid)+').Modules | ForEach-Object {$_.FileName} | ConvertTo-Json'
  a=subprocess.run([str(PS),'-NoProfile','-NonInteractive','-Command',command],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
  (self.dir/'MODULES.stdout').write_bytes(a.stdout);(self.dir/'MODULES.stderr').write_bytes(a.stderr)
  assert a.returncode==0
  paths=json.loads(a.stdout.decode('utf-8-sig'));paths=paths if isinstance(paths,list) else [paths];by={Path(p).name.lower():Path(p) for p in paths};modules=[]
  for p in [EXE,*[EXE.parent/n for n in ['llama-b570-memory.dll','ggml.dll','ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll']]]:
   actual=by[p.name.lower()];assert actual.resolve()==p.resolve() and sha(actual)==sha(p);modules.append(dict(path=str(actual),sha256=sha(actual)))
  api=by.get('vklayer_api_dump.dll')
  if api:modules.append(dict(path=str(api),sha256=sha(api),scope='optional_instrumentation'))
  weights=[x for x in self.events if x['event']=='WEIGHT_MAP'];ctx=[x for x in self.events if x['event']=='CONTEXT']
  assert len(weights)==len(ctx)==(2 if self.cfg['spec'] else 1)
  for x in weights:assert x['pid']==self.p.pid and x['all_weights_Vulkan0'] and x['tensors'] and all(t['backend_device']=='Vulkan0' and t['gpu_backend_buffer'] for t in x['tensors'])
  assert ctx[0]['ub']==self.cfg['ub'] and ctx[0]['outputs_max']==self.cfg['capacity']
  assert all(x['n_ctx']==1024 and x['load_forward_calls']==0 and x['numeric_path']=='Vulkan0_F16_KV_FAoff' for x in ctx)
  text=b''.join(self.errors).decode(errors='replace');kv=[l for l in text.splitlines() if 'KV buffer size' in l]
  assert len(kv)==len(ctx) and all('Vulkan0' in l and 'CPU' not in l for l in kv)
  assert not re.search('failed to allocate|out of (device |gpu )?memory',text,re.I)
  samples=[x for x in self.events if x['event']=='MEMORY'];self.memory(samples)
  save(self.dir/'IDENTITY.json',dict(status='PASS',owned_pid=self.p.pid,modules=modules,weight_maps=weights,contexts=ctx,kv_lines=kv,memory=samples,api_layer_loaded=api is not None,physical_residency='UNKNOWN'))
 def endpoint(self,x,c,obs):
  assert x['pid']==self.p.pid and x['prompt_ids']==c['prompt_ids'] and x['cap']==128 and x['observation_mode']==obs
  ids=x['ids'];flags=x['eog'];assert 0<len(ids)<=128 and len(ids)==len(flags)==x['length']
  assert all(type(i)is int and 0<=i<128256 for i in ids)
  assert flags==[i in {128001,128008,128009} for i in ids] and not any(flags[:-1]) and x['terminal_id']==ids[-1]
  assert x['stop_reason']==('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(ids)==128)
  assert x['reset_target_min']==x['reset_target_max']==-1 and not x['memory_violation']
  if self.cfg['spec']:assert x['reset_draft_min']==x['reset_draft_max']==-1
  a=x['actual_condition'];assert a['prefill_ub']==self.cfg['ub'] and a['continuation_ub']==self.cfg['continuation_ub'] and a['output_capacity']==self.cfg['capacity'] and a['maximum_k']==int(self.cfg['spec'])
  assert a['n_ctx']==1024 and a['logical_batch']==512 and a['threads']==10 and a['kv']=='F16' and not a['flash_attention']
  w=x['workload'];assert w['output_ids_count']==len(ids) and w['counter_semantics_sha256']==sha(ROOT/'COUNTER_SEMANTICS.json')
  assert w['proposal_generated']==sum(w[k] for k in ['accepted_committed','first_mismatch_rejected','unexamined_after_mismatch','terminal_discarded','unverified_before_verify'])
  assert len(ids)==sum(w[k] for k in ['initial_target_committed','accepted_committed','bonus_committed','correction_committed','fallback_committed'])
  for role in ['target','draft']:
   h=w[role+'_physical_width_hist'];assert sum(h.values())==w[role+'_micrographs'] and sum(int(k)*v for k,v in h.items())==w[role+'_micrograph_rows']
 def request(self,slot,c):
  charge(self.block['phase'],slot);uid=hashlib.sha256(slot.encode()).hexdigest()[:32]
  event(event='REQUEST_PID',slot=slot,block=self.name,pid=self.p.pid)
  req=dict(request_id=uid,prompt_ids=c['prompt_ids'],cap=128,capture=self.block['observation_mode']=='heavy',observation_mode=self.block['observation_mode'],phase96_diagnostic=self.block['observation_mode']=='heavy',own_bind_sham=self.block['own_bind_sham'],boundary_cuts=c['boundary_cuts'],prefill_partition=self.cfg['partition'],payload_dir=str(ROOT/'payloads'),prefill_schedule=c['schedule'],operator_capture=c.get('operator_capture',False),operator_layer=c.get('operator_layer',0),operator_dir=str(ROOT/'operator_payloads'),operator_bytes_existing=sum(p.stat().st_size for p in (ROOT/'operator_payloads').glob('*.tensor')))
  if c.get('restore_donors'):
   ds=load(ROOT/'DONORS.json');kv,l=c['restore_donors'];K=ds[c['id']+'|'+kv]['KV'];L=ds[c['id']+'|'+l]['logits']
   req['restore100']=dict(KV=dict(K,path=str(ROOT/'baseline/pr99'/K['path'])),logits=dict(L,path=str(ROOT/'baseline/pr99'/L['path'])),donor_labels=[kv,l])
  started=now();self.send(dict(op='CHECK'));self.wait('CHECK_OK');begin=time.perf_counter_ns()
  try:
   self.send(req);x=self.wait('RESULT',300);assert x['request_id']==uid
   self.endpoint(x,c,req['observation_mode']);elapsed=(time.perf_counter_ns()-begin)/1e6;finished=now()
   self.wait('PERSISTED')
   rp=self.dir/(uid+'.RESULT.json');save(rp,x);save(self.dir/(uid+'.REQUEST.json'),req)
   mp=self.dir/(uid+('.trace.json' if req['capture'] else '.memory.json'));evidence=load(mp);mem=evidence['memory'] if req['capture'] else evidence
   assert not mem['violation'];self.memory(mem['samples'])
   record=dict(slot=slot,phase=self.block['phase'],arm=self.arm,repeat=self.block['repeat'],task=c['id'],source_commit=self.freeze,status='COMPLETED',owned_pid=self.p.pid,diagnostic_elapsed_ms=elapsed,paid_formal_latency=False,started_utc=started,completed_utc=finished,raw_path=str(rp.relative_to(ROOT)).replace('\\','/'),raw_sha256=sha(rp),evidence_path=str(mp.relative_to(ROOT)).replace('\\','/'),evidence_sha256=sha(mp),identity_path=str((self.dir/'IDENTITY.json').relative_to(ROOT)).replace('\\','/'),identity_sha256=sha(self.dir/'IDENTITY.json'),actual_recipe=self.cfg,slot_config={k:v for k,v in c.items() if k not in ['prompt_ids']},observation_mode=req['observation_mode'],own_bind_sham=req['own_bind_sham'])
   save(ROOT/'records'/(uid+'.json'),record);event(event='REQUEST_COMPLETED',slot=slot,pid=self.p.pid,block=self.name,record_sha256=sha(ROOT/'records'/(uid+'.json')))
   return record
  except BaseException as e:
   save(self.dir/(uid+'.FAILED.json'),dict(slot=slot,error=str(e),utc=now()));event(event='REQUEST_FAILED',slot=slot,block=self.name,pid=self.p.pid,error=str(e));raise
 def finish_probe(self):
  self.p.stdin.write(b'PROBE_FINISH\n');self.p.stdin.flush();x=self.wait('PROBE_COMPLETE');assert x['forward_calls']==x['target_graphs']==x['draft_graphs']==0
  save(self.dir/'PROBE_COMPLETE.json',x);event(event='PROBE_COMPLETED',slot=self.name,pid=self.p.pid);self.close()
 def close(self,failed=False):
  if self.closed:return
  self.closed=True
  if hasattr(self,'watch_stop'):self.watch_stop.set();self.watch.join(timeout=2)
  if self.p:
   try:self.p.stdin.close();self.p.wait(timeout=30)
   except Exception:self.p.kill();self.p.wait()
   for t in getattr(self,'threads',[]):t.join(timeout=5)
  (self.dir/'stdout.jsonl').write_bytes(b''.join(self.lines));(self.dir/'stderr.log').write_bytes(b''.join(self.errors))
  life=dict(pid=self.p.pid if self.p else None,returncode=self.p.returncode if self.p else None,owned_seconds=time.monotonic()-self.begin,failed=failed or self.p and self.p.returncode!=0,utc=now())
  save(self.dir/'LIFECYCLE.json',life);event(event='WORKER_CLOSED',block=self.name,**life)
  if not failed:assert self.p and self.p.returncode==0
 def __enter__(self):return self
 def __exit__(self,t,e,tb):self.close(t is not None)
def main():
 assert not (ROOT/'STUDY_STARTED.json').exists(),'no replay'
 source_gate();save(ROOT/'STUDY_STARTED.json',dict(utc=now(),pid=os.getpid(),prospective_plan_sha256=digest(PLAN)))
 records=[]
 try:
  for b in PLAN['load_probes']:
   with Worker(b,True) as w:w.finish_probe()
  save(ROOT/'LOAD_ADMISSION.json',dict(status='PASS_ONE_ZERO_FORWARD_NATIVE_PROBE',utc=now()))
  op_blocked=False
  for b in PLAN['blocks']:
   if op_blocked and b['phase']=='P1C' and b['observation_mode']=='heavy':
    for q in b['slots']:event(event='SLOT_NOT_STARTED',slot=q['slot'],reason='Observer full endpoint guard failed')
    continue
   with Worker(b) as w:
    for x in b['slots']:
     records.append(w.request(x['slot'],dict(CASES[x['task']],**{k:v for k,v in x.items() if k!='task'})))
     save(ROOT/'STUDY_RECORDS.json',records)
     if b['phase']=='P1C':
      r=records[-1];xx=load(ROOT/r['raw_path']);old=next(t for t in load(ROOT/'baseline/pr99/STUDY_RECORDS.json') if t['task']==r['task'] and t['arm']==r['arm'] and t['repeat']==0);oo=load(ROOT/'baseline/pr99'/old['raw_path']);keys=['ids','eog','length','terminal_id','stop_reason','cap']
      if any(xx[k]!=oo[k] for k in keys):
       op_blocked=True;save(ROOT/'OPERATOR_OBSERVER_GUARD.json',dict(status='FAILED',slot=r['slot'],full_endpoint_changed=True));break
     save(ROOT/'PROGRESS.json',dict(status='RUNNING',completed=len(records),planned=133,last_slot=x['slot'],utc=now()))
  # Standalone independent P0 gate is recomputed before any conditional cross.
  p=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'code/gate100.py'),'--root',str(ROOT)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=120)
  (ROOT/'versions/P0_GATE.stdout').write_bytes(p.stdout);(ROOT/'versions/P0_GATE.stderr').write_bytes(p.stderr)
  assert p.returncode==0,p.stderr.decode(errors='replace')
  if load(ROOT/'STATE_RESTORE_ADMISSION.json')['status']=='PASS':
   for b in PLAN['conditional_blocks']:
    with Worker(b) as w:
     for x in b['slots']:
      records.append(w.request(x['slot'],dict(CASES[x['task']],**{k:v for k,v in x.items() if k!='task'})))
      save(ROOT/'STUDY_RECORDS.json',records);save(ROOT/'PROGRESS.json',dict(status='RUNNING',completed=len(records),planned=133,last_slot=x['slot'],utc=now()))
  save(ROOT/'STUDY_COMPLETION.json',dict(status='COMPLETED',requests_started=len(records),requests_completed=len(records),zero_forward_load_probes=1,warmups=0,forks=0,retries=0,owned_gpu_seconds=owned(),utc=now()))
  print('STUDY_COMPLETED',len(records),flush=True)
 except BaseException as e:
  save(ROOT/'STUDY_RECORDS_PARTIAL.json',records)
  save(ROOT/'STUDY_COMPLETION.json',dict(status='STOPPED_NO_REPLAY',requests_started=sum(x['event']=='REQUEST_STARTED' for x in rows()),requests_completed=len(records),error=str(e),owned_gpu_seconds=owned(),utc=now()));raise
if __name__=='__main__':main()
