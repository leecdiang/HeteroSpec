"""Separate CPU monitor/auditor processes. Never initialize a device/backend."""
import json
import os
import pathlib
import shutil
import struct
import sys
import threading
import time
from legacy import HERE,OLD,ROOT,RUN,OUT,load,save,sha,parse,modules,need,available_ram,runtime_gate,audit_raw,analyze_files,STAGES
from timing import Clock,PERIOD_NS
from os_process import Target
from v5_usage import bounded_usage

def rows(path):
    if not path.exists():return []
    return [parse(s) for s in path.read_text(encoding='utf-8').splitlines() if s]

class Tail:
    def __init__(self,path):self.path=pathlib.Path(path);self.offset=0;self.pending=b''
    def read(self):
        if not self.path.exists():return []
        with self.path.open('rb') as f:f.seek(self.offset);b=f.read(2*1024*1024);self.offset=f.tell()
        self.pending+=b;need(len(self.pending)<=4*1024*1024,'bounded incremental event buffer')
        lines=self.pending.split(b'\n');self.pending=lines.pop();return [parse(x) for x in lines if x]

def fault(job,name,clock):
    path=job.get('faults',{}).get(name)
    if not path:return
    need(job['purpose']=='CPU_TEST','fault injection is CPU-only')
    path=pathlib.Path(path);path.with_suffix('.entered').write_text(str(clock.now()))
    while not path.exists():time.sleep(.005)

def full_usage(job):
    bases=[pathlib.Path(p) for p in job['storage_roots']];run=pathlib.Path(job['run_root'])
    actual=sum(f.stat().st_size for p in bases if p.exists() for f in p.rglob('*') if f.is_file())
    files=[p for p in run.rglob('*') if p.is_file()] if run.exists() else []
    reserve=sum(p.stat().st_size for p in files)+len(files)*1024+1024**2
    return dict(output_bytes=actual+job.get('external_log_reserved_bytes',0),archive_reserve_bytes=reserve)

def monitor(job):
    folder=pathlib.Path(job['folder']);clock=Clock(job);lock=threading.Lock();stop=threading.Event()
    target=Target(job['pid']);need(target.times()['creation_FILETIME']==job['creation_FILETIME'],'monitor target creation identity')
    def emit(event,**data):
        with lock:
            with (folder/'MONITOR.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(dict(event=event,**data),allow_nan=False)+'\n');f.flush()
    emit('MONITOR_START',ns=clock.now(),pid=os.getpid(),target_pid=job['pid'],clock='CPU_TEST_SHARED_VIRTUAL' if clock.path else 'SYSTEM_MONOTONIC_NS')
    def sample(kind):
        try:
            while not stop.is_set() and not (folder/'EXIT_OBSERVED.json').exists():
                if not target.active():emit('TARGET_EXIT_DETECTED',ns=clock.now(),stream=kind);break
                begin=clock.now();emit('READ_BEGIN',stream=kind,begin_ns=begin)
                try:
                    fault(job,'before_'+kind,clock)
                    if job.get('faults',{}).get('raise_'+kind):raise RuntimeError('injected '+kind+' API failure')
                    # A race is recorded as incomplete, without invented values.
                    if not target.active():emit('READ_DISCARDED',stream=kind,begin_ns=begin,end_ns=clock.now(),reason='exit between poll and read');break
                    if kind=='resource':
                        values=dict(RSS=target.rss(),host_available=available_ram(),disk_free=shutil.disk_usage(job['disk_root']).free)
                        values['control_RSS']=[]
                        if (folder/'CONTROL_PIDS.json').exists():
                            for role,pid in load(folder/'CONTROL_PIDS.json').items():
                                helper=Target(pid)
                                try:
                                    if helper.active():values['control_RSS'].append(dict(role=role,pid=pid,RSS=helper.rss()))
                                finally:helper.close()
                    else:values=bounded_usage(job)
                    end=clock.now()
                    if not target.active() or (folder/'EXIT_OBSERVED.json').exists():
                        emit('READ_DISCARDED',stream=kind,begin_ns=begin,end_ns=end,reason='exit during read; values not admitted')
                    else:emit('READ_END',stream=kind,begin_ns=begin,end_ns=end,values=values)
                except Exception as e:
                    if not target.active():emit('READ_DISCARDED',stream=kind,begin_ns=begin,end_ns=clock.now(),reason='exit/read race: '+str(e))
                    else:emit('READ_ERROR',stream=kind,begin_ns=begin,end_ns=clock.now(),error=str(e))
                    stop.set();break
                stop.wait(.1)
        except Exception as e:emit('MONITOR_ERROR',stream=kind,ns=clock.now(),error=str(e));stop.set()
    threads=[threading.Thread(target=sample,args=(k,),name=k) for k in ('resource','directory')]
    for t in threads:t.start()
    for t in threads:t.join()
    emit('MONITOR_CLOSE',ns=clock.now(),pid=os.getpid(),modules=modules());target.close()

def auditor(job):
    folder=pathlib.Path(job['folder']);clock=Clock(job);test=job['purpose']=='CPU_TEST';tail=Tail(folder/'raw.jsonl')
    def emit(event,**data):
        with (folder/'AUDITOR.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(dict(event=event,ns=clock.now(),**data),allow_nan=False)+'\n');f.flush()
    try:
        emit('AUDITOR_START',pid=os.getpid(),modules=modules());gate=None
        while gate is None:
            for e in tail.read():
                if e['event']=='AWAIT_RUNTIME_GATE':gate=e
            if gate is None:
                need(not (folder/'EXIT_OBSERVED.json').exists(),'child exited before runtime gate');time.sleep(.005)
        emit('GATE_AUDIT_BEGIN');fault(job,'gate_audit',clock)
        if test:
            need(sha(job['test_module'])==job['test_module_sha256'],'CPU test module hash mismatch');gate_modules=[]
        else:gate_modules=runtime_gate(gate,load(job['F0_path']))
        save(folder/'GATE_MODULES.json',gate_modules);emit('GATE_AUDIT_OK')
        while not (folder/'EXIT_OBSERVED.json').exists():time.sleep(.005)
        emit('POST_AUDIT_BEGIN');fault(job,'post_audit',clock)
        raw=rows(folder/'raw.jsonl');need(raw and raw[-1]['event']=='CLOSE','complete child close event')
        if test:
            need(sha(job['test_module'])==job['test_module_sha256'],'CPU closing module hash mismatch')
            need((folder/'output.bin').read_bytes()==b'CPU-ONLY-EXPECTED-OUTPUT','CPU output missing/truncated')
            save(folder/'POST_AUDIT.json',dict(origin='CPU_TEST_NOT_GPU',output_sha256=sha(folder/'output.bin')))
            closing=[]
        else:
            f0=load(job['F0_path']);closing=runtime_gate(raw[-1],f0)
            audit=audit_raw(raw,load(folder/'REQUEST.wire'),job['pid'],load(OLD/'EXPECTED_GRAPHS.json'))
            save(folder/'NATIVE_AUDIT.json',audit)
            if job['request']['kind']=='graph':
                request=job['request'];data=pathlib.Path(request['input']).read_bytes();need(sha(request['input'])==request['input_sha256'],'input drift')
                manifest=load(OLD/'REFERENCE_MANIFEST.json')['inputs'][job['input_id']];reference={}
                for stage,entry in manifest['stages'].items():
                    need(sha(OLD/entry['path'])==entry['sha256'],'frozen FP64 reference identity')
                    reference[stage]=[v[0] for v in struct.iter_unpack('<d',(OLD/entry['path']).read_bytes())]
                analysis,vectors=analyze_files(request,audit['graph'],folder,data,reference)
                save(folder/'ANALYSIS.json',analysis);dest=folder/'normalized';dest.mkdir()
                for stage in STAGES:(dest/(stage+'.f32')).write_bytes(vectors[stage])
            save(folder/'POST_AUDIT.json',dict(origin='FROZEN_NATIVE_OUTPUT_AUDIT',raw_sha256=sha(folder/'raw.jsonl'),request_sha256=sha(folder/'REQUEST.wire')))
        # The directory scan remains a complete check, after exit as well.
        storage=full_usage(job);need(storage['output_bytes']+storage['archive_reserve_bytes']<=job['limits']['output_bytes'],'post-audit output budget')
        save(folder/'CLOSING_MODULES.json',closing);emit('POST_AUDIT_OK',storage=storage)
    except Exception as e:emit('AUDIT_ERROR',error=str(e));raise

if __name__=='__main__':
    command=sys.argv[1];job=load(sys.argv[2]);need(command in ('monitor','audit'),'CPU worker role')
    (monitor if command=='monitor' else auditor)(job)
