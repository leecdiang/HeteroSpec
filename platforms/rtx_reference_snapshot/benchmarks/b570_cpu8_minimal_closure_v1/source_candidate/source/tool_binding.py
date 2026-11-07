"""Prospective guarded watchdog invocation, actual provider exports and OS evidence."""
import json,hashlib,sys
from pathlib import Path
from evidence_contract import need,member
def load(p):return json.loads(Path(p).read_bytes())
def norm(s):return str(s).replace('/',chr(92))
def check(root,run,freeze_sha,frozen,start,receipt,binding_path):
 root=Path(root);b=load(member(root,binding_path))
 from operation_roles_v7 import operation as current_operation
 from operation_pricing_v7 import envelope
 operation,op=current_operation(root,'C-formal-watchdog','C','formal_cpu8')
 need(b['operation_id']==operation,'actual formal role binding')
 argv=op['argv'];original=Path(load(root/'CAMPAIGN.json')['original_root'])
 plan_path=root/'CPU8_EXECUTION_ENVELOPE.json';plan=load(plan_path)
 need(plan.get('schema')=='B570_C_FROZEN_ENVELOPE_V1' and
      plan.get('task_uuid')==load(root/'CAMPAIGN.json').get('task_uuid') and
      frozen.get('cpu8_execution_envelope_sha256')==hashlib.sha256(plan_path.read_bytes()).hexdigest(),
      'immutable C operation plan')
 need(type(plan.get('phase_seconds')) is int and 0<plan['phase_seconds']<op['seconds'] and
      op['seconds']==plan['operation_seconds'] and
      op['max_job_processes']==plan['active_job_limit'], 'real current formal envelope')
 quoted=envelope(op) # source arithmetic does not certify provider hard boundary
 sys.path.insert(0,str(root/'src/rev2'));from verify import command_args
 need([norm(x) for x in argv]==[norm(x) for x in command_args(start['command'])],'actual watchdog command')
 need(hashlib.sha256(start['command'].encode()).hexdigest()==start['command_sha256'],'actual command digest')
 need(Path(argv[0])==Path(frozen['python'])==Path(start['image']),'actual interpreter')
 script=original/'source/outer_watchdog.py';indices=[i for i,x in enumerate(argv) if norm(x)==norm(script)]
 need(len(indices)==1 and argv[1:indices[0]]==['-I','-S','-B'],'actual isolated watchdog entry')
 tail=argv[indices[0]+1:];need(len(tail)%2==0,'watchdog argument pairs')
 pairs=list(zip(tail[::2],tail[1::2]));args=dict(pairs);need(len(args)==len(pairs),'duplicate watchdog option')
 keys={'--root','--run','--mode','--phase-limit','--freeze-sha256','--supervisor-script'}
 need(set(args)==keys and Path(args['--root'])==original and args['--run']==run and args['--mode']=='cpu8' and args['--freeze-sha256']==freeze_sha,'watchdog root/run/mode/freeze')
 need(args['--phase-limit']==str(plan['phase_seconds']) and Path(args['--supervisor-script'])==original/'source/cpu8_supervisor.py','watchdog phase/entry')
 need(receipt['watchdog_pid']==start['pid'] and receipt['outer_job_empty'] and receipt['owned_handles_closed'] and receipt['error'] is None,'watchdog receipt identity/closure')
 from delivery_binding_v6 import invocation
 actual=invocation(root,operation,argv,root/'operations'/operation/'stdout.log')
 need(actual['pid']==start['pid'] and actual['created_filetime']==start['created_filetime'],'guard/watchdog OS identity')
 ends=[]
 for line in (root/'operations'/operation/'stdout.log').read_text().splitlines():
  try:z=json.loads(line)
  except ValueError:continue
  if isinstance(z,dict) and 'watchdog_closed' in z:ends.append(z)
 need(ends==[dict(watchdog_closed=True,error=None,run=run)],'actual watchdog terminal output')
 return dict(status='TOOL_WATCHDOG_BOUND',run=run,watchdog_pid=start['pid'],actual=actual,quoted_budget=quoted,scope='Actual C guarded provider chain and native OS invocation; separate provider boundary authentication and full OS coverage still required')
