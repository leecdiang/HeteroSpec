"""Bounded operator replay orchestrator; no model-forward requests, explicit separate ledger."""
from common98 import *
import collections,math
def main():
 plan=load(ROOT/'PLAN.json');f0=load(ROOT/'F0_BASE.json');auth=load(ROOT/'F0_AUTHENTICATED.json')
 assert auth['status']=='PASS_ACTUAL_AUTHENTICATED_GITHUB_BYTES'
 for p in f0['runtime_files']:assert sha(ROOT/p['path'])==p['sha256']
 records=load(ROOT/'STUDY_RECORDS.json');hist=load(ROOT/'baseline/pr99/STUDY_RECORDS.json');jobs=[]
 def end(x):return {k:x[k] for k in ['ids','eog','length','terminal_id','stop_reason','cap']}
 for task in ['GSM8K/test/1248','GSM8K/test/831']:
  rs=[r for r in records if r['phase']=='P1C' and r['task']==task]
  assert len(rs)==9,'Incomplete capture-on/off native guard'
  for r in rs:
   x=load(ROOT/r['raw_path']);old=next(z for z in hist if z['task']==task and z['arm']==r['arm'] and z['repeat']==0)
   assert end(x)==end(load(ROOT/'baseline/pr99'/old['raw_path'])),'Observer changed full native output'
  r=next(r for r in rs if r['repeat']==1 and r['arm']=='A');x=load(ROOT/r['raw_path']);ts=x['operator100']['tensors']
  selectors=[('rms','norm-0','RMS_NORM'),('scale','attn_norm-0','MUL'),('q','Qcur-0','MUL_MAT'),('k','Kcur-0','MUL_MAT'),('v','Vcur-0','MUL_MAT')]
  for tag,name,op in selectors:
   matches=[t for t in ts if t['name']==name and t['op']==op]
   if len(matches)!=1:
    save(ROOT/'receipts'/f'REPLAY_BLOCKED_{task.split("/")[-1]}_{tag}.json',dict(status='NOT_ADMITTED',reason='Frozen operator selector unavailable or ambiguous',matches=len(matches)));continue
   t=matches[0];operands=[]
   try:
    for o in t['operands']:
     assert o['payload'] and o['ne'][2:]==[1,1]
     assert o['nb'][0]==(4 if o['dtype']=='f32' else o['nb'][0])
     j=dict(o);j['payload']=dict(o['payload'],path=str(ROOT/o['payload']['path']))
     j['token_axis']=1 if o['ne'][1]==len(x['prompt_ids']) and '.weight' not in o['name'] else -1
     operands.append(j)
    assert len(operands)==(1 if op=='RMS_NORM' else 2)
   except Exception as e:
    save(ROOT/'receipts'/f'REPLAY_BLOCKED_{task.split("/")[-1]}_{tag}.json',dict(status='NOT_ADMITTED',reason='No faithful dense captured operands',error=str(e)));continue
   for rep in range(2):
    for geom in ['full','split']:
     N=len(x['prompt_ids']);jobs.append(dict(slot=f'OP/{task}/{tag}/r{rep}/{geom}',task=task,tag=tag,repeat=rep,geometry=geom,N=N,op=op,operands=operands,op_params=t['op_params'],schedule=[N] if geom=='full' else [128,N-128],native_reference=t['payload'],native_source_record=r['raw_path']))
 save(ROOT/'OPERATOR_REPLAY_PLAN_REALIZED.json',dict(frozen_rule=plan['operator_replay_rule'],jobs=jobs))
 outputs=[]
 for q in jobs:
  ledger=[json.loads(s) for s in (ROOT/'LEDGER.jsonl').read_text().splitlines()]
  old=[r for r in ledger if r['event']=='OPERATOR_STARTED']
  assert len(old)<72 and not any(r['slot']==q['slot'] for r in old)
  seconds=sum(r['owned_seconds'] for r in ledger if r['event'] in ['WORKER_CLOSED','OPERATOR_CLOSED']);assert seconds<21600
  uid=hashlib.sha256(q['slot'].encode()).hexdigest()[:32];directory=ROOT/'raw'/('op_'+uid);directory.mkdir(exist_ok=False)
  exe=ROOT/'build/Release/b570-operator-replay.exe'
  job=dict(q,output_dir=str(ROOT/'operator_payloads'),existing_bytes=sum(p.stat().st_size for p in (ROOT/'operator_payloads').iterdir()))
  save(directory/'REQUEST.json',job);event(event='OPERATOR_STARTED',slot=q['slot'],prior_starts=len(old))
  start=time.monotonic();p=subprocess.Popen([str(exe)],cwd=exe.parent,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW);event(event='OPERATOR_PID',slot=q['slot'],pid=p.pid)
  try:
   p.stdin.write((json.dumps(job)+'\n').encode());p.stdin.flush();ready=p.stdout.readline();assert json.loads(ready)['event']=='REPLAY_READY'
   command='[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); @(Get-Process -Id '+str(p.pid)+').Modules | ForEach-Object {$_.FileName} | ConvertTo-Json'
   a=subprocess.run([str(PS),'-NoProfile','-NonInteractive','-Command',command],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30);assert a.returncode==0
   paths=json.loads(a.stdout.decode('utf-8-sig'));by={Path(v).name.lower():Path(v) for v in paths};pins=[]
   for n in ['b570-operator-replay.exe','ggml.dll','ggml-base.dll','ggml-vulkan.dll']:
    actual=by[n];assert actual.resolve()==(exe.parent/n).resolve();assert sha(actual)==sha(exe.parent/n);pins.append(dict(path=str(actual),sha256=sha(actual)))
   save(directory/'IDENTITY.json',dict(status='PASS_ACTUAL_LOADED_MODULES',pid=p.pid,modules=pins,ready=json.loads(ready)))
   stdout,stderr=p.communicate(b'RUN\n',timeout=180);stdout=ready+stdout
  except subprocess.TimeoutExpired:
   p.kill();stdout,stderr=p.communicate()
  owned=time.monotonic()-start
  (directory/'stdout.jsonl').write_bytes(stdout);(directory/'stderr.log').write_bytes(stderr)
  event(event='OPERATOR_CLOSED',slot=q['slot'],pid=p.pid,returncode=p.returncode,owned_seconds=owned)
  lines=[json.loads(s) for s in stdout.splitlines()];r=next((r for r in lines if r['event']=='REPLAY_RESULT'),None)
  result=dict(slot=q['slot'],status='COMPLETED' if p.returncode==0 and r else 'FAILED_NO_RETRY',pid=p.pid,returncode=p.returncode,owned_seconds=owned,raw_dir=directory.relative_to(ROOT).as_posix(),request_sha256=sha(directory/'REQUEST.json'),stdout_sha256=sha(directory/'stdout.jsonl'),stderr_sha256=sha(directory/'stderr.log'),result=r)
  outputs.append(result);save(ROOT/'OPERATOR_REPLAY_RECORDS.json',outputs)
  if result['status']!='COMPLETED':event(event='OPERATOR_FAILED',slot=q['slot'],pid=p.pid);break
 save(ROOT/'OPERATOR_REPLAY_COMPLETION.json',dict(started=len(outputs),completed=sum(r['status']=='COMPLETED' for r in outputs),no_retries=True,owned_seconds=sum(r['owned_seconds'] for r in outputs)))
 print('OPERATOR_COMPLETE',len(outputs),flush=True)
if __name__=='__main__':main()
