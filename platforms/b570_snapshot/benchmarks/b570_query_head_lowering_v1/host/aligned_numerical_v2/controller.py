"""Owned-process supervisor. No launch occurs on import or in CPU metadata tests."""
import pathlib
import ctypes
import shutil
import subprocess
import sys
import time
from panel_common import HERE,ROOT,RUN,LIMITS,need,parse,sha,save
sys.path.insert(0,str(ROOT/'host'))
from run_s0 import rss
from run_s1 import runtime_gate,available_ram

def output_usage():
    paths=(HERE,ROOT/'host_outputs/aligned_numerical_v2')
    actual=sum(f.stat().st_size for p in paths if p.exists() for f in p.rglob('*') if f.is_file())
    raw=sum(f.stat().st_size for f in RUN.rglob('*') if f.is_file()) if RUN.exists() else 0
    # Reserve one full raw copy plus generous per-entry ZIP overhead for export.
    count=sum(1 for f in RUN.rglob('*') if f.is_file()) if RUN.exists() else 0
    return actual,raw+count*1024+1024**2

def events(path,partial=False):
    if not path.exists():return []
    rows=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        try:rows.append(parse(line))
        except (ValueError,TypeError):
            if partial:break
            raise
    return rows

def launch(slot,request,wire_bytes,f0,owned):
    folder=RUN/slot['id'];folder.mkdir(exist_ok=False)
    wire=folder/'REQUEST.wire';wire.write_bytes(wire_bytes);raw=folder/'raw.jsonl'
    start=time.monotonic();samples=[];proc=None;code=None;stop=None;gate_sent=False;module_rows=[];closing_rows=[];creation=None
    try:
        with (folder/'stdout.log').open('xb') as so,(folder/'stderr.log').open('xb') as se:
            proc=subprocess.Popen([f0['executable']['path'],str(wire),str(raw)],stdin=subprocess.PIPE,stdout=so,stderr=se)
            times=[ctypes.c_ulonglong() for _ in range(4)]
            k=ctypes.WinDLL('kernel32',use_last_error=True)
            k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.c_void_p]*4
            need(k.GetProcessTimes(int(proc._handle),*[ctypes.byref(t) for t in times])!=0,'process creation identity')
            creation=times[0].value
            last=start
            while proc.poll() is None:
                now=time.monotonic();used=rss(proc);ram=available_ram();disk=shutil.disk_usage(ROOT).free;actual,reserve=output_usage()
                sample=dict(elapsed_s=now-start,gap_ms=(now-last)*1000,RSS=used,host_available=ram,disk_free=disk,output_bytes=actual,archive_reserve_bytes=reserve)
                samples.append(sample);last=now
                if (now-start>LIMITS['per_host_seconds'] or now-start+owned>LIMITS['owned_seconds'] or used is None or
                    used>LIMITS['worker_RSS_bytes'] or actual+reserve>LIMITS['output_bytes'] or ram<LIMITS['host_available_bytes'] or
                    disk<LIMITS['disk_free_bytes'] or sample['gap_ms']>LIMITS['maximum_actual_gap_ms']):
                    stop='RESOURCE_OR_OBSERVER_GATE';proc.kill();break
                if not gate_sent:
                    gate=next((e for e in events(raw,True) if e['event']=='AWAIT_RUNTIME_GATE'),None)
                    if gate:
                        try:
                            module_rows=runtime_gate(gate,f0);proc.stdin.write(b'GO\n');proc.stdin.flush();gate_sent=True
                        except Exception as e:stop='RUNTIME_GATE: '+str(e);proc.kill();break
                time.sleep(.1)
            code=proc.wait()
        if code==0 and stop is None and gate_sent:
            complete=events(raw);need(complete and complete[-1]['event']=='CLOSE','complete native close')
            closing_rows=runtime_gate(complete[-1],f0)
    except Exception as e:
        stop='PROCESS_OR_SUPERVISOR_EXCEPTION: '+str(e)
        if proc is not None and proc.poll() is None:proc.kill();code=proc.wait()
    finally:
        elapsed=time.monotonic()-start
        receipt=dict(pid=proc.pid if proc is not None else None,creation_FILETIME=creation,returncode=code,stop=stop,owned_wall_s=elapsed,
            request_sha256=sha(wire),raw_sha256=sha(raw) if raw.exists() else None,watchdog_samples=samples,
            actual_runtime_modules=module_rows,closing_runtime_modules=closing_rows,command=[f0['executable']['path'],str(wire),str(raw)])
        save(folder/'LIFECYCLE.json',receipt)
    need(code==0 and stop is None and gate_sent,'owned host failed; no expected-crash slots or retries')
    need(elapsed<=LIMITS['per_host_seconds'] and elapsed+owned<=LIMITS['owned_seconds'],'final owned-time gate')
    from native_audit import audit_lifecycle
    audit_lifecycle(receipt,events(raw),f0,owned)
    return events(raw),receipt
