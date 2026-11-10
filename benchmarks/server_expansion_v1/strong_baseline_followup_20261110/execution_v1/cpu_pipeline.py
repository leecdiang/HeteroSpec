"""Detached, finite S0 queue. No transition to qualify/run is implemented here."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from support import fresh,need,write,sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True);a=p.parse_args()
    here=Path(__file__).parent;work=a.work
    work.mkdir();start=time.monotonic();steps=[]
    namespace=a.root/'strong-baseline-followup-20261110'
    lock=(namespace/'cpu-build.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    activity=(namespace/'activity.lock').open('a+')
    fcntl.flock(activity,fcntl.LOCK_SH|fcntl.LOCK_NB)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='');env.pop('HS_STRONG_GPU_ADMISSION_FILE',None)
    def step(label,args):
        write(work/'STATE.json',dict(status='CPU_RUNNING',step=label,native_model_requests=0,GPU_admitted=False))
        so=work/(label+'.stdout.log');se=work/(label+'.stderr.log');t=time.monotonic()
        with so.open('xb')as out,se.open('xb')as err:
            r=subprocess.run(args,env=env,cwd=here.parent,stdout=out,stderr=err,stdin=subprocess.DEVNULL,timeout=1800)
        steps.append(dict(step=label,argv=args,returncode=r.returncode,caller_s=time.monotonic()-t,
                          stdout_sha256=sha(so),stderr_sha256=sha(se)))
        need(r.returncode==0,'CPU step failed: '+label)
    try:
        step('python-syntax',[sys.executable,'-B','-c',
             'import ast,pathlib;[(ast.parse(p.read_text(),filename=str(p)))for p in pathlib.Path('+repr(str(here.parent))+').rglob("*.py")]'])
        step('parent-guard-build',['/usr/bin/cc','-std=c11','-O2','-Wall','-Wextra','-D_GNU_SOURCE','-MD',
             '-MF',str(work/'parent-guard.d'),str(here/'parent_guard.c'),'-o',str(work/'parent-guard')])
        step('backend-build',[sys.executable,'-B',str(here/'build_backend.py'),'--root',str(a.root),'--out',str(work/'backend')])
        step('pristine-gold-build',[sys.executable,'-B',str(here/'build_gold.py'),'--root',str(a.root),'--out',str(work/'gold')])
        step('model-build',[sys.executable,'-B',str(here/'build_model.py'),'--root',str(a.root),
                            '--backend',str(work/'backend'),'--out',str(work/'model')])
        step('prospective-manifest',[sys.executable,'-B',str(here/'prepare.py'),'--root',str(a.root),'--out',str(work/'prospective')])
        step('compiled-closure',[sys.executable,'-B',str(here/'closure.py'),'--root',str(a.root),'--work',str(work),'--out',str(work/'COMPILED_CLOSURE.private.json')])
        for mode,flags in [('normal',[]),('optimized',['-O'])]:
            step('design-'+mode,[sys.executable,*flags,'-B','-m','unittest','-v','test_design_checks.py'])
            step('execution-'+mode,[sys.executable,*flags,'-B',str(here/'test_execution.py')])
        history=a.root/'q32-q4-full-20261109-01'
        state=next((history/'reference/runs/R-repeat-0/native').rglob('sequence.bin'))
        step('historical-real-reader',[sys.executable,'-B',str(here/'fixture_replay.py'),'--state',str(state),
            '--frontier',str(state.parent/'frontier.f32'),'--profile',str(history/'STATE_PROFILE.json'),
            '--out',str(work/'HISTORICAL_READER_FIXTURE.json')])
        config=dict(arm='G',n_ctx=1024,n_ubatch=32,output_reserve=32,kv='F16',flash_attention=False,
                    cuda_graphs=False,lowering='WHOLE',draft=False,residency='target_only',k=0,
                    draft_width=1,target_output_reserve=32,proposal_mode='live',threads=2)
        results=[]
        for worker in ('backend/operand-worker','model/model-worker'):
            for label,change,expected in [('G',dict(arm='G'),0),('B',dict(arm='B'),0),('C',dict(arm='C'),0),
                         ('reserve8',dict(output_reserve=8),2),('ub4',dict(n_ubatch=4),2),
                         ('graphs-on',dict(cuda_graphs=True),2),('wrong-backend',dict(arm='bad'),2)]:
                job=work/(worker.split('/')[0]+'-'+label+'.json');fresh(job,{**config,**change})
                before=time.monotonic_ns()
                r=subprocess.run([str(work/worker),'--echo',str(job)],capture_output=True,text=True,env=env,timeout=30)
                after=time.monotonic_ns()
                results.append(dict(worker=worker,case=label,expected=expected,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
                need(r.returncode==expected,'Native CPU config echo: '+worker+'/'+label)
                if expected==0 and worker.startswith('backend/'):
                    need(before<=json.loads(r.stdout)['monotonic_ns']<=after,'C++/Python POSIX monotonic clock domain')
            command=[str(work/worker),str(work/(worker.split('/')[0]+'-G.json')),str(work/'FORBIDDEN_GPU_OUTPUT')]
            if worker.startswith('backend/'):command.append('--admitted-by-host')
            r=subprocess.run(command,
                             capture_output=True,text=True,env=env,timeout=30)
            need(r.returncode==2 and 'GPU disabled'in r.stderr and not (work/'FORBIDDEN_GPU_OUTPUT').exists(),'GPU must remain disabled without reservation')
        fresh(work/'CPU_ECHO.json',dict(native_model_requests=0,records=results))
        r=subprocess.run([str(work/'parent-guard'),'--parent',str(os.getpid()),'--','/usr/bin/true'],env=env,timeout=30)
        need(r.returncode==0,'Parent guard direct execution')
        child_file=work/'PARENT_GUARD_HEARTBEAT_PID.txt'
        test_code='import os,subprocess,pathlib; p=subprocess.Popen('+repr([str(work/'parent-guard'),'--parent'])+'+[str(os.getpid()),"--","/usr/bin/sleep","30"],start_new_session=True);pathlib.Path('+repr(str(child_file))+').write_text(str(p.pid))'
        subprocess.run([sys.executable,'-B','-c',test_code],env=env,check=True,timeout=30)
        time.sleep(.3);child=Path('/proc/'+child_file.read_text().strip()+'/stat')
        need(not child.exists()or child.read_text().split()[2]=='Z','Zero-GPU child survived loss of its supervisor')
        fresh(work/'PARENT_GUARD_ZERO_GPU_PROOF.json',dict(status='PASSED',native_model_requests=0,
              orphaned_sleep_is_running=False,guard_sha256=sha(work/'parent-guard')))
        for name,job,expected in [('scalar',dict(role='pristine_scalar_gold',q=1),0),
                                 ('wide-rejected',dict(role='pristine_scalar_gold',q=4),2)]:
            path=work/('gold-echo-'+name+'.json');fresh(path,job)
            result=subprocess.run([str(work/'gold/gold-worker'),'--echo',str(path)],env=env,capture_output=True,text=True,timeout=30)
            need(result.returncode==expected,'Independent scalar gold CPU echo')
            fresh(work/('gold-echo-'+name+'-RESULT.json'),dict(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr,native_model_requests=0))
        status='CPU_IMPLEMENTATIONS_BUILT_F0_S1_NOT_ADMITTED'
    except BaseException as error:
        status='CPU_PIPELINE_FAILED'
        fresh(work/'FAILURE.json',dict(type=type(error).__name__,reason=str(error)))
        raise
    finally:
        write(work/'STATE.json',dict(status=status,steps=steps,caller_s=time.monotonic()-start,
              native_model_requests=0,GPU_admitted=False,auto_GPU_transition=False))


if __name__=='__main__':main()
