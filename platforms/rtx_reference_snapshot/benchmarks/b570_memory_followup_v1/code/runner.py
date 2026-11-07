"""Serial controller for the frozen engineering grid; no formal admission on UNKNOWN."""
from common import *
from probe import budget,config,probe
import threading,queue,statistics,math,traceback,ctypes
def signature(x):return (tuple(x['ids']),tuple(x['eog']),x['length'],x['terminal_id'],x['stop_reason'])
def endpoint(x,inp,cap):
 ids=x['ids'];flags=x['eog'];v=load(R/'VOCAB_CHECKS.json');eog=set(v['runtime_eog_ids'])
 assert x['prompt_ids']==inp['prompt_ids'] and 0<len(ids)<=cap and x['length']==len(ids) and len(flags)==len(ids) and x['terminal_id']==ids[-1]
 assert all(type(i)==int and 0<=i<v['vocab_tokens'] for i in ids) and all(type(b)==bool for b in flags) and flags==[i in eog for i in ids] and not any(flags[:-1])
 assert x['stop_reason']==('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(ids)==cap)
 assert x['reset_target_min']==x['reset_target_max']==-1 and not x['memory_violation']
 if x['draft_decode_calls']:assert x['reset_draft_min']==x['reset_draft_max']==-1
 return x
def recheck_freeze():
 f=load(R/'F0A.json');assert load(R/'F0A_REMOTE_READBACK.json')['status']=='PASS'
 for rel,m in f['files'].items():assert sha(R/rel)==m['sha256'],rel
class Worker:
 def __init__(self,profile,q,ub,mode,k,name):
  recheck_freeze();self.profile=profile;self.folder=R/'workers'/name;self.folder.mkdir(parents=True,exist_ok=False);self.start=time.perf_counter();self.closed=False;self.pid=None;self.proc=None;self.name=name
  target,draft,threshold=config(profile,q,ub,mode,k);b=budget(profile);assert b['engineering_units']<640 and b['owned_gpu_seconds']<28800
  for path in [target,draft]:
   if path=='NONE':continue
   a=next(x for x in load(R/'ASSET_CHECKS.json')['models'].values() if x['path']==path);assert sha(path)==a['sha256'] and Path(path).stat().st_size==a['bytes']
  self.base_gpu=b['owned_gpu_seconds'];exe=R/'build/Release/b570-memory-worker.exe';self.out=(self.folder/'stdout.jsonl').open('w',encoding='utf8');self.err=(self.folder/'stderr.log').open('wb');self.q=queue.Queue()
  cmd=[str(exe),profile,target,draft,str(ub),mode,str(k),str(self.folder),'resident'];save(self.folder/'SPEC.json',dict(profile=profile,draft=q,ub=ub,mode=mode,k=k,argv=cmd,threshold_bytes=threshold,utc=now()))
  event(event='LOAD_WARMUP_RESERVATION',profile=profile,name=name,unit=name+'_warm',planned_forward=True,charge_units=1,policy='One reserved warmup unit pays its loader failure or the eventual single warmup; never duplicated/reset.')
  event(event='WORKER_START',profile=profile,name=name,argv=cmd,binary_sha256=sha(exe))
  try:
   self.proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,text=True,encoding='utf8',bufsize=1,cwd=exe.parent,creationflags=subprocess.CREATE_NO_WINDOW);self.pid=self.proc.pid;event(event='WORKER_PID',profile=profile,name=name,pid=self.pid)
   def pump():
    for line in self.proc.stdout:self.out.write(line);self.out.flush();self.q.put(json.loads(line))
    self.q.put(None)
   threading.Thread(target=pump,daemon=True).start()
   self.wait('READY',300)
   log=(self.folder/'stderr.log').read_text(encoding='utf8',errors='replace');counts=__import__('re').findall(r'offloaded (\d+)/(\d+) layers to GPU',log);assert len(counts)==(1 if draft=='NONE' else 2) and all(a==b for a,b in counts)
   assert 'layer   0: dev = Vulkan0' in log or 'layer 0: dev = Vulkan0' in log
   ps="[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); Get-Counter '\\GPU Process Memory(*)\\Dedicated Usage','\\GPU Process Memory(*)\\Shared Usage' -ErrorAction Stop | ForEach-Object {$_.CounterSamples | Where-Object {$_.InstanceName -like 'pid_"+str(self.pid)+"_*'} | Select-Object Path,InstanceName,CookedValue,Timestamp} | ConvertTo-Json -Depth 4"
   counters=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True)
   save(self.folder/'WINDOWS_PROCESS_MEMORY.json',dict(pid=self.pid,utc=now(),returncode=counters.returncode,stdout=counters.stdout.decode('utf-8-sig',errors='replace'),stderr=counters.stderr.decode('utf-8-sig',errors='replace'),scope='Sampled Windows process counters; weight/KV physical mapping and paging remain UNKNOWN. Not residency admission.'))
   modules=subprocess.run(['powershell','-NoProfile','-Command',f"[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); (Get-Process -Id {self.pid}).Modules | Select-Object FileName,ModuleName | ConvertTo-Json"],capture_output=True,check=True);mods=json.loads(modules.stdout.decode('utf-8-sig'));actual=[]
   for m in mods:
    if m['ModuleName'].lower().startswith(('ggml','llama','b570')):
     path=Path(m['FileName']);assert path.parent.resolve()==exe.parent.resolve();actual.append(dict(**m,sha256=sha(path)))
   save(self.folder/'MODULES.json',dict(pid=self.pid,actual=actual,layer_offload_counts=counts,full_gpu_layer_execution=True,physical_residency='UNKNOWN'))
  except BaseException:self.close();raise
 def wait(self,event_name,timeout=300):
  end=time.perf_counter()+timeout
  while time.perf_counter()<end:
   assert time.perf_counter()-self.start+self.base_gpu<28800,'Owned GPU lifetime cap'
   try:x=self.q.get(timeout=1)
   except queue.Empty:continue
   if x is None:raise RuntimeError('Native worker exit:'+str(self.proc.poll()))
   if x['event']=='ERROR':raise RuntimeError(x['reason'])
   if x['event']==event_name:return x
  raise TimeoutError(event_name)
 def request(self,inp,unit,repeat,arm,cap=128,capture=False,warm=False):
  b=budget(self.profile);assert b['engineering_units']<640 or warm and b['engineering_units']==640
  folder=R/'raw'/unit;folder.mkdir(parents=True,exist_ok=False)
  event(event='REQUEST_START',profile=self.profile,unit=unit,task=inp['id'],repeat=repeat,arm=arm,warm=warm,pid=self.pid,cap=cap,capture=capture,stage='ENGINEERING')
  save(folder/'START.json',dict(utc=now(),input_ids_sha256=inp['prompt_ids_sha256'],profile=self.profile,pid=self.pid,arm=arm,repeat=repeat,task=inp['id'],cap=cap,capture=capture,warm=warm))
  try:
   self.proc.stdin.write(json.dumps(dict(op='CHECK'))+'\n');self.proc.stdin.flush();self.wait('CHECK_OK')
   start=time.perf_counter_ns();payload=dict(request_id=unit,prompt_ids=inp['prompt_ids'],cap=cap,capture=capture);self.proc.stdin.write(json.dumps(payload)+'\n');self.proc.stdin.flush();x=self.wait('RESULT');assert x['request_id']==unit;endpoint(x,inp,cap);elapsed=(time.perf_counter_ns()-start)/1e9
   # Full response parsed and native boundary checked; persistence and hashes follow.
   self.wait('PERSISTED');mem=load(self.folder/(unit+('.trace.json' if capture else '.memory.json')));mem=mem['memory'] if capture else mem
   assert not mem['violation'] and mem['samples']
   minimum=min(y['device_local_headroom_bytes'] for y in mem['samples']);maximum=max(h['usage_bytes'] for y in mem['samples'] for h in y['heaps'] if h['device_local']);threshold=load(R/'PIN_POLICY.json')['profiles'][self.profile]['dedicated_headroom_min_bytes'];assert minimum>=threshold
   receipt=dict(profile=self.profile,unit=unit,task=inp['id'],repeat=repeat,arm=arm,warm=warm,capture=capture,whole_request_seconds=elapsed,native=x,status='COMPLETE',qualified_ratio=None,observed_minimum_headroom_bytes=minimum,observed_maximum_heap_usage_bytes=maximum,max_memory_sample_gap_ms=mem['max_observed_gap_ms'])
   save(folder/'RESULT.json',receipt);event(event='REQUEST_END',profile=self.profile,unit=unit,status='COMPLETE',seconds=elapsed)
   save(R/'STATUS.json',dict(utc=now(),profile=self.profile,last_complete=unit,budget=budget(self.profile)));print(unit,round(elapsed,3),x['length'],x['stop_reason'],flush=True);return receipt
  except BaseException as e:save(folder/'FAILURE.json',dict(utc=now(),error=repr(e)));event(event='REQUEST_END',profile=self.profile,unit=unit,status='FAILED',error=repr(e));raise
 def close(self):
  if self.closed:return
  self.closed=True
  if self.proc and self.proc.poll() is None:
   try:self.proc.stdin.close();self.proc.wait(timeout=30)
   except (OSError,subprocess.TimeoutExpired):self.proc.kill();self.proc.wait(timeout=10)
  self.out.close();self.err.close();seconds=time.perf_counter()-self.start;event(event='WORKER_END',profile=self.profile,name=self.name,pid=self.pid,seconds=seconds,exit_code=self.proc.poll() if self.proc else None)
  save(self.folder/'CLOSE.json',dict(utc=now(),owned_process_lifetime_seconds=seconds,pid=self.pid,exit_code=self.proc.poll() if self.proc else None))
def panel(profile,q,ub,mode,k,arm):
 name=profile+'_'+arm;folder=R/'workers'/name
 assert not folder.exists(),'No replay of started panels; repair requires a new version and newly paid units'
 s=Worker(profile,q,ub,mode,k,name);records=[];rows=load(R/'ENGINEERING_INPUTS.json');warm=load(R/'SYNTHETIC_INPUTS.json')[0]
 try:
  s.request(warm,name+'_warm',0,arm,warm=True)
  for repeat in [1,2]:
   for i,inp in enumerate(rows):records.append(s.request(inp,f'{name}_r{repeat}_t{i:02}',repeat,arm))
 finally:s.close()
 save(R/'panels'/(name+'.json'),records);return records
def gm(xs):return math.exp(statistics.mean(math.log(x) for x in xs))
def run(profile):
 recheck_freeze();matrices={};summary=dict(profile=profile,status='ENGINEERING_IN_PROGRESS',candidates=[],ratios_qualified=None,residency='UNKNOWN',confirmation='NOT_ADMITTED')
 try:
  for ub in [32,128,512]:
   prepath=R/'probes'/f'ALLGPU_{profile}_NONE_{ub}_ordinary_k1/RECEIPT.json';pre=load(prepath) if prepath.exists() else None
   if pre and pre['status']!='LOADED_ONLY_PASS':summary.setdefault('ordinary_blocked',[]).append(pre);continue
   matrices[ub]=panel(profile,'NONE',ub,'ordinary',1,'R_UB'+str(ub))
  assert 128 in matrices,'R_stock unavailable'
  stock=matrices[128];by=lambda rs:{(x['repeat'],x['task']):x for x in rs};ref=by(stock)
  if any(signature(ref[1,t]['native'])!=signature(ref[2,t]['native']) for _,t in ref):summary['status']='IMPLEMENTATION_BLOCKED_UNSTABLE_R_STOCK';return summary
  good=[]
  for ub,records in matrices.items():
   m=by(records);ok=all(signature(x['native'])==signature(ref[x['repeat'],x['task']]['native']) for x in records);summary.setdefault('ordinary_grid',[]).append(dict(ub=ub,whole_output_equal=ok,gm_seconds=gm([x['whole_request_seconds'] for x in records])))
   if ok:good.append((gm([x['whole_request_seconds'] for x in records]),ub))
  prod=min(good)[1];summary['R_prod_ub']=prod;summary['R_stock_ub']=128;cub=32 if profile=='TIGHT_Q8' else prod
  matches={}
  for mode in ['native_greedy','vulkan_batched_repair']:matches[mode]=panel(profile,'NONE',cub,mode,3,'M_'+mode)
  summary['matched_whole_output_equal']={mode:all(signature(x['native'])==signature(ref[x['repeat'],x['task']]['native']) for x in rs) for mode,rs in matches.items()}
  for q in (['Q8_0','Q4_K_M'] if profile=='STANDARD_Q6' else ['Q4_K_M']):
   for mode in ['native_greedy','vulkan_batched_repair']:
    prepath=R/'probes'/f'ALLGPU_{profile}_{q}_{cub}_{mode}_k3/RECEIPT.json'
    # Q6 has used its12 dedicated probes. Actual selected-UB worker allocation
    # and reserved warmup charge supply the remaining native admission checks.
    pre=load(prepath) if prepath.exists() else dict(status='LOADED_ONLY_PASS',scope='MUST_PASS_ACTUAL_WORKER_ALLOCATION_BEFORE_FORWARD_NOT_A_CERTIFICATE')
    for k in [1,2,3]:
     cid=f'{q}_{mode}_k{k}';row=dict(candidate_id=cid,draft=q,mode=mode,k_max=k,prefill_ub=cub,output_capacity=4,qualified=False,residency='UNKNOWN',qualified_ratio=None)
     if pre['status']!='LOADED_ONLY_PASS':row['status']='MEMORY_BLOCKED_AT_LOAD';summary['candidates'].append(row);continue
     try:records=panel(profile,q,cub,mode,k,'C_'+cid)
     except BaseException as e:
      if 'MEMORY_BLOCKED' not in str(e):raise
      row.update(status='MEMORY_BLOCKED_DURING_ENGINEERING',error=repr(e));summary['candidates'].append(row);save(R/(profile+'_ENGINEERING.json'),summary);continue
     m=by(records);row['complete_raw_equal']=all(signature(x['native'])==signature(ref[x['repeat'],x['task']]['native']) for x in records) and summary['matched_whole_output_equal'][mode]
     row['observed_peak_heap_usage_bytes']=max(x['observed_maximum_heap_usage_bytes'] for x in records);row['observed_minimum_headroom_bytes']=min(x['observed_minimum_headroom_bytes'] for x in records)
     row['diagnostic_repeat_R_prod_C']=[gm([by(matrices[prod])[r,t]['whole_request_seconds']/m[r,t]['whole_request_seconds'] for rr,t in m if rr==r]) for r in [1,2]]
     row['status']='RAW_EQUIVALENT_RESIDENCY_UNKNOWN' if row['complete_raw_equal'] else 'RAW_OUTPUT_DIVERGENCE';row['score']=min(row['diagnostic_repeat_R_prod_C']);summary['candidates'].append(row)
     save(R/(profile+'_ENGINEERING.json'),summary)
  pre=R/'probes'/f'ALLGPU_{profile}_Q4_K_M_{cub}_native_greedy_k3/RECEIPT.json'
  if not pre.exists() or load(pre)['status']=='LOADED_ONLY_PASS':
   ns=panel(profile,'Q4_K_M',cub,'N_unrepaired',3,'N_diagnostic');summary['N_diagnostic']=dict(status='TRIGGER_OBSERVED' if any(signature(x['native'])!=signature(ref[x['repeat'],x['task']]['native']) for x in ns) else 'NO_TRIGGER',requests=25,first_divergences=[])
   for x in ns:
    a=x['native']['ids'];bids=ref[x['repeat'],x['task']]['native']['ids'];first=next((i for i in range(min(len(a),len(bids))) if a[i]!=bids[i]),min(len(a),len(bids)) if a!=bids else None)
    if first is not None:summary['N_diagnostic']['first_divergences'].append(dict(task=x['task'],repeat=x['repeat'],index=first,native_id=a[first] if first<len(a) else None,reference_id=bids[first] if first<len(bids) else None))
  else:summary['N_diagnostic']=dict(status='MEMORY_BLOCKED_UNTESTED',requests=0)
  # Physical residency is not asserted from budgets/offload logs. Preserve a
  # diagnostic ranking without designating a qualified candidate or new cohort.
  summary['status']='RESIDENCY_UNKNOWN_DIAGNOSTIC';eligible=[x for x in summary['candidates'] if x.get('complete_raw_equal')]
  chosen=sorted(eligible,key=lambda x:(-x['score'],x['k_max'],x['observed_peak_heap_usage_bytes'],x['candidate_id']))[0] if eligible else None
  summary['diagnostic_ranked_first']=chosen['candidate_id'] if chosen else None
  if chosen:
   synthetic=load(R/'SYNTHETIC_INPUTS.json');boundary={};paid=[]
   for arm in ['R_stock','C_selected']:
    for capture in [False,True]:
     mode='ordinary' if arm=='R_stock' else chosen['mode'];q='NONE' if arm=='R_stock' else chosen['draft'];ub=128 if arm=='R_stock' else cub;k=1 if arm=='R_stock' else chosen['k_max'];name=f'{profile}_BOUNDARY_{arm}_{int(capture)}';s=Worker(profile,q,ub,mode,k,name)
     try:
      s.request(synthetic[0],name+'_warm',0,arm,capture=capture,warm=True)
      for task in synthetic[1:3]:
       for cap in [1,2,3,4,31,32,128]:
        unit=name+'_'+task['id'].rsplit('/',1)[1]+'_'+str(cap);x=s.request(task,unit,0,arm,cap=cap,capture=capture);boundary[arm,capture,task['id'],cap]=x;paid.append(x)
      x=s.request(synthetic[3],name+'_LONGEST768',0,arm,capture=capture);boundary[arm,capture,synthetic[3]['id'],128]=x;paid.append(x)
     finally:s.close()
   equal=True
   for task in synthetic[1:]:
    for cap in ([1,2,3,4,31,32,128] if task!=synthetic[3] else [128]):
     if len({signature(boundary[a,c,task['id'],cap]['native']) for a in ['R_stock','C_selected'] for c in [False,True]})!=1:equal=False
   natural_eog=any(x['native']['stop_reason']=='EOG' for x in paid)
   summary['full_boundary_gate']=dict(status='RAW_CAP_CAPTURE_RESET_LONGEST_PASS' if equal and natural_eog else 'BLOCKED_BOUNDARY_DIVERGENCE_OR_EOG_UNOBSERVED',paid=60+4,native_exact_cap_eog_and_capture_outputs_equal=equal,natural_eog_observed=natural_eog,longest_native_prompt=768,physical_residency='UNKNOWN')
   if not equal or not natural_eog:summary['status']='IMPLEMENTATION_BLOCKED_BOUNDARY'
  else:summary['full_boundary_gate']='NOT_RUN_NO_RAW_EQUIVALENT_CANDIDATE'
  summary['F0B']='NOT_CREATED';summary['confirmation']='NOT_ADMITTED_RESIDENCY_UNKNOWN'
 except BaseException as e:
  summary.update(status='MEMORY_BLOCKED' if 'MEMORY_BLOCKED' in str(e) else 'IMPLEMENTATION_BLOCKED',error=repr(e),traceback=traceback.format_exc())
 finally:summary['budget']=budget(profile);save(R/(profile+'_ENGINEERING.json'),summary)
 return summary
if __name__=='__main__':
 import sys
 print(json.dumps(run(sys.argv[1]),indent=2),flush=True)
