"""One owned CPU worker per group; hard wall/RSS/output watchdog, no retry."""
import argparse, ctypes, datetime, json, os, pathlib, subprocess, sys, time
from common import ROOT, load, save, sha, modules
from inputs import write_input
sys.path.insert(0,str(ROOT))
import plan

def rss(proc):
    class Memory(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('faults',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ('peak_ws','ws','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile')]
    k=ctypes.WinDLL('kernel32',use_last_error=True);m=Memory();m.cb=ctypes.sizeof(m)
    k.K32GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong]
    if not k.K32GetProcessMemoryInfo(int(proc._handle),ctypes.byref(m),ctypes.sizeof(m)):return None
    return m.ws

def main():
    p=argparse.ArgumentParser();p.add_argument('group',choices=['development','held_after_code_lock']);a=p.parse_args();before=modules()
    if a.group!='development':assert (ROOT/'host/HOST_RULE_LOCK.json').exists()
    root=ROOT/'host_outputs'/a.group;root.mkdir(parents=True,exist_ok=False)
    cells=[]
    for cell in plan.cpu_cells():
        if cell['group']!=a.group:continue
        inp=root/(cell['id']+'.input');digest=write_input(inp,cell)
        raw=root/cell['id'];raw.mkdir();cells.append(dict(id=cell['id'],input=str(inp),input_sha256=digest,raw_dir=str(raw)))
    save(root/'inputs.json',cells)
    exe=ROOT/'build/Release/qh-real.exe';out=root/'raw.jsonl';err=root/'stderr.log';stdout=root/'stdout.log'
    git=os.environ.get('HETEROSPEC_GIT','git');commit=subprocess.check_output([git,'-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    oldelapsed=load(ROOT/'host/S0_DEVELOPMENT_RECEIPT.json')['owned_wall_s'] if a.group!='development' else 0
    start=time.monotonic();begin=datetime.datetime.now(datetime.timezone.utc).isoformat();maxrss=0;gate=None;samples=[]
    with stdout.open('wb') as so,err.open('wb') as se:
        proc=subprocess.Popen([str(exe),str(root/'inputs.json'),str(out)],stdout=so,stderr=se)
        while proc.poll() is None:
            used=rss(proc);maxrss=max(maxrss,used or 0)
            total=sum(f.stat().st_size for f in (ROOT/'host_outputs').rglob('*') if f.is_file())
            elapsed=time.monotonic()-start
            samples.append(dict(elapsed_s=elapsed,RSS=used,output_bytes=total))
            if elapsed+oldelapsed>14400 or maxrss>8*1024**3 or total>2*1024**3:
                gate='OWNED_CPU_BUDGET_STOP';proc.kill();break
            time.sleep(.1)
        code=proc.wait()
    elapsed=time.monotonic()-start
    events=[json.loads(x) for x in out.read_text().splitlines()] if out.exists() else []
    complete=[x for x in events if x['event']=='FIXTURE_COMPLETE'];started=[x for x in events if x['event']=='FIXTURE_START']
    loaded=next((x['loaded'] for x in events if x['event']=='MODULES'),[])
    for row in cells:assert sha(row['input'])==row['input_sha256']
    label='DEVELOPMENT' if a.group=='development' else 'HELD'
    save(ROOT/f'host/S0_{label}_RECEIPT.json',dict(group=a.group,commit=commit,pid=proc.pid,exe_sha256=sha(exe),begin_utc=begin,owned_wall_s=elapsed,
         returncode=code,gate=gate,planned_fixtures=len(cells),started_fixtures=len(started),completed_fixtures=len(complete),
         graph_computes_completed=6*len(complete),partial_active_graphs='UNKNOWN_IF_INTERRUPTED' if code else 0,
         unstarted_ids=[x['id'] for x in cells if x['id'] not in {r['id'] for r in started}],
         input_hashes=[dict(id=x['id'],sha256=x['input_sha256']) for x in cells],raw_jsonl_sha256=sha(out) if out.exists() else None,
         stderr=err.read_text(errors='replace'),peak_sampled_RSS=maxrss,watchdog_samples=samples,
         actual_loaded_modules=[dict(path=x,sha256=sha(x)) for x in loaded],modules_before=before,modules_after=modules(),
         new_model_processes=0,new_model_requests=0,GPU_starts=0,probes=0,warmups=0,retries=0))
    print(dict(group=a.group,returncode=code,complete=len(complete),owned_wall_s=elapsed,stderr=err.read_text(errors='replace')))
    raise SystemExit(code)

if __name__=='__main__':main()
