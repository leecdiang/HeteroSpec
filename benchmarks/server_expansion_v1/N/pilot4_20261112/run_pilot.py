"""Bounded actual user-systemd admission/supervision for one authorized attempt.

No model import. The native image is executed only after real kernel/resource,
identity, exclusive-device and durable deployment checks. No retry path exists.
"""
import argparse,fcntl,hashlib,json,os,select,subprocess,sys,time
from pathlib import Path

GPU=os.environ['HS_PILOT_GPU_UUID']
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(p,j,fresh=True):
 p=Path(p);raw=json.dumps(j,sort_keys=True,separators=(',',':')).encode()+b'\n'
 if fresh:
  fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 else:fd=os.open(str(p)+'.pending',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 try:
  if os.write(fd,raw)!=len(raw):raise RuntimeError('short write')
  os.fsync(fd)
 finally:os.close(fd)
 if not fresh:os.replace(str(p)+'.pending',p)
 d=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY);os.fsync(d);os.close(d)
def cmd(args,check=True):
 r=subprocess.run(args,capture_output=True,text=True,timeout=15)
 if check and r.returncode:raise RuntimeError('command failed: '+r.stderr)
 return r
def gpu_safe(empty):
 r=cmd(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'])
 entries=[x.split(',') for x in r.stdout.splitlines() if x.startswith(GPU)]
 if empty and entries:raise RuntimeError('allocated GPU has another task')
 if not empty and len(entries)>1:raise RuntimeError('new conflicting GPU task')
 if not empty and entries:
  pid=int(entries[0][1]);cg=Path('/proc',str(pid),'cgroup').read_text()
  if JOB_UNIT not in cg:raise RuntimeError('GPU process outside owned unit')
 free=cmd(['nvidia-smi','--query-gpu=uuid,memory.free','--format=csv,noheader,nounits']).stdout
 value=next(int(x.split(',')[1]) for x in free.splitlines() if x.startswith(GPU))
 if value<2048:raise RuntimeError('less than2GiB VRAM reserve')
 return dict(target_processes=len(entries),free_MiB=value,mono=time.monotonic())
def resources(root):
 available=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
 s=os.statvfs(root);disk=s.f_bavail*s.f_frsize
 if available<48*1024**3 or disk<32*1024**3:raise RuntimeError('RAM/disk admission floor failed')
 return dict(RAM_available=available,disk_available=disk)

def worker(jobfile):
 j=json.loads(Path(jobfile).read_text());out=Path(j['output'])
 if Path('/proc/self/cgroup').read_text()!='0::'+j['cgroup']+'\n':raise RuntimeError('wrong preexec cgroup')
 base=Path('/sys/fs/cgroup')/j['cgroup'].lstrip('/')
 for n,want in [('memory.max','25769803776'),('memory.swap.max','0'),('pids.max','128')]:
  if (base/n).read_text().strip()!=want:raise RuntimeError('real kernel limit mismatch')
 if os.environ.get('CUDA_VISIBLE_DEVICES')!=GPU:raise RuntimeError('wrong visible GPU')
 if sha(j['case_file'])!=j['case_sha256'] or sha(j['native_path'])!=j['native_sha256']:raise RuntimeError('preexec source/image identity')
 raw=Path(j['native_path']).read_bytes()
 image=os.memfd_create('single-approved-pilot',os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
 off=0
 while off<len(raw):off+=os.write(image,raw[off:off+1048576])
 fcntl.fcntl(image,fcntl.F_ADD_SEALS,fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK|fcntl.F_SEAL_SEAL)
 os.set_inheritable(image,True)
 write(out/'PREEXEC_KERNEL.json',dict(pid=os.getpid(),cgroup=j['cgroup'],limits={n:(base/n).read_text() for n in ('memory.max','pids.max','memory.swap.max')},native_sha256=j['native_sha256'],sealed=True))
 # stdout/stderr are fresh regular files, never an SSH pipe.
 for n,target in [('stdout',1),('stderr',2)]:
  f=os.open(out/(n+'.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);os.dup2(f,target);os.close(f)
 env={**os.environ,'GGML_CUDA_DISABLE_GRAPHS':'1','CUDA_VISIBLE_DEVICES':GPU}
 for n in ('LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT'):env.pop(n,None)
 os.execve('/proc/self/fd/'+str(image),[j['native_path'],jobfile,sha(jobfile)],env)

def launch(root,unit,exe,run_id,case,native,probe=False):
 global JOB_UNIT
 JOB_UNIT=unit
 if root.exists():raise RuntimeError('existing STATE/output cannot resume')
 root.mkdir(mode=0o700)
 cgroup='/user.slice/user-'+str(os.getuid())+'.slice/user@'+str(os.getuid())+'.service/app.slice/'+unit
 receipt=dict(run_id=run_id,deployment_reserved=0 if probe else 1,scope='CPU_SUBSTITUTE' if probe else 'AUTHORIZED_GPU_PILOT',model_request_limit=4,row_limit=8192,automatic_retry=False)
 write(root/'DEPLOYMENT_RESERVED.json',receipt)
 j=dict(run_id=run_id,output=str(root),cgroup=cgroup,approval_scope='USER_PILOT_4_8192_1',case_file=str(case),case_sha256=sha(case),native_path=str(exe),native_sha256=sha(exe),gpu_uuid=GPU,model_path=os.environ['HS_PILOT_MODEL_PATH'],deadline_mono=time.monotonic()+600,deployment_receipt=(root/'DEPLOYMENT_RESERVED.json').read_text())
 write(root/'JOB.json',j)
 write(root/'LEASE.json',dict(run_id=run_id,mono=time.monotonic(),GPU_safe=True))
 if not probe:gpu_safe(True);write(root/'RESOURCE_BEFORE.json',resources(root))
 argv=['systemd-run','--user','--unit='+unit,'--property=Type=exec','--property=MemoryMax=25769803776','--property=MemorySwapMax=0','--property=TasksMax=128','--property=CPUQuota=200%','--property=RuntimeMaxSec=600','--property=KillMode=control-group','--property=TimeoutStopSec=5','--property=OOMPolicy=stop','--setenv=CUDA_VISIBLE_DEVICES='+GPU]
 if probe:argv += [str(exe),str(root/'JOB.json')]
 else:argv += ['/usr/bin/python3','-I',str(Path(__file__).resolve()),'--worker',str(root/'JOB.json')]
 start=time.monotonic();r=cmd(argv);write(root/'LAUNCH.json',dict(argv=argv,stdout=r.stdout,stderr=r.stderr))
 try:
  while True:
   q=cmd(['systemctl','--user','show',unit,'--property=ActiveState','--property=Result','--property=ExecMainStatus','--property=ControlGroup'])
   terminal=any(x in q.stdout.splitlines() for x in ('ActiveState=inactive','ActiveState=failed'))
   if terminal:break
   if time.monotonic()>j['deadline_mono']:raise RuntimeError('bounded run deadline')
   sample=dict(run_id=run_id,mono=time.monotonic(),GPU_safe=True)
   if not probe:sample.update(gpu_safe(False));resources(root)
   for name in ('stdout.log','stderr.log'):
    if (root/name).exists() and (root/name).stat().st_size>16*1024**2:raise RuntimeError('log cap')
   write(root/'LEASE.json',sample,False)
   time.sleep(.3)
  write(root/'UNIT_EXIT.json',dict(stdout=q.stdout,elapsed_s=time.monotonic()-start))
  if 'Result=success' not in q.stdout or 'ExecMainStatus=0' not in q.stdout:raise RuntimeError('owned process failed: '+q.stdout)
  if not (root/('CPU_PROBE.json' if probe else 'RESULT.json')).exists():raise RuntimeError('process exited without complete result')
  base=Path('/sys/fs/cgroup')/cgroup.lstrip('/')
  if (base/'cgroup.procs').exists() and (base/'cgroup.procs').read_text().strip():raise RuntimeError('owned domain still has processes')
  if not probe:write(root/'RESOURCE_AFTER.json',dict(**resources(root),**gpu_safe(True)))
 except BaseException as e:
  write(root/'STOP_CONTROLLER.json',dict(reason=str(e),no_retry=True,deployments_reserved=0 if probe else 1))
  cmd(['systemctl','--user','stop',unit],False)
  raise

def main():
 p=argparse.ArgumentParser();p.add_argument('--attempt');p.add_argument('--build');p.add_argument('--worker');p.add_argument('--cpu-only',action='store_true');a=p.parse_args()
 if a.worker:return worker(a.worker)
 attempt=json.loads(Path(a.attempt).read_text());base=Path(attempt['root']);here=Path(__file__).resolve().parent;case=here/'CASE_FROZEN.json';src=Path(os.environ['HS_PILOT_HOST_ROOT'])/'run-01/stage-03/sources/reference'
 probe=base/'gate-cpu';prun='cpu-'+attempt['run_id'];exe=base/'gate-cpu-probe'
 cmd(['/usr/bin/g++','-std=c++17','-O2','-I'+str(src/'vendor'),'-I'+str(here),'-DHS_PILOT_RUN_ID='+json.dumps(prun),'-DHS_PILOT_OUTPUT='+json.dumps(str(probe)),str(here/'gate_cpu_probe.cpp'),'-o',str(exe)])
 libs=cmd(['readelf','-d',str(exe)]).stdout
 import re
 if set(re.findall(r'Shared library: \[([^]]+)\]',libs))-{'libstdc++.so.6','libgcc_s.so.1','libc.so.6','libm.so.6'}:raise RuntimeError('CPU probe has native dependency')
 launch(probe,'hs-'+prun+'.service',exe,prun,case,None,True)
 print('CPU_GATE_PASS',flush=True)
 if a.cpu_only:return
 build=Path(a.build);receipt=json.loads((build/'BUILD.private.json').read_text());native=build/'pilot-single-attempt'
 if sha(native)!=receipt['executable_sha256']:raise RuntimeError('frozen native build differs')
 # An existing reservation or output aborts, never creates a successor retry.
 launch(Path(attempt['native_output']),attempt['unit'],native,attempt['run_id'],case,receipt,False)
 print('GPU_ATTEMPT_FINISHED',flush=True)

if __name__=='__main__':main()
