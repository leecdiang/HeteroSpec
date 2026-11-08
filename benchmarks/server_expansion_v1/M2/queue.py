"""One-shot full native gates then bounded descriptive panels; no576 path."""
from pathlib import Path
import datetime,fcntl,json,os,sys,time,traceback
import harness as h
import qualify,panel

def main():
    root=Path(sys.argv[1]).resolve();builds=root/'m2-build-01';work=root/'m2-run-03';runtime=root/'m2-runtime-03';audit=root/'m2-audit-03'
    audit.mkdir();os.sched_setaffinity(0,{34,35});os.nice(5);started=time.monotonic();phase='prepare_runtime'
    sys.path.insert(0,str(root/'m1-runtime-01'))
    from common import need,read,save,sha
    h.need,h.read,h.save,h.sha=need,read,save,sha
    def event(status,**extra):
        with(audit/'events.jsonl').open('a')as f:f.write(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),phase=phase,status=status,elapsed_s=time.monotonic()-started,**extra))+'\n')
    try:
        h.prepare_runtime(root,runtime);sys.path.remove(str(root/'m1-runtime-01'));h.load(runtime,root/'repository-01')
        pin=read(root/'m1-source-01/M/RUNTIME_PIN.json');need(pin['commit']=='592abdfe9267fd97ecbde18cd0ee9a1bfc319e20','Qualified Linux successor pin')
        for name,digest in pin['files'].items():
            path=root/'m1-runtime-01'/Path(name).name if name.startswith('benchmarks/linux_transfer_v1/')else root/'repository-01'/name
            need(sha(path)==digest,'Original supervisor/reader source differs from qualified pin: '+name)
        for name,digest in pin['predecessor_public_indices'].items():need(sha(root/'public-export-final-01'/name)==digest,'Original reference index changed')
        need(sha(root/'run-01/reference-01/REFERENCE_FREEZE.json')==pin['reference_freeze_raw_sha256'],'Independent R freeze changed')
        h.prepare_work(root,work,runtime,builds)
        snapshots=[]
        for name in ('m2-run-01','m2-run-02'):
            manifest=root/(name+'-completed-snapshot.json');need(manifest.exists(),'Hash-locked predecessor snapshot required')
            snapshots.append(dict(work=str(root/name),manifest=str(manifest),sha256=sha(manifest)))
        save(work/'PREDECESSOR_BINDING.json',dict(snapshots=snapshots,reason='Add actual256-padded KV crossing probes before timing; source02 yielded only between completed native jobs. Completed native runs reused, numerical binaries/reference unchanged'))
        s=h.Study(root,work,builds,root/'repository-01');panel.selection(s)
        save(audit/'SOURCE_BINDING.json',dict(driver_source_commit=sys.argv[2],driver_tar_sha256=sha(root/'m2-driver-source-03.tar.gz'),
            build_source_commit='61bcce0552b1a80e9345fa199238ebb7bc63e6ff',baseline_head='55f501e9a93013a4b4d82cc4967e82b8d9054a81',
            cumulative_budget=read(work/'INHERITED_ACCOUNTING.json'),main205206208='Already complete, public full-byte readback/statistics PASS; preserved unchanged',
            study='M2 actual target physical width, not weight quantization',full_confirmation576='NOT_PERMITTED'))
        phase='wait_exclusive_study_mutex';event('WAITING')
        with(root/'STUDY_SCHEDULING.lock').open('a')as lock:
            while True:
                need(panel.may_start(),'No new optional GPU work near05:00 cutoff')
                try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
                except BlockingIOError:time.sleep(5)
            phase='native_qualification';event('STARTED');t=time.monotonic();qualify.qualification(s)
            save(audit/'QUALIFICATION_COST.json',dict(wall_s=time.monotonic()-t,new_native_jobs=s.new_native_jobs,logical_execute_calls=s.counter,reused_complete_jobs=s.reuses,overlaps_native_and_verifier_clocks=True));event('BASE_GATES_PASS')
            phase='owned_tape_production_and_replay_qualification';t=time.monotonic();panel.tapes_and_gate(s)
            save(audit/'OWNED_TAPE_GATE_COST.json',dict(wall_s=time.monotonic()-t));event('ALL_NATIVE_GATES_PASS')
            phase='descriptive_panel_freeze';panel.prepare(s)
            # Keep time for all24 startup/bursts and archival; per-worker original
            #900s timeout/960s cutoff admission remains enforced independently.
            latest=datetime.datetime(2026,11,8,19,30,tzinfo=datetime.timezone.utc)
            need(datetime.datetime.now(datetime.timezone.utc)<=latest,'Past03:30 whole-panel admission; skip descriptive timing without weakening gates')
            inherited=read(work/'INHERITED_ACCOUNTING.json');reserved=[json.loads(x)for x in(work/'ledger.jsonl').read_text().splitlines()if json.loads(x)['event']=='RESERVE']
            need(inherited['requests']+sum(x['requests']for x in reserved)+144<=2048,'No budget for complete replay+live panel; no partial favorable subset')
            phase='descriptive_replay_and_live_pilot';event('STARTED',live_measurements=64,target_replay_measurements=32,confirmation576=False);t=time.monotonic();panel.run(s)
            save(audit/'DESCRIPTIVE_PANEL_COST.json',dict(wall_s=time.monotonic()-t,live_measurements=64,replay_measurements=32,primers=48,inference='DESCRIPTIVE_ONLY'))
            event('COMPLETE')
        save(audit/'STATUS.json',dict(status='COMPLETE',phase=phase,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),wall_s=time.monotonic()-started,
            native_qualification='PASS',same_owned_tape_replay_qualification='PASS',live_pilot64='COMPLETE_DESCRIPTIVE',target_replay32='COMPLETE_MECHANISM_ONLY',
            confirmation576='NOT_RUN',main_results_unchanged=True,archive='PENDING_SEPARATE_POSTPROCESS'))
    except BaseException as e:
        event('FAILED_OR_SKIPPED_RETAINED',error=str(e));save(audit/'STATUS.json',dict(status='FAILED_OR_SKIPPED_RETAINED',phase=phase,error=str(e),
            wall_s=time.monotonic()-started,all_prior_outputs_retained=True,no_automatic_native_retries=True,confirmation576='NOT_RUN'))
        traceback.print_exc();raise

if __name__=='__main__':main()
