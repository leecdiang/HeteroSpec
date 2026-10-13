"""Prospectively sealed continuation of UNSTARTED registered slots only.
Original actor/common/controller/numerical code and request plan remain immutable.
Never replays a completed or failed start, and never enables another API dump.
"""
from controller96 import *
def main():
 amendment=load(ROOT/'REMAINING_EXECUTION.json');auth=load(ROOT/'REMAINING_AUTHENTICATED.json')
 assert auth['status']=='PASS_ACTUAL_AUTHENTICATED_GITHUB_BYTES' and auth['before_remaining_forward']
 assert sha(Path(__file__))==amendment['helper_sha256']
 assert auth['amendment_sha256']==sha(ROOT/'REMAINING_EXECUTION.json')
 source_gate()
 rr=rows();started={r['slot'] for r in rr if r['event']=='REQUEST_STARTED'}
 failed=[r['slot'] for r in rr if r['event']=='REQUEST_FAILED']
 assert len(started)==85 and failed==['P2/s0/C512|GSM8K/test/1248']
 assert not (ROOT/'REMAINING_STARTED.json').exists()
 assert load(ROOT/'raw/p2_s0_p2_C512_dispatch/WATCHDOG_STOP.json')['only_owned_pid']==24252
 assert load(ROOT/'raw/p2_s0_p2_C512_dispatch/LIFECYCLE.json')['returncode']==1
 remaining=[s['slot'] for b in PLAN['blocks'] for s in b['slots'] if s['slot'] not in started]
 assert remaining==amendment['remaining_slots'] and len(remaining)==23
 records=load(ROOT/'STUDY_RECORDS_PARTIAL.json');assert len(records)==84
 save(ROOT/'REMAINING_STARTED.json',dict(utc=now(),pid=os.getpid(),amendment_commit=auth['commit'],remaining_slots=remaining))
 event(event='UNSTARTED_ONLY_CONTINUATION',amendment_commit=auth['commit'],failed_slot_not_replayed=failed[0],remaining=23)
 try:
  for block in PLAN['blocks']:
   slots=[s for s in block['slots'] if s['slot'] not in started]
   if not slots:continue
   assert not block['api_dump'] and slots==block['slots'],'No observer change or partial block replay'
   with Worker(block) as w:
    for s in slots:
     records.append(w.request(s['slot'],CASES[s['task']]))
     save(ROOT/'PROGRESS.json',dict(status='RUNNING_UNSTARTED_ONLY',completed=len(records),failed=1,planned=108,last_slot=s['slot'],phase='P2',utc=now()))
   save(ROOT/'STUDY_RECORDS.json',records)
  assert len(records)==107
  save(ROOT/'STUDY_COMPLETION.json',dict(status='CLOSED_WITH_FAILED_DIAGNOSTIC',requests_started=108,requests_completed=107,requests_failed=1,failed_slots=failed,unexecuted_slots=[],zero_forward_load_probes=2,warmups=0,fork_forwards=0,retries=0,owned_gpu_seconds=owned(),utc=now(),amendment_commit=auth['commit']))
  print('ALL_REGISTERED_SLOTS_CLOSED',107,'completed',1,'failed; no replay',flush=True)
 except BaseException as e:
  save(ROOT/'STUDY_RECORDS_PARTIAL_2.json',records)
  save(ROOT/'STUDY_COMPLETION.json',dict(status='STOPPED_NO_REPLAY_SECOND_SCOPE',requests_started=sum(r['event']=='REQUEST_STARTED' for r in rows()),requests_completed=len(records),error=str(e),owned_gpu_seconds=owned(),utc=now()))
  raise
if __name__=='__main__':main()
