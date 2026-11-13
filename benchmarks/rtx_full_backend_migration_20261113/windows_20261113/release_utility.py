"""User-approved stop of one identity-bound OnDeviceModel utility; main read-only."""
import ctypes as C,json,sys,datetime
from ctypes import wintypes as W
from pathlib import Path
rows=json.load(sys.stdin);byid={x['ProcessId']:x for x in rows};child=byid[29020];main=byid[28000]
if child['ParentProcessId']!=28000 or child['Name']!='ChatGPT.exe' or main['Name']!='ChatGPT.exe':raise RuntimeError('unexpected family')
for needle in ['--type=utility','--utility-sub-type=on_device_model.mojom.OnDeviceModelService','--service-sandbox-type=on_device_model_execution']:
 if needle not in child['CommandLine']:raise RuntimeError('not authorized utility')
if '--type=' in main['CommandLine']:raise RuntimeError('protected process is not main')
k=C.WinDLL('kernel32',use_last_error=True)
def fn(n,r,*a):f=getattr(k,n);f.restype=r;f.argtypes=a;return f
open_=fn('OpenProcess',W.HANDLE,W.DWORD,W.BOOL,W.DWORD);close=fn('CloseHandle',W.BOOL,W.HANDLE);wait=fn('WaitForSingleObject',W.DWORD,W.HANDLE,W.DWORD)
query=fn('QueryFullProcessImageNameW',W.BOOL,W.HANDLE,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD));times=fn('GetProcessTimes',W.BOOL,W.HANDLE,*([C.POINTER(W.FILETIME)]*4));terminate=fn('TerminateProcess',W.BOOL,W.HANDLE,W.UINT)
handles=[]
def bound(row,access):
 h=open_(access,False,row['ProcessId'])
 if not h:raise C.WinError(C.get_last_error())
 handles.append(h);buf=C.create_unicode_buffer(32768);n=W.DWORD(32768);t=[W.FILETIME() for _ in range(4)]
 if not query(h,0,buf,C.byref(n)) or not times(h,*[C.byref(x) for x in t]):raise C.WinError(C.get_last_error())
 actual=(t[0].dwHighDateTime<<32)|t[0].dwLowDateTime
 epoch=datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc);dt=datetime.datetime.fromisoformat(row['CreationDate']).astimezone(datetime.timezone.utc);delta=dt-epoch;expected=(delta.days*86400+delta.seconds)*10000000+delta.microseconds*10
 if abs(actual-expected)>10 or buf.value.casefold()!=row['ExecutablePath'].casefold() or wait(h,0)!=258:raise RuntimeError('identity/lifetime mismatch')
 return h,actual
try:
 mh,mt=bound(main,0x101000);ch,ct=bound(child,0x101001)
 if not terminate(ch,0xe244):raise C.WinError(C.get_last_error())
 ended=wait(ch,10000)==0;main_alive=wait(mh,0)==258
 report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),authorized='User asked to handle utility and protect this chat main process',only_terminated_pid=29020,utility='on_device_model.mojom.OnDeviceModelService',utility_creation_filetime=ct,protected_main_pid=28000,main_creation_filetime=mt,utility_exit_confirmed=ended,main_alive_after=main_alive,settings_or_ACL_changes=0,other_processes_terminated=0)
 with (Path(__file__).resolve().parent/'evidence/UTILITY_RELEASE.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
 print(json.dumps(report))
 if not ended or not main_alive:raise RuntimeError('release/main check failed')
finally:
 for h in handles:close(h)
