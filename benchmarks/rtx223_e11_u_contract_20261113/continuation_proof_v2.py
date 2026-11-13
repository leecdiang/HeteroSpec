"""One explicitly rearmed idle-gated continuation; both prior native counts are0."""
from pathlib import Path
import json,importlib.util
HERE=Path(__file__).resolve().parent
def audit(events,attempt1,native,contract_sha):
 def need(c,s):
  if not c:raise RuntimeError(s)
 need(events[-1]['kind']=='CONTINUATION_STOPPED' and events[-1]['total_reserved']==430,'second controller must be closed430')
 need(not any(x['kind'].startswith('IDLE_') for x in events),'idle continuation already attempted')
 idx=next(i for i,x in enumerate(events) if x['kind']=='STOPPED')
 sp=importlib.util.spec_from_file_location('original',HERE/'continuation_proof.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
 initial=m.audit(events[:idx+1],attempt1,native,contract_sha)
 need(sum(x.get('reserved',0) for x in events if x['kind']=='RESERVED_BEFORE_TASK')==430,'no refund or reset')
 claims=[x for x in events if x['kind']=='CONTINUATION_CLAIMED'];need(len(claims)==1 and claims[0]['existing_reservation']==416 and claims[0]['additional_reserved']==0,'prior continuation binding')
 rows=[json.loads(x)['event'] for x in Path('D:/HeteroSpec-PC/rtx223-e11-u-contract/timing-002/attempt.jsonl').read_bytes().splitlines()]
 need(rows[-1]['kind']=='FAIL' and rows[-1]['failure'].startswith('foreign compute context') and rows[-1]['owned_process_exit_confirmed'],'second failure retained')
 need(not any(x.get('kind') in ['OWNED_SUSPENDED','PERMIT'] for x in rows),'second native may have started')
 ends=[x for x in rows if x.get('kind')=='EXIT'];need(len(ends)==1 and ends[0]['code'] is None and ends[0]['confirmed'],'second native did not exist')
 initial.update(prior_timing_admission_failures=2,prior_timing_permits=0,new_reservation=0,read_only_idle_wait_max_seconds=90,continuous_idle_seconds=10,one_rearmed_attempt_only=True)
 return initial
