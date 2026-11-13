#!/usr/bin/env python3
"""CPU-only explanatory summaries for revision 2; original measurements unchanged."""
from pathlib import Path
import csv
import hashlib
import json
import math

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
OUT=ROOT/'generated'
OUT.mkdir(exist_ok=True)

def read(name):
    return json.loads((DATA/name).read_bytes())

# Post-hoc influence check: retain equal weight for each of the 11 surviving roots.
# This changes neither the original 12-root estimand nor its stratified bootstrap.
rows=list(csv.DictReader((DATA/'closeout/service/S3_TIMINGS.csv').open(newline='')))
grid={}
for row in rows:
    if row['role']=='measured':
        grid.setdefault(row['root'],{}).setdefault(row['round'],{})[row['arm']]=float(row['service_s'])
assert len(grid)==12 and all(len(v)==4 for v in grid.values())
assert all(set(arms)=={'G','B','C'} for root in grid.values() for arms in root.values())
logs={root:sum(math.log(v['C']/v['B']) for v in rounds.values())/4 for root,rounds in grid.items()}
primary=math.exp(sum(logs.values())/12)
assert abs(primary-0.9848637428511184)<1e-14
loo=[{'omitted_root':root,'remaining_roots':11,
      'ratio':math.exp(sum(v for k,v in logs.items() if k!=root)/11)} for root in logs]
with (OUT/'s3_leave_one_root_out.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['omitted_root','remaining_roots','ratio']);w.writeheader();w.writerows(loo)

# Disjoint phase sums from the same S3 measured requests, not phase-level samples.
phase=read('v2/s3_cost_audit.json')['groups']
fields=[('prefill_s','Prefill'),('decode_s','Decode'),('reset_s','Reset'),
        ('planning_s','Planning'),('owned_host_output_copy_s','Owned output copy'),
        ('residual_unpartitioned_s','Unpartitioned residual'),('service_s','Resident service')]
phase_tex=[]
for key,label in fields:
    b,c=(phase[arm]['measured'][key] for arm in ['B','C'])
    if key=='service_s': phase_tex.append(r'\midrule')
    phase_tex.append(f'{label} & {b:.6f} & {c:.6f} & ${c-b:+.6f}$'+r'\\')
for arm in ['B','C']:
    m=phase[arm]['measured']
    assert m['requests']==48
    assert abs(sum(m[k] for k,_ in fields[:-1])-m['service_s'])<1e-10
(OUT/'table_s3_phases.tex').write_text(r'\newcommand{\SuppSthreePhaseRows}{%'+'\n'+'\n'.join(phase_tex)+'\n}\n')

# Public reconstruction of two observed free histories and a separate supplied corpus.
history=read('v2/history_REPORT.json')
actual=[]
for r in history['actual_free_cases']:
    assert r['canonical_body_same_tokenization'] and r['sampled_tokens']==128
    assert r['trimmed_KV_rows']==r['trimmed_prompt_stub_rows']+r['trimmed_materialized_sample_rows']==131
    assert r['LCP']==r['first_difference']['position_zero_based']
    actual.append({k:r[k] for k in ['case','initial_tokens','materialized_head','pending_position','LCP',
                                   'trimmed_KV_rows','next_input_tokens','next_suffix_rows','sampled_tokens']})
corpus=history['saved_public_corpus']['all']
assert corpus['later']==1127 and corpus['older_canonical_assistant_prefix_present']==331

# Source-derived 89-row geometry. These are logical shapes/counts, never GPU timings.
cost=read('v2/local_cost_REPORT.json')
static={r['arm']:r for r in cost['source_derived_proposed_append_work']}
assert static['W']['projection_tile_positions']==static['L']['projection_tile_positions']
assert static['W']['attention_tile_positions']==static['L']['attention_tile_positions']
keys=['rows','calls','projection_4column_groups_per_fully_consumed_projection',
      'attention_4query_tiles_per_layer','logical_F32_mask_bytes','attention_concat_nodes_per_layer',
      'guaranteed_strided_mask_cont_nodes_per_layer','guaranteed_strided_mask_cont_logical_F32_bytes_per_layer']

result={
 'scope':'CPU reanalysis of fixed public records; no new model/native/GPU run',
 's3':{'primary_equal_root_ratio':primary,'post_hoc_leave_one_root_out':{
   'label':'Exploratory post-hoc sensitivity; not preregistered; no confidence interval',
   'weighting':'Equal weight across the remaining 11 root-level mean log ratios',
   'minimum':min(x['ratio'] for x in loo),'maximum':max(x['ratio'] for x in loo),
   'primary_result_and_bootstrap_unchanged':True}},
 'natural_history':{'observed_free_cases':actual,
   'separate_supplied_history_prediction':{'older_canonical_assistant_spans':331,'later_nodes':1127,
     'scope':'Saved supplied-history CPU prediction, not free-generation frequency or GPU benefit'}},
 'source_derived_89_rows':{'scope':'Logical source construction; no measured launches, DRAM traffic or latency',
   'W':{k:static['W'][k] for k in keys},'L':{k:static['L'][k] for k in keys}},
 'input_sha256':{n:hashlib.sha256((DATA/n).read_bytes()).hexdigest() for n in
   ['closeout/service/S3_TIMINGS.csv','v2/s3_cost_audit.json','v2/history_REPORT.json','v2/local_cost_REPORT.json']}}
(OUT/'v2_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'primary':primary,'post_hoc_loo':result['s3']['post_hoc_leave_one_root_out'],
                  'history_cases':len(actual),'source_geometry':'23 identical ordered tiles in both arms'},indent=2))
