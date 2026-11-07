"""Exact S1 executor. Do not invoke without explicit author approval of F0 SHA."""
import argparse, ctypes, datetime, hashlib, json, os, pathlib, shutil, struct, subprocess, sys, time
from common import ROOT, load, save, sha, modules
from run_s0 import rss
sys.path.insert(0,str(ROOT))
import core, evidence, plan

def admission(f0,approved_sha):
    core.need(type(approved_sha) is str and approved_sha==sha(ROOT/'host/S1_F0.json'),'explicit author-approved exact F0 SHA required')
    core.need(f0['limits']['operator_host_attempts']==161 and f0['limits']['model_requests']==0,'wrong budget')
    for f,digest in f0['sources'].items():core.need(sha(ROOT/f)==digest,'source changed '+f)
    for x in [f0['executable']]+f0['dependencies']+f0['driver_files']:core.need(sha(x['path'])==x['sha256'],'runtime file changed')
    environment={k:v for k,v in sorted(os.environ.items()) if k.startswith(('GGML_','VK_','LLAMA_'))}
    core.need(environment==f0['environment'],'backend environment changed')

def available_ram():
    class Mem(ctypes.Structure):_fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ('total','available','pagefile','availpage','virtual','availvirtual','extended')]
    m=Mem();m.length=ctypes.sizeof(m);core.need(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))!=0,'host memory receipt');return m.available

def runtime_gate(event,f0):
    required={pathlib.Path(x['path']).name.lower():x['sha256'] for x in f0['dependencies']}
    drivers={pathlib.Path(x['path']).name.lower():set() for x in f0['driver_files']}
    for x in f0['driver_files']:drivers[pathlib.Path(x['path']).name.lower()].add(x['sha256'])
    seen=set();rows=[]
    for path in event['modules']:
        name=pathlib.Path(path).name.lower();digest=sha(path);rows.append(dict(path=path,sha256=digest))
        if name.startswith(('ggml','llama')):
            core.need(name in required and digest==required[name],'unadmitted numerical module '+name);seen.add(name)
        if name in drivers:core.need(digest in drivers[name],'driver identity mismatch '+name)
    core.need(seen==set(required),'missing numerical module')
    return rows

def read_events(path):
    if not path.exists():return []
    lines=path.read_text(encoding='utf-8').splitlines();rows=[]
    for line in lines:
        try:rows.append(json.loads(line))
        except json.JSONDecodeError:break # concurrent last line; completed audit rejects it later
    return rows

def slot_accounting(slots,started,completed,skipped):
    expected={s['id'] for s in slots}
    core.need(len(started)==len(set(started)) and set(started)<=expected,'duplicate/unplanned attempt')
    core.need(set(completed)<=set(started) and not set(skipped)&set(started),'invalid attempt state')
    return dict(failed=[s for s in started if s not in completed],
                unstarted=[s['id'] for s in slots if s['id'] not in started and s['id'] not in skipped])

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
            if now-start>180 or now-start+owned>3600 or (used or 0)>8*1024**3 or total>2*1024**3 or ram<8*1024**3 or disk<4*1024**3 or observations[-1]['gap_ms']>1000:
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
        core.need(cursor==len(source),'independent serialized input length');payload[0]=bytes(32)+payload[0]
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

def main():
    p=argparse.ArgumentParser();p.add_argument('--author-approved-f0-sha',required=True);a=p.parse_args();before=modules()
    f0=load(ROOT/'host/S1_F0.json');admission(f0,a.author_approved_f0_sha)
    root=ROOT/'host_outputs/S1_RUN';root.mkdir(exist_ok=False)
    inputs={x['id']:x for x in load(ROOT/'host/S1_INPUTS.json')}
    for x in inputs.values():core.need(sha(x['path'])==x['sha256'],'input bytes changed')
    slots=load(ROOT/'host/S1_PLAN.json')['slots'];ledger=(root/'LEDGER.jsonl').open('x',encoding='utf-8')
    def record(event,**kw):ledger.write(json.dumps(dict(event=event,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw))+'\n');ledger.flush()
    owned=0.;attempts=0;completed=[];started=[];skipped=[];selection=None;status='STOPPED';error=None;outputs={}
    try:
        for i,s in enumerate(slots):
            folder=root/s['id']
            if i and not supported[core.sha(s['cell']),s['mode']]:skipped.append(s['id']);record('SKIPPED_UNSUPPORTED',slot=s['id']);continue
            request=dict(study=core.STUDY,F0_sha256=a.author_approved_f0_sha,kind=s['kind'])
            if i==0:request['cells']=plan.operator_cells()
            else:
                data=inputs[core.sha(s['cell'])];request.update(cell=s['cell'],mode=s['mode'],input=data['path'],output_dir=str(folder/'vectors'))
            attempts+=1;started.append(s['id']);record('PROCESS_ATTEMPT',slot=s['id'],attempt=attempts,request=request)
            events,receipt=child(request,folder,f0,owned);owned+=receipt['owned_wall_s'];completed.append(s['id']);record('PROCESS_COMPLETE',slot=s['id'],receipt=receipt)
            if i==0:
                observations=[];supported={}
                for e in events:
                    if e.get('event')!='CAPABILITY':continue
                    nodes=[dict(id=str(n['id']),op=n['op'],supports_op=n['supports_op']) for n in e['nodes'] if n['executable']]
                    key=core.sha(e['cell']),e['mode'];supported[key]=all(n['supports_op'] for n in nodes)
                    observations.append(dict(cell_sha256=key[0],mode=key[1],compute_nodes=nodes,raw_sha256=receipt['raw_sha256']))
                census=dict(binding_sha256=a.author_approved_f0_sha,observations=observations)
                selection=evidence.choose_from_capabilities(census,a.author_approved_f0_sha)
                save(root/'CAPABILITY_CENSUS.json',census);save(root/'CANDIDATE_SELECTION.json',dict(choice=selection,census_sha256=sha(root/'CAPABILITY_CENSUS.json'),before_numerical_graph=True))
                record('CHOICE_FROZEN_BEFORE_OUTPUTS',choice=selection)
                core.need(selection in ('QH_C','QH_D'),selection)
            else:
                core.need(sha(inputs[core.sha(s['cell'])]['path'])==inputs[core.sha(s['cell'])]['sha256'],'input file changed after graph')
                key=core.sha(s['cell']);out=folder/'vectors/final.f32';outputs[key,s['mode'],s['repeat']]=out
                for (ck,mode,rep),other in list(outputs.items()):
                    if ck!=key:continue
                    q=s['cell']['geometry']['q']
                    comparison=evidence.compare_f32(out,other)
                    record('FULL_VECTOR_COMPARISON',left=s['id'],other_mode=mode,other_repeat=rep,metrics=comparison)
                    if q==1 or mode==s['mode']:core.need(comparison['bitwise_equal'],'q1/common-path or independent-repeat disagreement')
        status='S1_COMPLETE_PENDING_INDEPENDENT_STAGE_ANALYSIS'
    except Exception as e:error=str(e);record('STOP',error=error)
    finally:
        owned=sum(load(p)['owned_wall_s'] for p in root.glob('*/LIFECYCLE.json'))
        record('CLOSEOUT',status=status,attempts=attempts,owned_wall_s=owned)
        ledger.close();save(root/'CLOSEOUT.json',dict(status=status,error=error,attempts=attempts,owned_wall_s=owned,completed=completed,skipped_unsupported=skipped,
             **slot_accounting(slots,started,completed,skipped),selected_candidate=selection,model_requests=0,warmups=0,retries=0,automatic_S2=False,modules_before=before,modules_after=modules()))
    if error:raise SystemExit(error)

if __name__=='__main__':main()
