"""Wait exact assets, check tokenizer, then one independent Llama R/qualification.

Formal performance is not launched by this preparation coordinator. GPU phases
share a scheduling lock with D14; the native per-UUID process checks stay active.
"""
from pathlib import Path
import argparse, datetime, fcntl, json, subprocess, sys, time

def main():
    p=argparse.ArgumentParser()
    for key in ('baseline','runtime','builds','vocabulary-build','models','licenses','rule-freeze','admission-audit','work','assets','audit','repo'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--source-commit',required=True);a=p.parse_args();sys.dont_write_bytecode=True
    sys.path.insert(0,str(a.runtime.resolve()));from common import need,read,save,sha
    need(not a.audit.exists() and not a.work.exists() and not a.assets.exists(),'Fresh Llama preparation epoch');a.audit.mkdir(parents=True)
    here=Path(__file__).resolve().parent;frozen={str(x.resolve()):sha(x) for x in here.rglob('*') if x.is_file() and x.suffix in ('.py','.cpp','.hpp','.json')}
    save(a.audit/'SOURCE_FREEZE.private.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_commit=a.source_commit,files=frozen,
        rule_freeze_sha256=sha(a.rule_freeze/'FREEZE.json'),build_complete_sha256=sha(a.builds/'BUILD_COMPLETE.json'),
        vocabulary_build_sha256=sha(a.vocabulary_build/'BUILD.json'),candidate_Llama_forwards_seen=0,formal_performance='NOT_RUN',M2='NOT_RUN'))
    started=time.monotonic();phase='WAIT_EXACT_FULL_FILES'
    def execute(name,command):
        nonlocal phase;phase=name
        for path,h in frozen.items():need(sha(path)==h,'Frozen Llama source changed: '+path)
        save(a.audit/(name+'-START.json'),dict(phase=name,elapsed_s=time.monotonic()-started))
        with (a.audit/(name+'.stdout.log')).open('xb') as out,(a.audit/(name+'.stderr.log')).open('xb') as err:
            result=subprocess.run(command,stdout=out,stderr=err)
        need(result.returncode==0,'Retained failed phase: '+name+'; no automatic replay')
        save(a.audit/(name+'-COMPLETE.json'),dict(phase=name,elapsed_s=time.monotonic()-started))
    try:
        while not all((a.models/(r+'-VERIFIED.json')).exists() for r in ('target','draft')):
            need(time.monotonic()-started<12*3600,'Bounded exact-file wait expired; no model forward');time.sleep(30)
        execute('assets',[sys.executable,'-B',str(here/'check_assets.py'),'--runtime',str(a.runtime),'--build',str(a.vocabulary_build),
            '--models',str(a.models),'--out',str(a.assets),'--licenses',str(a.licenses)])
        phase='WAIT_D14_ADMISSION_AND_SERIAL_GPU_SLOT'
        while not (a.admission_audit/'STATUS.json').exists():
            need(time.monotonic()-started<12*3600,'Bounded GPU admission wait');time.sleep(30)
        need(read(a.admission_audit/'STATUS.json')['status']=='COMPLETE','D14 admission requires inspection before sharing the approved device')
        schedule=(a.baseline.parent/'STUDY_SCHEDULING.lock').open('a');fcntl.flock(schedule,fcntl.LOCK_EX)
        spec=read(here/'models.json');args=[]
        paths=dict(work=a.work,baseline=a.baseline,runtime=a.runtime,builds=a.builds,repo=a.repo,assets=a.assets,
            target=a.models/spec['target']['filename'],draft=a.models/spec['draft']['filename'])
        for key,value in paths.items():args+=['--'+key,str(value)]
        args+=['--rule-freeze',str(a.rule_freeze)]
        for name in ('prepare','reference','qualify','negatives'):execute(name,[sys.executable,'-B',str(here/'integrate.py'),name,*args])
        save(a.audit/'STATUS.json',dict(status='QUALIFIED_FORMAL_NOT_RUN',last_phase=phase,wall_s=time.monotonic()-started,
            qualification_sha256=sha(a.work/'qualification-01/NATIVE_CHECKS_COMPLETE.json'),formal_performance='NOT_RUN',M2='NOT_RUN'))
    except BaseException as e:
        save(a.audit/'STATUS.json',dict(status='FAILED_RETAINED',last_phase=phase,error=str(e),wall_s=time.monotonic()-started,
            no_automatic_retry=True,formal_performance='NOT_RUN'));raise

if __name__=='__main__':main()
