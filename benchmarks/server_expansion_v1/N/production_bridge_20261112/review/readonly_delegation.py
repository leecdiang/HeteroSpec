"""Read delegated user-manager cgroup capability. Never creates/mutates groups."""
import datetime,json,os,pathlib,stat,subprocess
uid=os.geteuid();base=pathlib.Path('/sys/fs/cgroup/user.slice')/('user-%s.slice'%uid)/('user@%s.service'%uid)
result={'schema':'hs.N1controller.cgroup-delegation-readonly.v1','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mutations':0,'enforcement_tested':False,'groups':[]}
q=subprocess.run(['systemctl','show','user@%s.service'%uid,'--property=ControlGroup','--property=Delegate','--property=MemoryAccounting','--property=MemoryMax'],capture_output=True,text=True,timeout=10)
result['manager_unit']={'returncode':q.returncode,'stdout':q.stdout,'stderr':q.stderr}
if base.is_dir():
 for p in [base]+sorted([x for x in base.iterdir() if x.is_dir()]):
  s=p.stat();fields={}
  for n in ['cgroup.controllers','cgroup.subtree_control','cgroup.procs','memory.max','memory.current','pids.max']:
   f=p/n
   if f.exists():fields[n]={'value':f.read_text(),'writable':os.access(f,os.W_OK)}
  result['groups'].append({'relative':str(p.relative_to('/sys/fs/cgroup')),'owned_by_euid':s.st_uid==uid,'mode':oct(stat.S_IMODE(s.st_mode)),'writable':os.access(p,os.W_OK),'fields':fields})
print(json.dumps(result,indent=2))
