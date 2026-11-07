"""Session boundary observations only; never inside a request timer."""
import subprocess
from base import now,save

def capture(path):
    observations=[]
    for fields,kind in [
        ('timestamp,name,driver_version,pstate,temperature.gpu,utilization.gpu,memory.used,clocks.current.sm,clocks.current.memory,power.draw,power.limit','gpu'),
        ('pid,process_name,used_gpu_memory','compute-apps')]:
        command=['nvidia-smi','--query-'+kind+'='+fields,'--format=csv']
        try:
            r=subprocess.run(command,capture_output=True,text=True,timeout=15,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            observations.append({'command':command,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        except (OSError,subprocess.TimeoutExpired) as e:
            observations.append({'command':command,'error':str(e),'status':'UNAVAILABLE'})
    save(path,{'utc':now(),'outside_request_timer':True,'observations':observations,
               'scope':'Boundary samples only; WDDM compute enumeration is not proof of absence of all background graphics activity.'})
