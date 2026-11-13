"""Read-only waiting occurs before any numerical worker or GPU attempt."""
from pathlib import Path
import ctypes as C,json,subprocess,time,os
def wait(root,ob,emit,end,stop_path):
 row=json.loads((root/'DEPLOYMENT.json').read_bytes())['modules']['nvml.dll'];m=ob.Management(row['path']);started=time.monotonic();quiet=None
 try:
  m.start()
  while time.monotonic()-started<90 and time.time()+120<end and not stop_path.exists():
   total,free,used,disk,pids=m.sample(root);util=m.utilization()
   cp=subprocess.run(['C:/Program Files/PowerShell/7/pwsh.exe','-NoProfile','-NonInteractive','-Command',"$p=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -ieq 'ToDesk.exe'} | Select-Object ProcessId,CommandLine); ConvertTo-Json -InputObject $p -Compress"],capture_output=True,text=True,timeout=8,creationflags=0x08000000)
   if cp.returncode:raise RuntimeError('cannot verify video-session inventory')
   rows=json.loads(cp.stdout);videos=[x['ProcessId'] for x in rows if not x.get('CommandLine') or '--isVideoSession=true' in x['CommandLine']]
   eligible=not pids and not videos and util<=5 and free>=10*1024**3 and disk>=20*1024**3 and not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
   if eligible:
    if quiet is None:quiet=time.monotonic()
   else:quiet=None
   seconds=0 if quiet is None else time.monotonic()-quiet
   emit(kind='IDLE_READ_ONLY_SAMPLE',compute_pids=pids,video_pids=videos,GPU_utilization_percent=util,free_bytes=free,quiet_seconds=seconds,native_process_created=False)
   if seconds>=10:
    emit(kind='IDLE_WINDOW_CONFIRMED',continuous_quiet_seconds=seconds,additional_reserved=0);return
   time.sleep(1)
  raise RuntimeError('exclusive idle window not established;no native worker started')
 finally:m.close()
