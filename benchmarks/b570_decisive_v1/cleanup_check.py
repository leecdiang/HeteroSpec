"""Exercise real Windows descendants on parent failure and timeout, no model."""
from host import *
def check():
 proof=ROOT/('cleanup-check-'+str(len(list(ROOT.glob('cleanup-check*')))));proof.mkdir()
 exe=Path(sys.executable);manifest=proof/'FILES.json'
 write(manifest,dict(files=[dict(path=str(exe),bytes=exe.stat().st_size,sha256=sha(exe))]))
 rows=[]
 for mode in ('parent-failure','timeout'):
  folder=proof/mode;folder.mkdir();child_file=folder/'child.json'
  code="import subprocess,sys,time,json; p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);open("+repr(str(child_file))+",'w').write(json.dumps({'pid':p.pid}));"+("sys.exit(2)" if mode=='parent-failure' else 'time.sleep(60)')
  args=[sys.executable,'-B',str(HERE/'supervisor.py'),'--manifest',str(manifest),'--receipt',str(folder/'SUPERVISOR.json'),'--process-limit','4','--limit','3','--minimum-free-bytes',str(20*1024**3),str(exe),'-c',code]
  with (folder/'host.log').open('x') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=30)
  sup=read(folder/'SUPERVISOR.json');assert sup['assigned_before_resume'] and sup['cleanup_verified']
  assert 2<=sup['job_accounting']['total_processes']<=4 and sup['job_accounting']['active_processes']==0
  assert child_file.exists()
  rows.append(dict(mode=mode,child_pid=read(child_file)['pid'],supervisor_sha256=sha(folder/'SUPERVISOR.json'),accounting=sup['job_accounting']))
 write(ROOT/'CLEANUP_PROOF.json',dict(utc=utc(),status='ACTUAL_DESCENDANT_CLEANUP_PASS',cases=rows,model_requests=0))
if __name__=='__main__':check()
