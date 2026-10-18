"""Independent CPU watchdog. An overdue monitor kills its named owned Job."""
import argparse,ctypes,hashlib,json,time,os
from ctypes import wintypes as W
from pathlib import Path
from common import load,save,sha
from clock_source import clock_ns,require_clock
from monitor_contract import Window,MAX_MONITOR_INTERVAL_NS,decode_sample

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True,type=Path);a=ap.parse_args();c=load(a.config)
    assert c['max_interval_ns']==MAX_MONITOR_INTERVAL_NS
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD]
    k.OpenJobObjectW.argtypes=[W.DWORD,W.BOOL,W.LPCWSTR];k.OpenJobObjectW.restype=W.HANDLE
    k.TerminateJobObject.argtypes=[W.HANDLE,W.UINT];k.CloseHandle.argtypes=[W.HANDLE]
    k.GetProcessTimes.argtypes=[W.HANDLE,ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME)]
    target=k.OpenProcess(0x100000|0x1000,False,c['target_pid']);assert target
    times=[W.FILETIME() for _ in range(4)];assert k.GetProcessTimes(target,*[ctypes.byref(t) for t in times]);assert (times[0].dwHighDateTime<<32|times[0].dwLowDateTime)==c['target_creation_filetime']
    window=Window(c['armed_ns']);pos=0;pending=b'';previous=c['config_token_sha256'];sequence=0;discarded=0;exit_ns=None
    info=require_clock()
    save(c['ready_path'],dict(pid=os.getpid(),monotonic_ns=clock_ns(),clock=info,config_sha256=sha(a.config)))
    def receipt(status):
        return dict(window.report(status),run_id=c['run_id'],execution_id=c['execution_id'],token=c['token'],target_pid=c['target_pid'],watchdog_pid=os.getpid(),config_sha256=sha(a.config),sample_chain_tail=previous,exit_observed_monotonic_ns=exit_ns,post_exit_samples_discarded=discarded,clock=info)
    try:
        while True:
            now=clock_ns()
            if k.WaitForSingleObject(target,0)==0:exit_ns=now
            path=Path(c['samples_path'])
            if path.exists():
                with path.open('rb') as f:f.seek(pos);data=f.read(2*1024**2+1)
                pos+=len(data);assert pos<=2*1024**2,'sample journal cap'
                pending+=data
                while b'\n' in pending:
                    line,pending=pending.split(b'\n',1);row,previous=decode_sample(line+b'\n',previous,c)
                    assert row['sequence']==sequence;sequence+=1
                    t=row['monotonic_ns'];assert t<=clock_ns(),'future/cross-clock timestamp'
                    if exit_ns is not None and t>exit_ns:discarded+=1;continue
                    window.sample(t)
            if Path(c['monitor_error_path']).exists():window.fail('monitor crashed',True)
            if exit_ns is not None:
                assert not pending,'truncated sample at exit'
                window.close(exit_ns);save(c['result_path'],receipt('PASS'));return
            window.check(clock_ns())
            resume=Path(c['resume_path'])
            if resume.exists():
                runtime_start=load(resume)['monotonic_ns']
                if now-runtime_start>c['native_timeout_ns']:window.fail('native runtime timeout')
            elif now-c['armed_ns']>5_000_000_000:window.fail('suspended setup timeout')
            time.sleep(.01)
    except BaseException as e:
        window.reason=window.reason or repr(e)
        if not Path(c['result_path']).exists():save(c['result_path'],receipt('FAIL'))
        # Independent of controller GIL, monitor thread, EOF and audit callbacks.
        job=k.OpenJobObjectW(8,False,c['job_name'])
        if job:k.TerminateJobObject(job,70)
        raise
    finally:k.CloseHandle(target)

if __name__=='__main__':main()
