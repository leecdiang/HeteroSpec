"""Bounded tool/PE inspection and explicitly accounted new telemetry, no graph."""
import ctypes,os,shutil,subprocess,time
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
def main():
    r=root();s=load(r/'RUN_SPEC.json');folder=r/'CAPABILITY';folder.mkdir()
    tools={x:shutil.which(x) for x in ['nsys','ncu','nvprof']}
    cache=Path('D:/hs104-e1-v1/native/build/CMakeCache.txt')
    report=dict(tools_on_PATH=tools,GGML_CUDA_GRAPHS_cache_ON='GGML_CUDA_GRAPHS:BOOL=ON' in cache.read_text(),cache_sha256=sha(cache),searched_roots=['C:/Program Files/NVIDIA Corporation','C:/Program Files (x86)/NVIDIA Corporation','D:/HeteroSpec-PC/tools','D:/HeteroSpec-PC/downloads','D:/HeteroSpec-PC/env','C:/Users/ASUS/.cache'],admitted_collector=None,ON='REQUESTED_BUT_UNVERIFIED',trace='PROFILE_UNAVAILABLE_NO_ADMITTED_COLLECTOR',decision='off-only plan prospectively before formal GPU',extra_capability_hosts=0,profile_hosts=0,graph_calls=0,reason='No installed admitted CUDA API/graph trace or trustworthy actual-launch counters found. Compiled graph feature alone does not authenticate activation. No new numerical build or unverified ON timing.')
    exe=str(Path(os.environ['SystemRoot'])/'System32/nvidia-smi.exe');queries=[]
    for i,args in enumerate([['--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu,clocks.sm,power.draw','--format=csv,noheader,nounits'],['--query-gpu=index,uuid,name,clocks.sm,clocks.current.sm','--format=csv'],['--query-gpu=index,uuid,clocks.sm','--format=csv,noheader,nounits']]):
        t=time.monotonic();p=subprocess.run([exe,*args],capture_output=True,timeout=10);row=dict(command=[exe,*args],executable_sha256=sha(exe),exit=p.returncode,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace'),seconds=time.monotonic()-t);save(folder/f'SMI_{i}.json',row);queries.append(row)
    result=dict(status='UNAVAILABLE')
    libpath=Path(os.environ['SystemRoot'])/'System32/nvml.dll'
    if libpath.exists():
        n=ctypes.WinDLL(str(libpath));result=dict(path=str(libpath),sha256=sha(libpath),calls=[])
        def call(name,args):
            fn=getattr(n,name);fn.restype=ctypes.c_int;rc=fn(*args);result['calls'].append(dict(name=name,status=rc));return rc
        if call('nvmlInit_v2',[])==0:
            h=ctypes.c_void_p();rc=call('nvmlDeviceGetHandleByIndex_v2',[ctypes.c_uint(0),ctypes.byref(h)])
            if rc==0:
                clock=ctypes.c_uint();call('nvmlDeviceGetClockInfo',[h,ctypes.c_uint(1),ctypes.byref(clock)]);result['SM_clock_MHz']=clock.value
                class U(ctypes.Structure):_fields_=[('gpu',ctypes.c_uint),('memory',ctypes.c_uint)]
                u=U();call('nvmlDeviceGetUtilizationRates',[h,ctypes.byref(u)]);result['utilization_gpu']=u.gpu
                class M(ctypes.Structure):_fields_=[('total',ctypes.c_ulonglong),('free',ctypes.c_ulonglong),('used',ctypes.c_ulonglong)]
                m=M();call('nvmlDeviceGetMemoryInfo',[h,ctypes.byref(m)]);result['memory_bytes']={k:getattr(m,k) for k in ['total','free','used']}
                temp=ctypes.c_uint();call('nvmlDeviceGetTemperature',[h,ctypes.c_uint(0),ctypes.byref(temp)]);result['temperature_C']=temp.value
            call('nvmlShutdown',[]);result['status']='RECORDED'
    save(folder/'NVML.json',result)
    report.update(explicit_SMI_queries=len(queries),NVML=result,clock_gate='EXCLUDED;invalid channel UNKNOWN;no frequency normalization',provenance='nvidia-smi and NVML share driver;not independent physical calibration;idle-only not task-active trace',scientific_GPU_hosts=0)
    save(V/'CAPABILITY.json',report);save(r/'CAPABILITY.json',report)
    print(queries);print(result)
if __name__=='__main__':main()
