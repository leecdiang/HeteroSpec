"""CPU-only final storage inventory. No enumeration of GPU or model assets."""
import ctypes as C,json,os,shutil,time
from ctypes import wintypes as W
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'repo/benchmarks/b570_zero_gpu_repair_v1';K=C.WinDLL('kernel32',use_last_error=True)
K.GetDiskFreeSpaceW.argtypes=[W.LPCWSTR]+[C.POINTER(W.DWORD)]*4
K.GetCompressedFileSizeW.argtypes=[W.LPCWSTR,C.POINTER(W.DWORD)];K.GetCompressedFileSizeW.restype=W.DWORD
v=[W.DWORD() for _ in range(4)];assert K.GetDiskFreeSpaceW('C:\\',*[C.byref(x) for x in v]);cluster=v[0].value*v[1].value
begin=time.perf_counter_ns();logical=allocated=files=dirs=0
for parent,directories,names in os.walk(B,followlinks=False):
    dirs+=len(directories)
    for name in directories:
        p=Path(parent,name);assert not p.is_symlink() and not p.is_junction(),p
    for name in names:
        p=Path(parent,name);assert not p.is_symlink() and not p.is_junction(),p
        size=p.stat().st_size;high=W.DWORD();C.set_last_error(0);low=K.GetCompressedFileSizeW(str(p),C.byref(high))
        assert low!=0xffffffff or C.get_last_error()==0,(p,C.get_last_error())
        actual=(high.value<<32)|low;allocated+=max(actual,((size+cluster-1)//cluster)*cluster);logical+=size;files+=1
metadata_reserve=files*4096+dirs*cluster;total=allocated+metadata_reserve
result=dict(status='CURRENT_STORAGE_INVENTORY_ONLY_NOT_COMPLETE_TASK_ADMISSION',begin_ns=begin,end_ns=time.perf_counter_ns(),cluster_bytes=cluster,files=files,directories=dirs,logical_bytes=logical,data_allocation_upper_bytes=allocated,metadata_reserve_bytes=metadata_reserve,current_physical_upper_bytes=total,closing_reserve_bytes=64*1024**2,charged_current_plus_closing_reserve_bytes=total+64*1024**2,cap_bytes=1073741824,within_current_cap=total+64*1024**2<=1073741824,available_disk_bytes=shutil.disk_usage(B).free,method='Per-file Windows GetCompressedFileSizeW versus cluster rounding, plus 4KiB per-file metadata and one cluster per directory; no old tree copied or deleted',limitations=['Transient preparation/tool storage peak and initial unobserved processes are not reconstructed; no complete budget qualification is claimed'])
with (D/'results/STORAGE_ACTUAL.json').open('x',encoding='utf-8') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(result))
assert result['within_current_cap'],'1GiB current+closing reserve exceeded'
