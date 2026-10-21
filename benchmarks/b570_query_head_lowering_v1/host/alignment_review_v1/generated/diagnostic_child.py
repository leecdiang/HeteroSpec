"""Frozen child supervisor adapted from original S1. Import only; no launch on import."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]))
import subprocess,time,shutil,hashlib,struct
from common import ROOT,save,sha
from run_s0 import rss
from run_s1 import runtime_gate,available_ram,read_events
sys.path.insert(0,str(ROOT))
import core
def child(request,folder,f0,owned):
    folder.mkdir();wire=folder/'REQUEST.wire';wire.write_bytes(core.encode(request))
    raw=folder/'raw.jsonl';start=time.monotonic();observations=[];stop=None;gate_sent=False;gate_modules=[]
    with (folder/'stdout.log').open('wb') as so,(folder/'stderr.log').open('wb') as se:
        proc=subprocess.Popen([f0['executable']['path'],str(wire),str(raw)],stdin=subprocess.PIPE,stdout=so,stderr=se)
        last=start
        while proc.poll() is None:
            now=time.monotonic();used=rss(proc);ram=available_ram();disk=shutil.disk_usage(ROOT).free
            total=sum(x.stat().st_size for x in folder.parent.rglob('*') if x.is_file())
            observations.append(dict(elapsed_s=now-start,gap_ms=(now-last)*1000,RSS=used,host_available=ram,disk_free=disk,output_bytes=total));last=now
            if now-start>60 or now-start+owned>420 or (used is None or used>8*1024**3) or total>128*1024**2 or ram<8*1024**3 or disk<4*1024**3 or observations[-1]['gap_ms']>1000:
                stop='PROSPECTIVE_RESOURCE_OR_OBSERVER_GATE';proc.kill();break
            if not gate_sent:
                gate=next((x for x in read_events(raw) if x.get('event')=='AWAIT_RUNTIME_GATE'),None)
                if gate:
                    try:gate_modules=runtime_gate(gate,f0);proc.stdin.write(b'GO\n');proc.stdin.flush();gate_sent=True
                    except Exception as e:stop='RUNTIME_GATE: '+str(e);proc.kill();break
            time.sleep(.1)
        code=proc.wait()
    elapsed=time.monotonic()-start;events=read_events(raw)
    result=dict(pid=proc.pid,returncode=code,stop=stop,owned_wall_s=elapsed,request_sha256=sha(wire),raw_sha256=sha(raw) if raw.exists() else None,
                actual_runtime_modules=gate_modules,watchdog_samples=observations,graph_start_events=sum(x.get('event')=='GRAPH_START' for x in events),
                graph_return_events=sum(x.get('event')=='GRAPH_RETURN' for x in events))
    save(folder/'LIFECYCLE.json',result)
    core.need(code==0 and stop is None and gate_sent,'owned worker failed: '+str(result))
    core.need(events[0]['event']=='HOST_START' and events[0]['pid']==proc.pid and events[0]['request']==request,'raw request/process reconstruction')
    core.need(events[-1]['event']=='CLOSE','incomplete raw close')
    # Reparse completed bytes strictly; no truncated line accepted by the final auditor.
    core.need(len(events)==len(raw.read_text().splitlines()),'truncated raw event')
    for e in events:
        if e.get('event')=='MEMORY_CHECKPOINT':core.need(e['backend_reported_free_bytes']>=512*1024**2,'memory gate')
    if request['kind']=='graph':
        core.need(result['graph_start_events']==result['graph_return_events']==1,'single graph ownership')
        core.need(any(x.get('event')=='GRAPH_OUTPUT' and x['input_bytes_unchanged'] for x in events),'missing full output/input identity')
        g=request['cell']['geometry'];n,q,h,hk=(g[k] for k in ('n','q','h','hk'));dest=pathlib.Path(request['output_dir'])
        output=next(x for x in events if x.get('event')=='GRAPH_OUTPUT')
        core.need(output['final']['ne']==[128*h,q,1,1] and (dest/'final.f32').stat().st_size==128*h*q*4,'full output dimensions')
        source=pathlib.Path(request['input']).read_bytes();cursor=28;payload=[]
        for size in (128*q*h*4,128*n*hk*2,128*n*hk*2,32*n*4):payload.append(source[cursor:cursor+size]);cursor+=size
        core.need(cursor==len(source),'independent serialized input length');payload[0]=bytes(request['q_offset_bytes'])+payload[0]
        if request['relocate_pq_mask'] and request['mode']=='PQ' and q>1:
            mask_bytes=payload[3]
            payload.extend(mask_bytes[j*n*4:(j+1)*n*4] for j in range(q))
        identities=[]
        for i,expected in enumerate(payload):
            digest=hashlib.sha256(expected).hexdigest();bp=dest/f'input-{i}.before.bin';ap=dest/f'input-{i}.after.bin'
            core.need(sha(bp)==sha(ap)==digest,'independent GPU input before/after SHA mismatch')
            identities.append(dict(input=i,source_sha256=digest,before_sha256=sha(bp),after_sha256=sha(ap)))
        save(folder/'INPUT_IDENTITY_AUDIT.json',identities)
        for f in pathlib.Path(request['output_dir']).glob('*.f32'):
            b=f.read_bytes();core.need(len(b)>0 and len(b)%4==0,'complete full-vector bytes')
            import math
            core.need(all(math.isfinite(x[0]) for x in struct.iter_unpack('<f',b)),'nonfinite vector')
    return events,result
