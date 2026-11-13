"""Observe only: pause admission on actual conflict, reserves or interference.

No CUDA context, process signals or changes to any foreign task. PID arguments
are used in memory to identify this study and are never logged. Five-second
sampling cannot exclude all interference; existing-service requests and short
events can be missed. Host admission separately checks every two seconds.
"""
from pathlib import Path
import argparse,json,os,subprocess,time,traceback
def write(p,x):
 tmp=Path(str(p)+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');os.replace(tmp,p)
def processes():
 rows={}
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   raw=(p/'stat').read_text();s=raw[raw.rfind(')')+2:].split();args=(p/'cmdline').read_bytes()
   rows[int(p.name)]=dict(own=b'q32-q4-full' in args,parent=int(s[1]),name=(p/'comm').read_text().strip())
  except (OSError,ValueError):pass
 for _ in range(4):
  for p in rows.values():p['own']=p['own']or rows.get(p['parent'],{}).get('own',False)
 ticks={}
 for pid,p in rows.items():
  if p['own']:continue
  try:
   for task in Path(f'/proc/{pid}/task').iterdir():
    raw=(task/'stat').read_text();s=raw[raw.rfind(')')+2:].split()
    ticks[(pid,int(task.name))]=dict(ticks=int(s[11])+int(s[12]),cpu=int(s[36]),name=p['name'])
  except (OSError,ValueError):pass
 return rows,ticks
def main():
 a=argparse.ArgumentParser();a.add_argument('--work',type=Path,required=True);x=a.parse_args();w=x.work
 cfg=json.loads((w/'config.private.json').read_text());boot=Path('/proc/sys/kernel/random/boot_id').read_text();hz=os.sysconf('SC_CLK_TCK');previous={};last=time.monotonic();hot=0
 write(w/'GUARD_BASELINE.private.json',dict(boot=boot.strip(),started=time.time(),policy='Only allocated-GPU conflict, reserve violation, reboot or measured CPU interference pauses; other-GPU jobs alone do not pause'))
 try:
  while not (w/'GUARD_DONE').exists():
   rows,ticks=processes();now=time.monotonic();foreign_cpu=0
   for key,p in ticks.items():
    old=previous.get(key)
    if old and p['cpu']in (32,33):foreign_cpu+=max(0,p['ticks']-old['ticks'])/hz/max(now-last,.001)
   hot=hot+1 if foreign_cpu>.25 else 0
   args=['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits']
   r=subprocess.run(args,capture_output=True,text=True,timeout=15,check=True);gpu=[];events=[]
   for line in r.stdout.splitlines():
    uuid,pid,memory=[s.strip()for s in line.split(',')];pid=int(pid);own=rows.get(pid,{}).get('own',False)
    gpu.append(dict(device=uuid,pid=pid,memory_MiB=memory,own=own,name=rows.get(pid,{}).get('name','unknown')))
    if uuid==cfg['gpu_uuid']and not own:events.append(dict(kind='allocated_GPU_conflict',pid=pid))
   mem={s.split(':')[0]:s.split(':')[1].strip()for s in Path('/proc/meminfo').read_text().splitlines()}
   if int(mem['MemAvailable'].split()[0])*1024<cfg['ram_reserve_bytes']:events.append(dict(kind='RAM_reserve'))
   st=os.statvfs(w)
   if st.f_bavail*st.f_frsize<cfg['disk_reserve_bytes']:events.append(dict(kind='disk_reserve'))
   if Path('/proc/sys/kernel/random/boot_id').read_text()!=boot:events.append(dict(kind='host_reboot'))
   if hot>=2:events.append(dict(kind='sustained_foreign_CPU_on_assigned_cores',cpu_equivalents=foreign_cpu))
   brief=dict(epoch=time.time(),gpu=gpu,foreign_cpu_on_assigned_cores=foreign_cpu,events=events)
   with (w/'RESOURCE_GUARD.private.jsonl').open('a')as f:f.write(json.dumps(brief)+'\n')
   write(w/'RESOURCE_GUARD_LATEST.private.json',brief)
   if events:write(w/'PAUSE.json',dict(status='PAUSED',events=events,automatic_resume=False));return
   previous=ticks;last=now;time.sleep(5)
  write(w/'GUARD_STOPPED.private.json',dict(status='CLOSED',epoch=time.time()))
 except BaseException as e:
  write(w/'PAUSE.json',dict(status='PAUSED',reason='Resource observation failed',error=str(e),automatic_resume=False));raise
if __name__=='__main__':main()
