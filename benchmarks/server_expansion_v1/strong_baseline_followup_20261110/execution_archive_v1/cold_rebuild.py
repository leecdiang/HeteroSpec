"""Bounded source-only CPU reconstruction; never executes a model or GPU job.

Review the immutable recipe first. Default is a full input/recipe preflight.
--execute compiles all numerical translation units, never imports old objects.
An ELF produced here remains unqualified until the complete GPU protocol runs.
"""
import argparse
import concurrent.futures
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import time


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()


def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def main(a):
    if a.out.exists():raise ValueError('Fresh output directory required; never overwrite or resume an uncertain build')
    if not 1<=len(a.cpus)<=2 or len(set(a.cpus))!=len(a.cpus):raise ValueError('One or two distinct authorized CPU cores required')
    os.sched_setaffinity(0,set(a.cpus));began=time.monotonic();a.out.mkdir(parents=True)
    if not 60<=a.max_seconds<=21600:raise ValueError('Finite build bound must be 60..21600 seconds')
    recipe=json.loads((a.source/'RECIPE.json').read_text())
    if recipe['numerical_inputs']!='SOURCE_ONLY_NO_OLD_OBJECT_ARCHIVE_ELF_OR_ORACLE':raise ValueError('Not a source-only recipe')
    for item in recipe['source_files']:
        p=a.source/item['path']
        if not p.is_relative_to(a.source) or p.is_symlink() or not p.is_file():raise ValueError('Invalid source path')
        if p.suffix in ('.o','.a','.so','.bin','.f32','.gguf'):raise ValueError('Prebuilt numerical input refused')
        if p.stat().st_size!=item['bytes'] or digest(p)!=item['sha256']:raise ValueError('Source bytes changed: '+item['path'])
    overrides=json.loads(a.tools.read_text()) if a.tools else {}
    replacements={'${R_SOURCE}':str(a.source/'R_source'),'${C_SOURCE}':str(a.source/'C_source'),
        '${FRONTEND}':str(a.source/'frontend'),'${R_NATIVE}':str(a.out/'R_native'),
        '${C_NATIVE}':str(a.out/'C_native'),'${MODEL_OUT}':str(a.out/'model'),'${CACHE}':str(a.out/'cache')}
    installed=[]
    for item in recipe['tools']:
        p=Path(overrides.get(item['marker'],item['recorded_path']))
        if not p.is_file() or digest(p)!=item['sha256']:raise ValueError('Exact recorded compiler/tool required: '+item['marker'])
        replacements[item['marker']]=str(p.resolve());installed.append(dict(marker=item['marker'],path=str(p),sha256=digest(p)))
    # System SDKs/libraries must be installed separately at the recorded paths.
    # Their exact hashes are checked; no implicit package upgrade/download.
    for item in recipe['external_requirements']:
        if not Path(item['path']).is_file() or digest(item['path'])!=item['sha256']:raise ValueError('Installed SDK/dependency differs: '+item['path'])
    def mapped(text):
        for old,new in replacements.items():text=text.replace(old,new)
        if '${' in text:raise ValueError('Unresolved recorded path marker')
        return text
    commands=[]
    for ordinal,item in enumerate(recipe['commands']):
        c=dict(item,ordinal=ordinal,cwd=mapped(item['cwd']))
        if 'shell'in c:c['shell']=mapped(c['shell']);argv=shlex.split(c['shell'])
        else:c['argv']=[mapped(x)for x in c['argv']];argv=c['argv']
        c['compile']='-c'in argv
        # Pre-create only output/dependency parents, not prebuilt outputs.
        c['output_dirs']=sorted({str((Path(c['cwd'])/argv[i+1]).parent)for i,x in enumerate(argv[:-1])if x in ('-o','-MF')})
        commands.append(c)
    preflight=dict(status='SOURCE_ONLY_CPU_REBUILD_PREFLIGHT_PASSED',GPU_requests=0,
        recipe_sha256=digest(a.source/'RECIPE.json'),sources=len(recipe['source_files']),
        commands=len(commands),tools=installed,external_hashes=len(recipe['external_requirements']),
        execute=a.execute,cpus=a.cpus,preflight_s=time.monotonic()-began,
        qualification='NOT_GPU_QUALIFIED; full independent R and protocol gates required on another build/device')
    write(a.out/'PREFLIGHT.json',preflight);write(a.out/'EXPANDED_COMMANDS.private.json',commands)
    if not a.execute:print(json.dumps(preflight));return
    # Never compete with the active study. A same-host reconstruction is only
    # allowed after a terminal controller/lock-close receipt, including partial.
    if not a.isolated_host:
        if not a.stage_state or not a.activity_lock:raise ValueError('Same-host execution requires terminal stage state and the shared activity lock')
        state=json.loads(a.stage_state.read_text())
        if state['status']not in ('S3_COMPLETE_REQUIRES_PUBLIC_ARCHIVE_REPLAY','S3_PARTIAL_STOPPED'):raise ValueError('Study is still active')
        if not (a.stage_state.parent/'CONTROLLER_CLOSED.private.json').is_file():raise ValueError('Controller has not closed')
    lock=None
    if a.activity_lock:
        lock=a.activity_lock.open('a+');fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
    for src,dst in [('seed/R_native','R_native'),('seed/C_native','C_native'),('seed/model','model'),('seed/cache','cache')]:
        if (a.source/src).exists():shutil.copytree(a.source/src,a.out/dst)
    for directory in ('R_native/bin','C_native','model','cache','logs'):(a.out/directory).mkdir(parents=True,exist_ok=True)
    # cmake_install.cmake files are provenance only; no install is invoked.
    for c in commands:
        Path(c['cwd']).mkdir(parents=True,exist_ok=True)
        for directory in c['output_dirs']:Path(directory).mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    def run(c):
        remaining=a.max_seconds-(time.monotonic()-began)
        if remaining<=0:raise TimeoutError('Whole CPU rebuild time budget exhausted')
        before=time.monotonic();base=a.out/'logs'/('%04d'%c['ordinal'])
        with base.with_suffix('.stdout').open('xb')as so,base.with_suffix('.stderr').open('xb')as se:
            result=subprocess.run(c.get('argv')or['/bin/bash','-e','-c',c['shell']],cwd=c['cwd'],env=env,
                stdin=subprocess.DEVNULL,stdout=so,stderr=se,timeout=min(1800,remaining))
        record=dict(ordinal=c['ordinal'],role=c['role'],exit_code=result.returncode,caller_s=time.monotonic()-before)
        write(base.with_suffix('.json'),record)
        if result.returncode:raise RuntimeError('Compile/link failed at recorded step '+str(c['ordinal']))
        return record
    records=[]
    try:
        for role in ('R','candidate-libraries','model-entry','model-counts','model-link'):
            items=[c for c in commands if c['role']==role]
            # All generated headers are frozen text inputs. Translation units
            # are independent; archive/link steps retain their original order.
            pool=concurrent.futures.ThreadPoolExecutor(max_workers=len(a.cpus))
            waiting=iter(c for c in items if c['compile']);pending=set()
            try:
                for _ in a.cpus:
                    c=next(waiting,None)
                    if c is not None:pending.add(pool.submit(run,c))
                while pending:
                    done,pending=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
                    for future in done:records.append(future.result())
                    for _ in done:
                        c=next(waiting,None)
                        if c is not None:pending.add(pool.submit(run,c))
            finally:
                for future in pending:future.cancel()
                pool.shutdown(wait=True,cancel_futures=True)
            for c in items:
                if not c['compile']:records.append(run(c))
        outputs=[a.out/'R_native/bin/transfer-worker',a.out/'model/model-worker']
        write(a.out/'COMPLETE.json',dict(status='SOURCE_ONLY_CPU_REBUILD_COMPLETE_UNQUALIFIED',GPU_requests=0,
            caller_s=time.monotonic()-began,steps=len(records),outputs=[dict(path=str(p),bytes=p.stat().st_size,sha256=digest(p))for p in outputs],
            required_next='Independent R, complete numeric/state/physical/resource qualification and prospective freezes before any timing'))
    except BaseException as error:
        write(a.out/'FAILURE.json',dict(reason=str(error),caller_s=time.monotonic()-began,no_automatic_retry=True,GPU_requests=0));raise
    finally:
        if lock:lock.close()


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('source','out'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('tools','stage-state','activity-lock'):p.add_argument('--'+name,type=Path)
    p.add_argument('--cpus',type=lambda s:[int(x)for x in s.split(',')],default=[34,35])
    p.add_argument('--execute',action='store_true');p.add_argument('--isolated-host',action='store_true')
    p.add_argument('--max-seconds',type=int,default=21600)
    args=p.parse_args();args.source=args.source.resolve();args.out=args.out.resolve();main(args)
