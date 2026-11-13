"""One sequential D14 lane, bounded by admission, source, R and native gates."""
from pathlib import Path
import argparse, datetime, fcntl, json, subprocess, sys, time

def main():
    p=argparse.ArgumentParser()
    for key in ('baseline','runtime','builds','repo','admission','admission-audit','target','draft','work','audit','predecessor-runtime'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--source-commit',required=True);p.add_argument('--stop-before-panel',action='store_true');a=p.parse_args();sys.dont_write_bytecode=True
    sys.path.insert(0,str(a.runtime.resolve()));from common import need,read,save,sha
    need(not a.audit.exists() and not a.work.exists(),'Fresh sequential study epoch');a.audit.mkdir(parents=True)
    here=Path(__file__).resolve().parent
    frozen={str(x.resolve()):sha(x) for x in here.rglob('*') if x.is_file() and x.suffix in ('.py','.cpp','.hpp','.json')}
    pin=read(here/'PREDECESSOR_PIN.json')
    for name,h in pin['files'].items():
        path=a.predecessor_runtime/Path(name).name if name.startswith('benchmarks/linux_transfer_v1/') else a.repo/name
        need(sha(path)==h,'Qualified predecessor source changed: '+name)
    save(a.audit/'SOURCE_FREEZE.private.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_commit=a.source_commit,
        files=frozen,qualified_linux_successor=pin['commit'],build_complete_sha256=sha(a.builds/'BUILD_COMPLETE.json'),
        old_ledger_sha256=sha(a.baseline/'ledger.jsonl'),M1_ledger_sha256=sha(a.baseline.parent/'m1-run-01/ledger.jsonl'),
        C4096='NOT_RUN',M2='NOT_RUN',automatic_native_or_formal_retries=False))
    start=time.monotonic();phase='WAIT_ZERO_FORWARD_ADMISSION'
    try:
        while not (a.admission/'ADMISSION.json').exists():
            status=a.admission_audit/'STATUS.json'
            if status.exists():need(read(status)['status']!='FAILED','Admission failed; no inference launched')
            need(time.monotonic()-start<10800,'Bounded admission wait expired; no inference launched');time.sleep(30)
        need(read(a.admission/'ADMISSION.json')['status']=='ZERO_FORWARD_C1024_ADMISSION_PASS','Actual admission gate')
        schedule=(a.baseline.parent/'STUDY_SCHEDULING.lock').open('a')
        fcntl.flock(schedule,fcntl.LOCK_EX)
        args=[]
        for key in ('work','baseline','runtime','builds','repo','admission','target','draft'):args+=['--'+key,str(getattr(a,key).resolve())]
        phases=('prepare','reference','qualify','negatives')+(() if a.stop_before_panel else ('panel',))
        for phase in phases:
            for path,h in frozen.items():need(sha(path)==h,'Frozen study source changed: '+path)
            save(a.audit/(phase+'-START.json'),dict(phase=phase,elapsed_s=time.monotonic()-start,source_commit=a.source_commit))
            if phase=='panel':
                command=[sys.executable,'-B',str(here/'run_panel.py')]
                for key in ('work','baseline','runtime','builds','repo'):command+=['--'+key,str(getattr(a,key).resolve())]
                command+=['--source-commit',a.source_commit]
            else:command=[sys.executable,'-B',str(here/'integrate.py'),phase,*args]
            with (a.audit/(phase+'.stdout.log')).open('xb') as out,(a.audit/(phase+'.stderr.log')).open('xb') as err:
                result=subprocess.run(command,stdout=out,stderr=err)
            need(result.returncode==0,'Retained failed phase: '+phase+'; no automatic replay')
            save(a.audit/(phase+'-COMPLETE.json'),dict(phase=phase,elapsed_s=time.monotonic()-start))
        save(a.audit/'STATUS.json',dict(status='QUALIFIED_FORMAL_NOT_RUN' if a.stop_before_panel else 'COMPLETE',last_phase=phase,wall_s=time.monotonic()-start,
            results_sha256=None if a.stop_before_panel else sha(a.work/'panel-01/RESULTS.json'),C4096='NOT_RUN',M2='NOT_RUN'))
    except BaseException as e:
        save(a.audit/'STATUS.json',dict(status='FAILED_RETAINED',last_phase=phase,error=str(e),wall_s=time.monotonic()-start,no_automatic_retry=True));raise

if __name__=='__main__':main()
