"""Never runs inference: seal PARTIAL if the owned detached pipeline exits early."""
from pathlib import Path
import json,time,subprocess,sys,os,traceback
import runner
ROOT=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
owner=read(ROOT/'PIPELINE_LOCK.json')
(ROOT/'recovery/WATCHDOG_START.json').write_text(json.dumps({'pid':os.getpid(),'manager':owner,'purpose':'No GPU forwards; only CPU partial preservation after owned manager exits'},indent=2)+'\n',encoding='utf-8')
while runner.identity(owner['pid'])==owner['creation_identity']:time.sleep(5)
if (ROOT/'DELIVERY_VERIFIED.json').exists():sys.exit(0)
if (ROOT/'LOCK.json').exists():
 job=read(ROOT/'LOCK.json')
 while runner.identity(job['pid'])==job['creation_identity']:time.sleep(5)
 # Dead owner only; retain stale identity rather than discard provenance.
 (ROOT/'LOCK.json').rename(ROOT/('LOCK.watchdog-stale-'+str(time.time_ns())+'.json'))
try:
 for name,args in [('independent_verify.py',[str(ROOT),'--allow-partial']),('audit_assets.py',['ASSET_POST.json']),('generate_report.py',[]),('seal_archive.py',[]),('publish_evidence.py',[])]:
  if name=='audit_assets.py' and (ROOT/'ASSET_POST.json').exists():continue
  with (ROOT/'recovery'/('watchdog-'+name+'.log')).open('a',encoding='utf-8') as log:
   subprocess.run([sys.executable,str(ROOT/name),*args],stdout=log,stderr=log,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
except BaseException:
 (ROOT/'WATCHDOG_FAILURE.json').write_text(json.dumps({'traceback':traceback.format_exc(),'state':'PARTIAL_PENDING_MANUAL_REPAIR'},indent=2)+'\n',encoding='utf-8');raise
