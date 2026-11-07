"""Run the authorized gated sequence with independent host resource telemetry."""
import ctypes, datetime, json, subprocess, sys, threading, time
from pathlib import Path
import run

def monitor(bundle,stop):
    with (bundle/'HOST_TELEMETRY.jsonl').open('a',encoding='utf-8') as f:
        while not stop.is_set():
            row={'utc':run.utc(),'ram_available_bytes':run.available_ram()}
            try:
                p=subprocess.run(['nvidia-smi','--query-gpu=uuid,memory.used,memory.free,temperature.gpu,power.draw,clocks.sm,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=8,creationflags=subprocess.CREATE_NO_WINDOW)
                row.update(gpu_csv=p.stdout.strip(),exit_code=p.returncode)
            except Exception as e:row['monitor_error']=repr(e)
            f.write(json.dumps(row)+'\n');f.flush()
            stop.wait(10)

if __name__=='__main__':
    bundle=Path(sys.argv[1]).resolve()
    stop=threading.Event();t=threading.Thread(target=monitor,args=(bundle,stop),daemon=True);t.start()
    try:print(json.dumps(run.advance(bundle),indent=2),flush=True)
    except Exception as e:
        run.save(bundle/'BLOCKED.json',{'utc':run.utc(),'status':'STOPPED_REVIEW_REQUIRED','error':repr(e),'next_action':'Retain all evidence and diagnose under ENGINEERING_POLICY; no automatic retry or reference substitution.'})
        raise
    finally:stop.set();t.join(timeout=15)
