"""Real CPU-only controller for launch integration tests, never production."""
import sys
sys.dont_write_bytecode=True
if sys.stdin.buffer.readline() not in (b'LAUNCH_GO\r\n',b'LAUNCH_GO\n'):raise SystemExit('owned CPU launcher gate')
import pathlib
import threading
import time
import json
import traceback
from legacy import HERE,PYTHON,LIMITS,load,save,sha,modules,need,EXTERNAL_RESERVED_BYTES
from supervisor import supervise
from lifecycle_audit import audit
from storage import Watch

cfg=load(sys.argv[1]);need(cfg['purpose']=='CPU_LAUNCH_TEST','CPU purpose')
root=pathlib.Path(cfg['case_root']);protected=[pathlib.Path(p) for p in cfg['protected_roots']]
source,out=protected[:2];folder=out/'active';release=root/'RELEASE_CHILD';module=source/'CPU_MODULE.bin'
start=time.monotonic_ns();finished=threading.Event();mutation={};thread_errors=[]
job=dict(purpose='CPU_TEST',folder=str(folder),disk_root=str(root),run_root=str(out),storage_roots=[str(p) for p in protected],
    limits=LIMITS,per_slot_seconds=8,panel_seconds=15,panel_begin_ns=start,external_log_reserved_bytes=EXTERNAL_RESERVED_BYTES,
    test_module=str(module),test_module_sha256=sha(module),cpu_child=dict(release=str(release)),faults={})
behavior=cfg['behavior']
if behavior=='resource_failure':job['faults']['raise_resource']=True
if behavior=='monitor_timeout':job['faults']['before_resource']=str(root/'BLOCK_RESOURCE')
if behavior=='cleanup_failure':job['faults']['raise_watch_cleanup']=True
if behavior=='notification_loss':
    original=Watch.accept
    def lost(self,data):return original(self,b'') # Actual parser's loss signal, CPU-only injection.
    Watch.accept=lost
if behavior=='exit_race':
    job['faults']['before_resource']=str(root/'BLOCK_RESOURCE');job['cpu_child']['exit_before_GO_when']=str(root/'EXIT_RACE')
def writer():
    try:
        deadline=time.monotonic()+10
        while not (folder/'WATCH_1.jsonl').exists() and time.monotonic()<deadline and not finished.is_set():time.sleep(.005)
        if finished.is_set():return
        print('LOG_AFTER_WATCH_READY stdout',flush=True);print('LOG_AFTER_WATCH_READY stderr',file=sys.stderr,flush=True)
        if behavior=='log_limit':
            for i in range(64):
                for name,stream,label in (('stdout',sys.stdout.buffer,b'OUT'),('stderr',sys.stderr.buffer,b'ERR')):
                    header=label+b'_SEQ='+str(i).zfill(4).encode()+b';';frame=header+b'X'*(4096-len(header));stream.write(frame);stream.flush()
                    with (folder/'PRODUCER_ACK.jsonl').open('a') as f:f.write(json.dumps(dict(stream=name,index=i,bytes=len(frame)))+'\n');f.flush()
            return
        mutated=False;count=0;executed_at=None
        while not finished.is_set():
            print('APPEND stdout '+str(count)+' '+'a'*128,flush=True);print('APPEND stderr '+str(count)+' '+'b'*128,file=sys.stderr,flush=True);count+=1
            if behavior=='exit_race' and pathlib.Path(job['faults']['before_resource']).with_suffix('.entered').exists():
                (root/'EXIT_RACE').write_text('exit');time.sleep(.1);pathlib.Path(job['faults']['before_resource']).write_text('release')
            if (folder/'EXECUTED').exists():
                if executed_at is None:executed_at=time.monotonic()
                if not mutated:
                    target={'source_results':source/'results'/'unexpected.bin','inactive':out/'inactive'/'old.bin','frozen_input':source/'inputs/frozen.input'}.get(behavior)
                    if target is not None:target.write_bytes(b'CPU-MUTATION');mutation.update(path=str(target),after_watch=True);mutated=True
                    if behavior=='normal' or behavior=='late_tree':(folder/'ACTIVE_GROWING.bin').write_bytes(b'active slot data');mutated=True
                if time.monotonic()-executed_at>.8:release.write_text('finish CPU child')
            time.sleep(.02)
    except BaseException as e:thread_errors.append(str(e))
thread=threading.Thread(target=writer,name='CPU_CONTROLLER_STDIO_WRITER',daemon=True);thread.start();life=None;exception=None
try:
    life=supervise(job,[str(PYTHON),str(HERE/'cpu_child.py'),str(folder/'CHILD.json')])
    if life['stop'] is None:audit(folder)
except BaseException as e:exception=str(e)
finally:
    finished.set()
    for value in job['faults'].values():
        if isinstance(value,str):pathlib.Path(value).write_text('release cleanup')
    thread.join(timeout=2)
    result=dict(purpose='CPU_LAUNCH_TEST',behavior=behavior,lifecycle=life,exception=exception,mutation=mutation,writer_errors=thread_errors,
        modules=modules(),device_queries=0,graph_computes=0,wall_seconds=(time.monotonic_ns()-start)/1e9)
    save(root/'CPU_CONTROLLER_RESULT.json',result)
if exception or life is None or life['stop'] is not None:raise SystemExit(12)
