"""Read-only Windows process GPU counters; no model API or residency certification."""
from common import *
import ctypes
from ctypes import wintypes
pdh=ctypes.WinDLL('pdh');pdh.PdhOpenQueryW.argtypes=[wintypes.LPCWSTR,ctypes.c_size_t,ctypes.POINTER(ctypes.c_void_p)];pdh.PdhOpenQueryW.restype=wintypes.DWORD
pdh.PdhAddEnglishCounterW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR,ctypes.c_size_t,ctypes.POINTER(ctypes.c_void_p)];pdh.PdhAddEnglishCounterW.restype=wintypes.DWORD
pdh.PdhCollectQueryData.argtypes=[ctypes.c_void_p];pdh.PdhCollectQueryData.restype=wintypes.DWORD
pdh.PdhGetFormattedCounterArrayW.argtypes=[ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),ctypes.POINTER(wintypes.DWORD),ctypes.c_void_p];pdh.PdhGetFormattedCounterArrayW.restype=wintypes.DWORD
pdh.PdhCloseQuery.argtypes=[ctypes.c_void_p]
class ValueUnion(ctypes.Union):_fields_=[('large',ctypes.c_int64),('double',ctypes.c_double),('long',ctypes.c_int32)]
class Value(ctypes.Structure):_fields_=[('status',wintypes.DWORD),('value',ValueUnion)]
class Item(ctypes.Structure):_fields_=[('name',wintypes.LPWSTR),('fmt',Value)]
ledger=[json.loads(s) for s in (R/'LEDGER.jsonl').read_text(encoding='utf8').splitlines()];closed={x['name'] for x in ledger if x['event']=='WORKER_END'};live=[x for x in ledger if x['event']=='WORKER_PID' and x['name'] not in closed];assert len(live)==1,'Read one actual owned worker PID'
pid=live[0]['pid'];query=ctypes.c_void_p();rows=[];rc=pdh.PdhOpenQueryW(None,0,ctypes.byref(query));assert rc==0
try:
 for label in ['Dedicated Usage','Shared Usage','Total Committed']:
  counter=ctypes.c_void_p();path='\\GPU Process Memory(*)\\'+label;rc=pdh.PdhAddEnglishCounterW(query,path,0,ctypes.byref(counter));record=dict(counter_path=path,add_status=int(rc),pid=pid)
  if rc==0:
   record['collect_status']=int(pdh.PdhCollectQueryData(query));size=wintypes.DWORD();count=wintypes.DWORD();rc=pdh.PdhGetFormattedCounterArrayW(counter,0x400,ctypes.byref(size),ctypes.byref(count),None);record['size_status']=int(rc)
   if size.value:
    buf=ctypes.create_string_buffer(size.value);rc=pdh.PdhGetFormattedCounterArrayW(counter,0x400,ctypes.byref(size),ctypes.byref(count),buf);record['format_status']=int(rc)
    if rc==0:
     arr=ctypes.cast(buf,ctypes.POINTER(Item));record['owned_samples']=[dict(instance=arr[i].name,status=int(arr[i].fmt.status),counter_large_integer=int(arr[i].fmt.value.large)) for i in range(count.value) if arr[i].name.startswith('pid_'+str(pid)+'_')]
  rows.append(record)
finally:pdh.PdhCloseQuery(query)
save(R/'residency_diagnostics'/('PDH_'+str(time.time_ns())+'.json'),dict(utc=now(),worker=live[0],rows=rows,status='RAW_PROCESS_COUNTER_OBSERVATION',observed_point='Concurrent engineering diagnostic; no formal timer is being measured',limitations=['Counter integers are retained without allocation attribution.','No per-weight/KV physical heap or paging trace; physical residency remains UNKNOWN.','Original frozen PowerShell Get-Counter module autoload failure is retained; this independent English-counter PDH read does not rewrite it.']))
print('Owned PID PDH diagnostic',pid,[(x['counter_path'],x.get('owned_samples')) for x in rows],flush=True)
