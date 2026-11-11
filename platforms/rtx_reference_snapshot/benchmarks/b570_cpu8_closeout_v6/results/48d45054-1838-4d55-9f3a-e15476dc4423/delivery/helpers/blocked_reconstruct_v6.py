"""Stopped-prefix raw reconstruction only. No live admission, process creation or native loads."""
import sys,json,hashlib,math,datetime
from pathlib import Path
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def rows(p):
 b=Path(p).read_bytes();parts=b.split(b'\n')
 rs=[json.loads(x) for x in parts[:-1] if x]
 need(all(x['seq']==i+1 for i,x in enumerate(rs)),'raw event sequence')
 return rs,dict(bytes=len(parts[-1]),sha256=hashlib.sha256(parts[-1]).hexdigest()) if parts[-1] else None
def audit(root):
 root=Path(root).resolve();sys.path[:0]=[str(root/'source'),str(root/'src/rev2')]
 context=load(root/'STOP_CONTEXT.json');need(context['status']=='ENGINEERING_BLOCKED','blocked context')
 need(not (root/'CAPABILITY_FREEZE.json').exists() and not (root/'source/FINAL_REVIEW_BINDING.json').exists(),'no new execution qualification')
 plan=load(root/'CPU8_PLAN.json');need(len(plan['cases'])==8,'eight-case plan')
 for c in plan['cases']:need(not (root/'legacy/runs'/c['run_id']).exists(),'formal case started')
 source=load(root/'delivery/CLOSEOUT_SOURCE_MANIFEST.json')
 for row in source['files']:need(sha(root/row['path'])==row['sha256'],'closeout source drift')
 known={};closed={};partial=[];operations=[];cost=0;total_starts=0
 for f in sorted((root/'processes').glob('*/OS_EVENTS.jsonl')):
  rs,tail=rows(f)
  if tail:partial.append(dict(path=f.relative_to(root).as_posix(),**tail))
  for x in rs:
   if x['event']=='PROCESS_CREATE':known[(x['pid'],x['created_filetime'])]=x
   if x['event']=='PROCESS_CLOSED':
    k=(x['pid'],x['created_filetime']);need(int(x['exit_filetime'])>int(k[1]),'native descendant lifetime');closed[k]=x
 for f in sorted((root/'tools').glob('*.operation.json')):
  x=load(f);rc=load(root/'operations'/x['id']/'RECEIPT.json');rs,tail=rows(root/'operations'/x['id']/'EVENTS.jsonl')
  need(rc['job_empty'] and any(z['event']=='GUARD_END' and z['receipt']==rc for z in rs),'raw Job closure')
  need(rc['intent_sha256']==sha(f),'operation intent binding')
  cap=load(root/'tools'/(x['id']+'.initial.json'));need(cap['request']==load(root/'tools'/(x['id']+'.intent.json'))['request'],'actual initial request')
  caps=[cap]+[load(z) for z in sorted((root/'tools').glob(x['id']+'.poll*.json'),key=lambda q:int(q.name.split('.poll')[1].split('.')[0]))]
  sid=cap['response'].get('session_id');terminal=False
  for i,c in enumerate(caps):
   need(not terminal,'response after terminal')
   if i:need(sid is not None and c['request']['session_id']==sid,'actual session chain')
   terminal=c['response'].get('exit_code') is not None
  need(terminal,'actual tool terminal missing')
  elapsed=math.ceil((datetime.datetime.fromisoformat(caps[-1]['observed_utc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(x['registered_utc'].replace('Z','+00:00'))).total_seconds())
  need(elapsed>=0,'tool clock')
  charge=(rc['total_job_processes']+2)*elapsed;cost+=charge;total_starts+=rc['total_job_processes']
  starts=[z for z in rs if z['event']=='OP_CREATED_SUSPENDED'];ends=[z for z in rs if z['event']=='OP_TERMINAL_OS']
  need(len(starts)==1 and len(ends)<=1,'root evidence cardinality')
  if ends:need((starts[0]['pid'],starts[0]['created_filetime'])==(ends[0]['pid'],ends[0]['created_filetime']) and int(ends[0]['exit_filetime'])>int(ends[0]['created_filetime']),'actual operation root exit')
  operations.append(dict(id=x['id'],status=rc['status'],error=rc['error'],actual_job_starts=rc['total_job_processes'],declared_cap=x['max_job_processes'],observed_peak=rc['peak_job_processes'],cap_overrun=rc['peak_job_processes']>x['max_job_processes'],job_empty=rc['job_empty'],actual_root_exit=ends[0] if ends else None,missing_root_exit=not bool(ends),provider_exit=caps[-1]['response']['exit_code'],captured_seconds=elapsed,conservative_process_seconds=charge,raw_sha256=sha(root/'operations'/x['id']/'EVENTS.jsonl')))
 need(cost==3613 and total_starts==407,'at-prefix raw budget reconstruction')
 old,_=rows(root/'processes/full-review/OS_EVENTS.jsonl');orig=[z for z in old if z['event']=='PROCESS_CREATE']
 outer,_=rows(root/'operations/037-final-review/EVENTS.jsonl');observer=next(z for z in outer if z['event']=='OP_CREATED_SUSPENDED')
 five=[observer]+orig;need(len({(z['pid'],z['created_filetime']) for z in five})==5,'five unique identities')
 probe,_=rows(root/'development/job-cap-diagnostic-01/probe.jsonl');old_checks=[z for z in probe if z['event']=='OLD_IDENTITY_CHECK']
 need(len(old_checks)==5 and all(z['status']=='PID_ABSENT' and z['winerror']==87 for z in old_checks),'old PID absence raw observation')
 six,_=rows(root/'operations/039-debug-startup-cap/RESOURCES.jsonl')
 trigger=next(z for z in six if len(z.get('job_pids',[]))==6)
 need(trigger['accounting']['active_limit']==4 and trigger['accounting']['active']==6 and all(z['live'] and z['exit_code']==259 for z in trigger['members']),'actual active six')
 e6,_=rows(root/'operations/039-debug-startup-cap/EVENTS.jsonl');ex6=[z for z in e6 if z['event']=='MEMBER_TERMINAL_OS']
 need({(z['pid'],z['created_filetime']) for z in ex6}=={(z['pid'],z['created_filetime']) for z in trigger['members']} and all(int(z['exit_filetime'])>int(z['created_filetime']) for z in ex6),'six actual OS exits')
 import native_gate_audit,integration_gates
 native=native_gate_audit.check(root)
 snap=root/'D0_EVIDENCE_SNAPSHOT';m=load(snap/'EXPECTED.json')['manifest_relative']
 d0=integration_gates.d0_reconstruct(root,dict(d0_snapshot='D0_EVIDENCE_SNAPSHOT',d0_manifest=m,d0_manifest_sha256=sha(snap/'legacy'/m),d0_expected_sha256=sha(snap/'EXPECTED.json')))
 missing=[dict(pid=k[0],created_filetime=k[1],exit_filetime=None) for k in sorted(set(known)-set(closed))]
 return dict(status='RECONSTRUCTION_ONLY',campaign_status='ENGINEERING_BLOCKED',uuid=context['uuid'],formal_qualified=0,formal_started=0,formal=[dict(case_id=c['id'],status='UNSTARTED') for c in plan['cases']],final_full_review=False,execution_frozen=False,operations=operations,native_development_gates=native,d0_original_raw_reconstruction=d0,five_review_identities=[dict(image=z['image'],pid=z['pid'],created_filetime=z['created_filetime'],parent_pid=z['parent_pid']) for z in five],old_five_pid_absence=old_checks,six_active_trigger=trigger,six_os_exits=ex6,at_prefix_budget=dict(conservative_process_seconds=cost,actual_job_starts=total_starts,outside_root_charge_units=2*len(operations),formal_process_reserve=13600,delivery_process_reserve=3600,development_remaining=787),known_descendants=len(known),retained_descendant_exit_filetimes=len(closed),missing_descendant_exits=missing,partial_journals=partial,whole_task_OS_ledger='UNKNOWN',guard_shell_provider_OS_lifecycles='UNKNOWN',forbidden_counts=context['forbidden_counts'],closeout_source_manifest_sha256=sha(root/'delivery/CLOSEOUT_SOURCE_MANIFEST.json'),scope='Read-only stopped-prefix reconstruction. No Windows acceptance or live PASS. Tail delivery costs are separate.')
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 root=Path(a.root).resolve();out=Path(a.output).resolve();need(root not in out.parents,'external report')
 b=(json.dumps(audit(root),sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 with out.open('xb') as f:f.write(b)
 sys.stdout.buffer.write(b);sys.stdout.buffer.flush()
if __name__=='__main__':main()
