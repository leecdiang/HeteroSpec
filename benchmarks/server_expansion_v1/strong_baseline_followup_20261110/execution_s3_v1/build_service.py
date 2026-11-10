"""Compile a new shared G/B/C frontend with a reset-inclusive native endpoint.

Already-qualified numerical archives and pristine R remain byte-identical.
This build is CPU-only; changed frontend requires fresh finite qualification.
"""
import argparse
import difflib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import time


def need(x,message):
    if not x:raise ValueError(message)


def read(p):return json.loads(Path(p).read_text())
def sha(p):
    import hashlib
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
    return h.hexdigest()


def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x')as f:json.dump(x,f,indent=2);f.write('\n')


def once(text,old,new):
    need(text.count(old)==1,'Pinned unique source anchor: '+old[:100]);return text.replace(old,new,1)


def patch_worker(old):
    new=once(old,'static double since(Clock::time_point t)',
        'static int64_t sb3_ns(){timespec t{};need(::clock_gettime(CLOCK_MONOTONIC,&t)==0,"S3 monotonic clock");return int64_t(t.tv_sec)*1000000000LL+t.tv_nsec;}\nstatic double since(Clock::time_point t)')
    new=once(new,'Pair fresh;Context*target=nullptr,*draft=nullptr;',
        'Pair fresh;Context*target=nullptr,*draft=nullptr;int64_t sb3_start=0,sb3_reset_end=0;int sb3_empty_min=0,sb3_empty_max=0;')
    new=once(new,'target->reset(capture,dir/"target");',
        'sb3_start=sb3_ns();target->reset(capture,dir/"target");'
        'sb3_empty_min=llama_memory_seq_pos_min(llama_get_memory(target->c),0);'
        'sb3_empty_max=llama_memory_seq_pos_max(llama_get_memory(target->c),0);'
        'need(sb3_empty_min<0&&sb3_empty_max<0,"S3 empty active state after complete reset");sb3_reset_end=sb3_ns();')
    new=once(new,'llama_synchronize(target->c);if(draft)llama_synchronize(draft->c);\n    r["ids"]',
        'llama_synchronize(target->c);if(draft)llama_synchronize(draft->c);\n'
        '    const int64_t sb3_end=sb3_ns();need(life=="resident"&&sb3_start>0&&!draft,"S3 resident target-only endpoint");'
        'r["S3_service"]={{"clock","CLOCK_MONOTONIC"},{"unit","s"},{"start_ns",sb3_start},'
        '{"reset_end_ns",sb3_reset_end},{"fence_ns",sb3_end},{"owned_ready_ns",sb3_end},{"end_ns",sb3_end},'
        '{"elapsed_s",double(sb3_end-sb3_start)*1e-9},{"reset_s",double(sb3_reset_end-sb3_start)*1e-9},'
        '{"empty_after_reset_min",sb3_empty_min},{"empty_after_reset_max",sb3_empty_max},'
        '{"initial_reset_included",true},{"all_required_outputs_owned",true},'
        '{"post_service_receipt_state_export_serialization_excluded",true},{"stop_separate_s",nullptr}};\n'
        '    r["ids"]')
    return new


def main(previous_configuration,out):
    need(not out.exists(),'Fresh shared frontend build');out.mkdir(parents=True);began=time.monotonic()
    c=read(previous_configuration);original=Path(c['executables']['model']['path']).parent
    need(sha(c['executables']['model']['path'])==c['executables']['model']['sha256'],'Original model binary changed')
    closure=read(c['compiled_closure']);need(sha(c['compiled_closure'])==c['compiled_closure_sha256'],'Prior compiled closure changed')
    for p,h in closure['files'].items():need(sha(p)==h,'Inherited dependency changed: '+p)
    front=out/'frontend';shutil.copytree(original/'frontend',front)
    worker=front/'worker.cpp';old=worker.read_text();new=patch_worker(old);worker.write_text(new)
    (out/'worker.cpp.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='qualified-S1/worker.cpp',tofile='S3/worker.cpp')))
    entry=front/'model_entry.cpp';old_entry=entry.read_text()
    new_entry=once(old_entry,'(grant.at("phase")=="S1"||grant.at("phase")=="S3")',
        '(grant.at("phase")=="S3_QUAL"||grant.at("phase")=="S3")')
    new_entry=once(new_entry,'if(grant.at("phase")=="S3")need(',
        'need(grant.at("complete_F2_readback")==true&&grant.at("prior_S1_qualified")==true,"S3 source/input qualification admission");\n        if(grant.at("phase")=="S3")need(')
    entry.write_text(new_entry)
    (out/'model_entry.cpp.diff').write_text(''.join(difflib.unified_diff(old_entry.splitlines(True),new_entry.splitlines(True))))
    steps=[]
    def command(label,argv,cwd):
        t=time.monotonic();save(out/(label+'.command.json'),dict(argv=argv,cwd=str(cwd)))
        with (out/(label+'.stdout.log')).open('xb')as so,(out/(label+'.stderr.log')).open('xb')as se:
            result=subprocess.run(argv,cwd=cwd,stdout=so,stderr=se,timeout=1800)
        steps.append(dict(label=label,returncode=result.returncode,caller_s=time.monotonic()-t))
        need(result.returncode==0,'CPU frontend command failed: '+label)
    try:
        args=read(original/'compile-model-entry/command.json')['argv']
        args=[a.replace(str(original/'frontend'),str(front)).replace(str(original/'model-entry.o'),str(out/'model-entry.o')).replace(str(original/'model-entry.d'),str(out/'model-entry.d'))for a in args]
        command('compile-model-entry',args,Path(read(original/'compile-model-entry/command.json')['cwd']))
        args=read(original/'link-model-worker/command.json')['argv'];newargs=[]
        for a in args:
            if a==str(original/'model-entry.o'):a=str(out/'model-entry.o')
            elif a==str(original/'model-worker'):a=str(out/'model-worker')
            elif a.startswith('-Wl,-Map='):a='-Wl,-Map='+str(out/'model-worker.map')
            newargs.append(a)
        command('link-model-worker',newargs,Path(read(original/'link-model-worker/command.json')['cwd']))
        files=dict(closure['files']);body=(out/'model-entry.d').read_text().replace('\\\n',' ').partition(':')[2]
        for p in shlex.split(body):
            need(Path(p).is_absolute()and Path(p).is_file(),'Absolute compiled dependency');files[p]=sha(p)
        files[str(out/'model-worker')]=sha(out/'model-worker')
        identity=[]
        for p in (original/'libllama.a',original.parent/'backend/libggml-cuda.a',original/'work-counts.o'):
            need(p.is_file(),'Unchanged linked numerical object');identity.append(dict(path=str(p),sha256=sha(p)))
        save(out/'COMPILED_CLOSURE.private.json',dict(closure,files=files,
             scope='Original numerical archives and all transitive bytes plus new shared reset-clock frontend',
             predecessor_closure_sha256=sha(c['compiled_closure'])))
        save(out/'BUILD.json',dict(status='CPU_BUILT_NOT_GPU_QUALIFIED',executable=str(out/'model-worker'),
             executable_sha256=sha(out/'model-worker'),unchanged_numerical_objects=identity,
             pristine_R_changed=False,original_service_seconds_field_unchanged=True,
             new_primary_endpoint='S3_service: immediately before Context::reset through final synchronize, before receipt/state export/serialization',
             source_hashes={str(p.relative_to(front)):sha(p)for p in front.rglob('*')if p.is_file()},
             steps=steps,caller_s=time.monotonic()-began,GPU_requests=0))
    except BaseException as error:
        save(out/'BUILD_FAILURE.json',dict(reason=str(error),steps=steps,caller_s=time.monotonic()-began,GPU_requests=0));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--previous-configuration',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();main(a.previous_configuration,a.out)
