"""Independent post-study arithmetic; reads retained records, never invokes author verifiers/models."""
from pathlib import Path
import collections, csv, hashlib, json, math, statistics, zipfile
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
ZIP=REPO/'paper/mlsys2027/manuscript/output/anonymous-evidence-index-v0.8.8.zip'
def bytes_for(name):
 with zipfile.ZipFile(ZIP) as z: return z.read(name)
def read(name): return json.loads(bytes_for(name))
def gm(values): return math.exp(statistics.mean(math.log(x) for x in values))
inputs=read('derived/inputs.json')
result={'status':'POST_STUDY; outcomes known; fixed original denominators',
        'input_sha256':{f:hashlib.sha256(bytes_for(f)).hexdigest() for f in ['derived/inputs.json','evidence/B570_original_H1.json','evidence/RTX_V4.json']},
        '358H':{}}
canonical=REPO/'analysis/358h_phase3_prompt_summary.csv'
source_rows=list(csv.DictReader(canonical.open(newline='')))
export_rows=inputs['358H']['rows']
fields=list(export_rows[0])
source_map={(r['task_id'],r['repetition'],r['condition']):{k:r[k] for k in fields} for r in source_rows}
export_map={(r['task_id'],r['repetition'],r['condition']):r for r in export_rows}
assert len(source_rows)==len(source_map)==len(export_map)==180 and source_map==export_map
result['canonical_358H_source_check']={'rows':180,'all_exported_fields_exactly_equal':True,'sha256':hashlib.sha256(canonical.read_bytes()).hexdigest()}
for mode in ['CPU','NPU']:
 rows=[r for r in inputs['358H']['rows'] if r['condition']==mode+'_DRAFT_K2']
 assert len(rows)==90
 groups=collections.defaultdict(list)
 for r in rows:
  b=float(r['baseline_end_to_end_ms']); t=float(r['verification_ms']); e=float(r['end_to_end_ms'])
  d=float(r['draft_replay_proposal_ms']); x=float(r['orchestration_residual_ms'])
  assert b>0 and t>0 and d>=0 and x>=0 and t<=e
  assert abs(t+d+x-e)<0.01
  groups[r['task_id']].append((b/t,b/e))
 assert len(groups)==30 and all(len(v)==3 for v in groups.values())
 bound={k:statistics.median(a for a,b in v) for k,v in groups.items()}
 actual={k:statistics.median(b for a,b in v) for k,v in groups.items()}
 assert all(actual[k]<=bound[k] for k in groups)
 result['358H'][mode]={'rows':90,'prompts':30,'repetitions_per_prompt':3,
    'original_prompt_gm_recomputed':gm(actual.values()),
    'total_time_bound_recomputed':sum(float(r['baseline_end_to_end_ms']) for r in rows)/sum(float(r['verification_ms']) for r in rows),
    'new_prompt_gm_upper_bound':gm(bound.values()),
    'new_prompt_bounds_at_or_above_parity':sum(v>=1 for v in bound.values()),
    'new_prompt_bound_min':min(bound.values()),'new_prompt_bound_max':max(bound.values()),
    'individual_row_bounds_at_or_above_parity':sum(a>=1 for v in groups.values() for a,b in v),
    'prompt_bounds':bound}
b=read('evidence/B570_original_H1.json'); cases=[]
assert len(b['rows'])==72
for r in b['rows']:
 a=r['arrays']; assert a['prediction']==a['live'] and len(a['live'])==128
 if r['repetition']==1 and a['reference']!=a['live']:
  first=next(i for i,(x,y) in enumerate(zip(a['reference'],a['live'])) if x!=y)
  cases.append({'task_id':r['task_id'],'first_difference':first,'remaining_ids_including_first':128-first,
    'mismatching_positions':sum(x!=y for x,y in zip(a['reference'],a['live']))})
result['B570']={'full_equal_predictions':72,'distinct_prompts':len(set(r['task_id'] for r in b['rows'])),
 'distinct_divergent_cases':cases,'distinct_nonreference_predicted_positions':sum(c['mismatching_positions'] for c in cases),
 'positions_strictly_after_first_difference':sum(c['mismatching_positions']-1 for c in cases)}
v=read('evidence/RTX_V4.json'); gates=collections.Counter(); cross=[]
for r in v['A']:
 c=r['conditions']; live=c['A_NATIVE_BATCHED_LIVE']['ids']
 for k,x in c.items(): gates[k]+=int(x['ids']==live)
 if r['repetition']==1:
  ref=c['A_REFERENCE_UB1']['ids']; ub=c['A_TARGET_ONLY_UB2']['ids']
  if ref!=live or ub!=live:
   cross.append({'task_id':r['task_id'],'reference_match':ref==live,'ub2_match':ub==live,
    'ref_equals_ub2':ref==ub,'reference_length':len(ref),'ub2_length':len(ub),'live_length':len(live),
    'reference_positional_mismatches_on_common_length':sum(a!=b for a,b in zip(ref,live)),
    'ub2_positional_mismatches_on_common_length':sum(a!=b for a,b in zip(ub,live))})
med=collections.defaultdict(lambda:collections.defaultdict(list)); bid=collections.defaultdict(dict)
for r in v['B']:
 t=r['timer']; assert t['frequency']>0
 ms=1000*t['qpc_delta']/t['frequency']; assert abs(ms-t['milliseconds'])<1e-9
 med[r['task_id']][r['condition']].append(ms);bid[(r['task_id'],r['repetition'])][r['condition']]=r['ids']
assert len(med)==19 and all(len(v)==3 for c in med.values() for v in c.values())
ratios=[statistics.median(c['B_TARGET_REFERENCE_UB1'])/statistics.median(c['B_SERIALIZED_K2_UB1']) for c in med.values()]
result['RTX']={'A_live_agreement_counts':dict(gates),'A_cross_cases':cross,
 'retrospective_two_target_only_array_oracle_prompts':sum(r['conditions']['A_REFERENCE_UB1']['ids']==r['conditions']['A_NATIVE_BATCHED_LIVE']['ids'] or r['conditions']['A_TARGET_ONLY_UB2']['ids']==r['conditions']['A_NATIVE_BATCHED_LIVE']['ids'] for r in v['A'] if r['repetition']==1),
 'B_qualified_serialized_pairs':sum(c['B_TARGET_REFERENCE_UB1']==c['B_SERIALIZED_K2_UB1'] for c in bid.values()),
 'B_batched_reference_equal_pairs':sum(c['B_TARGET_REFERENCE_UB1']==c['B_BATCHED_K2_UB2'] for c in bid.values()),
 'B_speedup_gm_independent':gm(ratios),'B_prompts_serialized_faster':sum(r>1 for r in ratios)}
m4=collections.defaultdict(lambda:collections.defaultdict(list))
for r in inputs['M4']: m4[(r['workload_family'],r['task_id'])][r['condition']].append(r['end_to_end_ns'])
assert len(m4)==60 and sum(len(a) for c in m4.values() for a in c.values())==540
mm=[{c:statistics.median(v) for c,v in x.items()} for x in m4.values()]
result['M4']={'prompts':60,'rows':540,'guard_over_always_gm':gm(x['GUARD_K2']/x['ALWAYS_SPEC_K2'] for x in mm),
 'always_over_two_fixed_mode_oracle_gm':gm(x['ALWAYS_SPEC_K2']/min(x['TARGET_ONLY'],x['ALWAYS_SPEC_K2']) for x in mm),
 'target_faster_prompts':sum(x['TARGET_ONLY']<x['ALWAYS_SPEC_K2'] for x in mm)}
(HERE/'acceptance_diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:{a:b for a,b in v.items() if a!='prompt_bounds'} for k,v in result.items() if k in ['358H','B570','RTX','M4']},indent=2))
