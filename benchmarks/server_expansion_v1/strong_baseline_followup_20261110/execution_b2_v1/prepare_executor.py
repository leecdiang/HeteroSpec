"""CPU-only scheduler/guard construction, unchanged native B2 ELF and timers."""
import argparse
import difflib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from execute import need,read,save,sha,utc


def prepare(root,work,main_configuration,original_guard):
    began=time.monotonic();c=read(main_configuration)
    need(read(work/'CPU_REUSE_COMPLETE.json')['original_32_cells_recomputed'] is True,'Numerical raw reuse checks first')
    need(not(work/'ledger.jsonl').exists(),'No B2 native progress may precede this freeze')
    runtime=work/'runtime-exec-01';need(not runtime.exists(),'Fresh scheduler epoch; never overwrite old host code')
    shutil.copytree(work/'runtime',runtime,ignore=shutil.ignore_patterns('__pycache__'))
    path=runtime/'host.py';before=path.read_text()
    anchor="p=subprocess.Popen([str(exe),str(Path(job_path).resolve()),str(out/'native')],"
    need(before.count(anchor)==1,'Exact original native launch boundary')
    after=before.replace(anchor,
        "guard=Path(config['native_parent_guard']);need(sha(guard)==config['native_parent_guard_sha256'],'Supervisor-loss guard changed')\n"
        "                p=subprocess.Popen([str(guard),'--parent',str(os.getpid()),'--',str(exe),str(Path(job_path).resolve()),str(out/'native')],",1)
    anchor="                def drain():"
    need(after.count(anchor)==1,'Exact native start record boundary')
    after=after.replace(anchor,
        "                save(out/'NATIVE_LAUNCH.private.json',dict(pid=p.pid,start_ticks=Path('/proc/'+str(p.pid)+'/stat').read_text().split()[21],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),utc_epoch=time.time()))\n"+anchor,1)
    compile(after,str(path),'exec');path.write_text(after)
    save(work/'NATIVE_GUARD_ADAPTER_DIFF.json',dict(native_ELF_changed=False,
         diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='prepared-host',tofile='executed-host'))))
    guard_path=work/'resource_guard.py'
    need(sha(original_guard)=='866c9a0f849809e6d60d34765f9a92c31b60c3057c8182c12be057ec701d62d5',
         'Original guard source identity')
    before=original_guard.read_text();after=before
    for old,new in [('def processes():','def processes(work):'),
                    ("own=b'pr210-b2-20261109-01' in args","own=str(work).encode() in args"),
                    ('rows,ticks=processes();','rows,ticks=processes(w);'),
                    ("w/'config.private.json'","w/'CURRENT_ALLOCATION_V2.private.json'")]:
        need(after.count(old)==1,'Exact resource guard adapter anchor');after=after.replace(old,new,1)
    compile(after,str(guard_path),'exec');guard_path.write_text(after)
    save(work/'RESOURCE_GUARD_ADAPTER_DIFF.json',dict(signals_foreign_processes=False,
         diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='old-guard',tofile='new-guard'))))
    allocation=read(work/'CURRENT_ALLOCATION.private.json')
    need(allocation['gpu_uuid']==c['gpu_uuid'],'Current single-card allocation binding')
    allocation.update(native_parent_guard=c['executables']['guard']['path'],
                      native_parent_guard_sha256=c['executables']['guard']['sha256'])
    save(work/'CURRENT_ALLOCATION_V2.private.json',allocation)
    inventory=read(root/'run-01/inventory.json')
    old_driver=inventory['tools']['nvidia-smi']['version']
    current=subprocess.run(['nvidia-smi','--version'],capture_output=True,text=True,check=True,timeout=20)
    need(old_driver['ok'] is True and current.stdout.strip()==old_driver['stdout'],'Driver/NVML contract changed; new numerical admission required')
    import os
    need(inventory['platform']==os.uname().sysname+' '+os.uname().release,'Kernel platform changed')
    plan=read(work/'PLAN.json');hardware=[]
    actual=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,name,compute_cap,memory.total',
                                   '--format=csv,noheader,nounits'],text=True,timeout=20)
    selected=[line.split(',')for line in actual.splitlines()if line.split(',')[1].strip()==c['gpu_uuid']]
    need(len(selected)==1 and int(selected[0][0])!=0,'Protected/unallocated device')
    now=[x.strip()for x in selected[0]]
    for core in ('loop4','packed'):
        launch=read(root/f'pr210-stage-b-20261109-05/runs/qualification-{core}-0/launch.json')
        previous=launch['initial']['gpu']
        need([previous[k]for k in ('index','uuid','name','compute_cap','memory.total')]==now,
             'B2 original numerical qualification hardware differs')
        hardware.append(dict(core=core,old_launch_sha256=sha(root/f'pr210-stage-b-20261109-05/runs/qualification-{core}-0/launch.json'),
                             exact_selected_GPU_fields_match=True))
    save(work/'HARDWARE_DRIVER_BINDING.private.json',dict(passed=True,hardware=hardware,
         original_inventory_sha256=sha(root/'run-01/inventory.json'),current_driver_stdout=current.stdout.strip(),
         allocated_uuid=c['gpu_uuid'],kernel=inventory['platform'],old_modules_and_all_compiled_dependencies='Rehashed during CPU reuse; checked again before every actual worker',utc=utc()))
    for path in runtime.glob('*.py'):
        compile(path.read_text(),str(path),'exec')
    # All fixed jobs must preserve both warm and measured factorial histories.
    cells=[('loop4',248),('loop4',252),('packed',248),('packed',252)]
    orders=[[0,1,3,2],[1,2,0,3],[2,3,1,0],[3,0,2,1]]
    for ordinal,worker in enumerate(plan['workers']):
        round_=ordinal//4;position=ordinal%4
        need((worker['core'],worker['boundary'])==cells[orders[round_][position]],'Fixed cell Williams order')
        job=read(work/worker['job']);need(sha(work/worker['job'])==worker['job_sha256'],'Fixed job identity')
        warm=['q4pair','q8','q8','q4pair']if round_%2==0 else['q8','q4pair','q4pair','q8']
        measured=['q4pair','q8','q8','q4pair']if round_<2 else['q8','q4pair','q4pair','q8']
        need([x['execution']for x in job['diagnostics']]==warm+measured,'Matched complete warm/measurement history')
        need(all(x['ids']==job['diagnostics'][0]['ids']and x['state_sha256']==job['diagnostics'][0]['state_sha256']
                 and x['frontier_sha256']==job['diagnostics'][0]['frontier_sha256']for x in job['diagnostics']),
             'Same eight tokens and complete initial state')
    save(work/'EXECUTOR_CPU_CHECKED.json',dict(status='CPU_PREPARED_NOT_PUBLIC_NOT_GPU_ADMITTED',
         utc=utc(),caller_s=time.monotonic()-began,native_requests=0,native_ELF_or_clock_boundary_changes=False,
         runtime=str(runtime),resource_guard=str(guard_path),parent_guard=c['executables']['guard'],
         all_16_jobs_128_operations_checked=True,driver_hardware_binding='PASSED',
         remaining=['Main32B complete public byte/statistical delivery', 'Complete B2 source/jobs/reuse/budget/window freeze',
                    'Full anonymous byte readback and bounded detached execution admission']))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('root','work','main-configuration','original-guard'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();prepare(a.root,a.work,a.main_configuration,a.original_guard)
