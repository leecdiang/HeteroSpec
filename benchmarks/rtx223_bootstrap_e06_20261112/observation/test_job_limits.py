"""CPU-only Windows Job enforcement. Creates no GPU lease or B attempt."""
import json
import os
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "runner"))
from winjob import AtomicJob, need

# No pages are touched. If unexpectedly accepted, immediately release and fail.
payload = """
import ctypes as C, json, subprocess, sys
k = C.WinDLL('kernel32',use_last_error=True)
k.VirtualAlloc.argtypes = [C.c_void_p,C.c_size_t,C.c_ulong,C.c_ulong]
k.VirtualAlloc.restype = C.c_void_p
k.VirtualFree.argtypes = [C.c_void_p,C.c_size_t,C.c_ulong]
p = k.VirtualAlloc(None,(2<<30)+65536,0x3000,4)
rc = C.get_last_error()
if p:
    k.VirtualFree(p,0,0x8000)
try:
    child = subprocess.Popen([sys.executable,'-I','-B','-S','-c','pass'])
except OSError as e:
    child_error = e.winerror
else:
    child.wait(2)
    child_error = None
print(json.dumps(dict(allocation_denied=not p,alloc_error=rc,child_create_error=child_error)))
"""
job = AtomicJob()
try:
    job.create([sys.executable,"-I","-B","-S","-c",payload], root,
               {"SystemRoot":os.environ["SystemRoot"]})
    need(job.active() == 1, "suspended process not bound")
    job.resume()
    expiry = time.monotonic() + 5
    while job.exit_code() is None and time.monotonic() < expiry:
        time.sleep(.01)
    need(job.exit_code() == 0, "fixture exit missing")
    receipt = json.loads(job.read(job.output))
    need(receipt["allocation_denied"] and receipt["child_create_error"] is not None,
         "Job did not reject over-limit operation")
    receipt.update(scope="CPU-only, real Win32 Job",job_active_after=job.active(),
                   native_probe_runs=0,model_loads=0,gpu_contexts=0,kernel_launches=0)
    print(json.dumps(receipt, indent=2))
finally:
    job.close()
