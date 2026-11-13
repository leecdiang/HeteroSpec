"""File/proc/NVML audit only. Never loads or executes a numerical model runtime.

Run with an explicit private JSON configuration argument. Prints one JSON receipt;
does not create any remote file, directory, cgroup, service or allocation.
"""
import datetime, hashlib, json, os, pathlib, shutil, stat, subprocess, sys, time

cfg=json.loads(sys.argv[1]); roots={k:pathlib.Path(v) for k,v in cfg['roots'].items()}
start=time.monotonic(); memo={}
def sha(p):
 p=pathlib.Path(p)
 if str(p) not in memo:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  memo[str(p)]=h.hexdigest()
 return memo[str(p)]
def identify(p):
 p=pathlib.Path(p); s=p.stat()
 return dict(bytes=s.st_size,sha256=sha(p),inode=s.st_ino,device=s.st_dev,mtime_ns=s.st_mtime_ns,resolved_path=str(p.resolve()))
def read(p):
 try:return pathlib.Path(p).read_text()
 except (OSError,UnicodeError) as e:return 'UNAVAILABLE:'+type(e).__name__
def command(argv):
 try:
  x=subprocess.run(argv,capture_output=True,text=True,timeout=20)
  return dict(argv=argv,returncode=x.returncode,stdout=x.stdout,stderr=x.stderr)
 except (OSError,subprocess.TimeoutExpired) as e:return dict(argv=argv,error=type(e).__name__)
def check(x):
 p=roots[x['root']]/x['relative_path']
 try:
  a=identify(p);return dict(x,**a,match=a['sha256']==x['sha256'] and ('bytes' not in x or x['bytes']==a['bytes']))
 except OSError as e:return dict(x,match=False,error=type(e).__name__)

# Identity reads precede resource/toolchain probes and all future preparation.
checks={k:[check(x) for x in v] for k,v in cfg['file_groups'].items()}
closures=[]
for x in cfg['source_locks']:
 p=roots['HS_ROOT']/x['lock']; raw=json.loads(p.read_text()); mismatches=[];count=0
 for rel,want in raw['sources'][x['role']].items():
  count+=1;f=roots['HS_ROOT']/x['source_root']/rel
  if not f.is_file() or sha(f)!=want:mismatches.append(rel)
 closures.append(dict(x,kind='SOURCE_LOCK',files_checked=count,all_match=not mismatches,mismatches=mismatches))
for x in cfg['dependencies']:
 p=roots['HS_ROOT']/x['receipt']; raw=json.loads(p.read_text());mismatches=[]
 for name,want in raw['files'].items():
  if not pathlib.Path(name).is_file() or sha(name)!=want:mismatches.append(name)
 closures.append(dict(x,kind='DEPENDENCIES',receipt_sha256=sha(p),files_checked=len(raw['files']),all_match=not mismatches,mismatches=mismatches))

mem={}
for line in read('/proc/meminfo').splitlines():
 if line.split(':')[0] in ['MemTotal','MemAvailable','SwapTotal','SwapFree']:mem[line.split(':')[0]+'_KiB']=int(line.split()[1])
d=shutil.disk_usage(roots['HS_ROOT']);v=os.statvfs(roots['HS_ROOT'])
gpu=command(['nvidia-smi','--query-gpu=index,uuid,name,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'])
compute=command(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'])
devices=[];processes=[]
if gpu.get('returncode')==0:
 for line in gpu['stdout'].strip().splitlines():
  f=[s.strip() for s in line.split(',')]
  if len(f)==7 and f[1]==cfg['target_uuid']:devices.append(dict(zip(['index','uuid','name','total_MiB','used_MiB','free_MiB','utilization_percent'],f)))
if compute.get('returncode')==0:
 for line in compute['stdout'].strip().splitlines():
  f=[s.strip() for s in line.split(',')]
  if len(f)==3:processes.append(dict(gpu_uuid=f[0],pid=f[1],used_MiB=f[2]))
locks=[];proc_locks=read('/proc/locks').splitlines()
for x in cfg['locks']:
 p=roots['HS_ROOT']/x['relative_path'];s=p.stat();identity='%02x:%02x:%s'%(os.major(s.st_dev),os.minor(s.st_dev),s.st_ino)
 locks.append(dict(relative_path=x['relative_path'],inode=s.st_ino,device=s.st_dev,identity_matches_old=s.st_ino==x['inode'],held=any(identity in q.split() for q in proc_locks)))
own_processes=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  if p.stat().st_uid!=os.geteuid():continue
  cmd=(p/'cmdline').read_bytes().replace(b'\x00',b' ').decode('utf8','replace')
  if any(t in cmd for t in cfg['same_task_process_needles']) and p.name!=str(os.getpid()):
   own_processes.append(dict(pid=int(p.name),command=cmd,exe=str((p/'exe').resolve()),stat=read(p/'stat')))
 except OSError:pass

cgroup_line=next((x[3:] for x in read('/proc/self/cgroup').splitlines() if x.startswith('0::')),None)
cgroups=[]
if cgroup_line is not None:
 base=pathlib.Path('/sys/fs/cgroup');cur=base/cgroup_line.lstrip('/');seen=set()
 for p in [cur,*cur.parents]:
  if p==base.parent or not str(p).startswith(str(base)) or str(p) in seen:continue
  seen.add(str(p));s=p.stat();fields={}
  for n in ['cgroup.type','cgroup.controllers','cgroup.subtree_control','cgroup.events','memory.max','memory.high','memory.current','memory.peak','memory.events','pids.max','pids.current']:
   f=p/n
   if f.exists():fields[n]=dict(value=read(f),writable_by_euid=os.access(f,os.W_OK))
  cgroups.append(dict(relative_path=str(p.relative_to(base)),directory_uid=s.st_uid,directory_gid=s.st_gid,directory_mode=oct(stat.S_IMODE(s.st_mode)),directory_writable_by_euid=os.access(p,os.W_OK),fields=fields))
tools=[]
for binary in ['g++','cmake','python3','readelf','node','systemctl']:
 p=shutil.which(binary)
 if not p:tools.append(dict(name=binary,available=False));continue
 x=dict(name=binary,available=True,path=p,**identify(p))
 if binary!='systemctl':x['version']=command([p,'--version'])
 tools.append(x)
systemd=command(['systemctl','--user','show','--property=ControlGroup','--property=Delegate','--property=MemoryAccounting','--property=MemoryMax','--property=DefaultMemoryAccounting']) if shutil.which('systemctl') else None
model=identify(roots['HS_ROOT']/cfg['model_relative_path'])
print(json.dumps(dict(schema='hs.N1controller.readonly-host-audit.v1',observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='FILE_PROC_NVML_ONLY_NO_NATIVE_MODEL_EXECUTION',authority='CPU_ONLY_GPU_NOT_AUTHORIZED',file_groups=checks,source_dependency_closures=closures,unique_files_hashed=len(memo),memory=mem,storage=dict(available_bytes=v.f_bavail*v.f_frsize,free_bytes=d.free,total_bytes=d.total),target_devices=devices,target_compute_processes=[p for p in processes if p['gpu_uuid']==cfg['target_uuid']],other_GPU_compute_process_count_only=sum(p['gpu_uuid']!=cfg['target_uuid'] for p in processes),nvml_query_status=dict(gpu=gpu.get('returncode'),compute=compute.get('returncode')),locks=locks,same_task_owned_processes=own_processes,cgroup_v2_path=cgroup_line,cgroup_v2_ancestry=cgroups,cgroup_mountinfo=[l for l in read('/proc/self/mountinfo').splitlines() if ' - cgroup2 ' in l],user_systemd_readonly=systemd,toolchain=tools,model_file=model,model_loaded=False,elapsed_s=time.monotonic()-start,execution_counters=dict(native_ELF=0,backend_init=0,models_including_vocab=0,contexts=0,placements=0,forward=0)),indent=2))
