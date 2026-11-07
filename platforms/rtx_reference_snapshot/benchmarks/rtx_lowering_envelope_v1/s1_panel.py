"""Separately approved, immutable next-slot executor. Never invoked by S0.

It cannot run without authenticated pre-output selection and an exact author
approved list of slot IDs. Partial approval never implies a full-panel launch.
"""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
import audit,safety
from s0_budget import ROOT,save
from recover_s0 import sha
def main():
    p=argparse.ArgumentParser();p.add_argument('--approval',required=True);a=p.parse_args();approval=audit.load(a.approval)
    assert approval['stage']=='S1B_EXACT_SLOTS' and approval['author_message_sha256']
    f0=audit.load(ROOT/'registration/S1_F0.json');assert sha(ROOT/'registration/S1_F0.json')==approval['approved_F0_sha256']
    assert (ROOT/'registration/REMOTE_S1_F0_BYTES.json').read_bytes()==(ROOT/'registration/S1_F0.json').read_bytes()
    for x in f0['files']:assert sha(x['path'])==x['sha256']
    root=Path(f0['execution_root']);selection=audit.load(root/'PREOUTPUT_SELECTION.json')
    assert selection['selected_QH'] in ('QH_C','QH_D'),'no admitted candidate; do not expand'
    remote=audit.load(root/'AUTHENTICATED_SELECTION.json');assert remote['selection_sha256']==sha(root/'PREOUTPUT_SELECTION.json') and remote['authenticated_commit']==approval['selected_census_commit']
    assert (root/'REMOTE_SELECTION_BYTES.json').read_bytes()==(root/'PREOUTPUT_SELECTION.json').read_bytes()
    census=audit.load(root/'CENSUS.json');support={(r['descriptor_id'],r['layout'],r['stage_outputs']):r['full_support'] for r in census['records']}
    plan=audit.load(ROOT/'S1_PLAN.json');slots={s['id']:s for s in plan['slots'] if s['kind']!='support'}
    chosen=approval['slot_ids'];assert chosen and len(chosen)==len(set(chosen)) and all(s in slots for s in chosen)
    order=[s['id'] for s in plan['slots'] if s['id'] in chosen];assert order==chosen,'fixed planned order'
    save(root/'PANEL_CONTROLLER.lock',dict(pid=os.getpid(),approved_slots=chosen));active=None
    try:
        for ident in chosen:
            s=slots[ident];layout=selection['selected_QH'] if s['layout']=='SELECTED_QH' else s['layout']
            key=(s['descriptor'],layout,s['kind']=='numeric');d=root/'slots'/hashlib.sha256(ident.encode()).hexdigest()[:24]
            assert not d.exists(),'already started/unstarted classification exists; no retry'
            d.mkdir(parents=True)
            if not support[key]:
                save(d/'NOT_SUPPORTED.json',dict(slot=ident,layout=layout,scientific_started=False))
                if layout in ('MQ','PQ','QB') or layout==selection['selected_QH']:raise RuntimeError('required graph not supported; stop expansion')
                continue
            # Counts are reconstructed from all immutable existing receipts,
            # never reset when a new substage authorizes the next slot list.
            starts=[audit.load(p) for p in root.rglob('BEFORE_START.json')]
            assert len(starts)<1009 and sum(x.get('reserved_graphs',0) for x in starts)+s['graph_computes']<=2808
            spent=sum(audit.load(p)['seconds'] for p in root.rglob('LIFETIME.json'));assert spent<7200
            assert sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<4*1024**3
            safety.query(f0['admission_policy'],d/'HOST_ADMISSION.json')
            job=dict(s,layout=layout,approved_stage_F0=approval['approved_F0_sha256'],runtime_directory=f0['runtime_directory'])
            save(d/'ADMITTED_JOB.json',job);argv=[str(ROOT/'native/build/bin/lowering113.exe'),'--gpu-run',str(d/'ADMITTED_JOB.json'),str(d/'native')]
            save(d/'BEFORE_START.json',dict(slot=ident,epoch=time.time(),command=argv,reserved_graphs=s['graph_computes'],warmups=s['warmups'],wire_job_sha256=sha(d/'ADMITTED_JOB.json')))
            env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','CUDA_','LLAMA_ARG_'))};env['GGML_CUDA_DISABLE_GRAPHS']='1';env['PATH']=f0['runtime_directory']+os.pathsep+env.get('PATH','')
            begin=time.perf_counter();code=-1;failure=None;polls=[]
            try:
                with (d/'stdout.log').open('xb') as out,(d/'stderr.log').open('xb') as err:
                    active=subprocess.Popen(argv,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
                    save(d/'PROCESS.json',dict(pid=active.pid,epoch=time.time(),monitor='owned-PID/deadline only; no in-window GPU polling'))
                    while active.poll()is None:
                        polls.append(time.perf_counter_ns())
                        if spent+time.perf_counter()-begin>=7200 or time.perf_counter()-begin>240:raise TimeoutError('owned-stage/host time ceiling')
                        if sum(p.stat().st_size for p in d.rglob('*') if p.is_file())>32*1024**2:raise RuntimeError('fixed host raw/profile size cap')
                        time.sleep(.1)
                    code=active.wait();assert code==0,'native host failed'
                record=audit.load(d/'native/RECORD.json');assert record['pid']==active.pid and record['graph_computes']==s['graph_computes'] and record['warmups']==s['warmups']
                audit.modules(record['modules'],f0['numerical_DLLs'],f0['runtime_directory']);audit.completed_intervals(record)
                if s['kind']=='numeric':
                    meta=audit.load(Path(s['root'])/'snapshot.json');checks={}
                    for stage in ('QK','softmax','AV'):
                        data=(d/'native'/(stage+'.bin')).read_bytes();reference=audit.canonical(s['root'],meta['native_'+stage]);checks[stage]=audit.numeric(reference,data)
                        if layout=='MQ' or meta['q_occupancy']==1:assert checks[stage]['bitwise_equal'],'MQ own-path/q1 common path gate'
                        if checks[stage]['nonfinite_mismatches']:raise RuntimeError('nonfinite mismatch gate')
                        if layout in ('PQ','QB'):
                            snap=next(c for c in audit.load(ROOT/'FULL_SNAPSHOTS.json')['contexts'] if c['context']['id']==s['descriptor'])
                            old=Path('D:/hs104-authenticated-final-restore/E1/data')/f'operators/{snap["index"]:03d}/{layout}-r{s["repeat"]}'/(stage+'.bin')
                            assert old.read_bytes()==data,'inherited PQ/QB correspondence gate'
                    # q>1 finite QH/MQ differences are retained, not used to switch layouts.
                    save(d/'NUMERICAL_AUDIT.json',checks)
                save(d/'COMPLETED.json',dict(slot=ident,status='PASS',record_sha256=sha(d/'native/RECORD.json')))
            except BaseException as exc:
                failure=repr(exc)
                if active and active.poll()is None:active.kill();active.wait()
                save(d/'FAILED.json',dict(slot=ident,error=failure,started_no_retry=True));raise
            finally:
                save(d/'LIFETIME.json',dict(seconds=time.perf_counter()-begin,exit_code=code,error=failure,max_deadline_poll_gap_seconds=max((b-a for a,b in zip(polls,polls[1:])),default=0)/1e9))
                active=None
    finally:
        if active and active.poll()is None:active.kill();active.wait()
        # This lock is removed only by its live owning controller, never by a
        # recovery tool guessing that an old PID is stale.
        (root/'PANEL_CONTROLLER.lock').unlink()
if __name__=='__main__':main()
