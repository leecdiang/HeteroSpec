"""Bounded S0 CPU checkpoint only. This entry cannot launch GPU work."""
import argparse
import datetime
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time
from support import fresh, need, sha, write


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--model',type=Path,required=True)
    a=p.parse_args()
    w=a.work
    src=Path(__file__).parent
    began=time.monotonic()
    def state(status, **extra):
        write(w/'CPU_STATE.json',dict(status=status,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              native_model_requests=0,GPU_admitted=False,**extra))
    with(w/'CPU_CHECKPOINT.lock').open('a+')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        need(not(w/'CPU_CHECKPOINT_COMPLETE.json').exists(),'Do not rerun complete checkpoint')
        state('RUNNING_CPU_CHECKS',step='source_integrity')
        manifest=json.loads((src/'SOURCE_SNAPSHOT_MANIFEST.json').read_text())
        for x in manifest['files']:
            f=src.parent/x['path']
            need(f.stat().st_size==x['bytes']and sha(f)==x['sha256'],'Source snapshot mismatch')
        for f in src.glob('*.py'):
            compile(f.read_text(),str(f),'exec')
        commands=[('design-check',[sys.executable,'-B','design_checks.py','--check']),
                  ('design-tests',[sys.executable,'-B','-m','unittest','-v','test_design_checks.py']),
                  ('design-tests-optimized',[sys.executable,'-O','-B','-m','unittest','-v','test_design_checks.py']),
                  ('inventory',[sys.executable,'-B',str(src/'inventory.py'),'--model',str(a.model),
                                 '--out',str(w/'CPU_DESCRIPTOR_INVENTORY.json')])]
        outcomes=[]
        try:
            for label,argv in commands:
                if(w/'STOP_REQUESTED').exists():
                    state('STOPPED_AT_SAFE_CPU_BOUNDARY',step=label)
                    return
                need(time.monotonic()-began<300,'CPU checkpoint bound')
                state('RUNNING_CPU_CHECKS',step=label)
                start=time.monotonic()
                with(w/'logs'/(label+'.stdout.log')).open('xb')as so,(w/'logs'/(label+'.stderr.log')).open('xb')as se:
                    done=subprocess.run(argv,cwd=src.parent,stdin=subprocess.DEVNULL,
                                        stdout=so,stderr=se,timeout=min(120,300-(time.monotonic()-began)))
                outcomes.append(dict(step=label,returncode=done.returncode,wall_s=time.monotonic()-start))
                need(done.returncode==0,'CPU step failed: '+label)
            inv=json.loads((w/'CPU_DESCRIPTOR_INVENTORY.json').read_text())
            fresh(w/'CPU_CHECKPOINT_COMPLETE.json',dict(passed=True,scope='CPU_STRUCTURE_AND_METADATA_ONLY',
                  steps=outcomes,native_model_requests=0,numerical_GPU_qualification='NOT_RUN',
                  backend_build='NOT_IMPLEMENTED_NOT_RUN',
                  new_scalar_gold_lower_bound=inv['required_new_scalar_gold_lower_bound'],
                  gold_plus_S2_plus_reserve_lower_bound=inv['minimum_gold_plus_S2_plus_reserve']))
            state('CPU_CHECKPOINT_COMPLETE_S0_IMPLEMENTATION_INCOMPLETE',
                  stop_reason='Backend patch/build, native integration, complete manifests and budget approval remain missing',
                  next_phase='S1_NOT_ADMITTED',automatic_GPU_transition=False)
        except Exception as e:
            state('FAILED_CPU_ONLY',error=str(e),steps=outcomes,automatic_retry=False)
            raise


if __name__=='__main__':
    main()
