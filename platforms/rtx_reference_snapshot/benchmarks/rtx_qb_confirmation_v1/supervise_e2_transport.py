"""Prospective recovery of untouched E2 sessions after pre-start transport EOF.

No frozen scientific driver, slot, model, task, budget or estimator is changed.
Only gh transport errors before any session-native load may be retried.
"""
import argparse
import contextlib
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import experiment as e

BASE_FREEZE_COMMIT='49b992b2ed1cabd05fad6e234cad2d3418c2b65a'
BASE_REGISTRATION='benchmarks/rtx_qb_confirmation_v1/registration/E2_F0.json'
REGISTRATION='benchmarks/rtx_qb_confirmation_v1/registration/E2_TRANSPORT_F0.json'

def untouched(out, session):
    if (out/f'SESSION-{session}.json').exists():return False
    if (out/'EXECUTION.lock').exists():return False
    return not any(f's{session}/' in e.read(p)['slot'] for p in (out/'ledger').glob('*.json'))

def is_transport(error):
    return isinstance(error,subprocess.CalledProcessError) and isinstance(error.cmd,list) and error.cmd[:2]==['gh','api']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--recovery',type=Path,required=True);p.add_argument('--amendment-commit',required=True)
    a=p.parse_args();out=a.out.resolve();repo=a.repo.resolve();recovery=a.recovery.resolve()
    e.require(untouched(out,4) and untouched(out,5),'only untouched sessions may be recovered')
    e.require(all((out/f'SESSION-{s}-COMPLETE.json').exists() for s in range(4)),'earlier sessions incomplete')
    e.save(recovery/'CONTROLLER_STARTED.json',dict(pid=os.getpid(),utc=e.utc(),amendment_commit=a.amendment_commit))
    try:
        local=(recovery/'F0.json').read_bytes()
        committed=subprocess.check_output(['git','show',f'{a.amendment_commit}:{REGISTRATION}'],cwd=repo)
        e.require(local==committed,'supplement differs from commit')
        for attempt in range(3):
            try:
                remote=subprocess.check_output(['gh','api',f'repos/leecdiang/HeteroSpec/contents/{REGISTRATION}?ref={a.amendment_commit}',
                                                '-H','Accept: application/vnd.github.raw+json'],cwd=repo)
                e.require(remote==local,'authenticated supplement bytes differ')
                break
            except subprocess.CalledProcessError as error:
                e.save(recovery/f'AMENDMENT_TRANSPORT-{attempt}.json',dict(utc=e.utc(),error=repr(error)))
                if attempt==2:raise
                time.sleep(10)
        frozen=e.read(recovery/'F0.json')
        for item in frozen['files']:
            path=Path(item['path'])
            e.require(path.stat().st_size==item['bytes'] and e.sha(path)==item['sha256'],'supplement file differs: '+str(path))
        e.require(e.sha(out/'FREEZE.json')==frozen['base_freeze_sha256'],'base scientific freeze changed')
        e.save(recovery/'AUTHENTICATED_READBACK.json',dict(status='PASS',utc=e.utc(),amendment_commit=a.amendment_commit,
                                                        supplement_sha256=e.sha(recovery/'F0.json'),new_native_requests_started=0))
        for session in (4,5):
            e.require(untouched(out,session),'session already has a scientific start')
            eligible=e.read(out/f'SESSION-{session-1}-COMPLETE.json')['epoch']+3600
            if session==5:eligible=max(eligible,e.read(out/'SESSION-0.json')['epoch']+86400)
            while time.time()<eligible:time.sleep(min(30,eligible-time.time()))
            for attempt in range(3):
                e.require(untouched(out,session),'no scientific retry allowed')
                d=recovery/f'session-{session}-transport-attempt-{attempt}';d.mkdir(exist_ok=False)
                e.save(d/'ATTEMPT_STARTED.json',dict(session=session,utc=e.utc(),pid=os.getpid(),
                                                   scientific_session_untouched=True,base_freeze_commit=BASE_FREEZE_COMMIT))
                try:
                    with (d/'stdout.log').open('x',encoding='utf-8') as stdout, (d/'stderr.log').open('x',encoding='utf-8') as stderr:
                        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
                            e.run_session(out,repo,BASE_FREEZE_COMMIT,BASE_REGISTRATION,session)
                    e.save(d/'COMPLETED.json',dict(session=session,utc=e.utc()))
                    break
                except BaseException as error:
                    safe=is_transport(error) and untouched(out,session)
                    e.save(d/'FAILED.json',dict(utc=e.utc(),error=repr(error),traceback=traceback.format_exc(),
                                               scientific_session_untouched=untouched(out,session),
                                               network_transport_recovery_admissible=safe))
                    if not safe or attempt==2:raise
                    time.sleep(10)
        result=e.analyze(out)
        e.save(out/'E2_ANALYSIS.json',result)
        e.save(out/'SUPERVISOR_COMPLETE.json',dict(utc=e.utc(),sessions=6,analysis_sha256=e.sha(out/'E2_ANALYSIS.json'),
                                                  original_controller_failure_retained=True,amendment_commit=a.amendment_commit))
        e.save(recovery/'CONTROLLER_COMPLETE.json',dict(utc=e.utc()))
    except BaseException as error:
        e.save(recovery/'CONTROLLER_FAILED.json',dict(utc=e.utc(),error=repr(error),traceback=traceback.format_exc()))
        raise

if __name__=='__main__':main()
