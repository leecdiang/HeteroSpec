"""Bounded read-only NVML/cgroup/ledger observer; no model/backend import."""
import json,os,subprocess,sys,time
from pathlib import Path
root=Path(sys.argv[1]);unit=sys.argv[2];gpu=sys.argv[3]
cg=Path('/sys/fs/cgroup/user.slice/user-'+str(os.getuid())+'.slice/user@'+str(os.getuid())+'.service/app.slice')/unit
with (root/'RESOURCE_TRACE.jsonl').open('x') as out:
 for i in range(1500):
  item=dict(wall=time.time(),mono=time.monotonic())
  try:item['state']=json.loads((root/'STATE.json').read_text())
  except (FileNotFoundError,json.JSONDecodeError):item['state']=None
  for name in ('memory.current','memory.peak','pids.current','memory.events'):
   try:item[name]=(cg/name).read_text()
   except FileNotFoundError:item[name]=None
  q=subprocess.run(['nvidia-smi','--query-gpu=uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5)
  item['GPU']=next((x for x in q.stdout.splitlines() if x.startswith(gpu)),None)
  raw=json.dumps(item,separators=(',',':'))+'\n'
  if out.tell()+len(raw.encode())>8*1024*1024:raise RuntimeError('observer log cap')
  out.write(raw);out.flush();os.fsync(out.fileno())
  if not cg.exists():break
  time.sleep(.5)
