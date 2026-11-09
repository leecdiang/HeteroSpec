"""Conditional detached B2: requires public32B delivery and B2 public binding.

No CUDA or native work while waiting. Skip the entire supplement when its
observed whole-panel runtime plus900s margin no longer fits the05:00 boundary.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,sys,time
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--q32-work',type=Path,required=True);a=p.parse_args();r,w=a.root,a.work;src=Path(__file__).parent
 def save(name,x):
  p=w/name;assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n')
 plan=read(w/'PLAN.json');prepared=read(w/'PREPARED.json');assert sha(w/'PLAN.json')==prepared['plan_sha256'];assert not(w/'NATIVE_CONTROLLER_TERMINAL.private.json').exists()
 stop=datetime.datetime(2026,11,9,21,tzinfo=datetime.timezone.utc).timestamp();latest=stop-plan['whole_panel_estimate_s']-900
 while True:
  if time.time()>=latest:
   save('SKIPPED_BEFORE_GPU.json',dict(reason='Full32B public delivery/B2 public binding was not ready while complete supplement plus900s margin still fitted',zero_native_requests=True,latest_admission_epoch=latest,observed_whole_panel_estimate_s=plan['whole_panel_estimate_s']));print('B2_SKIPPED_WINDOW',flush=True);return
  proof=a.q32_work/'Q32_DELIVERY_PUBLIC_READBACK_PASS.json';binding=w/'ACTIVATION_PUBLIC_BINDING.json'
  if proof.exists()and binding.exists():
   q=read(proof);b=read(binding)
   assert q['passed']and q['performance_complete']and q['independent_statistical_replay_passed']
   assert b['passed']and b['plan_sha256']==prepared['plan_sha256']and b['Q32_complete_public_readback']is True
   assert b['Q32_public_readback_sha256']==sha(proof)
   for x in b['source_files']:assert sha(x['path'])==x['sha256']
   break
  time.sleep(5)
 save('ACTIVATION_CHECKED.json',dict(passed=True,epoch=time.time(),Q32_public_proof_sha256=sha(proof),B2_public_binding_sha256=sha(binding),plan_sha256=prepared['plan_sha256'],unchanged_8B_budget=True))
 with(w/'controller.stdout.log').open('xb')as so,(w/'controller.stderr.log').open('xb')as se:
  result=subprocess.run(['taskset','-c','32,33','nice','-n','10',sys.executable,'-B',str(src/'b2_controlled.py'),'--root',str(r),'--work',str(w),'--execute'],stdin=subprocess.DEVNULL,stdout=so,stderr=se)
 save('NATIVE_CONTROLLER_TERMINAL.private.json',dict(epoch=time.time(),returncode=result.returncode,no_automatic_native_retry=True))
 if(w/'GUARD_DONE').exists():
  until=time.monotonic()+60
  while not(w/'GUARD_STOPPED.private.json').exists():
   if time.monotonic()>=until:save('ARCHIVE_DEFERRED.json',dict(reason='Wait for resource guard to close before terminal snapshot',zero_new_native_requests=True));return
   time.sleep(1)
 with(w/'archive.stdout.log').open('xb')as so,(w/'archive.stderr.log').open('xb')as se:
  archived=subprocess.run(['taskset','-c','34,35',sys.executable,'-B',str(src/'b2_export.py'),'--root',str(r),'--work',str(w),'--source',str(src)],stdin=subprocess.DEVNULL,stdout=so,stderr=se)
 save('PIPELINE_TERMINAL.private.json',dict(epoch=time.time(),controller_returncode=result.returncode,archive_returncode=archived.returncode,public_upload_and_remote_readback='Pending connected publication',no_more_native_requests=True))
if __name__=='__main__':main()
