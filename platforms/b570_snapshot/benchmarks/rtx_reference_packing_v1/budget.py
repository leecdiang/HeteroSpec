"""Own-child resource watchdog and immutable child lifetime ledger."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).parent
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n')
class Memory(ctypes.Structure):
    _fields_=[('cb',ctypes.c_ulong),('faults',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ('peak_ws','ws','peak_pool','pool','peak_nonpool','nonpool','page','peak_page')]
def main():
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
    ledger=ROOT/'child_ledger';ledger.mkdir(exist_ok=True)
    assert a.command and all(c.isalnum() or c in '_-' for c in a.label)
    for x in ledger.glob('*-START.json'):assert x.with_name(x.name.replace('-START','-EXIT')).exists(),'unresolved prior child; do not reset cost'
    spent=sum(json.loads(x.read_text())['seconds'] for x in ledger.glob('*-EXIT.json'))
    assert spent<14400
    lock=ROOT/'CPU_JOB.lock'
    with lock.open('x') as f:json.dump(dict(owner_pid=os.getpid(),label=a.label,epoch=time.time()),f)
    index=len(list(ledger.glob('*-START.json')));prefix=f'{index:03d}-{a.label}'
    save(ledger/(prefix+'-START.json'),dict(command=a.command,epoch=time.time(),label=a.label,prior_seconds=spent,watchdog_pid=os.getpid()))
    start=time.perf_counter();peak=None;reason=None;code=-1;error=None;child=None
    try:
        with (ledger/(prefix+'.stdout.log')).open('xb') as out,(ledger/(prefix+'.stderr.log')).open('xb') as err:
            child=subprocess.Popen(a.command,cwd=ROOT,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            save(ledger/(prefix+'-PID.json'),dict(pid=child.pid,epoch=time.time()))
            mem=Memory();mem.cb=ctypes.sizeof(mem)
            api=ctypes.WinDLL('psapi').GetProcessMemoryInfo;api.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong];api.restype=ctypes.c_int
            while True:
                if api(int(child._handle),ctypes.byref(mem),ctypes.sizeof(mem)):peak=max(peak or 0,mem.peak_ws)
                elapsed=time.perf_counter()-start
                if elapsed+spent>=14400 or (peak or 0)>8589934592:reason='TIME_OR_RSS_CAP'
                if sum(x.stat().st_size for x in ROOT.rglob('*') if x.is_file())>2147483648:
                    reason='DERIVED_OUTPUT_CAP'
                if reason and child.poll() is None:child.kill()
                if child.poll() is not None:break
                time.sleep(.1)
            code=child.wait()
    except BaseException as exc:
        error=repr(exc)
        if child is not None and child.poll() is None:child.kill();child.wait()
    finally:
        receipt=dict(seconds=time.perf_counter()-start,exit_code=code,peak_rss_bytes=peak,stop_reason=reason,error=error)
        save(ledger/(prefix+'-EXIT.json'),receipt);lock.unlink()
    print(json.dumps(dict(label=a.label,**receipt)))
    sys.exit(code if code else (1 if reason or error else 0))
if __name__=='__main__':main()
