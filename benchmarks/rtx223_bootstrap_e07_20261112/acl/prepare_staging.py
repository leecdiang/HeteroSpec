"""Plan/apply the specifically approved new AppContainer and new staging ACL.

Default is read-only. apply changes per-user security configuration and must be
called only after the user approves that exact change. It never alters sources,
model ACLs, parent-directory ACLs, System32 or an existing package/profile.
"""
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PACKAGE='HeteroSpec.RTX223.Bootstrap.B1'
STAGE=BASE/'rtx223-e07/staging-B1'
PROFILE_NAMES=['ggml-cuda.dll','ggml-base.dll','cudart64_12.dll','cublas64_12.dll',
               'cublaslt64_12.dll','msvcp140.dll','vcomp140.dll','vcruntime140.dll',
               'vcruntime140_1.dll','cupti64_2025.2.1.dll']

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def require(ok,message):
    if not ok:raise RuntimeError(message)

def plan():
    manifest=json.loads((BASE/'rtx223-e06/build/DEPLOYMENT.json').read_bytes())['modules']
    sources=[{'name':name,'path':manifest[name]['path'],'sha256':manifest[name]['sha256'],
              'bytes':manifest[name]['bytes']} for name in PROFILE_NAMES]
    for name,expected in [('cpu-probe.exe','8a5cc2607dfdf3e59902dbb359e09e20e4348aa736b7bd3fac788fa996f449cb'),
                          ('native-probe.exe','70fe177f4d7cdacbe25f73aaf27ef617f59f5832335708831185c5f76781b805')]:
        p=BASE/'rtx223-e06/build/probes-attempt-002'/name
        sources.append({'name':name,'path':str(p),'sha256':expected,'bytes':p.stat().st_size})
    for r in sources:
        require(sha(r['path'])==r['sha256'],'source changed '+r['name'])
    return {'package':PACKAGE,'capabilities':0,'stage':str(STAGE),'sources':sources,
            'copied_bytes':sum(r['bytes'] for r in sources),'stage_access':'package SID RX only',
            'profile_access':'Windows-created per-user storage and Temp',
            'model_parent_system_ACL_changes':False,'numeric_loads':0,'CUDA_calls':0}

def apply():
    data=plan()
    require(not STAGE.exists(),'Staging already exists; refuse overwrite')
    userenv=C.WinDLL('userenv',use_last_error=True)
    sid=C.c_void_p()
    create=userenv.CreateAppContainerProfile
    create.argtypes=[W.LPCWSTR,W.LPCWSTR,W.LPCWSTR,C.c_void_p,W.DWORD,C.POINTER(C.c_void_p)]
    create.restype=C.c_long
    # HRESULT_ALREADY_EXISTS is a refusal. Never adopt or delete an old profile.
    rc=create(PACKAGE,PACKAGE,'One-shot HeteroSpec B1 bootstrap, zero capabilities',None,0,C.byref(sid))
    require(rc==0,'CreateAppContainerProfile '+hex(rc&0xffffffff))
    adv=C.WinDLL('advapi32')
    sid_text=W.LPWSTR()
    convert=adv.ConvertSidToStringSidW
    convert.argtypes=[C.c_void_p,C.POINTER(W.LPWSTR)]
    require(convert(sid,C.byref(sid_text)),'SID conversion')
    package_sid=sid_text.value
    folder=W.LPWSTR()
    get_folder=userenv.GetAppContainerFolderPath
    get_folder.argtypes=[W.LPCWSTR,C.POINTER(W.LPWSTR)]
    get_folder.restype=C.c_long
    require(get_folder(package_sid,C.byref(folder))==0 and folder.value,'profile folder')
    profile=Path(folder.value)
    with (HERE/'PROFILE_CREATED.json').open('x',encoding='utf8') as f:
        json.dump({'package':PACKAGE,'package_sid':package_sid,'profile':str(profile),
                   'created_utc':datetime.now(timezone.utc).isoformat(),
                   'create_hresult':0,'capabilities':0},f,indent=2)
        f.flush();os.fsync(f.fileno())
    temp=profile/'Temp'
    temp.mkdir(exist_ok=True)
    STAGE.mkdir()
    try:
        for row in data['sources']:
            dst=STAGE/row['name']
            with Path(row['path']).open('rb') as src,dst.open('xb') as out:
                shutil.copyfileobj(src,out,1024*1024)
                out.flush();os.fsync(out.fileno())
            require(sha(dst)==row['sha256'],'copy changed '+row['name'])
        # Only the newly created staging tree is changed. The ACE applies to
        # existing copied children as well as any future children of this tree.
        icacls=Path(os.environ['SystemRoot'])/'System32/icacls.exe'
        result=subprocess.run([str(icacls),str(STAGE),'/grant',f'*{package_sid}:(OI)(CI)(RX)','/T','/C'],
                              stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (HERE/'STAGING_ICACLS.log').write_bytes(result.stdout)
        require(result.returncode==0,'staging ACL grant failed')
        data.update(profile_created=True,package_sid=package_sid,profile=str(profile),temp=str(temp),
                    applied_utc=datetime.now(timezone.utc).isoformat(),
                    files=[{'path':str(STAGE/r['name']),'sha256':r['sha256'],
                            'bytes':r['bytes']} for r in data['sources']])
        with (HERE/'STAGING_APPLIED.json').open('x',encoding='utf8') as f:
            json.dump(data,f,indent=2);f.flush();os.fsync(f.fileno())
        print(json.dumps(data,indent=2))
    finally:
        # Preserve the approved new profile and all partially prepared evidence
        # until the root verifies that every dependent child and handle ended.
        adv.FreeSid.argtypes=[C.c_void_p]
        adv.FreeSid(sid)
        k=C.WinDLL('kernel32');k.LocalFree.argtypes=[C.c_void_p];k.LocalFree(sid_text)
        ole=C.WinDLL('ole32');ole.CoTaskMemFree.argtypes=[C.c_void_p];ole.CoTaskMemFree(folder)

if __name__=='__main__':
    if sys.argv[1:]==['apply']:
        apply()
    elif sys.argv[1:] in ([],['plan']):
        print(json.dumps(plan(),indent=2))
    else:raise SystemExit('plan | apply (explicit user approval required)')
