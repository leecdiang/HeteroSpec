"""Sequential GPU work; resume only completed immutable units, never retry a slot."""
from smol_verify import *

def done(name):
 p=SROOT/'units'/(EPOCH+'-'+name)/'SUPERVISOR.json'
 if not p.exists():return False
 assert read(p)['status']=='complete' and read(p)['cleanup_verified'],('incomplete attempt; retain and repair explicitly',name)
 folder=SROOT/EPOCH/'runs'/name
 assert (folder/'MODULE_AUDIT.json').exists(),('finish existing postprocessing explicitly',name)
 assert not list(folder.glob('*.json.states/*.bin')),('finish lossless storage first',name)
 return True

def qualify_root(group,index):
 prefix='dev' if group=='development' else 'test';r=input_row(group,index)
 q=SROOT/EPOCH/f'{prefix}-{index}-QUALIFICATION.json'
 if q.exists():assert read(q)['status']=='FINITE_NATIVE_CAPTURE_MATCH';return
 for arm in ARMS:
  name=f'{prefix}-{index}-{arm}-heavy'
  if not done(name):execute(name,arm,[r,dict(r,heavy_state=True)],heavy=True)
  name=f'{prefix}-{index}-{arm}-off'
  if not done(name):execute(name,arm,[r,dict(r,audit_final=True)])
 if not done(f'{prefix}-{index}-oldR'):old_reference(group,index)
 path=SROOT/EPOCH/f'{prefix}-{index}-FORCED_PLAN.json'
 if not path.exists():plan(group,index)
 for j,job in enumerate(read(path)['independent_token_only_jobs']):
  name=f'{prefix}-{index}-forced-{j}'
  if not done(name):execute(name,'M',[job],heavy=True,forced=True)
 check(group,index)

def development_all():
 for i in range(4):qualify_root('development',i)

if __name__=='__main__':
 started=utc();t0=time.monotonic();success=False
 try:
  if sys.argv[1]=='development':development_all()
  else:qualify_root(sys.argv[1],int(sys.argv[2]))
  success=True
 finally:
  write(SROOT/EPOCH/('COORDINATOR-'+started.replace(':','').replace('.','')+'.json'),dict(started_utc=started,finished_utc=utc(),wall_seconds=time.monotonic()-t0,success=success,includes_child_native=True,additive_to_native_cost=False))
