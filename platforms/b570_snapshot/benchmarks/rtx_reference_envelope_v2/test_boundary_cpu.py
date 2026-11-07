import copy,json,subprocess,time
from pathlib import Path
from common import V,load,save,sha
from lifecycle import Child
from run import root,helper,env
def main():
    s=load(root()/'RUN_SPEC.json');plan=load(root()/'R1/PLAN.json');folder=root()/'R1/CPU';folder.mkdir();command=load(V/'BUILD.json')['command'];command[command.index(str(V/'native.cpp'))]=str(V/'boundary_cpu.cpp');command[-1]=str(V/'build/boundary_cpu.exe');r=subprocess.run(command,capture_output=True,timeout=600);save(folder/'BUILD.json',dict(command=command,exit=r.returncode,stderr=r.stderr.decode(errors='replace'),GPU_calls=0));assert r.returncode==0;worker=Child(helper());count=0;words=0
    for c in plan['fixtures']:
        for l in ['PQ','QB','QH_C']:
            job=dict(spec=str(root()/'RUN_SPEC.json'),context=c,layout=l);save(folder/f'job{count}.json',job);worker.run([str(V/'build/boundary_cpu.exe'),str(folder/f'job{count}.json'),str(folder/f'graph{count}.json')],folder/f'host{count}',120,env(s),s['host_RAM_bytes']);rows=load(folder/f'graph{count}.json');words+=rows['whole_Q_mask_output_words'];count+=1
    for i,layout in enumerate(['PQ','QB','QH_C']):
        c=next(c for c in plan['fixtures'] if c['q']==2);job=dict(spec=str(root()/'RUN_SPEC.json'),execution_id=s['execution_id'],context=c,layout=layout,lifecycle='persistent_inputs',capture_reference=True,stage='R1_REFERENCE',warmups=0,calls=1);save(folder/f'negative{i}.json',job)
        try:worker.run([str(V/'build/boundary.exe'),'--cpu',str(folder/f'negative{i}.json'),str(folder/f'negative{i}')],folder/f'reject{i}',120,env(s),s['host_RAM_bytes'])
        except AssertionError:pass
        else:raise AssertionError('illegal reference capture accepted')
        error=load(folder/f'negative{i}/NATIVE_ERROR.json');assert error['reason']=='capture restricted to independent serial reference';assert not any('cuda' in p.lower() or 'cublas' in p.lower() for p in error['modules'])
    save(V/'R1_CPU_TESTS.json',dict(status='PASS',actual_full_graphs=count,full_storage_words_checked=words,illegal_capture_cases_rejected=3,GPU_calls=0,CUDA_loads=0,independent_external_review=False,native_sha256=sha(V/'build/boundary.exe')));print(count,words)
if __name__=='__main__':main()
