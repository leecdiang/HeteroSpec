"""Independent F0 semantic audit. CPU-only; never relaxes the frozen contract."""
import json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from protocol import read_json,file_sha,write_new

def evaluate(f0,rows):
 universal_100ms='every100ms during requests' in f0['safety_sampling']
 violations=[dict(slot=x['slot'],task=x['task'],arm=x['arm'],actual_requested_period_ms=x['requested_period_ms'],observed_max_gap_ms=x['max_observed_gap_ms'],scope='F0 universal100ms declaration vs original runtime checkpoint-only receipt') for x in rows if universal_100ms and x['arm']=='R' and x['requested_period_ms']!=100]
 return dict(status='VIOLATION_REQUIRES_STOP' if violations else 'NO_CADENCE_VIOLATION_IN_SUPPLIED_RECEIPTS',violations=violations,declared_sampling=f0['safety_sampling'],not_a_residency_or_memory_sufficiency_certificate=True)
def main():
 plan=read_json(ROOT/'p0/PLAN_P1.json');rows=[]
 for s in plan['slots']:
  p=ROOT/'_host/run'/s['slot']/(s['slot']+('.trace.json' if s['mode']=='diagnostic' else '.memory.json'))
  if not p.exists():continue
  x=read_json(p);m=x['memory'] if s['mode']=='diagnostic' else x
  rows.append(dict(slot=s['slot'],task=s['task'],arm=s['arm'],mode=s['mode'],requested_period_ms=m['requested_period_ms'],max_observed_gap_ms=m['max_observed_gap_ms'],samples=len(m['samples']),raw_path=str(p.relative_to(ROOT)),raw_sha256=file_sha(p)))
 result=evaluate(read_json(ROOT/'p0/F0_EXECUTION.json'),rows);result.update(F0_sha256=file_sha(ROOT/'p0/F0_EXECUTION.json'),receipts=rows,original_R_source_sha256=file_sha(ROOT/'_host/pr97/baseline/pr92_restore/native/worker.cpp'),source_semantics='Original Memory.start enables periodic sampling only for heavy(); all registered originalR slots use counts. Original R must not be rebuilt or silently treated as100ms.',stop_action='Only owned active PID12836 terminated with verified frozen image path; exit99. No retries or remaining-slot continuation.',past_records='Raw endpoints/work/identity retained as exploratory evidence with execution-contract limitation; not a compliant complete P1.',repair_policy='No retroactive F0 edits, safety relaxation, reference replacement, or scientific retries. Any future experiment requires its own prospectively accurate F0 and author budget confirmation.')
 write_new(ROOT/'p1/EXECUTION_CONTRACT_AUDIT.json',result);print(json.dumps(dict(status=result['status'],violations=len(result['violations']),F0=result['F0_sha256'])))
if __name__=='__main__':main()
