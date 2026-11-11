"""Thin PR101 worker adapter: new study, immutable mixtures, explicit counts/heavy contracts."""
from __future__ import annotations
import argparse,importlib,json,os,subprocess,sys,threading,time
from pathlib import Path
from contracts import *

def verify_f0(run,repo,commit):
 require(len(commit)==40 and all(c in '0123456789abcdef' for c in commit),'full new F0 commit required');path='benchmarks/b570_decision_frontier_v1/registration/F0.json';body=(run/'F0.json').read_bytes();local=subprocess.check_output(['git','show',commit+':'+path],cwd=repo);remote=subprocess.check_output(['gh','api','repos/leecdiang/HeteroSpec/contents/'+path+'?ref='+commit,'-H','Accept: application/vnd.github.raw+json'],cwd=repo)
 require(body==local==remote,'new registration actual remote bytes mismatch')
 f=read(run/'F0.json')
 ps='C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe';cmd="[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); Get-CimInstance Win32_VideoController | Select-Object Name,PNPDeviceID,DriverVersion | ConvertTo-Json"
 live=json.loads(subprocess.check_output([ps,'-NoProfile','-NonInteractive','-Command',cmd],creationflags=subprocess.CREATE_NO_WINDOW).decode('utf-8-sig'));require(next(p for p in live if 'DEV_E20C' in p['PNPDeviceID'])==f['driver_identity'],'live B570 driver identity changed')
 for p in f['bindings']:
  q=Path(p['path']);require(q.stat().st_size==p['bytes'] and sha(q)==p['sha256'],'asset/source/layout binding changed: '+str(q))
 return f

def directory_bytes(p):return sum(q.stat().st_size for q in p.rglob('*') if q.is_file())
def completed_receipts(run):return [read(p) for p in (run/'receipts').glob('*.json')]
def gate(plan,run,stages,f0,commit):
 expected=[s for s in plan['requests'] if s['stage'] in stages];receipts={r['slot']['slot']:r for r in completed_receipts(run)}
 require(all(s['slot'] in receipts and receipts[s['slot']]['status']=='COMPLETED' and receipts[s['slot']]['endpoint']==s['reference_endpoint'] for s in expected),'anchor/observer gate incomplete or failed')
 for s in expected:validate_new_receipt(receipts[s['slot']],s,run,f0,commit)
 return len(expected)

def execute(run,repo,commit,stage):
 require(os.name=='nt' and not sys.flags.optimize,'native Windows, non-optimized Python required');require(not os.environ.get('VK_INSTANCE_LAYERS'),'no Vulkan observer layers');f=verify_f0(run,repo,commit);plan=read(run/'PLAN.json');base=Path(f['baseline_path']);budget=plan['budgets'];validate_new_plan(plan)
 stages=['anchor_counts','anchor_heavy','subset_counts','subset_heavy'];require(stage in stages,'stage')
 if stage=='anchor_heavy':gate(plan,run,['anchor_counts'],f,commit)
 if stage=='subset_counts':gate(plan,run,['anchor_counts','anchor_heavy'],f,commit)
 if stage=='subset_heavy':gate(plan,run,['anchor_counts','anchor_heavy','subset_counts'],f,commit)
 sys.path.insert(0,str(base/'code'));common=importlib.import_module('common98');module=importlib.import_module('controller100');module.ROOT=common.ROOT=run;module.PLAN={'arms':{'A':read(base/'PLAN.json')['arms']['A']},'limits':{'api_dump_bytes':0}};module.EXE=Path(f['worker_path']);module.TARGET=Path(f['target_model_path']);module.source_gate=lambda:commit
 # Recheck frozen executables, DLLs, driver files and adapter bodies before every owned process.
 def actor_gate():
  for p in f['bindings']:
   if p.get('scope')=='ACTOR_CODE_RUNTIME_DRIVER':require(Path(p['path']).stat().st_size==p['bytes'] and sha(Path(p['path']))==p['sha256'],'actor binding changed')
  return commit
 module.source_gate=actor_gate
 module.charge=lambda kind,slot:common.event(event='REQUEST_STARTED',kind=kind,slot=slot)
 active={};active_lock=threading.Lock();original_popen=subprocess.Popen;watch_stop=threading.Event();stop_reason=[];current_slot={}
 def tracked_popen(args,*aa,**kk):
  native=isinstance(args,(list,tuple)) and str(Path(args[0]).resolve()).lower()==str(module.EXE.resolve()).lower()
  if not native:return original_popen(args,*aa,**kk)
  start=time.monotonic();common.event(event='NATIVE_PROCESS_START_ATTEMPT',slot=current_slot['id'])
  try:p=original_popen(args,*aa,**kk)
  except BaseException as e:common.event(event='NATIVE_PROCESS_CREATE_FAILED',slot=current_slot['id'],error=repr(e),elapsed_seconds=time.monotonic()-start);raise
  with active_lock:active[p.pid]=(p,start,current_slot['id'])
  return p
 subprocess.Popen=tracked_popen
 def watchdog():
  while not watch_stop.wait(.5):
   try:owned=module.owned();size=directory_bytes(run)
   except (OSError,ValueError):continue
   reason='OWNED_TIME_LIMIT' if owned>=budget['owned_native_process_seconds'] else 'OUTPUT_DISK_LIMIT' if size>=budget['new_run_bytes'] else None
   if reason:
    stop_reason.append(reason)
    with active_lock:
     for p,start,slot in active.values():
      if p.poll() is None:
       common.event(event='WATCHDOG_OWNED_CHILD_STOP',slot=slot,pid=p.pid,reason=reason,owned_seconds=owned,output_bytes=size);p.kill()
    return
 watch=threading.Thread(target=watchdog,daemon=True);watch.start();lock=run/'EXECUTION.lock'
 with lock.open('x') as stream:stream.write(str(os.getpid()))
 try:
  for s in sorted((s for s in plan['requests'] if s['stage']==stage),key=lambda s:s['order']):
   receipt=run/'receipts'/(s['slot']+'.json');require(not receipt.exists(),'attempted coordinate immutable; no replay')
   led=module.rows();require(not any(x.get('slot')==s['slot'] and x['event']=='ATTEMPT_STARTED' for x in led),'slot already attempted')
   require(sum(x['event']=='ATTEMPT_STARTED' for x in led)<budget['request_start_attempts_including_failed_loads'],'168 attempt budget');require(module.owned()<budget['owned_native_process_seconds'],'time budget');require(directory_bytes(run)<budget['new_run_bytes'],'disk budget');require(not stop_reason,'watchdog stop')
   # All preflight file hashes are checked before starting the new owned process; no native smoke/probe.
   for spec in (s['mixture_spec'],s['initial_logits_spec']):require(Path(spec['path']).stat().st_size==spec['bytes'] and sha(Path(spec['path']))==spec['sha256'],'mixture/input pin')
   current_slot['id']=s['slot'];common.event(event='ATTEMPT_STARTED',slot=s['slot'],stage=stage,mode=s['mode'],task=s['task'],direction=s['direction']);worker=None;started=time.monotonic()
   try:
    block={'name':s['slot'],'phase':stage,'arm':'A','repeat':s['repeat'],'observation_mode':s['mode'],'own_bind_sham':False};worker=module.Worker(block)
    # Source controller only changes paths for restore donors; the unchanged native body hashes and input bytes are retained.
    case={'id':s['task'],'prompt_ids':s['prompt_ids'],'boundary_cuts':s['cuts'] if s['mode']=='heavy' else [],'schedule':[],'restore_donors':[s['state'],'recipient_'+s['recipient']],'operator_capture':False}
    rec=worker.request(s['slot'],case);x=read(run/rec['raw_path']);e=validate_endpoint(x,s['prompt_ids'],rec['owned_pid'],s['mode']);evidence=read(run/rec['evidence_path']);require(sha(run/rec['raw_path'])==rec['raw_sha256'] and sha(run/rec['evidence_path'])==rec['evidence_sha256'],'native raw tampered')
    require(rec['evidence_path'].endswith('.trace.json' if s['mode']=='heavy' else '.memory.json'),'counts/heavy evidence path');channel=validate_channel(evidence,x,s['prompt_ids'],rec['owned_pid'],s['mode']);p=x['restore100'];require(p['post_restore_KV_sha256']==s['mixture_spec']['sha256'] and p['post_restore_logits_sha256']==s['initial_logits_spec']['sha256'],'native restore differs')
    initial=np.fromfile(s['initial_logits_spec']['path'],dtype='<f4');require(top2(initial)[0]==x['ids'][0],'RESTORE_T0_ANOMALY');require(e==s['reference_endpoint'],'ENDPOINT_OBSERVER_CONTROL_MISMATCH')
    if s['mode']=='heavy':
     r=Resolver(run,run)
     for t in s['cuts']:z,proof=logits_at(x,t,r,s['initial_logits_spec']);require(z is not None,'advertised heavy full-logit capture missing')
    worker.close();worker=None;common.save(receipt,{'status':'COMPLETED','slot':s,'endpoint':e,'record':rec,'channel_validation':channel,'elapsed_attempt_seconds':time.monotonic()-started,'paid_latency':False});common.event(event='ATTEMPT_COMPLETED',slot=s['slot'])
   except BaseException as error:
    if worker is not None:
     try:worker.close(True)
     except BaseException as close_error:common.event(event='OWNED_CLOSE_ERROR',slot=s['slot'],error=repr(close_error))
    common.save(receipt,{'status':'FAILED','slot':s,'error':repr(error),'elapsed_attempt_seconds':time.monotonic()-started,'native_process_create_attempted':any(x.get('slot')==s['slot'] and x['event']=='NATIVE_PROCESS_START_ATTEMPT' for x in module.rows())});common.event(event='ATTEMPT_FAILED',slot=s['slot'],error=repr(error));raise
   finally:
    with active_lock:
     for pid in [pid for pid,(p,_,__) in active.items() if p.poll() is not None]:active.pop(pid)
  print(json.dumps({'stage':stage,'status':'PASS_ALL_ENDPOINTS_MATCH_REFERENCE','completed':sum(s['stage']==stage for s in plan['requests']),'owned_seconds':module.owned()}))
 finally:
  watch_stop.set();watch.join(timeout=2)
  with active_lock:
   for p,started,slot in active.values():
    if p.poll() is None:common.event(event='FINAL_OWNED_CHILD_STOP',slot=slot,pid=p.pid);p.kill();p.wait(timeout=30)
  subprocess.Popen=original_popen;lock.unlink()

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--f0-commit',required=True);ap.add_argument('--stage',choices=('anchor_counts','anchor_heavy','subset_counts','subset_heavy'),required=True);a=ap.parse_args();execute(a.run,a.repo,a.f0_commit,a.stage)
