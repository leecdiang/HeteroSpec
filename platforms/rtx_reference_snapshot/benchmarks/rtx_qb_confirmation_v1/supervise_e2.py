"""Single prospective E2 supervisor; no retry, no schedule/result adaptation."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import experiment as e

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('out','repo'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--freeze-commit',required=True)
    p.add_argument('--registration',default='benchmarks/rtx_qb_confirmation_v1/registration/E2_F0.json')
    a=p.parse_args();out=a.out.resolve();repo=a.repo.resolve()
    e.verify_freeze(out,repo,a.freeze_commit,a.registration)
    e.save(out/'SUPERVISOR_STARTED.json',dict(pid=os.getpid(),utc=e.utc(),freeze_commit=a.freeze_commit,
                                             no_scientific_retry=True))
    session=None
    try:
        for session in range(6):
            # An already launched session is never restarted, even if interrupted.
            e.require(not (out/f'SUPERVISOR_SESSION-{session}-STARTED.json').exists(),'session launch already exists')
            if session:
                eligible=e.read(out/f'SESSION-{session-1}-COMPLETE.json')['epoch']+3600
                if session==5:eligible=max(eligible,e.read(out/'SESSION-0.json')['epoch']+86400)
                while time.time()<eligible:
                    time.sleep(min(30,eligible-time.time()))
            e.save(out/f'SUPERVISOR_SESSION-{session}-STARTED.json',dict(session=session,utc=e.utc(),epoch=time.time()))
            cmd=[sys.executable,'-B',str(Path(__file__).parent/'experiment.py'),'run-session',
                 '--out',str(out),'--repo',str(repo),'--freeze-commit',a.freeze_commit,
                 '--registration',a.registration,'--session',str(session)]
            with (out/f'SESSION-{session}.stdout.log').open('xb') as stdout, (out/f'SESSION-{session}.stderr.log').open('xb') as stderr:
                child=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
                e.save(out/f'SUPERVISOR_SESSION-{session}-PROCESS.json',dict(pid=child.pid,command=cmd,utc=e.utc()))
                code=child.wait()
            e.save(out/f'SUPERVISOR_SESSION-{session}-EXIT.json',dict(returncode=code,utc=e.utc()))
            e.require(code==0,f'session {session} failed; no retry')
        result=e.analyze(out)
        e.save(out/'E2_ANALYSIS.json',result)
        e.save(out/'SUPERVISOR_COMPLETE.json',dict(utc=e.utc(),sessions=6,analysis_sha256=e.sha(out/'E2_ANALYSIS.json')))
    except BaseException as error:
        e.save(out/'SUPERVISOR_FAILED.json',dict(utc=e.utc(),session=session,error=repr(error),traceback=traceback.format_exc()))
        try:e.save(out/'E2_ANALYSIS_AT_STOP.json',e.analyze(out))
        except BaseException as analysis_error:e.save(out/'E2_ANALYSIS_FAILED.json',dict(error=repr(analysis_error),utc=e.utc()))
        raise

if __name__=='__main__':main()
