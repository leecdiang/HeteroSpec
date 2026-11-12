"""Remove only the new, identity-matched AppContainer profile after root signoff.

Default is a read-only plan. No staging/source/ACL/ledger deletion is provided.
"""
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
PACKAGE='HeteroSpec.RTX223.Bootstrap.B1'
record=json.loads((HERE/'PROFILE_CREATED.json').read_bytes())
if record['package']!=PACKAGE or record['create_hresult']!=0 or record['capabilities']!=0:
    raise RuntimeError('Not the profile created by this approved task')

class Entry(C.Structure):
    _fields_=[('size',W.DWORD),('uses',W.DWORD),('pid',W.DWORD),('heap',C.c_size_t),
              ('module',W.DWORD),('threads',W.DWORD),('parent',W.DWORD),('priority',W.LONG),
              ('flags',W.DWORD),('name',W.WCHAR*260)]

k=C.WinDLL('kernel32',use_last_error=True)
def fn(dll,name,result,*args):
    f=getattr(dll,name);f.restype=result;f.argtypes=args;return f
snapshot=fn(k,'CreateToolhelp32Snapshot',W.HANDLE,W.DWORD,W.DWORD)
first=fn(k,'Process32FirstW',W.BOOL,W.HANDLE,C.POINTER(Entry))
next_=fn(k,'Process32NextW',W.BOOL,W.HANDLE,C.POINTER(Entry))
close=fn(k,'CloseHandle',W.BOOL,W.HANDLE)
h=snapshot(2,0)
if not h or h==W.HANDLE(-1).value:raise RuntimeError('Cannot check live child images')
try:
    e=Entry();e.size=C.sizeof(e)
    if not first(h,C.byref(e)):raise RuntimeError('Cannot enumerate live processes')
    while True:
        if e.name.lower() in ('native-probe.exe','cpu-probe.exe'):
            raise RuntimeError('Probe image still exists; preserve profile')
        if not next_(h,C.byref(e)):
            if C.get_last_error()!=18:raise RuntimeError('Incomplete process snapshot')
            break
finally:close(h)
if Path('D:/HeteroSpec-PC/rtx223-bootstrap-b1/B1.lock').exists():
    raise RuntimeError('B lease marker exists; preserve profile')
userenv=C.WinDLL('userenv',use_last_error=True)
derive=fn(userenv,'DeriveAppContainerSidFromAppContainerName',C.c_long,W.LPCWSTR,C.POINTER(C.c_void_p))
sid=C.c_void_p()
if derive(PACKAGE,C.byref(sid))!=0:raise RuntimeError('Cannot derive expected package SID')
adv=C.WinDLL('advapi32')
convert=fn(adv,'ConvertSidToStringSidW',W.BOOL,C.c_void_p,C.POINTER(W.LPWSTR))
text=W.LPWSTR()
folder=W.LPWSTR()
try:
    if not convert(sid,C.byref(text)) or text.value!=record['package_sid']:
        raise RuntimeError('Package SID mismatch')
    get_folder=fn(userenv,'GetAppContainerFolderPath',C.c_long,W.LPCWSTR,C.POINTER(W.LPWSTR))
    if get_folder(text,C.byref(folder))!=0 or Path(folder.value).resolve()!=Path(record['profile']).resolve():
        raise RuntimeError('Current-user profile path mismatch or not present')
    report={'package':PACKAGE,'package_sid':text.value,'profile':folder.value,
            'probe_images_in_snapshot':0,'B_marker_present':False,
            'staging_delete':False,'source_or_model_acl_changes':False,
            'utc':datetime.now(timezone.utc).isoformat()}
    if sys.argv[1:]==['apply-after-owned-processes-ended']:
        delete=fn(userenv,'DeleteAppContainerProfile',C.c_long,W.LPCWSTR)
        rc=delete(PACKAGE)
        report.update(delete_hresult=hex(rc&0xffffffff),deleted=rc==0)
        with (HERE/'PROFILE_CLEANUP.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
        if rc!=0:raise RuntimeError('DeleteAppContainerProfile '+hex(rc&0xffffffff))
    elif sys.argv[1:] not in ([],['plan']):raise SystemExit('plan | apply-after-owned-processes-ended')
    print(json.dumps(report,indent=2))
finally:
    fn(adv,'FreeSid',C.c_void_p,C.c_void_p)(sid)
    if text:fn(k,'LocalFree',C.c_void_p,C.c_void_p)(text)
    if folder:fn(C.WinDLL('ole32'),'CoTaskMemFree',None,C.c_void_p)(folder)
