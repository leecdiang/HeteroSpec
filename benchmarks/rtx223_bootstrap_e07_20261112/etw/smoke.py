"""Exercise the actual observer's ETW path using only an isolated Python child.

No management DLL, numeric probe, CUDA provider or GPU access. A second start
is never attempted. The test does not acquire the device mutex or B ledger.
"""
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

scope = Path(__file__).resolve().parents[2] / "rtx223-e06"
sys.path.insert(0, str(scope / "runner"))
from observation import TraceRecord, function, require
from runner import runner_context

dll = Path(sys.argv[1]).resolve(strict=True)
require(hashlib.sha256(dll.read_bytes()).hexdigest() ==
        "e9e8a5f0a375f7d793104ce489a68db28ebcc3eae7c7a3b43b64f7b2e69366f2",
        "unrecognized ETW-only test artifact")
trace = C.WinDLL(str(dll), winmode=0x900)
start = function(trace, "hs_trace_start", W.DWORD)
bind = function(trace, "hs_trace_bind", W.DWORD, W.DWORD)
stop = function(trace, "hs_trace_stop", W.DWORD, C.POINTER(W.DWORD))
read = function(trace, "hs_trace_next", W.DWORD, C.POINTER(TraceRecord), W.DWORD)
receipt = {"scope": "CPU_ETW_ONLY", "runner_context": runner_context(),
           "observed_utc": datetime.now(timezone.utc).isoformat(),
           "observer_sha256": hashlib.sha256(dll.read_bytes()).hexdigest(),
           "management_library_loads": 0, "numerical_DLL_loads": 0}
child = None
try:
    rc = start()
    receipt["start_status"] = rc
    receipt["diagnostic_stage"] = trace.hs_trace_stage()
    require(rc == 0, "ETW start denied/failed")
    child = subprocess.Popen([sys.executable, "-I", "-S", "-B", "-c", "input()"],
                             stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
    get_times = function(C.WinDLL("kernel32"), "GetProcessTimes", W.BOOL,
                         W.HANDLE, *([C.POINTER(C.c_ulonglong)] * 4))
    times = [C.c_ulonglong() for _ in range(4)]
    require(get_times(int(child._handle), *(C.byref(t) for t in times)), "child creation time")
    require(bind(child.pid) == 0, "cannot bind ETW")
    require(child.communicate(b"\n", timeout=5) == (None,None) and child.returncode == 0,
            "CPU child completion")
finally:
    if child and child.poll() is None:
        child.kill()
        child.wait()
    lost = (W.DWORD * 3)()
    receipt.update(stop_status=stop(lost), loss_counters=list(lost))
    if receipt.get("start_status") == 0 and receipt["stop_status"] == 0:
        counts = {1:0,2:0,5:0,6:0}
        endpoint = []
        image_names = set()
        while True:
            rec = TraceRecord()
            rc = read(C.byref(rec), C.sizeof(rec))
            if rc == 259: break
            require(rc == 0 and rec.pid == child.pid and rec.event in counts, "ETW drain failure")
            counts[rec.event] += 1
            if rec.event in (1,2):
                endpoint.append((rec.event,rec.creation))
            if rec.event == 5:
                image_names.add(Path(rec.path).name.lower())
        receipt["counts"] = counts
        receipt["exit_identity_matched"] = endpoint == [(1,times[0].value),(2,times[0].value)]
        receipt["expected_images_matched"] = {Path(sys.executable).name.lower(), "ntdll.dll"} <= image_names
        receipt["pass"] = (not any(lost) and counts[1] == counts[2] == 1 and counts[5] > 0
                           and receipt["exit_identity_matched"] and receipt["expected_images_matched"])
    else:
        receipt["pass"] = False
    text = json.dumps(receipt, indent=2)
    with Path(sys.argv[2]).open("x",encoding="utf-8") as out:
        out.write(text+"\n")
    print(text)
if not receipt["pass"]:
    sys.exit(1)
