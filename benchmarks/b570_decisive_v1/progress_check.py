"""Exercise the request deadline with an actual contained descendant tree."""
from host import *

def check(epoch='01'):
 folder=ROOT/('progress-check'+epoch);folder.mkdir();exe=Path(sys.executable)
 manifest=folder/'FILES.json';write(manifest,dict(files=[dict(path=str(exe),bytes=exe.stat().st_size,sha256=sha(exe))]))
 child=folder/'child.json'
 code="import subprocess,sys,time,json; p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);open("+repr(str(child))+",'w').write(json.dumps({'pid':p.pid}));print('HS_READY',flush=True);time.sleep(60)"
 args=[sys.executable,'-B',HERE/'supervisor.py','--manifest',manifest,'--receipt',folder/'SUPERVISOR.json','--process-limit','4','--limit','20','--progress-limit','2','--minimum-free-bytes',str(20*1024**3),exe,'-c',code]
 with (folder/'host.log').open('x') as f:subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=30)
 r=read(folder/'SUPERVISOR.json');assert r['error']=='Request progress timeout' and r['cleanup_verified'] and r['job_accounting']['active_processes']==0 and child.exists()
 write(folder/'PROOF.json',dict(status='ACTUAL_REQUEST_DEADLINE_DESCENDANT_CLEANUP_PASS',supervisor_sha256=sha(folder/'SUPERVISOR.json'),model_requests=0))

if __name__=='__main__':check(sys.argv[1] if len(sys.argv)>1 else '01')
