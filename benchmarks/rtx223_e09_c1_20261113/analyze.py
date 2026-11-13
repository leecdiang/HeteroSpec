"""Closed CPU-only analysis, all48 batches and both orders preserved."""
from pathlib import Path
import json,csv,statistics,math,hashlib,datetime
p=Path(__file__).resolve().parent;sha=lambda f:hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
r=json.loads((p/'evidence/e09-timing-001/result.json').read_bytes());q=json.loads((p/'evidence/e09-qualification-001/result.json').read_bytes())
assert r['explicit_prelaunch_charged']==320 and q['explicit_prelaunch_charged']==14 and len(r['paired_timings'])==48
assert len(r['post_batch_bitwise'])==48 and all(x['activation_exact'] and x['output_exact'] for x in r['post_batch_bitwise'])
summary={};pairs=[]
for mode in ['kernel-only','complete-operator']:
 summary[mode]={}
 for arm in [1,2]:
  values=[x['event_ms']*1000/4 for x in r['paired_timings'] if x['mode']==mode and x['arm']==arm]
  summary[mode]['B' if arm==1 else 'C1']=dict(raw_us=values,median_us=statistics.median(values),mean_us=statistics.mean(values),sample_cv=statistics.stdev(values)/statistics.mean(values),range_us=[min(values),max(values)])
 ratios=[];rawpairs=[]
 for block in range(12):
  rows=[x for x in r['paired_timings'] if x['mode']==mode and x['block']==block];assert len(rows)==2 and {x['arm'] for x in rows}=={1,2}
  values={x['arm']:x['event_ms'] for x in rows};ratio=values[2]/values[1];ratios.append(ratio);rawpairs.append(dict(block=block,order=['B' if x['arm']==1 else 'C1' for x in rows],C1_over_B=ratio))
 g=math.exp(statistics.mean(map(math.log,ratios)));pairs.append(dict(mode=mode,raw_pairs=rawpairs,geomean_C1_over_B=g,time_change_pct=100*(g-1),C1_slower_pairs=sum(x>1 for x in ratios),total_pairs=12))
with (p/'ALL_SAMPLES.csv').open('x',newline='',encoding='utf8') as f:
 fields=['mode','block','position','arm','batch_repetitions','event_ms','per_operator_us','host_complete_s'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for row in r['paired_timings']:w.writerow({k:row[k] for k in fields if k not in ('arm','per_operator_us')}|dict(arm='B' if row['arm']==1 else 'C1',per_operator_us=row['event_ms']*1000/4))
phase=[]
for name in ('qualification-001','timing-001'):
 f=Path('D:/HeteroSpec-PC/rtx223-e09-c1')/name/'attempt.jsonl';rows=[json.loads(x)['event'] for x in f.read_bytes().splitlines()];tail=rows[-1];assert tail['kind']=='PASS' and tail['owned_process_exit_confirmed'];samples=[x for x in rows if x.get('observer') in ('watermark','initial_watermarks')];phase.append(dict(phase=name,journal_sha256=sha(f),exit_confirmed=True,temperature_max_c=max(x['temperature_c'] for x in samples),sampled_peak_device_used=max(x['used'] for x in samples),final_watermark=samples[-1]))
events=[json.loads(x) for x in Path('D:/HeteroSpec-PC/rtx223-e09-c1/family.jsonl').read_bytes().splitlines()];reserved=sum(x['reserved'] for x in events if x['kind']=='RESERVED_BEFORE_TASK');assert reserved==369
result=dict(schema='heterospec.e09.C1-single-fixture.v1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent='ba019f30522352c87cac2cc527082ecc6c73ed97',device=r['device'],summary=summary,paired_ratios=pairs,resources=r['resources'],phases=phase,usage=dict(family_limit=415,reserved=369,explicit_prelaunch_admitted=334,timing_admitted=320,qualification_admitted=14,unused_reserved_not_refunded=35,unreserved=46,model_loads=0,decode_calls=0,numerical_root_DLL_loads=0,whole_lifecycle_physical_launches=None,implicit_context_count=None),gates=dict(parent_reuse='PASS_CPU_GGUF_PAYLOAD_AND_CAPTURE_IDENTITY',source_build='PASS64_REG_3072_SHARED_ZERO_SPILL',CPU_restricted_ETW='PASS',ABC1_bitwise='PASS6_FULL_REPLAYS',paired_timing='PASS48_RAW_BATCHES_AND_CHECKS',C1_beats_B='FAIL_THIS_CASE',native_service='NOT_RUN',qualification66='NOT_RUN',round_two='NOT_RUN',physical4096='NOT_CLOSED',achieved_occupancy='NOT_MEASURED',memory_traffic='NOT_MEASURED'),decision='Resource target met; relative gap narrows versus historical separate-session C/B but C1 still slower than concurrent B. No service/model expansion. Cross-input proposal only.',limitations=['one real q8 fixture, one session, no population/stable5% claim','e08 ABC five-repetition batches and this BC1 four-repetition batches/post-check copies differ; no strict C/C1 paired comparison','higher theoretical occupancy is not achieved occupancy or a demonstrated cause; serial groups also change weight reload and synchronization','post-batch bitwise checks are outside CUDA events; host_complete_s excludes those copies/checks','library/driver internal kernels and implicit contexts remain unknown; no original4096 physical contract proof'],input_sha256=dict(qualification=sha(p/'evidence/e09-qualification-001/result.json'),timing=sha(p/'evidence/e09-timing-001/result.json'),analysis_source=sha(Path(__file__))))
(p/'RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(dict(pairs=pairs,summary=summary,usage=result['usage']),indent=2))
