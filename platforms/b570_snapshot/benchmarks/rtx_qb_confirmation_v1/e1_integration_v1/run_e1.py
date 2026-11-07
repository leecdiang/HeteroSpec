"""Frozen bounded native E1 orchestration. All started coordinates are immutable."""
import argparse
import importlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiment as e
import adapter

ROOT=Path('D:/hs104-e1-v1');REPO=Path(__file__).resolve().parents[3]
REG='benchmarks/rtx_qb_confirmation_v1/registration/E1_F0.json'
STAGES=('QK','softmax','AV')

class Ledger:
    def __init__(self,root=ROOT):
        self.root=root;self.directory=root/'ledger';self.directory.mkdir(exist_ok=True)
        self.events=[e.read(p) for p in sorted(self.directory.glob('*.json'))]
        self.native_seconds=sum(e.read(p)['seconds'] for p in (root/'runs').rglob('LIFETIME.json'))
        self.life=self.native_seconds;self.active_start=None
    def lifetime(self):return self.life
    def owned(self):return self.life+(time.perf_counter()-self.active_start if self.active_start is not None else 0)
    def charge(self,family,phase,kind,slot):
        e.require(not any(x['slot']==slot for x in self.events),'started E1 slot cannot be retried')
        e.require(self.owned()<21600-252,'E1 combined native owned cap')
        limits={'load':72,'operator':432}
        if kind in ('warmup','request'):e.require(sum(x['kind'] in ('warmup','request') for x in self.events)<216,'E1 request cap')
        else:e.require(kind in limits and sum(x['kind']==kind for x in self.events)<limits[kind],'E1 process/operator cap')
        row=dict(utc=e.utc(),family=family,phase=phase,kind=kind,slot=slot)
        e.save(self.directory/f'{len(self.events):06d}.json',row);self.events.append(row)

def admit_snapshot(root,registry,context):
    e.require(set(registry)=={p.name for p in root.iterdir() if p.is_file()},'snapshot membership changed')
    for name,h in registry.items():e.require(e.sha(root/name)==h,'snapshot input/lifetime differs: '+name)
    m=e.read(root/'snapshot.json');q=context['q']
    e.require((m['layer'],m['phase'],m['q_occupancy'])==(context['layer'],context['phase'],q),'observed selected geometry differs')
    e.require(m['captured_key_extent']>=context['min_key'],'minimum observed key extent missed')
    Q,K,V,M=[m[n] for n in ('Q','K','V','mask')]
    e.require([x['type'] for x in (Q,K,V,M)]==[0,1,1,0],'unsupported input types')
    e.require(Q['ne'][1]==q and Q['ne'][3]==K['ne'][3]==1 and Q['ne'][2]%K['ne'][2]==0 and M['ne'][2:]==[1,1],'unsupported captured geometry')
    e.require(K['ne'][1]==m['captured_key_extent'],'key metadata differs')
    for name in ('Q','K','V','mask','native_QK','native_softmax','native_AV'):
        x=m[name];p=(root/x['file']).resolve()
        e.require(p.is_relative_to(root.resolve()) and p.stat().st_size==x['bytes'],'tensor span/path differs')
    return m

def distance(a,b):
    e.require(len(a)==len(b) and len(a)%4==0,'operator output span differs')
    n=len(a)//4;ua=struct.unpack('<'+'I'*n,a);ub=struct.unpack('<'+'I'*n,b)
    fa=struct.unpack('<'+'f'*n,a);fb=struct.unpack('<'+'f'*n,b)
    def ordered(x):return 0x80000000-(x&0x7fffffff) if x&0x80000000 else 0x80000000+x
    finite=[i for i in range(n) if math.isfinite(fa[i]) and math.isfinite(fb[i])];finite_set=set(finite)
    return dict(bitwise_equal=a==b,elements=n,equal_elements=sum(x==y for x,y in zip(ua,ub)),
                max_error=max((abs(fa[i]-fb[i]) for i in finite),default=None),
                max_ULP=max((abs(ordered(ua[i])-ordered(ub[i])) for i in finite),default=None),
                nonfinite_pairs=n-len(finite),nonfinite_bit_mismatches=sum(ua[i]!=ub[i] for i in range(n) if i not in finite_set))

def numerical(root,replays):
    qualification=e.compare_e1(root,replays)
    rows=[]
    if qualification['qualification']=='PASS':
        for left,right in (('MQ','PQ'),('MQ','QB'),('PQ','QB')):
            values={s:distance((replays/f'{left}-r0'/(s+'.bin')).read_bytes(),(replays/f'{right}-r0'/(s+'.bin')).read_bytes()) for s in STAGES}
            rows.append(dict(pair=left+'/'+right,first_divergence_operator=next((s for s in STAGES if not values[s]['bitwise_equal']),None),stages=values))
    return dict(qualification=qualification,pairs=rows,kernel='UNKNOWN',reduction_tree='UNKNOWN')

def authenticate(commit):
    e.require(not sys.flags.optimize and len(commit)==40,'unoptimized full F0 required')
    local=(ROOT/'FREEZE.json').read_bytes()
    committed=subprocess.check_output(['git','show',f'{commit}:{REG}'],cwd=REPO)
    e.require(local==committed,'local E1 freeze differs')
    actual=subprocess.check_output(['gh','api',f'repos/leecdiang/HeteroSpec/contents/{REG}?ref={commit}',
                                    '-H','Accept: application/vnd.github.raw','-H','Accept-Encoding: identity'],cwd=REPO)
    e.require(actual==committed,'authenticated E1 freeze differs')
    for item in json.loads(local)['files']:
        path=Path(item['path']);e.require(path.stat().st_size==item['bytes'] and e.sha(path)==item['sha256'],'E1 frozen file changed: '+str(path))
    result=e.read(Path('D:/hs-qb-confirmation-v02/exact_restoration_20261015/E2_ANALYSIS.json'))
    e.require(result['time_block_gate']=='PASS' and all(r['status']=='QUALIFIED_FINITE_PANEL' for r in result['comparisons']),'E2 admission lost')
    e.save(ROOT/'AUTHENTICATED_READBACK.json',dict(utc=e.utc(),commit=commit,registration=REG,sha256=e.digest(local),status='PASS'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--freeze-commit',required=True);a=p.parse_args()
    e.require(not (ROOT/'RUN_STARTED.json').exists() and not (ROOT/'EXECUTION.lock').exists(),'E1 already attempted; no scientific retry')
    authenticate(a.freeze_commit)
    plan=e.read(ROOT/'PLAN.json');sys.path.insert(0,plan['legacy'])
    common=importlib.import_module('run_common');native=importlib.import_module('resident')
    for module in (common,native):module.LOCAL=ROOT;module.PUB=ROOT;module.PORT=19615
    ledger=Ledger();e.require(not ledger.events,'E1 ledger already has starts')
    e.save(ROOT/'F0A_REMOTE_RECEIPT.json',dict(commit=a.freeze_commit,registration=REG))
    lock=ROOT/'EXECUTION.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    e.save(ROOT/'RUN_STARTED.json',dict(pid=os.getpid(),utc=e.utc(),commit=a.freeze_commit))
    try:
        for index,context in enumerate(plan['contexts']):
            family=context['family'];ident=context['id'];c=context['condition'];summary=ROOT/'contexts'/f'{index:03d}.json'
            captured=None;status=None;result={};records=[];stop=threading.Event();watch=None
            e.cool(native,ROOT/'cooldown'/f'{index:03d}.json',e.read(ROOT/'HOST.json'))
            class Worker(native.Resident):
                def __init__(self):
                    super().__init__(ledger,family,c,'e1',ident)
                    self.child_environment=adapter.clean_environment(os.environ,0,self.d/'trace.jsonl',context);self.bound_requests=0
                def request(self,route,body=None,timeout=240):
                    if route=='/completion':
                        binding=adapter.serialized_binding(body,context,self.child_environment)
                        e.save(self.d/'REQUEST_BINDINGS'/f'{self.bound_requests:02d}.json',binding);self.bound_requests+=1
                    return super().request(route,body,timeout)
                def __enter__(self):
                    try:return super().__enter__()
                    except BaseException:
                        self.__exit__(None,None,None)
                        raise
                def __exit__(self,*args):
                    if hasattr(self,'p') and self.p.poll() is None:
                        self.p.terminate()
                        try:self.p.wait(timeout=10)
                        except subprocess.TimeoutExpired:self.p.kill();self.p.wait(timeout=10)
                    if hasattr(self,'log') and not self.log.closed:self.log.close()
                    if hasattr(self,'start') and not (self.d/'LIFETIME.json').exists():
                        seconds=time.perf_counter()-self.start
                        e.save(self.d/'LIFETIME.json',dict(seconds=seconds,utc=e.utc(),pid=self.p.pid if hasattr(self,'p') else None,phase='e1'))
                        ledger.life+=seconds
                    ledger.active_start=None
            worker=Worker();native.clean_env=lambda mask,trace:adapter.clean_environment(os.environ,mask,trace,context)
            try:
                with worker as w:
                    ledger.active_start=w.start
                    def watchdog():
                        while not stop.wait(.5):
                            if ledger.owned()>=21600-2:
                                if w.p.poll() is None:w.p.kill()
                                return
                    watch=threading.Thread(target=watchdog,daemon=True);watch.start()
                    meta=dict(E1_coordinate=context,excluded_from_paid_cost=True)
                    records.append(w.complete(plan['warmups'][family],ident+'/WARM',warmup=True,meta=meta))
                    records.append(w.complete(context['task'],ident+'/CAPTURE',mode='heavy',meta=meta))
                    records.append(w.complete(context['task'],ident+'/CAPTURE_OFF',meta=meta))
                e.require(all(r['contract_valid'] and not r['workload_error'] for r in records),'native endpoint/workload contract failed')
                same=e.signature(records[1])==e.signature(records[2]);result['capture_on_off_full_equal']=same
                phase_root=worker.d/'snapshots'/context['phase']
                if not (phase_root/'snapshot.json').exists():status='NOT_OBSERVED'
                else:
                    captured=phase_root;m=e.read(captured/'snapshot.json')
                    trace=[json.loads(line) for line in (worker.d/'trace.jsonl').read_bytes().splitlines()]
                    callers=[x for x in trace if x.get('event')=='decode' and x.get('role')=='target' and x.get('phase')==context['phase'] and x.get('caller_batch',0)>=context['q']]
                    e.require(callers,'native caller trace absent')
                    e.save(captured/'LOGICAL_BOUNDARY.json',dict(native_decode=callers[0],all_matching_native_callers=callers,
                           physical_query_token_attribution='UNKNOWN unless caller width equals captured physical width; no synthesized prefix',
                           exposed_task=context['task']['id'],capture_request_slot=ident+'/CAPTURE',native_scope_mask=0))
                    registry={p.name:e.sha(p) for p in captured.iterdir() if p.is_file()}
                    admit_snapshot(captured,registry,context)
                    e.save(ROOT/'snapshot_registry'/f'{index:03d}.json',dict(context=context,root=str(captured),registry=registry))
                    result['geometry']={k:m[k] for k in ('layer','phase','q_occupancy','captured_key_extent')}
                    mask=m['mask'];mask_bytes=(captured/mask['file']).read_bytes()
                    result['geometry']['visible_mask_keys_per_query']=[sum(math.isfinite(struct.unpack_from('<f',mask_bytes,t*mask['nb'][0]+j*mask['nb'][1])[0])
                                                                          for t in range(m['captured_key_extent'])) for j in range(context['q'])]
                    result['geometry']['extent_is_not_unmasked_context_length']=True
                    result['source_lifetime']=dict(same_captured_input_bytes=True,registry=registry,raw_caller_trace=str(worker.d/'trace.jsonl'))
                    if not same:status='NOT_ADMITTED_CAPTURE_OBSERVER_MISMATCH'
                    else:
                        replays=ROOT/'operators'/f'{index:03d}';failures=[]
                        for repeat in range(2):
                            arms=['MQ','PQ','QB'];shift=(index+repeat)%3
                            for arm in arms[shift:]+arms[:shift]:
                                admit_snapshot(captured,registry,context)
                                slot=ident+f'/operator/{arm}/r{repeat}';ledger.charge(family,'operator','operator',slot)
                                dest=replays/f'{arm}-r{repeat}';start=time.perf_counter();code=None
                                command=[str(ROOT/'native/build/bin/querylayout-replay.exe'),str(captured),arm,str(dest),str(ROOT/'native/build/bin')]
                                try:
                                    r=subprocess.run(command,capture_output=True,timeout=min(120,max(1,21600-ledger.owned()-2)),creationflags=subprocess.CREATE_NO_WINDOW)
                                    dest.mkdir(parents=True,exist_ok=True);(dest/'stdout.log').write_bytes(r.stdout);(dest/'stderr.log').write_bytes(r.stderr);code=r.returncode
                                    if code:failures.append(dict(slot=slot,exit_code=code))
                                except subprocess.TimeoutExpired as error:
                                    dest.mkdir(parents=True,exist_ok=True);(dest/'stdout.log').write_bytes(error.stdout or b'');(dest/'stderr.log').write_bytes(error.stderr or b'')
                                    failures.append(dict(slot=slot,error=repr(error)))
                                finally:
                                    seconds=time.perf_counter()-start;ledger.life+=seconds
                                    e.save(ROOT/'runs/operator'/f'{index:03d}-{arm}-r{repeat}'/'LIFETIME.json',dict(seconds=seconds,utc=e.utc(),command=command,exit_code=code))
                                    admit_snapshot(captured,registry,context)
                        result['operator_failures']=failures
                        if failures:status='NOT_ADMITTED_OPERATOR_FAILURE'
                        else:
                            result['numerical']=numerical(captured,replays);status=result['numerical']['qualification']['qualification']
            except Exception as error:
                status='NOT_ADMITTED_EXECUTION_FAILURE';result.update(error=repr(error),traceback=traceback.format_exc())
            finally:
                stop.set()
                if watch:watch.join(timeout=2)
            e.save(summary,dict(index=index,context=context,status=status,records=records,result=result,utc=e.utc(),started_slots_never_retried=True))
            print(index,ident,status,flush=True)
            e.require(ledger.owned()<21600-252,'E1 owned limit; untouched remaining coordinates withheld')
        e.save(ROOT/'RUN_COMPLETE.json',dict(utc=e.utc(),contexts=72,native_owned_seconds=ledger.life,
                                           requests=sum(x['kind'] in ('warmup','request') for x in ledger.events),
                                           workers=sum(x['kind']=='load' for x in ledger.events),operators=sum(x['kind']=='operator' for x in ledger.events)))
    except BaseException as error:
        e.save(ROOT/'RUN_FAILED.json',dict(utc=e.utc(),error=repr(error),traceback=traceback.format_exc()))
        raise
    finally:lock.unlink()
if __name__=='__main__':main()
