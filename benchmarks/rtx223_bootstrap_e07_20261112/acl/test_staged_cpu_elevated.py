"""CPU-only test after the explicit profile/staging approval has been applied."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
plan=json.loads((HERE/'STAGING_APPLIED.json').read_bytes())
STAGE=Path(plan['stage'])
FAKE=STAGE/'cpu-probe.exe'
SHA='8a5cc2607dfdf3e59902dbb359e09e20e4348aa736b7bd3fac788fa996f449cb'
if hashlib.sha256(FAKE.read_bytes()).hexdigest()!=SHA:raise RuntimeError('CPU image changed')
spec=importlib.util.spec_from_file_location('r',BASE/'rtx223-e06/runner/runner.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
w=r.win
class MockObserver:
    def start(self):pass
    def bind(self,pid,creation):pass
    def poll(self):pass
    def checkpoint(self,stage):pass
    def finish(self):return {'valid':True}
    def close(self):pass

out=HERE/'cpu-staged-elevated-001'
targets=r.protected_models()
paths=[Path(x['path']) for x in plan['files'] if Path(x['path']).suffix.lower()=='.dll']
paths += [Path(os.environ['SystemRoot'])/'System32'/n for n in ('nvcuda.dll','nvml.dll')]
receipt={'scope':'CPU_APPCONTAINER_ONLY','runner_context':r.runner_context(),
         'package':r.PACKAGE,'observed_utc':datetime.now(timezone.utc).isoformat(),
         'cpu_probe_sha256':SHA,'protected_model_paths':len(targets),'readable_image_count':None,
         'principal_model_read_denied':False,'job_active_limit':1,'pass':False,
         'management_library_loads':0,'numerical_DLL_loads':0,
         'stage':str(STAGE),'profile':plan['profile']}
log=r.Journal(out,{'scope':'CPU_STAGED_ACL'})
job=w.AtomicJob()
try:
    env={'SystemRoot':os.environ['SystemRoot'],'LOCALAPPDATA':plan['profile'],
         'TEMP':plan['temp'],'TMP':plan['temp']}
    result=r.execute(job,log,MockObserver(),[FAKE],STAGE,env,'cpu-fake',work=5,hard=8,
                     package=r.PACKAGE,protected=targets,readable_images=paths)
    receipt['pass']=result=='COMPLETE' and job.active()==0
    if receipt['pass']:
        receipt.update(principal_model_read_denied=True,readable_image_count=len(paths))
except Exception as exc:
    receipt['error']=str(exc)
finally:
    job.close();log.close()
    with (HERE/'STAGED_CPU_ELEVATED.json').open('x',encoding='utf8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt,indent=2))
sys.exit(0 if receipt['pass'] else 1)
