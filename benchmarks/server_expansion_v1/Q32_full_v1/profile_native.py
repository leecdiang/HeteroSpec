"""Bounded own-process CUDA trace; diagnostic only, never a timing panel.

Reuse the complete host SHA, allocation, lock, budget and two-second resource
checks. The only launch adapter prefixes Nsight to the unchanged executable.
No CPU sampling, system-wide tracing, GPU metrics, or foreign process attach.
"""
from pathlib import Path
import argparse,copy,fcntl,json,os,subprocess,sys,time,traceback

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--attempt',choices=['01','02'],required=True);a=p.parse_args();r,w=a.root,a.work
 sys.path.insert(0,str(r/'q32-q4-full-source-10'));from build import read,sha,save
 out=w/('diagnostic-'+a.attempt);out.mkdir(exist_ok=True);assert not list(out.iterdir()),'Fresh diagnostic; no native retry'
 # Wait for the active qualification request and all comparisons to return.
 while not(w/'PIPELINE_COORDINATOR_CLOSED06.private.json').exists():time.sleep(2)
 sys.path.insert(0,str(w/'runtime-04'));import host
 cfg=read(w/'config-reference-frozen.private.json');cfg['worker_timeout_s']=360;save(out/'config.private.json',cfg)
 original=read(w/'qualification-06/jobs/geometry-W_REF1L_M-0.json');job=copy.deepcopy(original);job.pop('cases')
 prompt=original['cases'][0]['forced'][0]['ids'];x=dict(id='owned-short-diagnostic-p31-cap1',prompt_ids=prompt,cap=1)
 job['inputs']=[dict(name=name,input=x,capture=heavy)for name,heavy in [('H0',True),('C0',False),('C1',False),('H1',True)]]
 save(out/'job.json',job);build=r/'q32-q4-full-build-09/loop4/BUILD.json';exe=read(build)['executable']
 prefix=['/usr/local/bin/nsys','profile','--trace=cuda','--sample=none','--cpuctxsw=none','--cuda-memory-usage=false','--force-overwrite=false','--export=sqlite','--duration=300','--kill=sigterm','--output='+str(out/'own-cuda')]
 real_popen=subprocess.Popen
 original_check=host.check_resources
 def traced_resources(config,group=None):
  if group is None:return original_check(config,group)
  # Nsight starts its app in a distinct process group. Accept only our exact
  # native argv/UID/executable when it is a proven descendant of this launcher.
  # All other GPU processes still go through the unchanged conflict rejection.
  native_groups=set()
  for proc in host.processes(config['gpu_uuid']):
   pid=proc['pid'];p=Path('/proc')/str(pid)
   try:
    argv=(p/'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
    expected=[os.fsencode(exe),os.fsencode(out/'job.json'),os.fsencode(out/'run/native')]
    if argv!=expected:continue
    assert p.stat().st_uid==os.getuid()and sha(p/'exe')==read(build)['executable_sha256']
    ancestor=pid;seen=set()
    while ancestor!=group and ancestor>1:
     assert ancestor not in seen;seen.add(ancestor)
     raw=Path(f'/proc/{ancestor}/stat').read_text();ancestor=int(raw[raw.rfind(')')+2:].split()[1])
    assert ancestor==group,'Only the launched profiler native descendant'
    native_groups.add(os.getpgid(pid))
   except FileNotFoundError:continue
  assert len(native_groups)<=1,'One native diagnostic process only'
  return original_check(config,next(iter(native_groups))if native_groups else group)
 def traced(argv,*args,**kwargs):
  if isinstance(argv,list)and argv and argv[0]==exe:
   sampler=r/'q32-q4-full-source-10/sample-own-cpu.so';assert sampler.is_file()
   save(out/'TRACE_LAUNCH.json',dict(argv=prefix+argv,executable_sha256=sha(exe),nsys_sha256=sha(Path('/usr/local/bin/nsys').resolve()),sampler_sha256=sha(sampler),purpose='Locate native host/CUDA time; profiler results cannot enter qualification or clean panel',system_wide=False,perf_sampling=False,own_instruction_sampling='10ms SIGPROF, signal-context RIP only, no unwind',foreign_attach=False))
   # Apply the diagnostic sampler to the native child only. Nsight itself and
   # its helper processes do not receive this library or its output path.
   argv=prefix+['env','LD_PRELOAD='+str(sampler),'Q32_OWN_SAMPLE_DIRECTORY='+str(out),*argv]
  return real_popen(argv,*args,**kwargs)
 host.subprocess.Popen=traced
 host.check_resources=traced_resources
 try:
  with(r/'STUDY_SCHEDULING.lock').open('a+')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   host.run(out/'config.private.json',build,out/'job.json',out/'run','development')
  save(out/'COMPLETE.json',dict(passed=True,epoch=time.time(),scope='Diagnostic collection complete; no performance or numerical eligibility inferred'))
 except BaseException as e:
  save(out/'FAILURE.json',dict(error=str(e),traceback=traceback.format_exc(),epoch=time.time(),no_automatic_native_retry=True));raise
 finally:host.subprocess.Popen=real_popen;host.check_resources=original_check
if __name__=='__main__':main()
