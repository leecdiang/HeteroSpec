"""Unchanged PR233 preexec/util functions only; no launcher/main or model imports."""
import fcntl,hashlib,json,os,subprocess
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
