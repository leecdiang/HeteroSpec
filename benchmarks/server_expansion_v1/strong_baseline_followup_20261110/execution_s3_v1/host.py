"""S3-only epoch of the original bounded host. Same GPU and global journal."""
from contextlib import ExitStack
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
from ledger import Ledger
from support import fresh,need,read,sha,write
from public_text import transform


def utc():return dt.datetime.now(dt.timezone.utc).isoformat()


def epoch(value):
    stamp=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    need(stamp.tzinfo is not None,'Explicit UTC offset required')
    return stamp.timestamp()


def relevant_environment():
    return {key:value for key,value in os.environ.items()if key.startswith(('CUDA_','GGML_','LD_','NVIDIA_','OMP_','OPENBLAS_'))}


def resource(config,own_pid=None):
    """Read-only NVML/OS inventory; never initializes a CUDA context."""
    uuid=config['gpu_uuid']
    fields='uuid,memory.total,memory.used,utilization.gpu,temperature.gpu,clocks.sm,power.draw'
    p=subprocess.run(['nvidia-smi','--query-gpu='+fields,'--format=csv,noheader,nounits'],
                     capture_output=True,text=True,timeout=20,check=True)
    lines=[line.split(',')for line in p.stdout.splitlines()]
    selected=[row for row in lines if row[0].strip()==uuid];need(len(selected)==1,'Allocated physical GPU missing')
    g=[x.strip()for x in selected[0]];total,used=int(g[1])*1024**2,int(g[2])*1024**2
    need(total-used>=config['gpu_reserve_bytes'],'GPU safety reserve exhausted')
    if own_pid is None:need(used<=config.get('max_idle_gpu_memory_bytes',128*1024**2),'Assigned GPU has pre-existing resident storage/service')
    p=subprocess.run(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],
                     capture_output=True,text=True,timeout=20,check=True)
    users=[]
    for line in p.stdout.splitlines():
        pieces=[x.strip()for x in line.split(',')]
        if len(pieces)==2 and pieces[0]==uuid:users.append(int(pieces[1]))
    need(not(set(users)-({own_pid}if own_pid else set())),'Allocated GPU has another process; stop own work only')
    memory={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()if ':'in line and line.split()[1].isdigit()}
    need(memory['MemAvailable']>=config['ram_reserve_bytes'],'RAM reserve exhausted')
    free=shutil.disk_usage(config['output_root']).free
    need(free>=config['disk_required_free_bytes'],'Disk raw/archive/safety reserve exhausted')
    load_fraction=os.getloadavg()[0]/max(1,os.cpu_count()or 1)
    need(load_fraction<=config.get('max_host_load_fraction',.8),'Host load can interfere; stop own work at safe checkpoint')
    other_busy=sum(row[0].strip()!=uuid and row[3].strip().isdigit()and int(row[3])>0 for row in lines)
    return dict(utc=utc(),monotonic_ns=time.monotonic_ns(),selected_gpu=g,selected_processes=users,
                mem_available_bytes=memory['MemAvailable'],disk_free_bytes=free,host_load_fraction=load_fraction,
                other_GPU_busy_count=other_busy,other_GPU_activity_alone_is_not_a_stop=True)


def verify_files(entries):
    for path,digest in entries.items():need(sha(path)==digest,'Frozen file bytes changed: '+path)


def verify_public_readback(proof):
    need(proof['status']=='COMPLETE_FILE_BYTES_MATCHED' and len(proof['commit'])==40 and proof['files'],
         'Missing complete immutable public readback')
    seen=set()
    for entry in proof['files']:
        need(entry['public_path']not in seen,'Duplicate public readback file');seen.add(entry['public_path'])
        need(entry['url'].startswith('https://raw.githubusercontent.com/leecdiang/HeteroSpec/'+proof['commit']+'/'),
             'Public readback URL/commit binding')
        need(sha(entry['source_file'])==entry['sha256']==sha(entry['downloaded_file']) and
             Path(entry['source_file']).stat().st_size==entry['bytes']==Path(entry['downloaded_file']).stat().st_size,
             'Public readback payload changed/truncated')


class Host:
    def __init__(self,configuration):
        self.config=read(configuration);self.stack=ExitStack();self.c=self.config
        self.root=Path(self.c['output_root']);self.root.mkdir(parents=True,exist_ok=True)
        self.manifest=read(self.c['manifest']);need(sha(self.c['manifest'])==self.c['manifest_sha256'],'Manifest binding')
        need(self.c['schema']=='hs.strong.S3-host-admission.v1','Host admission schema')
        need(self.c['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'Host rebooted: audit before any new worker')
        need(relevant_environment()==self.c['parent_environment'],'Execution environment changed since admission')
        inherited=os.environ.get('CUDA_VISIBLE_DEVICES')
        if inherited:
            allowed={x.strip()for x in inherited.split(',')}
            need(self.c['gpu_uuid']in allowed or str(self.c['gpu_index'])in allowed,'Assigned GPU outside inherited scheduler visibility')
        need(self.c['GPU_authorized']is True and self.c['F0_public_readback']['status']=='COMPLETE_FILE_BYTES_MATCHED',
             'No allocation/F0 authority')
        need(self.c['F0_public_readback']['commit'] and self.c['F0_public_readback']['files'],'Empty F0 public evidence')
        verify_public_readback(self.c['F0_public_readback'])
        need(self.c['F2_public_readback']==self.c['F0_public_readback'],'Complete prospective S3 freeze binding')
        core=read(self.c['frozen_core']);need(sha(self.c['frozen_core'])==self.c['frozen_core_sha256'],'Complete admission core changed')
        for key,value in core.items():
            if key not in ('execution_phase','output_root','F0_public_readback','F2_public_readback'):
                need(self.c.get(key)==value,'Actual S3 configuration differs from frozen core: '+key)
        need(self.c['output_root']==self.c['phase_output_roots'][self.c['execution_phase']], 'Wrong predeclared phase output directory')
        public_core=Path(self.c['public_core']);registered={e['source_file']:e['sha256']for e in self.c['F2_public_readback']['files']}
        need(registered.get(str(public_core))==sha(public_core)and public_core.read_text()==
             transform(Path(self.c['frozen_core']).read_text(),self.c['study_root']),'Complete actual admission was not publicly read back')
        need(sha(self.c['S1_certificate'])==self.c['S1_certificate_sha256']and
             read(self.c['S1_certificate'])['status']=='ALL_REQUIRED_S1_GATES_PASSED','Predecessor S1 must be complete')
        verify_files(self.c['source_files']);verify_files(self.c['frozen_files']);self.closure=read(self.c['compiled_closure'])
        need(sha(self.c['compiled_closure'])==self.c['compiled_closure_sha256'],'Compiled closure binding')
        verify_files(self.closure['files'])
        self.allowed_modules={str(Path(path).resolve()):digest for path,digest in self.closure['files'].items()}
        for binary in self.c['executables'].values():self.allowed_modules[str(Path(binary['path']).resolve())]=binary['sha256']
        self.ledger=Ledger(self.c['ledger'],self.c['inheritance'],self.c['budget_approval'])

    def __enter__(self):
        lockdir=Path.home()/'.cache/reference-compatible-gpu-locks';lockdir.mkdir(parents=True,exist_ok=True)
        lifecycle=self.stack.enter_context((self.root/'lifecycle.lock').open('a+'))
        fcntl.flock(lifecycle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if self.c['execution_phase']=='S3':
            activity=self.stack.enter_context((Path(self.c['ledger']).parent/'activity.lock').open('a+'))
            fcntl.flock(activity,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for path in (self.root.parent/'coordinator.lock',lockdir/(self.c['gpu_uuid']+'.lock')):
            f=self.stack.enter_context(path.open('a+'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fresh(self.root/'LOCK_ACQUIRED.private.json',dict(pid=os.getpid(),utc=utc(),GPU_admitted=True))
        try:resource(self.c)
        except BaseException:
            self.stack.close()
            write(self.root/'LOCK_RELEASED.private.json',dict(utc=utc(),reason='entry resource gate failed',pid=os.getpid()))
            raise
        return self

    def __exit__(self,typ,value,tb):
        write(self.root/'LOCK_RELEASED.private.json',dict(utc=utc(),reason=str(value)if value else'normal',pid=os.getpid()))
        self.stack.close()

    def run(self,worker,job,executable,phase='S3_QUAL',expected_error=None):
        caller_begin=time.monotonic()
        need(phase in ('S3_QUAL','S3'),'Unregistered phase')
        need(phase==self.c['execution_phase'],'Wrong admitted execution phase')
        if executable=='model':
            need(self.c.get('new_root_oracles')and sha(self.c['new_root_oracles'])==self.c['new_root_oracles_sha256']and
                 read(self.c['new_root_oracles'])['status']=='ALL24_REPEATED_PRISTINE_R_REQUESTS_PASSED_AND_ORACLES_FROZEN',
                 'No candidate before complete independent new-root oracle freeze')
        if phase=='S3':
            need(sha(self.c['S3_certificate'])==self.c['S3_certificate_sha256']and
                 read(self.c['S3_certificate'])['status']=='ALL_NEW_ROOT_AND_FRONTEND_GATES_PASSED','No complete new-root qualification')
            need(sha(self.c['new_root_oracles'])==self.c['new_root_oracles_sha256'],'Frozen independent new-root oracle changed')
            proof=self.c.get('S3_admission_cost_proof',{})
            need(proof.get('whole_phase_fits')is True and proof.get('caller_cost_classes')and
                 proof.get('closeout_reserve_s',0)>=900,'No observed complete-caller whole-phase time proof')
            need(time.time()+proof['required_s']<=epoch(self.c['allocation_end_utc']),
                 'Complete S3 plus archive/replay reserve no longer fits')
        registered=[w for w in self.manifest['workers']if w['worker_id']==worker['worker_id']]
        need(len(registered)==1 and registered[0]==worker,'Worker is outside the exact frozen manifest')
        registered_job=Path(self.c['manifest']).parent/worker['job']
        need(sha(registered_job)==worker['job_sha256']and read(registered_job)==job,'Exact complete F2 native job changed')
        order=[w for w in self.manifest['workers']if(w['stage']=='formal')==(phase=='S3')]
        ledger=self.ledger.snapshot();remaining=[w for w in order if not all(
            ledger['operations'].get(op['operation_id'])=='COMPLETE'for op in w['operations'])]
        need(remaining and remaining[0]['worker_id']==worker['worker_id'],'Fixed worker order or previous outcome is incomplete')
        now=time.time();need(epoch(self.c['allocation_start_utc'])<=now<=epoch(self.c['last_new_worker_utc']),
                             'No current worker launch window')
        need(epoch(self.c['allocation_end_utc'])-now>=self.c['worker_timeout_s']+60,'Worker cannot finish in allocation')
        need(not(self.root/'STOP_REQUESTED').exists(),'Stop requested at safe worker boundary')
        verify_files(self.c['source_files'])
        name=worker['worker_id'];need(name and '/'not in name and '\\'not in name and name not in ('.','..'),'Worker ID')
        w=self.root/'workers'/name;need(not w.exists(),'Existing worker state; never duplicate launch');w.mkdir(parents=True)
        exe=self.c['executables'][executable];need(sha(exe['path'])==exe['sha256'],'Executable changed')
        if executable in ('R','model'):
            model=self.c['model'];need(Path(model['path']).stat().st_size==model['bytes']and sha(model['path'])==model['sha256'],'Full frozen model bytes changed')
        fresh(w/'JOB.json',job);job_sha=sha(w/'JOB.json')
        fresh(w/'WORKER.json',worker)
        before=resource(self.c);fresh(w/'RESOURCE_BEFORE.private.json',before)
        for op in worker['operations']:
            self.ledger.event('RESERVE',op['operation_id'],op['reserved_rows'],worker=name,
                               phase=phase,job_sha256=job_sha,manifest_sha256=self.c['manifest_sha256'])
        grant=dict(schema='hs.strong.native-reservation.v1',phase=phase,GPU_authorized=True,
                   complete_F0_readback=True,complete_F2_readback=True,prior_S1_qualified=True,
                   budget_reserved=True,private_gpu_uuid=self.c['gpu_uuid'],job_sha256=job_sha)
        if phase=='S3':grant.update(numerically_qualified=True,new_root_oracles_frozen=True)
        fresh(w/'GRANT.private.json',grant)
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=self.c['gpu_uuid'],CUDA_DEVICE_ORDER='PCI_BUS_ID',
                 HS_STRONG_GPU_ADMISSION_FILE=str(w/'GRANT.private.json'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1')
        if executable in ('R','gold'):env.pop('GGML_CUDA_DISABLE_GRAPHS',None)
        guard=self.c['executables']['guard'];need(sha(guard['path'])==guard['sha256'],'Supervisor-loss guard changed')
        argv=[guard['path'],'--parent',str(os.getpid()),'--','taskset','-c',self.c['native_cpu_affinity'],exe['path'],str(w/'JOB.json'),str(w/'native')]
        if executable=='operand':argv.append('--admitted-by-host')
        p=None;began=caller_begin;started=None;returncode=None;reason=None;start_ticks=None;launch_begin_ns=None
        for op in worker['operations']:self.ledger.event('START',op['operation_id'],worker=name,utc=utc())
        try:
            with (w/'stdout.log').open('xb')as out,(w/'stderr.log').open('xb')as err,(w/'TELEMETRY.private.jsonl').open('x')as telemetry:
                launch_begin_ns=time.monotonic_ns()
                p=subprocess.Popen(argv,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
                started=time.monotonic();start_ticks=Path('/proc/'+str(p.pid)+'/stat').read_text().split()[21]
                fresh(w/'LAUNCH.private.json',dict(argv=argv,pid=p.pid,start_ticks=start_ticks,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                     uid=os.getuid(),utc=utc(),job_sha256=job_sha,executable_sha256=exe['sha256'],launch_begin_monotonic_ns=launch_begin_ns))
                while p.poll()is None:
                    need(time.monotonic()-started<=self.c['worker_timeout_s'],'Native worker timeout')
                    sample=resource(self.c,p.pid);telemetry.write(json.dumps(sample,allow_nan=False)+'\n');telemetry.flush()
                    time.sleep(2)
                returncode=p.wait()
            if expected_error is None:
                need(returncode==0,'Unexpected native failure')
                result=read(w/'native/result.json');need(result['status']=='COMPLETE','Incomplete native receipt')
                actual_modules=result.get('native_module_maps')
                if actual_modules is not None:
                    checked={}
                    for path in actual_modules:
                        actual=str(Path(path).resolve());need(actual in self.allowed_modules,'Unregistered loaded ELF: '+actual)
                        digest=sha(actual);need(digest==self.allowed_modules[actual],'Loaded module bytes differ');checked[actual]=digest
                    fresh(w/'ACTUAL_MODULES.private.json',checked)
                else:
                    # The unchanged R reports dl_iterate_phdr names. Absolute
                    # files are verified; vDSO is explicitly a non-file.
                    need(executable=='R','Missing actual module maps')
                    checked={}
                    for path in result['modules_after']:
                        if path=='linux-vdso.so.1':continue
                        actual=str(Path(path).resolve());need(Path(path).is_absolute() and actual in self.allowed_modules,'Unresolved pristine R module')
                        digest=sha(actual);need(digest==self.allowed_modules[actual],'Pristine R loaded bytes differ');checked[actual]=digest
                    fresh(w/'ACTUAL_MODULES.private.json',checked)
            else:
                need(returncode==2,'Expected descriptor rejection did not occur')
                errors=[json.loads(line.split('HS_NATIVE_FAILURE ',1)[1])for line in(w/'stderr.log').read_text().splitlines()if line.startswith('HS_NATIVE_FAILURE ')]
                need(len(errors)==1 and errors[0]['error']==expected_error and errors[0]['backend_initialization_entered']is False,
                     'Negative failed for the wrong reason or reached CUDA initialization')
                fresh(w/'EXPECTED_REJECTION.json',errors[0])
            for op in worker['operations']:self.ledger.event('COMPLETE',op['operation_id'],worker=name,utc=utc())
        except BaseException as error:
            reason=str(error)
            if p is not None and p.poll()is None:
                stat=Path('/proc/'+str(p.pid)+'/stat')
                need(stat.exists()and stat.read_text().split()[21]==start_ticks and os.getpgid(p.pid)==p.pid,
                     'Own process identity uncertain; no signal sent')
                os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(timeout=15)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
            for op in worker['operations']:
                if self.ledger.snapshot()['operations'].get(op['operation_id'])=='START':
                    self.ledger.event('FAILED',op['operation_id'],worker=name,utc=utc(),
                                      reason='Owned native attempt failed; full original details retained in HOST and phase failure logs',
                                      reason_sha256=__import__('hashlib').sha256(reason.encode()).hexdigest())
            raise
        finally:
            fresh(w/'HOST.json',dict(status='FAILED'if reason else'COMPLETE',returncode=p.returncode if p else None,
                reason=reason,caller_s=time.monotonic()-began,launch_to_exit_observation_s=time.monotonic()-started if started else None,
                expected_rejection=expected_error is not None,
                launch_begin_monotonic_ns=launch_begin_ns,exit_observed_monotonic_ns=time.monotonic_ns(),
                clock='host monotonic; exit is observed by polling, not exact native lifetime',
                stdout_sha256=sha(w/'stdout.log')if(w/'stdout.log').exists()else None,
                stderr_sha256=sha(w/'stderr.log')if(w/'stderr.log').exists()else None,no_reservation_refund=True))
        time.sleep(self.c['fixed_worker_gap_s'])
        return w
