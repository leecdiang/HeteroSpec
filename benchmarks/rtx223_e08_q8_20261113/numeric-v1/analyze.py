"""CPU-only analysis of closed, unfiltered GPU receipts."""
from pathlib import Path
import csv,json,math,statistics,hashlib,datetime
p=Path(__file__).resolve().parent;e08=p.parent;ev=p/'evidence'
sha=lambda f:hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
r=json.loads((ev/'timing-001/result.json').read_bytes());q=json.loads((ev/'qualification-001/result.json').read_bytes())
assert r['status']==q['status']=='PASS_OPERATOR_ONLY'
assert r['explicit_prelaunch_charged']==355 and q['explicit_prelaunch_charged']==14
rows=r['paired_timings'];assert len(rows)==36
assert all(x['batch_repetitions']==5 and x['event_ms']>0 for x in rows)
summary={};pairs=[]
for mode in ['kernel-only','complete-operator']:
 summary[mode]={}
 for arm in range(3):
  values=[x['event_ms']*1000/5 for x in rows if x['mode']==mode and x['arm']==arm]
  summary[mode]['ABC'[arm]]=dict(samples_us=values,median_us=statistics.median(values),mean_us=statistics.mean(values),sample_cv=statistics.stdev(values)/statistics.mean(values))
 for reference,candidate in [(0,1),(0,2),(1,2)]:
  ratios=[]
  for block in range(6):
   block_rows={x['arm']:x['event_ms'] for x in rows if x['mode']==mode and x['block']==block};assert len(block_rows)==3
   ratios.append(block_rows[candidate]/block_rows[reference])
  ratio=math.exp(statistics.mean(map(math.log,ratios)))
  pairs.append(dict(mode=mode,reference='ABC'[reference],candidate='ABC'[candidate],time_ratios=ratios,geomean_time_ratio=ratio,geomean_time_change_pct=100*(ratio-1),candidate_faster_blocks=sum(x<1 for x in ratios),n_blocks=6))
with (p/'TIMING_SAMPLES.csv').open('x',newline='',encoding='utf8') as f:
 fields=['mode','block','position','arm','batch_repetitions','event_ms','per_operator_us','host_complete_s'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for row in rows:w.writerow({k:row[k] for k in fields if k not in ('arm','per_operator_us')}|dict(arm='ABC'[row['arm']],per_operator_us=row['event_ms']*1000/5))
attempts=[]
for phase,reservation,actual in [('capture-001',64,0),('capture-002',64,64),('capture-003',32,4),('qualification-001',14,14),('timing-001',355,355)]:
 path=Path('D:/HeteroSpec-PC/rtx223-e08')/phase/'attempt.jsonl';events=[json.loads(x)['event'] for x in path.read_bytes().splitlines()];tail=events[-1]
 temps=[e['temperature_c'] for e in events if e.get('observer') in ('initial_watermarks','watermark')]
 used=[e['used'] for e in events if e.get('observer') in ('initial_watermarks','watermark')]
 etw=[e for e in events if e.get('observer')=='ETW_counts']
 attempts.append(dict(phase=phase,status=tail['kind'],reserved=reservation,explicit_admitted=actual,wall_seconds=tail['wall_seconds'],owned_exit_confirmed=tail['owned_process_exit_confirmed'],temperature_max_c=max(temps),sampled_peak_device_used_bytes=max(used),ETW_counts=etw[-1]['counts'] if etw else None,journal_path=str(path),journal_sha256=sha(path)))
assert sum(x['reserved'] for x in attempts)==529 and sum(x['explicit_admitted'] for x in attempts)==437
result=dict(schema='heterospec.e08.closed.q8-operator-data.v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_PR230='ee999060ea342e96014827f6c14ff8d5118b3d18',device=r['device'],summary=summary,paired_comparisons=pairs,resources=r['resources'],attempts=attempts,usage=dict(explicit_application_reservations=529,explicit_application_admitted_attempts=437,unused_unreserved_of_567=38,unused_reservations_not_refunded=92,model_load_calls=3,successful_model_loads=2,decode_calls=2,actual_token_rows_per_decode=8,successful_bounded_operand_captures=1,operator_qualification_launches=14,operator_timing_launches=355,physical_lifecycle_kernels=None,implicit_context_count=None),gates=dict(bootstrap='PASS_ATTEMPT006',real_q8_capture='PASS_ATTEMPT003',bitwise_ABC='PASS_ONE_FIXTURE_SIX_REPLAYS',paired_timing='PASS_SINGLE_SESSION_NEGATIVE_C_VS_B',C_faster_than_B='FAIL_ALL_TWELVE_PAIRS',original_full_lifecycle_4096='FAIL_NOT_CLOSED',production_native_admission='BLOCKED_UNCHANGED',native_request_chain='NOT_RUN',qualification_66='NOT_RUN',round_two='NOT_RUN',paper_change='NOT_RUN'),limits=['One genuine q8 prefix fixture; CPU-mapped remainder of unchanged model. No equivalence to all-GPU request/service baseline.','Two A complete-operator samples are high and retained. No trimming, repeated-run stability or population confidence claim.','CUDA event intervals include device queues and any host submission gaps; exclude allocations, transfers, model load and qualification.','No numeric CUPTI/profiler. Actual occupancy, L2/DRAM traffic, hidden library work and entire physical lifecycle remain unknown.'],input_sha256=dict(raw_timing=sha(ev/'timing-001/result.json'),raw_qualification=sha(ev/'qualification-001/result.json'),source=sha(Path(__file__))))
(p/'ANALYSIS.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(dict(summary=summary,paired_comparisons=pairs,usage=result['usage']),indent=2))
