"""Execute a bounded synthetic CPU matrix through the unchanged worker request."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def ident(path):
    p=Path(path); data=p.read_bytes()
    return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def write(path, obj):
    if path.exists(): raise FileExistsError(path)
    path.write_text(json.dumps(obj,indent=2)+'\n')


def cases(k):
    rows=[('initial_cap',7,10,1),('short_cap',248,10,2),
          ('full_cap',257,10,k+1),('bonus_cap',7,10,k+2),
          ('multi_cap',253,10,20),('full_eog',7,126-k,32),
          ('short_eog',248,124 if k==3 else 122,32),('initial_eog',7,126,32)]
    result=[]
    for name,length,last,cap in rows:
        prompt=[8+(7*i)%80 for i in range(length)];prompt[-1]=last
        result.append({'name':name,'input':{'prompt_ids':prompt,'cap':cap}})
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--fixture',type=Path,required=True)
    p.add_argument('--lib-dir',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    a.build=a.build.resolve();a.fixture=a.fixture.resolve();a.lib_dir=a.lib_dir.resolve();a.out=a.out.resolve()
    a.out.mkdir(exist_ok=False)
    build=json.loads((a.build/'BUILD.json').read_text())
    fixture=json.loads((a.fixture/'FIXTURE.json').read_text())
    if build['status']!='BUILT_NOT_EXECUTED':raise ValueError('Build did not complete')
    for name,expected in build['outputs'].items():
        if ident(a.build/name)!={k:expected[k] for k in ['bytes','sha256']}:
            raise ValueError('Built binary identity drift: '+name)
    for model in fixture['models']:
        if ident(a.fixture/model['name'])!={k:model[k] for k in ['bytes','sha256']}:
            raise ValueError('Fixture identity drift')
    for name,expected in build['libraries_after'].items():
        if ident(a.lib_dir/name)!={k:expected[k] for k in ['bytes','sha256']}:
            raise ValueError('Library identity drift before run')
    matrix=[]
    for relation in ('same','mismatch'):
        for k in (3,7):
            target=a.fixture/'target.gguf';draft=a.fixture/('target.gguf' if relation=='same' else 'draft_mismatch.gguf')
            job={'synthetic_fixture':True,'target_model':str(target),'draft_model':str(draft),
                 'target_model_sha256':ident(target)['sha256'],'draft_model_sha256':ident(draft)['sha256'],
                 'numerical_library_sha256':[v['sha256'] for v in build['libraries_after'].values()],
                 'k':k,'inputs':cases(k),'target_output_reserve':8,'draft':True,'draft_width':4,
                 'proposal_mode':'live','threads':1}
            name=f'{relation}_k{k}';write(a.out/(name+'.JOB.json'),job)
            matrix.append({'name':name,'job':name+'.JOB.json','relation':relation,'k':k,'request_count':len(job['inputs'])})
    write(a.out/'PLAN.json',{'schema':'heterospec.cpu-integration-plan.v1','matrix':matrix,
          'model_calls_scope':'32 synthetic worker requests per arm, eager and deferred; no GPU',
          'selection':'Fixed 8 cases per relation and k before first model execution',
          'performance_claim':False,'timeout_per_process_seconds':120,
          'build_receipt':ident(a.build/'BUILD.json'),'fixture_receipt':ident(a.fixture/'FIXTURE.json'),
          'run_script':ident(Path(__file__))})
    env=os.environ.copy()
    for key in list(env):
        if key.startswith('HS_') or key.startswith('GGML_CUDA'):env.pop(key)
    env.pop('LD_PRELOAD',None);env.pop('LD_AUDIT',None)
    env['OMP_NUM_THREADS']='1';env['OPENBLAS_NUM_THREADS']='1'
    env['LD_LIBRARY_PATH']=str(a.lib_dir)
    env['GGML_BACKEND_PATH']=str(a.lib_dir)
    records=[]
    def launch(name,cmd,expected=0):
        started=time.monotonic();stdout=a.out/(name+'.stdout');stderr=a.out/(name+'.stderr')
        with stdout.open('xb') as so,stderr.open('xb') as se:
            try:
                proc=subprocess.run(cmd,env=env,stdout=so,stderr=se,timeout=120)
                code=proc.returncode; timeout=False
            except subprocess.TimeoutExpired:
                code=None;timeout=True
        record={'name':name,'argv':cmd,'returncode':code,'timed_out':timeout,
                'elapsed_seconds':time.monotonic()-started,'stdout':ident(stdout),'stderr':ident(stderr),
                'classification':'EXPECTED_EXIT' if code==expected else 'UNEXPECTED_FAILURE'}
        records.append(record);write(a.out/(name+'.RUN.json'),record)
        if code!=expected:raise RuntimeError(f'{name} returned {code}; failure retained')
    try:
        guarded=a.out/'guarded_gpu_required'
        launch('guarded_gpu_required',[str(a.build/'guarded_entry'),str(a.out/matrix[0]['job']),str(guarded)],expected=2)
        failure=json.loads((guarded/'failure.json').read_text())
        if failure.get('error')!='GPU required':raise RuntimeError('Original guarded entry failed for an unexpected reason')
        for cell in matrix:
            for mode in (0,1):
                name=cell['name']+f'_mode{mode}'
                launch(name,[str(a.build/f'cpu_request_{mode}'),str(a.out/cell['job']),str(a.out/name)])
        after={name:ident(a.lib_dir/name) for name in build['libraries_after']}
        before={name:{k:v[k] for k in ['bytes','sha256']} for name,v in build['libraries_after'].items()}
        if before!=after:raise RuntimeError('Library identity drift after execution')
        for model in fixture['models']:
            if ident(a.fixture/model['name'])!={k:model[k] for k in ['bytes','sha256']}:
                raise RuntimeError('Model identity drift after execution')
        summary={'schema':'heterospec.cpu-integration-run.v1','status':'EXECUTED_PENDING_OFFLINE_COMPARISON',
                 'records':records,'libraries_before':before,'libraries_after':after,
                 'original_entry_result':'GPU required; no production CLI model run',
                 'model_requests':64,'GPU_requests':0,'performance_claim':False}
        write(a.out/'RUN_SUMMARY.json',summary)
        print(json.dumps({'status':summary['status'],'out':str(a.out)}))
    except Exception as exc:
        write(a.out/'FAILED_RUN.json',{'error':str(exc),'records':records,'GPU_requests':0,'performance_claim':False})
        raise


if __name__=='__main__':main()
