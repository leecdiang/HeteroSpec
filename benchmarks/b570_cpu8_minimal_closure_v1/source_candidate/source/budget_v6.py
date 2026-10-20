"""Prospective v6 operation admission. Integer-ceiling concurrent-lifetime upper charges."""
import datetime,json,math
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def load(p):return json.loads(Path(p).read_bytes())

def captured_interval(operation,events):
 """Validate failed and successful tool chains alike before any lifetime charge."""
 from delivery_binding_v6 import utc
 need(events,'missing captured interval')
 origin=previous=utc(operation['registered_utc'])
 sid=events[0]['response'].get('session_id');terminal=False
 need(sid is None or (type(sid) is int and sid>0),'settlement session type')
 for i,e in enumerate(events):
  need(not terminal,'settlement after terminal')
  observed=utc(e['observed_utc']);need(previous<=observed,'settlement capture clock');previous=observed
  if i:need(sid is not None and type(e['request'].get('session_id')) is int and e['request']['session_id']==sid,'settlement actual session')
  response=e['response'];returned=response.get('session_id')
  need(returned is None or (type(returned) is int and returned==sid),'settlement changed session')
  code=response.get('exit_code');need(code is None or type(code) is int,'settlement terminal type')
  terminal=code is not None
 need(terminal,'settlement no terminal response')
 return math.ceil((previous-origin).total_seconds())

def snapshot(root,stage,next_bound=0,next_wall=0,next_starts=0):
 root=Path(root).resolve();p=load(root/'OPERATION_POLICY.json');c=load(root/'CAMPAIGN.json')
 need(stage in p['reserves'],'stage');reserved=p['reserves'][stage]
 task_uuid=c.get('task_uuid')
 need(type(task_uuid) is str and task_uuid,'current task UUID required')
 from operation_pricing_v7 import envelope
 life=starts=0;open_ops=[]
 for f in (root/'tools').glob('*.operation.json'):
  x=load(f)
  need(type(x) is dict and type(x.get('id')) is str and x['id']+'.operation.json'==f.name,
       'actual operation filename/id mismatch')
  need(x.get('task_uuid')==task_uuid and x.get('stage') in ('B','C'),
       'foreign task operation must not affect current budget')
  if stage in ('B','C'):
   need(x['stage']==stage,'wrong phase operation in current task')
  # Reject any unknown or underquoted open operation BEFORE it can decrease
  # cumulative balance. The quote is conditional, not provider hard proof.
  quote=envelope(x)
  need(type(x.get('lifetime_bound_seconds')) is int and
       x['lifetime_bound_seconds']==quote['max_process_seconds'] and
       type(x.get('starts_bound')) is int and
       x['starts_bound']==quote['owned_job_starts_limit']+quote['owned_outer_starts_limit'],
       'unpriced operation in protected ledger')
  r=f.with_name(f.name.replace('.operation.json','.settled.json'))
  if r.exists():
   z=load(r);need(z['operation_sha256']==__import__('hashlib').sha256(f.read_bytes()).hexdigest(),'operation settlement binding')
   need(type(z['charged_process_seconds']) is int and 0<=z['charged_process_seconds']<=x['lifetime_bound_seconds'],'settlement envelope')
   from delivery_binding_v6 import capture
   events=[capture(root,x['id'],'initial')]
   polls=sorted((root/'tools').glob(x['id']+'.poll*.json'),key=lambda p:int(p.name.split('.poll')[1].split('.')[0]))
   events += [capture(root,x['id'],p.name.split('.')[1]) for p in polls]
   need(events[0]['request']==load(root/'tools'/(x['id']+'.intent.json'))['request'],'settlement actual request')
   elapsed=captured_interval(x,events)
   receipt=load(root/'operations'/x['id']/'RECEIPT.json')
   need(receipt['intent_sha256']==z['operation_sha256'] and receipt['job_empty'],'settlement native closure')
   need(type(receipt.get('begin_ns')) is int and type(receipt.get('end_ns')) is int and
        0<=receipt['begin_ns']<=receipt['end_ns'], 'native monotonic interval missing')
   elapsed=max(elapsed,math.ceil((receipt['end_ns']-receipt['begin_ns'])/1_000_000_000))
   from operation_pricing_v7 import envelope
   quote=envelope(x)
   need(type(receipt['total_job_processes']) is int and
        0<=receipt['total_job_processes']<=quote['owned_job_starts_limit'],'native actual starts exceed quote')
   actual_starts=receipt['total_job_processes']+quote['owned_outer_starts_limit']
   charge=actual_starts*elapsed+quote['provider_lifetime_reserve_seconds']
   need(z['charged_process_seconds']>=charge and z['charged_starts']==actual_starts and
        charge<=x['lifetime_bound_seconds'],'settlement undercharge or envelope overrun')
   # Distinct observed + outside charging; no unexplained +2 or zero-cost provider.
   # A larger saved conservative settlement must never reduce later cumulative billing.
   life+=max(charge,z['charged_process_seconds']);starts+=actual_starts
  else:life+=x['lifetime_bound_seconds'];starts+=x['starts_bound'];open_ops.append(x['id'])
 wall=math.ceil((datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(c['first_preparation_utc'].replace('Z','+00:00'))).total_seconds())
 need(wall>=0,'clock')
 for v in (next_bound,next_wall,next_starts):need(type(v) is int and v>=0,'integer ceiling required')
 need(life+next_bound+reserved['process_seconds']<=p['total_process_seconds'],'V6_PROTECTED_PROCESS_RESERVE')
 need(wall+next_wall+reserved['wall_seconds']<=p['total_wall_seconds'],'V6_PROTECTED_WALL_RESERVE')
 need(starts+next_starts+reserved['starts']<=p['starts_limit'],'V6_PROTECTED_START_RESERVE')
 return dict(charged_process_seconds=life,charged_starts=starts,wall_seconds=wall,reserved=reserved,open_operations=open_ops,scope='Conservative envelope accounting; exact observed identities separately retained; full OS ledger UNKNOWN')
