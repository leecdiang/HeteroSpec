"""Prospective v6 operation admission. Integer-ceiling concurrent-lifetime upper charges."""
import datetime,json,math
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def load(p):return json.loads(Path(p).read_bytes())
def snapshot(root,stage,next_bound=0,next_wall=0,next_starts=0):
 root=Path(root).resolve();p=load(root/'OPERATION_POLICY.json');c=load(root/'CAMPAIGN.json')
 need(stage in p['reserves'],'stage');reserved=p['reserves'][stage]
 life=starts=0;open_ops=[]
 for f in (root/'tools').glob('*.operation.json'):
  x=load(f);r=f.with_name(f.name.replace('.operation.json','.settled.json'))
  if r.exists():
   z=load(r);need(z['operation_sha256']==__import__('hashlib').sha256(f.read_bytes()).hexdigest(),'operation settlement binding')
   need(type(z['charged_process_seconds']) is int and 0<=z['charged_process_seconds']<=x['lifetime_bound_seconds'],'settlement envelope')
   from delivery_binding_v6 import capture
   events=[capture(root,x['id'],'initial')]
   polls=sorted((root/'tools').glob(x['id']+'.poll*.json'),key=lambda p:int(p.name.split('.poll')[1].split('.')[0]))
   events += [capture(root,x['id'],p.name.split('.')[1]) for p in polls]
   need(events[0]['request']==load(root/'tools'/(x['id']+'.intent.json'))['request'],'settlement actual request')
   sid=events[0]['response'].get('session_id');terminal=False
   for i,e in enumerate(events):
    need(not terminal,'settlement after terminal')
    if i:need(sid is not None and type(e['request'].get('session_id')) is int and e['request']['session_id']==sid,'settlement actual session')
    terminal=e['response'].get('exit_code') is not None
   need(terminal,'settlement no terminal response')
   elapsed=math.ceil((datetime.datetime.fromisoformat(events[-1]['observed_utc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(x['registered_utc'].replace('Z','+00:00'))).total_seconds())
   receipt=load(root/'operations'/x['id']/'RECEIPT.json')
   need(receipt['intent_sha256']==z['operation_sha256'] and receipt['job_empty'],'settlement native closure')
   need(z['charged_process_seconds']>=(x['max_job_processes']+2)*elapsed and z['charged_starts']==receipt['total_job_processes']+2,'settlement undercharge')
   need(type(receipt['total_job_processes']) is int and receipt['total_job_processes']>=0,'native total starts')
   # Closed operation upper bound uses every actual start for the entire captured interval.
   # Original settlements remain immutable evidence, not the cumulative budget source.
   life+=(receipt['total_job_processes']+2)*elapsed;starts+=z['charged_starts']
  else:life+=x['lifetime_bound_seconds'];starts+=x['starts_bound'];open_ops.append(x['id'])
 wall=math.ceil((datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(c['first_preparation_utc'].replace('Z','+00:00'))).total_seconds())
 need(wall>=0,'clock')
 for v in (next_bound,next_wall,next_starts):need(type(v) is int and v>=0,'integer ceiling required')
 need(life+next_bound+reserved['process_seconds']<=p['total_process_seconds'],'V6_PROTECTED_PROCESS_RESERVE')
 need(wall+next_wall+reserved['wall_seconds']<=p['total_wall_seconds'],'V6_PROTECTED_WALL_RESERVE')
 need(starts+next_starts+reserved['starts']<=p['starts_limit'],'V6_PROTECTED_START_RESERVE')
 return dict(charged_process_seconds=life,charged_starts=starts,wall_seconds=wall,reserved=reserved,open_operations=open_ops,scope='Conservative envelope accounting; exact observed identities separately retained; full OS ledger UNKNOWN')
