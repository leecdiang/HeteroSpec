from pathlib import Path
import json,time,subprocess,os,threading,queue,uuid,traceback
import runner
R=Path(__file__).parent
class Cross:
 def __init__(self):
  self.dir=R/'sessions'/('B-cross-'+uuid.uuid4().hex[:8]);self.dir.mkdir();self.err=(self.dir/'stderr.log').open('w',encoding='utf8');self.out=(self.dir/'stdout.log').open('w',encoding='utf8')
  import re
  avail=subprocess.check_output([str(runner.BIN/'b570-pilot-cross.exe'),'--list-devices'],encoding='utf8',errors='replace');ds=re.findall(r'(Vulkan\d+): Intel\(R\) Arc\(TM\) B570 Graphics',avail);assert len(ds)==1
  d=ds[0];cmd=[str(runner.BIN/'b570-pilot-cross.exe'),'--model',str(runner.ASSET/'models/gguf/Qwen3-8B-Q8_0.gguf'),'--device',d,'--n-gpu-layers','all','--fit','off','--ctx-size','1024','--batch-size','512','--ubatch-size','128','--flash-attn','off','--n-predict','128','--temp','0','--top-k','0','--top-p','1','--min-p','0','--seed','123','--threads','10','--threads-batch','10','--log-verbosity','3','--no-warmup','--reasoning','off','--simple-io','--no-conversation']
  env={k:v for k,v in os.environ.items() if not k.startswith('HS_')};env.update(HS_PREFILL_OUTPUT=str(self.dir/'initial.json'),HS_PREFILL_UB='128')
  start=time.monotonic();self.p=subprocess.Popen(cmd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,text=True,encoding='utf8',bufsize=1,creationflags=subprocess.CREATE_NO_WINDOW);self.q=queue.Queue()
  runner.save(self.dir/'SESSION.json',dict(command=cmd,pid=self.p.pid,creation_identity=runner.identity(self.p.pid),source_commit=runner.source(),device_preflight=avail,hidden_warmups=0))
  def pump():
   for line in self.p.stdout:self.out.write(line);self.out.flush();self.q.put(line.strip())
   self.q.put(None)
  threading.Thread(target=pump,daemon=True).start()
  while self.wait()!='HS_READY':pass
  self.err.flush();log=(self.dir/'stderr.log').read_text(encoding='utf8',errors='replace');assert f'using device {d} (Intel(R) Arc(TM) B570 Graphics)' in log and 'offloaded 37/37 layers to GPU' in log
  runner.save(self.dir/'SESSION_LOAD.json',dict(model_and_context_load_seconds=time.monotonic()-start,forwards=0))
 def wait(self):
  for _ in range(300):
   if runner.stopped():raise RuntimeError('Manual STOP')
   try:
    line=self.q.get(timeout=1)
    if line is None:raise RuntimeError('Owned cross process exited '+str(self.p.poll()))
    return line
   except queue.Empty:runner.heartbeat(self.p.pid)
  raise TimeoutError('Cross result missing')
 def request(self,u,case,donor,recipe):
  dest=R/'aux'/u.replace('/','_');receipt=dest/'RESULT.json'
  if receipt.exists():
   r=runner.read(receipt)
   for f,h in r['files'].items():assert runner.sha(R/f)==h
   return r
  dest.mkdir(parents=True,exist_ok=True);attempt=dest/('attempt-'+uuid.uuid4().hex);attempt.mkdir()
  req=dict(request_id=u,checkpoint=str(R/donor['checkpoint']),batch=case['batch'],recipe=recipe,output=str(attempt/'cross.json'))
  runner.save(attempt/'START.json',dict(utc=runner.now(),source_commit=runner.source(),request=req,manifest_sha256=runner.sha(R/'B_MANIFEST.json'),session=self.dir.name))
  events=[json.loads(s) for s in (R/'LEDGER.jsonl').read_text().splitlines()];assert sum(e['event']=='TARGET_FORWARD_START' for e in events)<24
  source_before={f:runner.sha(R/f) for f in donor['all_checkpoint_files']};runner.event('TARGET_FORWARD_START',unit_id=u,warm=False)
  start=time.monotonic();self.p.stdin.write(json.dumps(req)+'\n');self.p.stdin.flush()
  try:
   while True:
    line=self.wait()
    if line.startswith('HS_RESULT '):m=json.loads(line[10:]);break
   assert m['request_id']==u
   source_after={f:runner.sha(R/f) for f in donor['all_checkpoint_files']};assert source_before==source_after
   runner.save(attempt/'SOURCE_UNCHANGED.json',dict(before=source_before,after=source_after,unchanged=True))
   r=dict(unit_id=u,task=case['task'],round=case['round'],donor=donor['label'],recipe=recipe,session=self.dir.name,host_seconds=time.monotonic()-start,files={str(p.relative_to(R)).replace('\\','/'):runner.sha(p) for p in attempt.iterdir() if p.is_file()})
   runner.save(receipt,r);runner.event('TARGET_FORWARD_COMPLETE',unit_id=u,host_seconds=r['host_seconds']);return r
  except BaseException as e:runner.save(attempt/'FAILURE.json',dict(error=repr(e)));runner.event('TARGET_FORWARD_FAILURE',unit_id=u,error=repr(e));raise
 def close(self):
  start=time.monotonic()
  if self.p.poll() is None:
   self.p.stdin.close()
   try:self.p.wait(timeout=20)
   except subprocess.TimeoutExpired:
    if runner.identity(self.p.pid)==runner.read(self.dir/'SESSION.json')['creation_identity']:self.p.kill();self.p.wait(timeout=10)
  self.err.close();self.out.close();runner.save(self.dir/'SESSION_CLOSE.json',dict(process_exit_code=self.p.poll(),model_session_cleanup_seconds=time.monotonic()-start))
def main():
 manifest=runner.read(R/'B_MANIFEST.json');freeze=runner.read(R/'B_FREEZE.json')
 for f,h in freeze['sources'].items():assert runner.sha(R/f)==h
 for f,h in freeze['binaries'].items():assert runner.sha(R/f)==h
 runner.acquire();runner.STAGE='B';results=[]
 try:
  # Natural full-output shams first. Each independently initialized original path has one excluded warm request.
  for ci,c in enumerate(manifest['cases']):
   if c['status']!='ALIGNED':continue
   for di,d in enumerate(c['donors']):
    u=f'B_SHAM/{ci}/{di}/{c["task"]}';p=R/'raw'/runner.hashlib.sha256(u.encode()).hexdigest()[:20]/'RESULT.json'
    if p.exists():
     r=runner.read(p)
     for f,h in r['files'].items():assert runner.sha(R/f)==h
     results.append(r);continue
    conf=dict(d['config']);s=runner.Session('B-sham-'+str(ci)+'-'+str(di)+'-'+uuid.uuid4().hex[:6],conf)
    inp=next(i for i in runner.read(R/'DEV_INPUTS.json') if i['id']==c['task']);inp=dict(inp)
    try:
     s.request(f'B_SHAM/{ci}/{di}/WARM/{s.name}',inp,True)
     before={f:runner.sha(R/f) for f in d['all_checkpoint_files']};inp['resume']=str(R/d['checkpoint']);r=s.request(u,inp)
     after={f:runner.sha(R/f) for f in d['all_checkpoint_files']};runner.save(R/'derived'/('SHAM_SOURCE-'+str(ci)+'-'+str(di)+'.json'),dict(unit=u,before=before,after=after,unchanged=before==after));assert before==after
     results.append(r)
    finally:s.close()
  runner.save(R/'B_SHAM_RESULTS.json',results)
  cross=Cross();aux=[]
  try:
   for ci,c in enumerate(manifest['cases']):
    if c['status']!='ALIGNED':continue
    for di,d in enumerate(c['donors']):
     for ri,recipe in enumerate(c['recipes']):aux.append(cross.request(f'B_CROSS/{ci}/{di}/{ri}',c,d,recipe))
  finally:cross.close()
  runner.save(R/'B_CROSS_RESULTS.json',aux)
 except BaseException:
  runner.save(R/'B_WORKER_FAILURE.json',dict(utc=runner.now(),traceback=traceback.format_exc()));raise
 finally:runner.release()
if __name__=='__main__':main()
