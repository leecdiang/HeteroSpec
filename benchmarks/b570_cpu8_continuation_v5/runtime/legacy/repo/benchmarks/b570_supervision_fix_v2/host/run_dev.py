"""Prepare a registered bounded attempt, then use the real compiled PS launcher."""
import subprocess,sys
from common import HERE,BASE,need,load,now,write_new
args=sys.argv[1:];name=args[args.index('--id')+1]
prepared=subprocess.run([sys.executable,'-B',str(HERE/'prepare_round.py'),*args],capture_output=True)
for stream,b in (('prepare.stdout',prepared.stdout),('prepare.stderr',prepared.stderr)):
    with (BASE/'task'/(name+'.'+stream+'.log')).open('xb') as f:f.write(b)
need(prepared.returncode==0,'prospective preparation failed; retained stderr')
config=BASE/'runs'/name/'CONFIG.json'
ps='C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
launch=[ps,'-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(HERE/'launch.ps1'),'-CasePath',str(config)]
begin=now();p=subprocess.run(launch,capture_output=True,timeout=210)
for stream,b in (('launch.stdout',p.stdout),('launch.stderr',p.stderr)):
    with (BASE/'task'/(name+'.'+stream+'.log')).open('xb') as f:f.write(b)
write_new(BASE/'runs'/name/'LAUNCH_RECEIPT.json',dict(argv=launch,begin_ns=begin,end_ns=now(),exit_code=p.returncode))
print('attempt',name,'launcher_exit',p.returncode,'raw retained; independent auditor decides case qualification')
raise SystemExit(p.returncode)
