"""AppContainer launch diagnostics. CPU images only, never resumes any child."""
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
from contextlib import ExitStack

BASE = Path(__file__).resolve().parents[2]
w = runpy.run_path(str(BASE/'rtx223-e06/runner/winjob.py'))
fake = BASE/'rtx223-e06/build/probes-attempt-002/cpu-probe.exe'
assert hashlib.sha256(fake.read_bytes()).hexdigest() == '8a5cc2607dfdf3e59902dbb359e09e20e4348aa736b7bd3fac788fa996f449cb'
PACKAGE = 'HeteroSpec.RTX223.Bootstrap.B1'
results=[]
for label, image, cwd, package in (
    ('same_cpu_plain_job',fake,fake.parent,None),
    ('same_cpu_appcontainer_job',fake,fake.parent,PACKAGE),
    ('same_cpu_system_cwd',fake,Path(os.environ['SystemRoot'])/'System32',PACKAGE),
    ('system_image_appcontainer_job',Path(os.environ['SystemRoot'])/'System32/cmd.exe',Path(os.environ['SystemRoot'])/'System32',PACKAGE),
):
    job=w['AtomicJob']()
    try:
        job.create([str(image)],cwd,{'SystemRoot':os.environ['SystemRoot']},package)
        results.append({'case':label,'created_suspended':True,'resumed':False,'active':job.active()})
    except Exception as exc:
        results.append({'case':label,'created_suspended':False,'error':str(exc)})
    finally:
        if job.process:
            job.kill()
            w['Wait'](job.process,2000)
        job.close()

with ExitStack() as stack:
    caps=w['no_caps'](PACKAGE,stack)
    adv=C.WinDLL('advapi32')
    sid_text=W.LPWSTR()
    fn=adv.ConvertSidToStringSidW
    fn.argtypes=[C.c_void_p,C.POINTER(W.LPWSTR)]
    if not fn(caps.sid,C.byref(sid_text)):
        raise RuntimeError('SID conversion')
    env=C.WinDLL('userenv')
    folder=W.LPWSTR()
    fn=env.GetAppContainerFolderPath
    fn.argtypes=[W.LPCWSTR,C.POINTER(W.LPWSTR)]
    fn.restype=C.c_long
    rc=fn(sid_text,C.byref(folder))
    profile={'derived_sid_succeeded':True,'folder_hresult':hex(rc&0xffffffff),'folder':folder.value}
    # API buffers only; no profile is created or deleted.
    k=C.WinDLL('kernel32')
    k.LocalFree.argtypes=[C.c_void_p]
    k.LocalFree(sid_text)
    if folder:
        C.WinDLL('ole32').CoTaskMemFree(folder)
print(json.dumps({'scope':'CPU suspended-creation diagnostics; no GPU, profiles or ACL changes',
                  'cases':results,'profile_probe':profile},indent=2))
