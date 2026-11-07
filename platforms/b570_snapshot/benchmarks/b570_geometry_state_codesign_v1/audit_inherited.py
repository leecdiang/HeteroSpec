"""Independent CPU reconstruction from restored PR92 raw, not executor conclusions.
Historical observations remain historical; this does not execute or qualify any PR108 slot.
"""
import collections,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent;BASE=ROOT/'_host/pr97/baseline/pr92_restore'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 rows=load(BASE/'FORMAL_RECORDS.json');inputs={c['id']:c for c in load(BASE/'CONFIRMATION_INPUTS.json')['families']['Llama']};checks=0;ends={};counts=collections.Counter();forwards=collections.Counter()
 for row in rows:
  p=BASE/row['raw_path'];assert sha(p)==row['raw_evidence_sha256'];r=load(p);c=inputs[row['task']];w=r['workload'];ids=r['ids'];flags=r['eog']
  assert r['prompt_ids']==c['prompt_ids'];assert r['pid']==row['worker_pid'];assert len(ids)==r['length']==len(flags) and r['terminal_id']==ids[-1]
  assert flags==[i in {128001,128008,128009} for i in ids] and not any(flags[:-1]);assert r['stop_reason']==('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(ids)==128)
  assert ids==row['output']['ids'] and flags==row['output']['eog_flags'];assert w['output_ids_count']==len(ids)==sum(w[k] for k in ['initial_target_committed','accepted_committed','bonus_committed','correction_committed','fallback_committed'])
  assert w['proposal_generated']==sum(w[k] for k in ['accepted_committed','first_mismatch_rejected','unexamined_after_mismatch','terminal_discarded','unverified_before_verify'])
  for role in ('target','draft'):
   h=w[role+'_physical_width_hist'];assert sum(h.values())==w[role+'_micrographs'] and sum(int(k)*v for k,v in h.items())==w[role+'_micrograph_rows'];checks+=2
  assert w['target_verification_rows']==w['proposal_verified']+w['verification_seed_rows'];assert w['target_micrograph_rows']==len(c['prompt_ids'])+w['target_verification_rows']+w['target_ordinary_rows']
  assert math.isfinite(r['native_request_ms']) and r['native_request_ms']>0 and not any(r['observation'].values())
  assert r['actual_condition']['output_capacity']==(1 if row['condition'].startswith('R_') else 4)
  ends.setdefault((row['condition'],row['task']),set()).add(json.dumps([ids,flags,r['stop_reason']],separators=(',',':')));counts[row['condition']]+=1;forwards[row['condition']]+=r['target_decode_calls']+r['draft_decode_calls'];checks+=13
 assert len(rows)==1200 and all(len(v)==1 for (arm,task),v in ends.items() if arm=='R_stock')
 result=dict(status='PASS_INDEPENDENT_HISTORICAL_RAW_RECONSTRUCTION',scope='Original PR92 raw only; no new PR108 experimental qualification',historical_records=len(rows),checks=checks,historical_requests_by_arm=dict(counts),historical_forward_callers_by_arm=dict(forwards),original_R_stable_on_all_24_tasks=True,new_PR108_native_starts=0,original_R_binary_sha256=sha(BASE/'build/Release/b570-evidence-worker.exe'),original_reference_timer_source='native/worker.cpp start before reset through native end synchronization and memory stop; native_request_ms',original_reference_prefill_source='single caller up to512 with final-only logits; physical internal ub128; capacity1')
 (ROOT/'p0/INHERITED_RAW_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
