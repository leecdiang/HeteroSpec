"""Actual kernel/preexec/sealed-image successor probe, standard libraries only."""
import argparse,fcntl,importlib.util,json,os,subprocess,time,re
from pathlib import Path
def main(config):
 here=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('control',here/'control.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);cfg=json.loads(Path(config).read_text());base=Path(cfg['root']);root=base/'bridge-cpu01';root.mkdir(mode=0o700);(root/'MANIFEST.json').write_bytes((base/'MANIFEST.json').read_bytes());out=root/'worker';out.mkdir(mode=0o700);exe=root/'std-only-probe';src=Path(cfg['model_path']).parents[1]/'run-01/stage-03/sources/reference'
 argv=['/usr/bin/g++','-std=c++17','-O2','-I'+str(src/'vendor'),'-DHS_SUCC_ROOT='+json.dumps(str(root)),'-DHS_SUCC_MANIFEST_SHA='+json.dumps(c.sha(root/'MANIFEST.json')),str(here/'cpu_probe.cpp'),'-o',str(exe)]
 r=subprocess.run(argv,capture_output=True,text=True,timeout=60);c.write(root/'COMPILE.json',dict(argv=argv,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
 if r.returncode:raise RuntimeError('CPU probe compile failure')
 libs=c.cmd(['readelf','-d',str(exe)]).stdout
 if set(re.findall(r'Shared library: \[([^]]+)\]',libs))-{'libstdc++.so.6','libgcc_s.so.1','libc.so.6','libm.so.6'}:raise RuntimeError('probe has runtime/CUDA dependency')
 fd=os.open(root/'COUNTER.LOCK',os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);unit='hs-'+cfg['run_id']+'-bridge-cpu.service';cg='/user.slice/user-'+str(os.getuid())+'.slice/user@'+str(os.getuid())+'.service/app.slice/'+unit;wid=cfg['run_id']+'-CPU_ONLY'
 job=dict(run_id=cfg['run_id']+'-CPU_ONLY',worker_id=wid,role='R',output=str(out),ledger_root=str(root),cgroup=cg,gpu_uuid=cfg['gpu_uuid'],native_path=str(exe),native_sha256=c.sha(exe),manifest_file_sha256=c.sha(root/'MANIFEST.json'),model_path=cfg['model_path'],model_fd=198,model_stat=c.stat(cfg['model_path']),worker_deadline_mono=time.monotonic()+60,lock_inode=os.fstat(fd).st_ino,sources={str(here/n):c.sha(here/n) for n in ['successor_gate.hpp','cpu_probe.cpp','control.py']})
 import hashlib
 job['job_payload_sha256']=hashlib.sha256(c.encode(job).rstrip(b'\n')).hexdigest();c.write(out/'JOB.json',job);c.write(root/'STATE.json',dict(run_id=job['run_id'],consumed=dict(requests=0,rows=0,deployments=0),raw_bytes=0,requests={},passed_roles=[],active_worker=dict(id=wid,role='R',job_sha256=job['job_payload_sha256'])))
 c.write(root/'LEASE.json',dict(run_id=job['run_id'],worker_id=wid,mono=time.monotonic(),GPU_safe=True))
 launch=['systemd-run','--user','--unit='+unit,'--property=Type=exec','--property=MemoryMax=25769803776','--property=MemorySwapMax=0','--property=TasksMax=128','--property=CPUQuota=200%','--property=RuntimeMaxSec=60','--property=KillMode=control-group','--property=TimeoutStopSec=2','--setenv=CUDA_VISIBLE_DEVICES='+cfg['gpu_uuid'],'/usr/bin/python3','-I',str(here/'control.py'),'--worker',str(out/'JOB.json')]
 try:
  r=c.cmd(launch);c.write(root/'LAUNCH.json',dict(argv=launch,stdout=r.stdout,stderr=r.stderr))
  while True:
   q=c.cmd(['systemctl','--user','show',unit,'--property=ActiveState','--property=Result','--property=ExecMainStatus','--property=ControlGroup'])
   if any(x in q.stdout.splitlines() for x in ['ActiveState=inactive','ActiveState=failed']):break
   if time.monotonic()>=job['worker_deadline_mono']:raise RuntimeError('CPU bridge timeout')
   c.write(root/'LEASE.json',dict(run_id=job['run_id'],worker_id=wid,mono=time.monotonic(),GPU_safe=True),False);time.sleep(.3)
  c.write(root/'UNIT_EXIT.json',dict(stdout=q.stdout))
  if 'Result=success' not in q.stdout or 'ExecMainStatus=0' not in q.stdout or not (out/'CPU_RESULT.json').exists():raise RuntimeError('actual CPU bridge failed')
  b=Path('/sys/fs/cgroup')/cg.lstrip('/')
  if (b/'cgroup.procs').exists() and (b/'cgroup.procs').read_text().strip():raise RuntimeError('CPU process not released')
  c.write(root/'RESULT.json',dict(status='PASS_ACTUAL_KERNEL_PREEXEC_SEALED_CPU_ADMISSION',probe=json.loads((out/'CPU_RESULT.json').read_text()),owned_domain_empty=True,shared_GPU_used=False))
 finally:c.cmd(['systemctl','--user','stop',unit],False);os.close(fd)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args();main(a.config)
