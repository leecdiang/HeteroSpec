"""Wait for the pinned acquisition receipt, then launch one bounded admission.

The source/build snapshot is frozen before waiting. A failed launch is retained
and never retried here. This entrypoint cannot launch qualification or timing.
"""
from pathlib import Path
import argparse, datetime, json, subprocess, sys, time

def main():
    p=argparse.ArgumentParser()
    for key in ('baseline','supervisor','build','work','target','draft','receipt','audit'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--source-commit',required=True)
    p.add_argument('--wait-seconds',type=int,default=14400)
    a=p.parse_args();sys.dont_write_bytecode=True
    sys.path.insert(0,str(a.supervisor.resolve()));from common import need,read,save,sha
    need(0<a.wait_seconds<=14400,'Bounded acquisition wait')
    need(not a.audit.exists() and not a.work.exists(),'Fresh audit and native epoch')
    a.audit.mkdir(parents=True)
    here=Path(__file__).resolve().parent
    source={str(x.resolve()):sha(x) for x in sorted(here.rglob('*')) if x.is_file() and x.suffix in ('.py','.cpp','.json','.hpp')}
    for path in (a.build/'BUILD.json',a.build/'DEPENDENCIES.json',a.supervisor/'admission_host.py',a.supervisor/'common.py',a.supervisor/'pins.json'):
        source[str(path.resolve())]=sha(path)
    manifest=read(here/'models.json');expected=manifest['target']
    save(a.audit/'SOURCE_FREEZE.private.json',dict(schema='server-d14.admission-freeze.v1',source_commit=a.source_commit,
        frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=source,expected_target=expected,
        old_R_freeze_sha256=sha(a.baseline/'reference-01/REFERENCE_FREEZE.json'),
        old_ledger_sha256=sha(a.baseline/'ledger.jsonl'),M1_ledger_sha256=sha(a.baseline.parent/'m1-run-01/ledger.jsonl'),
        max_model_forwards=0,only_phase='C1024_ZERO_FORWARD_ADMISSION',C4096='NOT_RUN'))
    began=time.monotonic()
    try:
        while not a.receipt.exists():
            need(time.monotonic()-began<a.wait_seconds,'Acquisition deadline reached; no GPU launch')
            time.sleep(30)
        r=read(a.receipt)
        need(r.get('verified') is True and r.get('sha256')==expected['sha256'] and r.get('bytes')==expected['bytes'],'Exact acquisition receipt')
        need(a.target.stat().st_size==expected['bytes'] and sha(a.target)==expected['sha256'],'Actual complete target before launch')
        for path,h in source.items():need(sha(path)==h,'Frozen admission source/build changed: '+path)
        save(a.audit/'LAUNCH.json',dict(source_freeze_sha256=sha(a.audit/'SOURCE_FREEZE.private.json'),
            acquisition_receipt_sha256=sha(a.receipt),target_sha256=sha(a.target),wait_and_verification_s=time.monotonic()-began,
            model_forwards_permitted=0))
        command=[sys.executable,'-B',str(here/'run_admission.py')]
        for key in ('baseline','supervisor','build','work','target','draft'):command+=['--'+key,str(getattr(a,key).resolve())]
        with (a.audit/'stdout.log').open('xb') as out,(a.audit/'stderr.log').open('xb') as err:
            result=subprocess.run(command,stdout=out,stderr=err)
        need(result.returncode==0,'Admission failed; retain epoch, no automatic retry')
        save(a.audit/'STATUS.json',dict(status='COMPLETE',admission_sha256=sha(a.work/'ADMISSION.json'),
            wait_and_admission_wall_s=time.monotonic()-began,model_forwards=0))
    except BaseException as e:
        save(a.audit/'STATUS.json',dict(status='FAILED',error=str(e),wait_and_admission_wall_s=time.monotonic()-began,
            no_automatic_retry=True))
        raise

if __name__=='__main__':main()
