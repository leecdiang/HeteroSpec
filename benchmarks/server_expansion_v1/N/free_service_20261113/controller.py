"""Bounded real user-systemd/seqpacket owner; no automatic GPU retries."""
import argparse,fcntl,hashlib,importlib.util,json,os,select,socket,struct,subprocess,time
from pathlib import Path
_spec=importlib.util.spec_from_file_location('preexec',Path(__file__).with_name('preexec.py'));_p=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_p)
sha,write,cmd,stat,wrapper=_p.sha,_p.write,_p.cmd,_p.stat,_p.wrapper
def encode(j):return json.dumps(j,sort_keys=True,separators=(',',':')).encode()
_shared_guard=None
def resources(root,gpu,cg=None,cpu=False):
 if _shared_guard is not None:
  fd,path,inode=_shared_guard
  if os.fstat(fd).st_ino!=inode or Path(path).stat().st_ino!=inode:raise RuntimeError("shared coordinator lock identity lost")
 apps=cmd(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits']).stdout;entries=[x.split(',') for x in apps.splitlines() if x.startswith(gpu+',')]
 if cg is None and entries:raise RuntimeError('target GPU occupied before launch')
 if cg is not None:
  if len(entries)>1:raise RuntimeError('target GPU conflict')
  for x in entries:
   if Path('/proc',str(int(x[1])),'cgroup').read_text()!='0::'+cg+'\n':raise RuntimeError('target process outside owned resource domain')
 free=cmd(['nvidia-smi','--query-gpu=uuid,memory.free,utilization.gpu','--format=csv,noheader,nounits']).stdout;device=next(x.split(',') for x in free.splitlines() if x.startswith(gpu+','));vram=int(device[1]);util=device[2].strip();ram=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'));d=os.statvfs(root);disk=d.f_bavail*d.f_frsize
 if ram<48*1024**3 or disk<(160 if cg is None else 64)*1024**3 or vram<(12000 if cg is None else 2048):raise RuntimeError('resource reserve pressure')
 return dict(mono=time.monotonic(),wall=time.time(),GPU_safe=True,free_MiB=vram,RAM_available=ram,disk_available=disk,target_processes=len(entries),GPU_utilization_percent=util,CPU_loadavg=Path('/proc/loadavg').read_text().strip(),cpu_substitute=cpu)
def geometry(root):
 refs=json.loads((root/'REFERENCES.json').read_text());results={}
 for case in ['C0','C1']:
  plans={}
  for p in (root/'CANDIDATE/episodes').glob('*/EPISODE.json'):
   e=json.loads(p.read_text())
   if e['stage']=='HEAVY' and e['case']==case:plans[e['arm']]=[(x['position'],x['width'],x['expected_extents']) for x in e['dispatch']['plan']]
  if set(plans)!=set(['W','L']):raise RuntimeError('incomplete prospective geometry qualification')
  results[case]=dict(actual_partition_distinct=plans['W']!=plans['L'],W_calls=len(plans['W']),L_calls=len(plans['L']))
 ok=not results['C0']['actual_partition_distinct'] and results['C1']['actual_partition_distinct'];write(root/'ACTUAL_GEOMETRY_GATE.json',dict(status='PASS' if ok else 'NO_GO_NO_REPLACEMENT',cases=results,source='actual native cache requirements and execution plans after real free generation'))
 return ok
def run_worker(cfg,range_,artifact,cpu=False,bad_nonce=False):
 root=Path(cfg['root']);here=Path(__file__).resolve().parent;role=range_['role'];out=root/role;out.mkdir(mode=0o700);unit='hs-'+cfg['run_id']+'-'+role.lower()+'.service';cg='/user.slice/user-'+str(os.getuid())+'.slice/user@'+str(os.getuid())+'.service/app.slice/'+unit;counter=os.open(root/'COUNTER.LOCK',os.O_RDWR|os.O_NOFOLLOW);fcntl.flock(counter,fcntl.LOCK_EX|fcntl.LOCK_NB);state=json.loads((root/'STATE.json').read_text());window=json.loads((root/'WINDOW.json').read_text())
 if state['active_worker'] is not None or state['next_operation']!=range_['first_operation'] or not cpu and state['consumed']['deployments']>=4:raise RuntimeError('stage/order/deployment reservation')
 before=resources(root,cfg['gpu_uuid'],cpu=cpu);write(out/'RESOURCE_BEFORE.json',before);worker_id=cfg['run_id']+'-'+role;runtime=180 if cpu else min(9000 if role=='CANDIDATE' else 3600,int(window['deadline_wall']-time.time())-10)
 if runtime<120:raise RuntimeError('insufficient safe worker window')
 job=dict(run_id=cfg['run_id'],worker_id=worker_id,role=role,kind=range_['kind'],ledger_root=str(root),output=str(out),cgroup=cg,gpu_uuid=cfg['gpu_uuid'],native_path=artifact['path'],native_sha256=artifact['sha256'],manifest_file_sha256=sha(root/'MANIFEST.json'),model_path=cfg['model_path'],model_fd=198,model_stat=stat(cfg['model_path']),worker_deadline_mono=time.monotonic()+runtime,lock_inode=os.fstat(counter).st_ino,controller_pid=os.getpid(),first_operation=range_['first_operation'],end_operation=range_['end_operation'],sources=json.loads((root/'CONTROLLER_IDENTITY.json').read_text())['sources'])
 if cfg.get('parent_ledger_path'):
  parent=json.loads((root/'PARENT_LEDGER_IDENTITY.json').read_text());job['sources'][cfg['parent_ledger_path']]=parent['sha256']
 job['job_payload_sha256']=hashlib.sha256(encode(job)).hexdigest();write(out/'JOB.json',job);state['active_worker']=dict(id=worker_id,role=role,job_sha256=job['job_payload_sha256']);state['consumed']['deployments']+=0 if cpu else 1;write(root/'STATE.json',state,False);fcntl.flock(counter,fcntl.LOCK_UN)
 write(root/'LEASE.json',dict(run_id=cfg['run_id'],worker_id=worker_id,mono=time.monotonic(),GPU_safe=True),not (root/'LEASE.json').exists())
 listener=socket.socket(socket.AF_UNIX,socket.SOCK_SEQPACKET);sockpath=root/'SUPERVISOR.sock'
 # A new listener per worker uses a distinct path directory via rename after
 # close, owned by this controller; unknown stale sockets are never removed.
 if sockpath.exists():raise RuntimeError('unknown socket path; cannot restart')
 listener.bind(str(sockpath));os.chmod(sockpath,0o600);listener.listen(1);listener.setblocking(False)
 launch=['systemd-run','--user','--unit='+unit,'--property=Type=exec','--property=MemoryMax=25769803776','--property=MemorySwapMax=0','--property=TasksMax=128','--property=CPUQuota=200%','--property=RuntimeMaxSec='+str(runtime),'--property=KillMode=control-group','--property=TimeoutStopSec=5','--property=OOMPolicy=stop','--setenv=CUDA_VISIBLE_DEVICES='+cfg['gpu_uuid'],'/usr/bin/python3','-I',str(Path(__file__).resolve()),'--worker',str(out/'JOB.json')]
 started=time.monotonic();conn=None;validator=None;vlogs=[];current=None;response_start=reset_start=None;timing={};early=False;seen_done=False;last_sample=0;last_unit=0
 try:
  r=cmd(launch);write(out/'LAUNCH.json',dict(argv=launch,stdout=r.stdout,stderr=r.stderr));trace=(out/'RESOURCE_TRACE.jsonl').open('x')
  while True:
   now=time.monotonic()
   if now>=job['worker_deadline_mono'] or time.time()>=window['deadline_wall']:raise RuntimeError('worker/global GPU deadline')
   if now-last_sample>=.4:
    sample=resources(root,cfg['gpu_uuid'],cg,cpu);sample.update(run_id=cfg['run_id'],worker_id=worker_id);base=Path('/sys/fs/cgroup')/cg.lstrip('/')
    for n in ['memory.current','memory.peak','pids.current']:
     try:sample[n]=(base/n).read_text().strip()
     except FileNotFoundError:sample[n]='EXIT_RACE'
    write(root/'LEASE.json',sample,False);trace.write(json.dumps(sample,sort_keys=True)+'\n');trace.flush();last_sample=now
    if trace.tell()>32*1024**2:raise RuntimeError('resource trace cap')
    for n in ['stdout.log','stderr.log']:
     if (out/n).exists() and (out/n).stat().st_size>16*1024**2:raise RuntimeError('worker log cap')
   if validator is not None and validator.poll() is not None:
    code=validator.returncode;validator=None
    for f in vlogs:f.flush();os.fsync(f.fileno());f.close()
    vlogs=[]
    if code:raise RuntimeError('independent episode raw/producer gate failed: '+current['episode'])
    certpath=root/'certificates'/(current['episode']+'.json');cert=json.loads(certpath.read_text());stop=False
    if cert['stage']=='R':
     refs=json.loads((root/'REFERENCES.json').read_text());refs[cert['case']]=current['relative_path'];write(root/'REFERENCES.json',refs,False)
    if cert['stage']=='HEAVY' and json.loads((root/'STATE.json').read_text())['next_operation']==18:stop=not geometry(root);early=stop
    if cert['stage']=='WARM' and json.loads((root/'STATE.json').read_text())['next_operation']==26:write(root/'ALL_LIGHT_WARM_GATES_PASS.json',dict(status='PASS',next_operation=26))
    timing['independent_validation_wall_s']=time.monotonic()-timing['validation_start_mono'];timing.pop('validation_start_mono');write(root/'timings'/(current['episode']+'.json'),timing)
    if cert['stage']=='WARM' and json.loads((root/'STATE.json').read_text())['next_operation']==26:
     warm=[]
     for f in (root/'certificates').glob('*.json'):
      cc=json.loads(f.read_text())
      if cc['stage']=='WARM':warm.append(json.loads((root/'timings'/(cc['episode']+'.json')).read_text()))
     ss=json.loads((root/'STATE.json').read_text());mm=json.loads((root/'MANIFEST.json').read_text());need_rows=sum(o['rows_max'] for o in mm['operations'][26:]);need_seconds=2*sum(t['controller_service_plus_reset_s']+t['independent_validation_wall_s'] for t in warm)+300
     admissible=len(warm)==4 and ss['consumed']['requests']+16<=42 and ss['consumed']['rows']+need_rows<=40000 and time.time()+need_seconds<window['deadline_wall']
     write(root/'PERFORMANCE_ADMISSION.json',dict(status='PASS' if admissible else 'NO_GO_STOP_AFTER_QUALIFICATION',planned_requests=16,remaining_requests=42-ss['consumed']['requests'],row_upper=need_rows,estimated_required_seconds=need_seconds,remaining_wall_seconds=window['deadline_wall']-time.time(),source='two rounds bounded from four actual full light warm episodes plus independent audits and300s cleanup'))
     stop=not admissible;early=stop
    conn.send(encode(dict(event='COMMIT',episode=current['episode'],nonce=current['nonce'],certificate_sha256=sha(certpath),stop=stop)));current=None;timing={}
   readers=[listener] if conn is None else [conn];ready=select.select(readers,[],[],.03)[0]
   if ready:
    if conn is None:
     conn,_=listener.accept();conn.setblocking(False);pid,uid,gid=struct.unpack('3i',conn.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12));pre=json.loads((out/'PREEXEC_KERNEL.json').read_text())
     if uid!=os.getuid() or pid!=pre['pid'] or pre['native_sha256']!=job['native_sha256'] or Path('/proc',str(pid),'cgroup').read_text()!='0::'+cg+'\n':raise RuntimeError('unknown actual peer/child owner')
     write(out/'ACTUAL_PEER.json',dict(pid=pid,uid=uid,cgroup=cg,native_sha256=job['native_sha256'],preexec_sealed=pre['sealed']))
    else:
     b=conn.recv(65536)
     if not b:
      conn.close();conn=None;seen_done=True
     else:
      msg=json.loads(b);event=msg['event']
      if msg['worker_id']!=worker_id:raise RuntimeError('wrong worker frame')
      if event=='HELLO':
       if msg['job_sha256']!=job['job_payload_sha256'] or msg['native_sha256']!=job['native_sha256'] or msg['pid']!=pid:raise RuntimeError('HELLO source/process binding')
       conn.send(encode(dict(event='HELLO_ACK')))
      elif event=='READY':
       if current is not None:raise RuntimeError('concurrent episode')
       idx=json.loads((root/'STATE.json').read_text())['next_operation'];expected='CPU-E0' if cpu else 'E%03d'%(idx+1)
       if msg['episode']!=expected:raise RuntimeError('episode order')
       if not cpu and json.loads((root/'MANIFEST.json').read_text())['operations'][idx]['stage']=='MEASURE' and not (root/'ALL_LIGHT_WARM_GATES_PASS.json').exists():raise RuntimeError('timing before light qualification')
       current=dict(episode=msg['episode'],nonce=msg['nonce']);response_start=time.monotonic();resources(root,cfg['gpu_uuid'],cg,cpu);conn.send(encode(dict(event='GO',episode=msg['episode'],nonce='intentionally-wrong' if bad_nonce else msg['nonce'])))
      elif event=='SERVICE_DONE':
       if not current or msg['episode']!=current['episode'] or msg['nonce']!=current['nonce']:raise RuntimeError('response frame binding')
       timing.update(episode=msg['episode'],controller_response_s=time.monotonic()-response_start,native_response_s=msg['native_response_s'])
      elif event=='RESET_READY':
       reset_start=time.monotonic();conn.send(encode(dict(event='RESET_GO',episode=msg['episode'],nonce=msg['nonce'])))
      elif event=='RESET_DONE':timing.update(controller_reset_s=time.monotonic()-reset_start,native_reset_s=msg['native_reset_s'])
      elif event=='AUDIT_READY':
       if validator is not None or current is None or msg['episode']!=current['episode'] or msg['nonce']!=current['nonce']:raise RuntimeError('audit frame binding')
       path=Path(msg['relative_path'])
       if path.is_absolute() or '..' in path.parts or str(path)!=role+'/episodes/'+current['episode']:raise RuntimeError('audit path outside worker')
       current['relative_path']=str(path);timing['controller_service_plus_reset_s']=timing['controller_response_s']+timing['controller_reset_s'];timing['native_service_plus_reset_s']=timing['native_response_s']+timing['native_reset_s'];timing['validation_start_mono']=time.monotonic()
       vlogs=[(out/(msg['episode']+'-verify.stdout.log')).open('x'),(out/(msg['episode']+'-verify.stderr.log')).open('x')];validator=subprocess.Popen(['/usr/bin/python3','-I',str(here/'verify.py'),'--root',str(root),'--relative',str(path),'--nonce',msg['nonce'],'--jobsha',job['job_payload_sha256'],'--checker',cfg['raw_checker'],'--out',str(root/'certificates'/(msg['episode']+'.json'))],stdout=vlogs[0],stderr=vlogs[1])
      elif event=='WORKER_DONE':seen_done=True
      else:raise RuntimeError('unknown peer event '+event)
   if now-last_unit>=.5:
    q=cmd(['systemctl','--user','show',unit,'-p','ActiveState','-p','Result','-p','ExecMainStatus','-p','ControlGroup']);last_unit=now
    if any(x in q.stdout.splitlines() for x in ['ActiveState=inactive','ActiveState=failed']):break
  trace.flush();os.fsync(trace.fileno());trace.close();write(out/'UNIT_EXIT.json',dict(stdout=q.stdout,elapsed_s=time.monotonic()-started,cpu_substitute=cpu))
  success='Result=success' in q.stdout and 'ExecMainStatus=0' in q.stdout
  if cpu and bad_nonce:
   if success or not (out/'CPU_REJECT.json').exists():raise RuntimeError('CPU bad nonce not rejected')
  elif not success:raise RuntimeError('owned worker failed: '+q.stdout)
  elif cpu:
   if not (out/'CPU_RESULT.json').exists():raise RuntimeError('CPU substitute incomplete')
  elif not (out/'RESULT.json').exists():raise RuntimeError('worker result incomplete')
  if validator is not None:raise RuntimeError('process exit before independent gate closed')
  base=Path('/sys/fs/cgroup')/cg.lstrip('/')
  if (base/'cgroup.procs').exists() and (base/'cgroup.procs').read_text().strip():raise RuntimeError('owned domain not empty')
  write(out/'RESOURCE_AFTER.json',resources(root,cfg['gpu_uuid'],cpu=cpu));fcntl.flock(counter,fcntl.LOCK_EX|fcntl.LOCK_NB);state=json.loads((root/'STATE.json').read_text());state['active_worker']=None;state['completed_workers'].append(role);state['unit_elapsed_s']+=0 if cpu else time.monotonic()-started;state['status']='CPU_TEST_ONLY' if cpu else 'SAFE_EARLY_STOP_NO_PERFORMANCE' if early else 'WORKER_COMPLETE';write(root/'STATE.json',state,False);fcntl.flock(counter,fcntl.LOCK_UN);return early
 except BaseException as e:
  write(out/'STOP_CONTROLLER.json',dict(reason=str(e),no_automatic_retry=True))
  cmd(['systemctl','--user','stop',unit],False)
  if validator is not None:validator.terminate();validator.wait(timeout=5)
  raise
 finally:
  for f in vlogs:
   if not f.closed:f.close()
  if conn:conn.close()
  listener.close();os.rename(sockpath,out/'SUPERVISOR.closed.sock');os.close(counter)
def initialize(cfg,cpu=False):
 root=Path(cfg['root']);window=dict(start_wall=time.time(),start_mono=time.monotonic(),deadline_wall=time.time()+(180 if cpu else 14400),deadline_mono=time.monotonic()+(180 if cpu else 14400))
 if (root/'STATE.json').exists() or (root/'STATE.next').exists():raise RuntimeError('STATE exists: cannot restart')
 fd=os.open(root/'COUNTER.LOCK',os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);os.close(fd);(root/'certificates').mkdir();(root/'timings').mkdir();write(root/'WINDOW.json',window);write(root/'REFERENCES.json',{});write(root/'STATE.json',dict(run_id=cfg['run_id'],scope='SYNTHETIC_CPU_ONLY' if cpu else 'NEW_USER_FREE_SERVICE_AUTHORITY',consumed=dict(requests=0,rows=0,deployments=0),raw_bytes=0,metadata_bytes=0,next_operation=0,passed_episodes=[],completed_workers=[],active_worker=None,unit_elapsed_s=0,status='INITIALIZED'))
def main(config):
 global _shared_guard
 cfg=json.loads(Path(config).read_text());root=Path(cfg['root']);resources(root,cfg['gpu_uuid']);owner=os.open(root/'OWNER.LOCK',os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB);device=os.open(cfg['device_lease_path'],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);fcntl.flock(device,fcntl.LOCK_EX|fcntl.LOCK_NB);os.write(device,encode(dict(run_id=cfg['run_id'],pid=os.getpid())));os.fsync(device)
 shared=None
 try:
  shared=os.open(cfg['shared_lock_path'],os.O_RDONLY|os.O_NOFOLLOW);ss=os.fstat(shared)
  if ss.st_ino!=cfg['shared_lock_inode'] or ss.st_uid!=os.getuid():raise RuntimeError('unknown shared coordinator identity')
  fcntl.flock(shared,fcntl.LOCK_EX|fcntl.LOCK_NB);_shared_guard=(shared,cfg['shared_lock_path'],ss.st_ino)
  if sha(cfg['parent_ledger_path'])!=json.loads((root/'PARENT_LEDGER_IDENTITY.json').read_text())['sha256']:raise RuntimeError('old ledger changed')
  initialize(cfg);manifest=json.loads((root/'MANIFEST.json').read_text());build=json.loads((Path(cfg['build'])/'BUILD.private.json').read_text())
  here=Path(__file__).resolve().parent
  for name,want in build['source_files'].items():
   if Path(name).suffix in ['.cpp','.hpp'] and sha(here/name)!=want:raise RuntimeError('compiled source identity differs '+name)
  write(root/'CONTROLLER_IDENTITY.json',dict(pid=os.getpid(),sources={str(p):sha(p) for p in here.glob('*') if p.is_file()}))
  artifacts={x['kind']:dict(path=str(Path(cfg['build'])/x['file']),sha256=x['sha256']) for x in build['artifacts']}
  for r in manifest['worker_ranges']:
   artifact=artifacts[r['kind']]
   if sha(artifact['path'])!=artifact['sha256']:raise RuntimeError('actual executable differs')
   if run_worker(cfg,r,artifact):break
  state=json.loads((root/'STATE.json').read_text());complete=state['next_operation']==42;state['status']='COMPLETE_EXPLORATORY_PANEL' if complete else 'QUALIFICATION_SAFE_STOP_NO_PANEL';write(root/'STATE.json',state,False);write(root/'RESULT.json',dict(status=state['status'],consumed=state['consumed'],next_operation=state['next_operation'],unit_elapsed_s=state['unit_elapsed_s'],performance_complete=complete,no_automatic_new_work=True))
 finally:
  if shared is not None:os.close(shared)
  os.close(device);os.close(owner)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config');p.add_argument('--worker');a=p.parse_args()
 if a.worker:wrapper(a.worker)
 else:main(a.config)
