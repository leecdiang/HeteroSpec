#!/usr/bin/env python3
"""Host-only historical descriptive accounting. No GPU clocks, fitting, or future-input policy."""
from pathlib import Path
import csv,json,math,statistics as st,collections as co,zipfile,hashlib
import argparse
ROOT=Path(__file__).parent;OLD=ROOT
ap=argparse.ArgumentParser();ap.add_argument('--archives',type=Path,required=True);args=ap.parse_args();Z=args.archives
PINS={1:'732a3bce85050698facf48df324387a889ed98bb5c0af671a7b2a84654c4d131',2:'4a3a3dac9eb4be318d3300024378277b4ea43afc9f038319222aa96713f161f4'}
def groups(rows,fn):
 g=co.defaultdict(list)
 for x in rows:g[fn(x)].append(x)
 return g
def gm(xs):return math.exp(st.mean(math.log(x)for x in xs))
for pin in json.loads((ROOT/'SOURCE_MANIFEST.json').read_text()):
 assert hashlib.sha256((ROOT/pin['local']).read_bytes()).hexdigest()==pin['materialized_sha256']
r=[];sources=[]
for d,sha in PINS.items():
 p=Z/f'main-day{d}-increment.part-002.zip';assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
 sources.append({'name':p.name,'sha256':sha,'bytes':p.stat().st_size})
 with zipfile.ZipFile(p)as z:
  assert z.testzip()is None
  for n in z.namelist():
   if not n.endswith('off.json'):continue
   raw=z.read(n);x=json.loads(raw)
   if x['slot']['stage']!='formal':continue
   x['_source']={'archive':p.name,'member':n,'sha256':hashlib.sha256(raw).hexdigest()};r.append(x)
assert len(r)==672
G=co.defaultdict(dict)
for x in r:
 s=x['slot'];G[(s['family'],s['date_slot'],s['session_slot'],s['input_id'])][x['arm']]=x
rows=[]
for scope in ['GS','PQ','QB']:
 for key,a in G.items():
  m,c=a['M_'+scope],a['C_'+scope];M,C=m['service_seconds'],c['service_seconds'];L=c['length'];N=L-1
  assert c['context']['cap']==128 and c['context']['n_ctx']==1024 and c['context']['draft_ub']==1
  assert L==m['length'] and c['ids']==m['ids'] and c['stop_reason']==m['stop_reason']
  nc=len(c['cycles']);accepted=sum(v['accepted']for v in c['cycles']);proposed=sum(len(v['proposals'])for v in c['cycles'])
  assert c['target_calls']==1+nc and m['target_calls']==L and c['draft_calls']==1+4*nc and proposed==3*nc
  mp=m['target_phases'].get('PREFILL',0);cp=c['target_phases'].get('PREFILL',0);dp=c['draft_phases'].get('PREFILL',0)
  ordinary=m['target_phases']['ORDINARY'];verify=c['target_phases']['VERIFY'];propose=c['draft_phases']['PROPOSE'];seed=c['draft_phases']['DRAFT_SYNC']
  mg=M-sum(m['target_phases'].values());cg=C-sum(c['target_phases'].values())-sum(c['draft_phases'].values());assert mg>=0 and cg>=0
  fixed=dp+cp-mp;Bdecode=ordinary-verify-propose-seed;B= Bdecode+mg-cg
  assert abs((C-M)-(fixed-B))<1e-12
  row={'scope':scope,'family':key[0],'date':key[1],'session':key[2],'input':key[3],'prompt_tokens':c['prompt_tokens'],'output_tokens':L,'continuation_tokens_after_initial':N,'stop_reason':c['stop_reason'],'target_calls_M':m['target_calls'],'target_calls_C':c['target_calls'],'draft_calls_C':c['draft_calls'],'cycles':nc,'accepted':accepted,'proposed':proposed,'acceptance':accepted/proposed,'output_after_initial_per_cycle':N/nc,'target_rows_verified':4*nc,'verify_rows_per_committed_after_initial':4*nc/N,'M_s':M,'C_s':C,'D_M_over_C':M/C,'M_target_prefill_s':mp,'C_target_prefill_s':cp,'C_draft_prefill_s':dp,'M_ordinary_s':ordinary,'C_verify_s':verify,'C_propose_s':propose,'C_seed_decode_DRAFT_SYNC_s':seed,'M_unassigned_host_gap_s':mg,'C_unassigned_host_gap_s':cg,'C_minus_M_host_gap_s':cg-mg,'C_setup_s':c['setup_seconds'],'M_setup_s':m['setup_seconds'],'C_teardown_s':c['teardown_seconds'],'M_teardown_s':m['teardown_seconds'],'fixed_prefill_extra_F_s':fixed,'nonprefill_decode_saving_s':Bdecode,'nonprefill_accounting_saving_B_s':B,'total_C_minus_M_s':C-M,'ordinary_ms_per_step':1000*ordinary/N,'verify_ms_per_cycle':1000*verify/nc,'propose_ms_per_draft_call':1000*propose/proposed,'seed_ms_per_cycle':1000*seed/nc,'draft_prefill_ms_per_token':1000*dp/c['prompt_tokens'],'continuation_target_call_reduction_factor':N/nc,'total_target_call_reduction_factor':L/(nc+1),'M_source':m['_source'],'C_source':c['_source']}
  row['synchronized_C_ms_per_cycle']=1000*(verify+propose+seed)/nc
  row['observed_rate_required_tokens_per_cycle_decode_only']=(verify+propose+seed)/nc/(ordinary/N)
  row['observed_rate_required_tokens_per_cycle_full_request']=(fixed/nc+(verify+propose+seed)/nc+(cg-mg)/nc)/(ordinary/N)
  assert ((N/nc)>row['observed_rate_required_tokens_per_cycle_full_request']) == (M>C)
  # Two explicitly incompatible accounting extrapolations, neither identified from actual length sweeps.
  # A extrapolates ALL non-prefill residual at its one observed average rate.
  if B>0 and fixed>0:
   row['frozen_rate_A_parity_total_output']=1+N*fixed/B
   row['frozen_rate_A_with_10ms_parity_total_output']=1+N*(fixed+.010)/B
  else:row['frozen_rate_A_parity_total_output']=None;row['frozen_rate_A_with_10ms_parity_total_output']=None
  # B holds unassigned CPU/host gap DIFFERENCE fixed, extrapolates synchronized decode only.
  adjusted_fixed=fixed+cg-mg
  row['frozen_rate_B_parity_total_output']=1+N*adjusted_fixed/Bdecode if Bdecode>0 and adjusted_fixed>0 else None
  row['frozen_rate_A_exceeds_original_cap128']=row['frozen_rate_A_parity_total_output'] is not None and row['frozen_rate_A_parity_total_output']>128
  row['frozen_rate_A_exceeds_nctx1024_conservative_remaining_slot_screen']=row['frozen_rate_A_parity_total_output'] is not None and row['frozen_rate_A_parity_total_output']>1024-c['prompt_tokens']
  row['natural_EOG_cannot_force_extension']=c['stop_reason']=='EOG'
  rows.append(row)
assert len(rows)==288
summary=[]
for key,v in groups(rows,lambda x:(x['scope'],x['family'],x['input'].split('/')[0])).items():
 summary.append({'scope':key[0],'family':key[1],'domain_length_confounded_group':key[2],'blocks':len(v),'unique_inputs':len({x['input']for x in v}),'D_gm':gm(x['D_M_over_C']for x in v),'C_over_M_total':sum(x['C_s']for x in v)/sum(x['M_s']for x in v),'draft_losing_blocks':sum(x['C_s']>x['M_s']for x in v),**{k:st.mean(x[k]for x in v)for k in ['prompt_tokens','output_tokens','acceptance','cycles','target_calls_M','target_calls_C','draft_calls_C','verify_rows_per_committed_after_initial','M_ordinary_s','C_verify_s','C_propose_s','C_seed_decode_DRAFT_SYNC_s','C_draft_prefill_s','fixed_prefill_extra_F_s','nonprefill_decode_saving_s','nonprefill_accounting_saving_B_s','C_minus_M_host_gap_s','draft_prefill_ms_per_token']}})
perinput=[]
for key,v in groups(rows,lambda x:(x['scope'],x['family'],x['input'])).items():
 q=v[0];rec={k:q[k]for k in ['scope','family','input','prompt_tokens','output_tokens','stop_reason','acceptance','cycles','target_calls_M','target_calls_C','draft_calls_C']};rec['sessions']=len(v);rec['D_gm']=gm(x['D_M_over_C']for x in v)
 for k in ['C_draft_prefill_s','fixed_prefill_extra_F_s','nonprefill_decode_saving_s','nonprefill_accounting_saving_B_s','total_C_minus_M_s','M_ordinary_s','C_verify_s','C_propose_s','C_seed_decode_DRAFT_SYNC_s','C_minus_M_host_gap_s']:
  rec[k+'_mean']=st.mean(x[k]for x in v)
 for k in ['frozen_rate_A_parity_total_output','frozen_rate_B_parity_total_output']:
  values=[x[k]for x in v if x[k]is not None];rec[k+'_range']=[min(values),max(values)]if values else None
 rec['threshold_outside_cap_blocks']=sum(x['frozen_rate_A_exceeds_original_cap128']for x in v);rec['threshold_outside_context_blocks']=sum(x['frozen_rate_A_exceeds_nctx1024_conservative_remaining_slot_screen']for x in v);perinput.append(rec)
# #162: genuinely crossed input selection, but only service times available in these compact records.
x162=json.loads((OLD/'data/pr162-epoch07-FINAL_COST.json').read_text());meta=json.loads((OLD/'data/pr162-epoch07-HELDOUT.json').read_text())['inputs'];cross=[]
for key,v in groups(x162['blocks'],lambda x:(meta[x['input']]['domain'],meta[x['input']]['stratum'])).items():
 cross.append({'domain':key[0],'length_band':key[1],'inputs':len({x['input']for x in v}),'sessions':len({x['session']for x in v}),'blocks':len(v),'D_QB':gm(x['service_seconds']['M_QB']/x['service_seconds']['C_QB']for x in v),'QB_profitable_blocks':sum(x['service_seconds']['M_QB']>x['service_seconds']['C_QB']for x in v),'mean_C_minus_M_s':st.mean(x['service_seconds']['C_QB']-x['service_seconds']['M_QB']for x in v),'phase_or_output_evidence':'Not present in this compact cost table; no cross-study phase-cause inference.'})
res={'source_commit':'29511ed91eb9f3d9773cfdda53e3554b0f4ad08b','archive_sources':sources,'records':672,'paired_scope_blocks':288,'all_invariants_passed':True,'summary':summary,'per_input':perinput,'pr162_crossed_service_only':cross,'per_block':rows,'estimand_warning':'Model-specific, scope-specific, exposed fixed-input panel, two dates/four repeated sessions. No predictive evaluation or independent 288-sample population inference.','clock_warning':'Synchronized host decode elapsed includes llama_decode, batch_free, llama_synchronize; DRAFT_SYNC is actual seed decode, not isolated synchronization latency. No GPU-only timing.','threshold_warning':'No output-length intervention or within-request timestamp series. Frozen-rate A/B are illustrative extrapolations, NOT measured break-even lengths, bounds, policy predictions or authorization to extend natural EOG. 1024 minus prompt length is only a conservative slot screen, not an exact output-token legal maximum: initial output comes from prefill, final pending output may not consume a slot, and speculative rows need further margin.'}
(ROOT/'mechanism.json').write_text(json.dumps(res,indent=2)+'\n')
with(ROOT/'mechanism_per_block.csv').open('w')as f:
 fields=[k for k in rows[0]if not k.endswith('_source')];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
print(json.dumps({'summary':[x for x in summary if x['scope']=='QB'],'crossed':cross},indent=2))
