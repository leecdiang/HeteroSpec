"""Read-only post-P1 native reconstruction. Never starts or retries a native slot."""
import collections,hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from protocol import read_json,digest,file_sha,validate_plan,encode
from contracts import validate_record
from raw_audit import audit
PLAN=read_json(ROOT/'p0/PLAN_P1.json');RUNTIME=read_json(ROOT/'p0/RUNTIME.json');RUN=ROOT/'_host/run';OUT=ROOT/'p1'
def write(name,x):
 with (OUT/name).open('xb') as f:f.write(encode(x))
def endpoint(x):return {k:x[k] for k in ('ids','eog','length','terminal_id','stop_reason','cap')}
def main():
 validate_plan(PLAN);ledger=[json.loads(s) for s in (RUN/'LEDGER.jsonl').read_text().splitlines()];attempted={r['slot'] for r in ledger if r['event']=='PROCESS_ATTEMPT'};started={r['slot'] for r in ledger if r['event']=='REQUEST_START'}
 valid={};invalid=[];raw_results=[];witnesses=[];physical=collections.Counter();actual_forwards=0;native_seconds=0;charged_seconds=0;closed=set();minimum_headroom=None;maximum_sample_gap_ms=0;minimum_host_RAM=None;phase_records=[]
 for s in PLAN['slots']:
  d=RUN/s['slot'];p=d/'RESULT.json'
  if (d/'LIFECYCLE.json').exists():
   life=read_json(d/'LIFECYCLE.json');closed.add(s['slot']);charged_seconds+=life['owned_seconds'];native_seconds+=(life.get('native_process_times') or {}).get('native_owned_seconds',0)
  if not p.exists():continue
  result=read_json(p)
  memory_path=d/(s['slot']+('.trace.json' if s['mode']=='diagnostic' else '.memory.json'))
  if memory_path.exists():
   payload=read_json(memory_path);memory=payload['memory'] if s['mode']=='diagnostic' else payload
   for sample in memory['samples']:minimum_headroom=sample['device_local_headroom_bytes'] if minimum_headroom is None else min(minimum_headroom,sample['device_local_headroom_bytes'])
   maximum_sample_gap_ms=max(maximum_sample_gap_ms,memory['max_observed_gap_ms'])
  if (d/'SAFETY.jsonl').exists():
   for line in (d/'SAFETY.jsonl').read_text().splitlines():
    sample=json.loads(line);minimum_host_RAM=sample['available'] if minimum_host_RAM is None else min(minimum_host_RAM,sample['available'])
  if s['mode']=='diagnostic':phase_records.append(dict(slot=s['slot'],task=s['task'],arm=s['arm'],producer=s['request']['recipe']['producer'],initial_logits=result.get('initial108'),handoff=result.get('binding108'),logical_KV_identity_against_original_R='UNKNOWN'))
  row=dict(slot=s['slot'],task=s['task'],arm=s['arm'],session=s['session'],mode=s['mode'],raw_path=str(p.relative_to(ROOT)),raw_sha256=file_sha(p),endpoint=endpoint(result),native_request_ms=result['native_request_ms'],actual_condition=result['actual_condition'],target_decode_calls=result['target_decode_calls'],draft_decode_calls=result['draft_decode_calls']);raw_results.append(row)
  actual_forwards+=result['target_decode_calls']+result['draft_decode_calls'];physical['target_micrographs']+=result['workload']['target_micrographs'];physical['draft_micrographs']+=result['workload']['draft_micrographs'];physical['target_rows']+=result['workload']['target_micrograph_rows'];physical['draft_rows']+=result['workload']['draft_micrograph_rows']
  try:
   rebuilt=audit(d,s,RUNTIME);normalized=read_json(d/'NORMALIZED.json');validate_record(s,normalized,digest(RUNTIME),d)
   assert normalized['endpoint']==rebuilt['endpoint'] and normalized['request_wall_ms']==rebuilt['request_ms'];valid[s['slot']]=row
   for i,w in enumerate(rebuilt['verify_multirow_witnesses']):
    if i==0:witnesses.append(dict(slot=s['slot'],task=s['task'],arm=s['arm'],phase='VERIFY',trace_path=str((d/(s['slot']+'.trace.json')).relative_to(ROOT)),trace_sha256=file_sha(d/(s['slot']+'.trace.json')),runtime_sha256=digest(RUNTIME),native_worker_sha256=RUNTIME['roles'][s['request']['recipe']['runtime']]['sha256'],observed=w))
  except Exception as e:invalid.append(dict(slot=s['slot'],task=s['task'],arm=s['arm'],error=str(e),raw_result_preserved=True))
 assert closed==attempted,'An owned process remains unclosed'
 refs={};reference_stability={}
 for c in PLAN['panel']:
  slots=[s for s in PLAN['slots'] if s['arm']=='R' and s['task']==c['id']];v=[valid[s['slot']]['endpoint'] for s in slots if s['slot'] in valid];ok=len(v)==2 and v[0]==v[1];reference_stability[c['id']]=ok
  if ok:refs[c['id']]=v[0]
 arms={};counterexamples=[];observer_failures=[]
 for name in ('R_SHADOW',*[r['name'] for r in PLAN['recipes'] if r['name']!='R']):
  tasks=[]
  for c in PLAN['panel']:
   slots=[s for s in PLAN['slots'] if s['arm']==name and s['task']==c['id']];values={s['mode']:valid[s['slot']] for s in slots if s['slot'] in valid};complete=len(values)==2;equal=complete and values['counts']['endpoint']==values['diagnostic']['endpoint'];matches={mode:(row['endpoint']==refs[c['id']] if c['id'] in refs else None) for mode,row in values.items()}
   if complete and not equal:observer_failures.append(dict(arm=name,task=c['id']))
   for mode,ok in matches.items():
    if ok is False:
     e=values[mode]['endpoint'];r=refs[c['id']];first=next((i for i,(a,z) in enumerate(zip(e['ids'],r['ids'])) if a!=z),min(e['length'],r['length']) if e['length']!=r['length'] else None);counterexamples.append(dict(arm=name,task=c['id'],mode=mode,slot=values[mode]['slot'],first_differing_output_index=first,reference_length=r['length'],candidate_length=e['length'],reference_stop=r['stop_reason'],candidate_stop=e['stop_reason']))
   tasks.append(dict(task=c['id'],complete_counts_and_diagnostic=complete,observer_endpoint_equal=equal if complete else None,reference_matches=matches,full_reference_qualified=complete and equal and all(v is True for v in matches.values()) and len(matches)==2,descriptive_request_ms={mode:row['native_request_ms'] for mode,row in values.items()}))
  arms[name]=dict(tasks=tasks,complete_reference_qualified=all(t['full_reference_qualified'] for t in tasks))
 original_ok=all(reference_stability.values());shadow_ok=arms['R_SHADOW']['complete_reference_qualified'];multirow=any(w['arm']=='C_R_QB' for w in witnesses);complete=len(valid)==80 and len(attempted)==len(started)==80 and not invalid and not observer_failures
 gate=complete and original_ok and shadow_ok and arms['C_R_QB']['complete_reference_qualified'] and arms['C_R_PQ']['complete_reference_qualified'] and multirow
 missing=[{k:s[k] for k in ('slot','task','arm','session','mode','stage')} for s in PLAN['slots'] if s['slot'] not in attempted]
 partial_started=[s['slot'] for s in PLAN['slots'] if s['slot'] in started and not any(r['slot']==s['slot'] for r in raw_results)];partial_new_events=[r for r in ledger if r['event']=='FORWARD_START' and r['slot'] in partial_started]
 unknown_original_partial=[s['slot'] for s in PLAN['slots'] if s['arm']=='R' and s['slot'] in partial_started]
 contract=read_json(OUT/'EXECUTION_CONTRACT_AUDIT.json');assert contract['status']=='VIOLATION_REQUIRES_STOP'
 gate=False
 summary=dict(execution_contract_qualified=False,execution_contract_audit='EXECUTION_CONTRACT_AUDIT.json',record_validation_scope='Raw endpoint/work/identity validity only; frozen safety cadence violation prevents complete compliant P1 qualification',status='COMPLETED' if complete else 'STOPPED_OR_INCOMPLETE',F0_sha256=file_sha(ROOT/'p0/F0_EXECUTION.json'),process_attempts=len(attempted),request_starts=len(started),native_forward_callers_completed_requests=actual_forwards,observed_partial_new_forward_starts=len(partial_new_events),unknown_partial_original_R_forward_coordinates=unknown_original_partial,operator_starts=0,owned_native_PID_seconds=native_seconds,charged_owned_seconds=charged_seconds,raw_output_bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file()),valid_records=len(valid),invalid_records=invalid,unstarted=missing,reference_stability=reference_stability,arms=arms,counterexamples=counterexamples,observer_failures=observer_failures,physical_work=dict(physical),minimum_sampled_B570_signed_headroom_bytes=minimum_headroom,maximum_native_safety_sample_gap_ms=maximum_sample_gap_ms,minimum_sampled_available_host_RAM_bytes=minimum_host_RAM,legacy_phase_binding_counter_scope='Old phase_binding_calls counts only legacy repair branch; it does not count all PR108 geometry-bind calls. New effective graph invalidation/dispatch time remains unmeasured.',C_R_QB_source_bound_VERIFY_multirow_observed=multirow,P1_to_P2_gate='PASS_REQUEST_SEPARATE_P2_AUTHORIZATION' if gate else 'NO_GO_NO_ADDITIONAL_SCIENTIFIC_SEARCH',performance_aggregate='WITHHELD_P1_IS_DESCRIPTIVE_ONLY',qualified_speedup=None,P2_started=False,P3_started=False,hardware_stage1='HOLD_MISSING_EVIDENCE')
 write('PRODUCER_STATE_OBSERVATIONS.json',phase_records);write('ENDPOINTS_P1.json',raw_results);write('VERIFY_WITNESSES.json',witnesses);write('ANALYSIS_P1.json',summary);print(json.dumps({k:summary[k] for k in ('status','process_attempts','request_starts','valid_records','invalid_records','counterexamples','observer_failures','P1_to_P2_gate','C_R_QB_source_bound_VERIFY_multirow_observed')}))
if __name__=='__main__':main()
