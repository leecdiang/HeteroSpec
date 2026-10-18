"""GPU admission is callable only by an authorized future GPU controller."""
import ctypes,json,subprocess,time
from pathlib import Path
from s0_budget import save
class Power(ctypes.Structure):
    _fields_=[('AC',ctypes.c_ubyte),('flags',ctypes.c_ubyte),('percent',ctypes.c_ubyte),('system',ctypes.c_ubyte),('life',ctypes.c_uint32),('full',ctypes.c_uint32)]
def query(policy,receipt):
    # Never imported-and-called by S0 preparation or tests. The caller's actual
    # F0/readback/author gate must have passed before this first device query.
    begin=time.perf_counter();cmd=[policy['nvidia_smi'],'--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits']
    result=subprocess.run(cmd,capture_output=True,timeout=30);assert result.returncode==0,result.stderr
    rows=result.stdout.decode().strip().splitlines();assert len(rows)==1
    gpu,driver,total,used,util,temp=[x.strip() for x in rows[0].split(',')];power=Power();assert ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power))
    observation=dict(gpu=gpu,driver=driver,total_MiB=float(total),used_MiB=float(used),util=float(util),temp=float(temp),AC=power.AC,owned_query_seconds=time.perf_counter()-begin,command=cmd)
    save(Path(receipt),observation)
    assert (gpu,driver,float(total))==(policy['gpu'],policy['driver'],policy['total_MiB'])
    assert power.AC==1 and float(total)-float(used)>=512 and float(util)<=5 and float(temp)<=55,'fixed admission threshold failed; do not launch/retry census'
    return observation
