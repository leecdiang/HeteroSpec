"""One bounded server-side qualification chain; fail closed, no automatic retries.

Uses existing delegated user-systemd domains before exec. No dependency on SSH.
Only the explicitly frozen R/repeat/cold phases are implemented here initially.
"""
import argparse,fcntl,hashlib,json,os,subprocess,sys,time
from pathlib import Path
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def encode(j):return json.dumps(j,sort_keys=True,separators=(',',':')).encode()+b'\n'
def write(p,j,fresh=True):
 p=Path(p);target=p if fresh else Path(str(p)+'.pending');raw=encode(j);fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 try:
  if os.write(fd,raw)!=len(raw):raise RuntimeError('partial durable write')
  os.fsync(fd)
 finally:os.close(fd)
 if not fresh:os.replace(target,p)
 d=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY);os.fsync(d);os.close(d)
def cmd(argv,check=True):
 r=subprocess.run(argv,capture_output=True,text=True,timeout=15)
 if check and r.returncode:raise RuntimeError('command failed '+r.stderr)
 return r
def stat(p):
 s=os.fstat(p) if isinstance(p,int) else os.stat(p)
 return dict(dev=s.st_dev,ino=s.st_ino,size=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)
def resources(root,gpu,unit=None):
 apps=cmd(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits']).stdout
 entries=[x.split(',') for x in apps.splitlines() if x.startswith(gpu+',')]
 if unit is None and entries:raise RuntimeError('allocated GPU not empty')
 if unit is not None:
  if len(entries)>1:raise RuntimeError('new GPU conflict')
  for e in entries:
   if Path('/proc',str(int(e[1])),'cgroup').read_text()!='0::'+unit+'\n':raise RuntimeError('GPU PID outside exact owned domain')
 g=cmd(['nvidia-smi','--query-gpu=uuid,memory.free','--format=csv,noheader,nounits']).stdout
 free=next(int(x.split(',')[1]) for x in g.splitlines() if x.startswith(gpu+','))
 ram=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'));v=os.statvfs(root);disk=v.f_bavail*v.f_frsize
 if free<2048 or ram<48*1024**3 or disk<553094505923:raise RuntimeError('resource reserve unavailable')
 return dict(mono=time.monotonic(),wall=time.time(),GPU_safe=True,free_MiB=free,RAM_available=ram,disk_available=disk,target_processes=len(entries))
def wrapper(jobfile):
 j=json.loads(Path(jobfile).read_text());root=Path(j['ledger_root']);out=Path(j['output']);gpu=j['gpu_uuid'];base=Path('/sys/fs/cgroup')/j['cgroup'].lstrip('/')
 if Path('/proc/self/cgroup').read_text()!='0::'+j['cgroup']+'\n':raise RuntimeError('not in preexec domain')
 for n,w in [('memory.max','25769803776'),('memory.swap.max','0'),('pids.max','128')]:
  if (base/n).read_text().strip()!=w:raise RuntimeError('kernel limit not active')
 if os.environ.get('CUDA_VISIBLE_DEVICES')!=gpu:raise RuntimeError('UUID environment differs')
 if sha(root/'MANIFEST.json')!=j['manifest_file_sha256'] or sha(j['native_path'])!=j['native_sha256']:raise RuntimeError('preexec frozen image/manifest differs')
 for p,h in j['sources'].items():
  if sha(p)!=h:raise RuntimeError('preexec source differs')
 fd=os.open(j['model_path'],os.O_RDONLY|os.O_NOFOLLOW)
 if stat(fd)!=j['model_stat'] or sha('/proc/self/fd/'+str(fd))!='408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6' or stat(fd)!=j['model_stat']:raise RuntimeError('full original model identity differs')
 os.dup2(fd,j['model_fd'],inheritable=True);os.close(fd)
 raw=Path(j['native_path']).read_bytes();image=os.memfd_create('bounded-qualified-worker',os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING);off=0
 while off<len(raw):off+=os.write(image,raw[off:off+1048576])
 fcntl.fcntl(image,fcntl.F_ADD_SEALS,fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK|fcntl.F_SEAL_SEAL);os.set_inheritable(image,True)
 write(out/'PREEXEC_KERNEL.json',dict(pid=os.getpid(),pid_start=Path('/proc/self/stat').read_text().split()[21],cgroup=j['cgroup'],sealed=True,native_sha256=j['native_sha256'],model_sha256='408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6',limits={n:(base/n).read_text() for n in ['memory.max','memory.swap.max','pids.max']}))
 for n,target in [('stdout',1),('stderr',2)]:
  fd=os.open(out/(n+'.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);os.dup2(fd,target);os.close(fd)
 env={**os.environ,'GGML_CUDA_DISABLE_GRAPHS':'1','CUDA_VISIBLE_DEVICES':gpu}
 for n in ['LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']:env.pop(n,None)
 os.execve('/proc/self/fd/'+str(image),[j['native_path'],jobfile,sha(jobfile)],env)
def main(config):
 cfg=json.loads(Path(config).read_text());root=Path(cfg['root']);here=Path(__file__).resolve().parent;manifest=json.loads((root/'MANIFEST.json').read_text());window=manifest['window'];gpu=cfg['gpu_uuid'];build=Path(cfg['build']);receipt=json.loads((build/'BUILD.private.json').read_text());exe=build/'bounded-reference';owner=None;counter=None;device=None;unit=None
 if (root/'STATE.json').exists() or (root/'STATE.next').exists():raise RuntimeError('existing STATE cannot restart or resume')
 if sha(exe)!=receipt['executable_sha256']:raise RuntimeError('native build identity changed')
 if time.time()>=window['no_new_worker_wall']:raise RuntimeError('no safe GPU start time remains')
 # Three independent owned locks; unknown pre-existing objects always reject.
 for name in ['OWNER.LOCK','COUNTER.LOCK']:
  fd=os.open(root/name,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if name=='OWNER.LOCK':owner=fd
  else:counter=fd;fcntl.flock(fd,fcntl.LOCK_UN)
 device=os.open(cfg['device_lease_path'],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);fcntl.flock(device,fcntl.LOCK_EX|fcntl.LOCK_NB);os.write(device,encode(dict(run_id=cfg['run_id'],owner_pid=os.getpid(),root=str(root))));os.fsync(device)
 state=dict(run_id=cfg['run_id'],status='ADMITTED_BOUNDED_QUALIFICATION',consumed=dict(requests=4,rows=732,deployments=1),raw_bytes=0,requests={},passed_roles=[],active_worker=None,prior_immutable_debit=manifest['original_gpu_pilot'])
 write(root/'STATE.json',state);write(root/'RESOURCE_BEFORE.json',resources(root,gpu))
 try:
  for role in ['R','REPEAT','COLD']:
   if time.time()>=window['no_new_worker_wall'] or time.monotonic()+1200>window['deadline_mono']:raise RuntimeError('new-worker cutoff')
   resource=resources(root,gpu);write(root/(role+'-RESOURCE_BEFORE.json'),resource)
   fcntl.flock(counter,fcntl.LOCK_EX|fcntl.LOCK_NB);state=json.loads((root/'STATE.json').read_text())
   if state['active_worker'] is not None or state['consumed']['deployments']>=10:raise RuntimeError('unknown active worker or deployment ceiling')
   expected=['R','REPEAT','COLD'][:['R','REPEAT','COLD'].index(role)]
   if state['passed_roles']!=expected:raise RuntimeError('stage order')
   planned=[x for x in manifest['operations'] if x['role']==role]
   if state['consumed']['requests']+len(planned)>76 or state['consumed']['rows']+sum(x['rows'] for x in planned)>85738:raise RuntimeError('insufficient remaining stage budget')
   out=root/role;out.mkdir(mode=0o700);worker_id=cfg['run_id']+'-'+role.lower();unit='hs-'+worker_id+'.service';cg='/user.slice/user-'+str(os.getuid())+'.slice/user@'+str(os.getuid())+'.service/app.slice/'+unit
   job=dict(run_id=cfg['run_id'],worker_id=worker_id,role=role,output=str(out),ledger_root=str(root),cgroup=cg,gpu_uuid=gpu,native_path=str(exe),native_sha256=receipt['executable_sha256'],manifest_file_sha256=sha(root/'MANIFEST.json'),model_path=cfg['model_path'],model_fd=198,model_stat=stat(cfg['model_path']),worker_deadline_mono=min(window['deadline_mono'],time.monotonic()+1200),lock_inode=os.fstat(counter).st_ino,sources={str(here/n):h for n,h in receipt['source_files'].items()})
   job['job_payload_sha256']=hashlib.sha256(encode(job).rstrip(b'\n')).hexdigest();write(out/'JOB.json',job);state['active_worker']=dict(id=worker_id,role=role,job_sha256=job['job_payload_sha256']);state['consumed']['deployments']+=1;write(root/'STATE.json',state,False);fcntl.flock(counter,fcntl.LOCK_UN)
   write(root/'LEASE.json',dict(run_id=cfg['run_id'],worker_id=worker_id,mono=time.monotonic(),GPU_safe=True),not (root/'LEASE.json').exists())
   argv=['systemd-run','--user','--unit='+unit,'--property=Type=exec','--property=MemoryMax=25769803776','--property=MemorySwapMax=0','--property=TasksMax=128','--property=CPUQuota=200%','--property=RuntimeMaxSec=1200','--property=KillMode=control-group','--property=TimeoutStopSec=5','--property=OOMPolicy=stop','--setenv=CUDA_VISIBLE_DEVICES='+gpu,'/usr/bin/python3','-I',str(Path(__file__).resolve()),'--worker',str(out/'JOB.json')]
   started=time.monotonic();launch=cmd(argv);write(out/'LAUNCH.json',dict(argv=argv,stdout=launch.stdout,stderr=launch.stderr))
   with (out/'RESOURCE_TRACE.jsonl').open('x') as trace:
    while True:
     q=cmd(['systemctl','--user','show',unit,'--property=ActiveState','--property=Result','--property=ExecMainStatus','--property=ControlGroup'])
     if any(x in q.stdout.splitlines() for x in ['ActiveState=inactive','ActiveState=failed']):break
     if time.monotonic()>=job['worker_deadline_mono'] or time.time()>=window['deadline_wall']:raise RuntimeError('hard bounded deadline reached')
     sample=resources(root,gpu,cg);sample.update(run_id=cfg['run_id'],worker_id=worker_id)
     b=Path('/sys/fs/cgroup')/cg.lstrip('/')
     for n in ['memory.current','memory.peak','pids.current']:
      try:sample[n]=(b/n).read_text().strip()
      except FileNotFoundError:sample[n]='EXIT_RACE'
     trace.write(json.dumps(sample,sort_keys=True)+'\n');trace.flush()
     if trace.tell()>8*1024**2:raise RuntimeError('resource trace cap')
     for n in ['stdout.log','stderr.log']:
      if (out/n).exists() and (out/n).stat().st_size>16*1024**2:raise RuntimeError('native log cap')
     write(root/'LEASE.json',sample,False);time.sleep(.3)
    trace.flush();os.fsync(trace.fileno())
   write(out/'UNIT_EXIT.json',dict(stdout=q.stdout,elapsed_seconds=time.monotonic()-started))
   if 'Result=success' not in q.stdout or 'ExecMainStatus=0' not in q.stdout:raise RuntimeError('owned native worker failed: '+q.stdout)
   base=Path('/sys/fs/cgroup')/cg.lstrip('/')
   if (base/'cgroup.procs').exists() and (base/'cgroup.procs').read_text().strip():raise RuntimeError('owned domain not released')
   write(out/'RESOURCE_AFTER.json',resources(root,gpu));fcntl.flock(counter,fcntl.LOCK_EX|fcntl.LOCK_NB)
   state=json.loads((root/'STATE.json').read_text())
   # Original raw files are compared after actual process exit. A JSON success
   # alone never qualifies the next stage. No GPU calls in the independent verifier.
   check=subprocess.run(['/usr/bin/python3','-I',str(here/'verify.py'),'--ledger',str(root),'--role',role,'--out',str(root/(role+'-INDEPENDENT.json'))],capture_output=True,text=True,timeout=480)
   write(root/(role+'-VERIFY_PROCESS.json'),dict(returncode=check.returncode,stdout=check.stdout,stderr=check.stderr))
   if check.returncode:raise RuntimeError('strict independent comparison failed: '+check.stderr[-2000:])
   state['passed_roles'].append(role);state['active_worker']=None;write(root/'STATE.json',state,False);fcntl.flock(counter,fcntl.LOCK_UN);unit=None
  state=json.loads((root/'STATE.json').read_text());state['status']='REFERENCE_REPEAT_COLD_COMPLETE_STRONG_NOT_IMPLEMENTED';write(root/'STATE.json',state,False);write(root/'QUALIFICATION_RESULT.json',dict(status=state['status'],consumed=state['consumed'],passed_roles=state['passed_roles'],next='Only after source-bound strong adapter is implemented and CPU-checked; no automatic performance or N1a261 promotion'))
 except BaseException as e:
  write(root/'STOP_CONTROLLER.json',dict(reason=str(e),no_automatic_retry=True,unit=unit))
  if unit:cmd(['systemctl','--user','stop',unit],False)
  raise
 finally:
  for fd in [device,counter,owner]:
   if fd is not None:os.close(fd)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config');p.add_argument('--worker');a=p.parse_args()
 if a.worker:wrapper(a.worker)
 else:main(a.config)
