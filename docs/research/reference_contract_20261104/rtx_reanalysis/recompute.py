#!/usr/bin/env python3
"""Read-only deterministic CPU reanalysis of pinned historical HeteroSpec tables.
No GPU, no inferential p-values. Sessions/inputs are not invented independent days.
"""
from pathlib import Path
import json,csv,math,statistics as st,collections as co,hashlib
D=Path(__file__).parent/'data'
def csvread(n): return list(csv.DictReader((D/n).open()))
def js(n): return json.loads((D/n).read_text())
def gm(xs): return math.exp(st.mean(math.log(x) for x in xs))
def groups(rows,fn):
 out=co.defaultdict(list)
 for r in rows: out[fn(r)].append(r)
 return out
def eq(a,b): assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10),(a,b)
out={'scope':'Historical observed finite panels; descriptive exploratory reanalysis, not new measurements or population inference.'}
# 120: independently regenerate graph paired means from eligible host table.
r=[r for r in csvread('pr120-TIMING_HOST.csv') if r['stage']=='T1' and r['eligible']=='True' and r['timing_eligible']=='True' and int(r['q'])>1]
a={}
for view,rows in groups(r,lambda r:r['cost_view']).items():
 pairs=groups(rows,lambda r:(r['context_id'],r['block']))
 vals=[]
 for key,v in pairs.items():
  m={x['layout']:float(x['mean']) for x in v}; assert len(m)==3
  vals.append((m['QB']/m['QH_C'],m['PQ']/m['QB'],m['QB']-m['QH_C']))
 a[view]={'n_pairs':len(vals),'QB_QH':gm(v[0] for v in vals),'PQ_QB':gm(v[1] for v in vals),'QB_minus_QH_us':st.mean(v[2] for v in vals)}
out['pr120_host_recompute']=a
# 121 primary contrasts: don't use unreliable clock channel or normalize across days.
r=csvread('pr121-HOSTS.csv'); meta={r['case_id']:r for r in csvread('pr121-INPUTS.csv')};a={}
for stage in ['confirm','holdout']:
 rows=[x for x in r if x['stage']==stage and int(meta[x['case_id']]['q'])>1]
 pairs=groups(rows,lambda r:(r['case_id'],r['block']))
 v=[]
 for key,rr in pairs.items():
  m={x['arm']:float(x['resident_mean_us']) for x in rr};assert len(m)==4
  v.append({k:m[k]/m['QH_C'] for k in ['QB_A','QB_B']}|{'PQ_QB':m['PQ']/m['QB_A'],'diff':m['QB_A']-m['QH_C']})
 a[stage]={'n_pairs':len(v),**{k:gm(x[k] for x in v) for k in ['QB_A','QB_B','PQ_QB']},'difference_us':st.mean(x['diff'] for x in v)}
out['pr121_host_recompute']=a
#122 replay vs mapping: pair exact case/block/mode, never profiler with clean.
r=[x for x in csvread('pr122-HOST_COSTS.csv') if x['stage']=='confirm' and x['profile']=='False']; assert len(r)==768
p=groups(r,lambda x:(x['case_id'],x['block'])); vals=[]
for key,rr in p.items():
 m={(x['arm'],x['mode']):float(x['resident_mean_us']) for x in rr};assert len(m)==8
 vals.append({'case':key[0],'QB_ON_OFF':m['QB_A','ON']/m['QB_A','OFF'],'QH_QB_OFF':m['QH_C','OFF']/m['QB_A','OFF'],'QH_QB_ON':m['QH_C','ON']/m['QB_A','ON'],'ON_QH_minus_QB_us':m['QH_C','ON']-m['QB_A','ON'],'OFF_QH_minus_QB_us':m['QH_C','OFF']-m['QB_A','OFF']})
out['pr122_by_geometry']={g:{k:(st.mean(x[k] for x in rr) if k.endswith('_us') else gm(x[k] for x in rr)) for k in vals[0] if k!='case'} for g,rr in groups(vals,lambda x:x['case'].rsplit('-v',1)[0]).items()}
#123 independent clean-host T0 ratios/phase additivity, failed padding kept in coverage.
r=[x for x in csvread('pr123-HOST_COSTS.csv') if x['stage']=='timed' and x['profile']=='False'];a={}
for geom,rr in groups(r,lambda x:x['cell'].rsplit('-v',1)[0]).items():
 pairs=groups(rr,lambda x:x['task_id'].rsplit('-a',1)[0]);vv=[]
 for _,rows in pairs.items():
  m={x['arm']:float(x['primary_mean_us']) for x in rows}
  if 'QH_compact'in m: vv.append(m['QH_compact']/m['QB_A'])
 if vv:a[geom]={'n_pairs':len(vv),'QH_compact_QB':gm(vv)}
out['pr123_T0']=a
out['pr123_padding_mismatch']={'qualification_failures':len(csvread('pr123-NUMERICAL_MISMATCHES.csv')),'coverage':dict(co.Counter(r['status'] for r in csvread('pr123-COVERAGE.csv')))}
#144 complete request block costs, keep failed Llama outside qualified timings.
r=csvread('pr144-results-BLOCK_RESULTS.csv');a={}
for fam,rr in groups(r,lambda x:x['family']).items():
 rr=[x for x in rr if x['qualified_family_cost']=='True']
 if not rr:continue
 for x in rr:eq(float(x['QB_over_dual_PQ']),float(x['QB'])/((float(x['PQ_A'])+float(x['PQ_B']))/2))
 a[fam]={'n_blocks':len(rr),'QB_dualPQ':gm(float(x['QB_over_dual_PQ']) for x in rr),'QB_R':gm(float(x['QB_over_R']) for x in rr),'strata':{s:{'QB_dualPQ':gm(float(x['QB_over_dual_PQ']) for x in rows),'QB_R':gm(float(x['QB_over_R']) for x in rows),'n':len(rows)}for s,rows in groups(rr,lambda x:x['stratum']).items()}}
out['pr144']=a
#147 measurement-level service = request + setup + teardown invariant.
r=[x for x in csvread('pr147-results-TIMING.csv') if x['category']=='measurement'];assert len(r)==864
errors=[abs(float(x['service_seconds'])-sum(float(x[k]) for k in ['request_seconds','setup_seconds','teardown_seconds'])) for x in r]
a={}
for cell,rr in groups(r,lambda x:(x['k'],x['lifecycle'])).items():
 ratios=[];parts=[]
 for key,v in groups(rr,lambda x:(x['input'],x['session'])).items():
  m={x['label']:float(x['service_seconds']) for x in v};assert len(m)==3
  ratios.append(m['QB']/((m['PQ_A']+m['PQ_B'])/2))
 a['/'.join(cell)]={'n_blocks':len(ratios),'QB_dualPQ':gm(ratios),'reversed_blocks':sum(x>1 for x in ratios),'service_mean':st.mean(float(x['service_seconds'])for x in rr),'setup_teardown_mean_ms':1000*st.mean(float(x['setup_seconds'])+float(x['teardown_seconds'])for x in rr)}
out['pr147']={'cells':a,'max_phase_sum_residual_seconds':max(errors)}
#151 recompute ALL nine contrasts from 72 per-family input/session logs and verify summaries.
p=js('pr151-analysis.json')['results'];a={}
for fam,x in p.items():
 r=x['input_session_effects'];assert len(r)==72 and len({(z['date_slot'],z['session_slot'],z['input_id'])for z in r})==72
 for s in x['summary']:eq(math.exp(st.mean(v['log_effects'][s['contrast']]for v in r)),s['ratio'])
 for z in r:
  e=z['log_effects'];eq(e['D_QB']-e['D_PQ'],e['M_QB_over_M_PQ']-e['C_QB_over_C_PQ']);eq(e['I_QB_vs_GS'],e['D_QB']-e['D_GS'])
 task={g:{k:math.exp(st.mean(z['log_effects'][k]for z in rr)) for k in ['D_GS','D_PQ','D_QB','C_QB_over_C_PQ','M_QB_over_M_PQ']} for g,rr in groups(r,lambda z:z['input_id'].split('/')[0]).items()}
 per={g:{'D_QB':math.exp(st.mean(z['log_effects']['D_QB']for z in rr)),'positive_sessions':sum(z['log_effects']['D_QB']>0 for z in rr),'sessions':len(rr)}for g,rr in groups(r,lambda z:z['input_id']).items()}
 # Time-only retrospective sensitivity, no contemporaneous outcome used to select later actions.
 decisions={g:st.mean(z['log_effects']['D_QB']for z in rr)>0 for g,rr in groups([z for z in r if z['date_slot']==0],lambda z:z['input_id']).items()}
 test=[z for z in r if z['date_slot']>0]
 # Relative cost to always-draft: M/C = exp(D) when choosing no draft, else 1.
 ratio=math.exp(st.mean(0 if decisions[z['input_id']] else z['log_effects']['D_QB'] for z in test))
 a[fam]={'task_length_confounded':task,'per_input':per,'day0_frozen_input_identity_policy_vs_always_draft_days1_2':ratio,'day0_identity_decisions':decisions,'policy_warning':'Retrospective exposed-input sensitivity only; input memorization, not deployable or new validation. Ratios use equal geometric weights, not wall-time savings.'}
out['pr151']=a
# Later raw seconds where available. Preserve same panel/session labels; no pooled cross-experiment test.
for n,fn in [(159,'pr159-host_execution-COST_RECOMPUTATION.json'),(162,'pr162-epoch07-FINAL_COST.json')]:
 j=js(fn);r=j['blocks'];a={}
 for key in ['layout','D_QB','D_PQ','CQB_R','MQB_R']:
  val=gm(z[key]for z in r);eq(val,j['means'][key]);a[key]=val
 a['blocks']=len(r);a['inputs']=len({z['input']for z in r});a['sessions']=len({z['session']for z in r});a['draft_positive_blocks']=sum(z['D_QB']>1 for z in r)
 a['per_input_draft']={str(k):{'D_QB':gm(z['D_QB']for z in rr),'positive_sessions':sum(z['D_QB']>1 for z in rr)}for k,rr in groups(r,lambda z:z['input']).items()}
 if 'service_seconds'in r[0]:
  for z in r:
   s=z['service_seconds'];eq(z['D_QB'],s['M_QB']/s['C_QB']);eq(z['layout'],s['C_QB']/((s['C_PQ_A']+s['C_PQ_B'])/2))
 out['pr'+str(n)]=a
# Crossed, prospectively selected domain x length panel in PR162; exploratory regrouping.
meta=js('pr162-epoch07-HELDOUT.json')['inputs'];rr=js('pr162-epoch07-FINAL_COST.json')['blocks']
strata={}
for key,v in groups(rr,lambda x:(meta[x['input']]['domain'],meta[x['input']]['stratum'])).items():
 strata['/'.join(key)]={'blocks':len(v),'inputs':len({x['input']for x in v}),'D_QB':gm(x['D_QB']for x in v),'D_PQ':gm(x['D_PQ']for x in v),'layout':gm(x['layout']for x in v),'profitable_draft_blocks':sum(x['D_QB']>1 for x in v)}
out['pr162']['crossed_strata']=strata
sensitivity=[]
for sess,v in [('all',rr)]+list(groups(rr,lambda x:x['session']).items()):
 costs=[(x['service_seconds']['C_QB']if meta[x['input']]['stratum']=='short'else x['service_seconds']['M_QB'],x['service_seconds']['C_QB'],x['service_seconds']['M_QB'])for x in v]
 sensitivity.append({'session':sess,'gate_over_C_gm':gm(a/b for a,b,c in costs),'gate_over_M_gm':gm(a/c for a,b,c in costs),'gate_over_C_sum':sum(a for a,b,c in costs)/sum(b for a,b,c in costs),'gate_over_M_sum':sum(a for a,b,c in costs)/sum(c for a,b,c in costs)})
out['pr162']['retrospective_short_draft_long_target_sensitivity']=sensitivity
out['pr162']['routing_warning']='The bands were prefrozen but this action rule was selected after outcomes. Not independent validation or implementable measured gain; no policy overhead charged.'
for model in ['qwen8b02','qwen14b02']:
 j=js('pr166-'+model+'-COST.json');r=j['blocks'];out['pr166_'+model]={'blocks':len(r),'ratios':{k:gm(z[a]/z[b]for z in r)for k,(a,b)in {'CQB_CPQ':('C_QB','C_PQ'),'MQB_CQB':('M_QB','C_QB'),'MQB_MPQ':('M_QB','M_PQ')}.items()},'input_ratios':j['input_ratios']}
# All local input bytes can be reverified; fixed Git refs recorded separately.
out['input_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(D.iterdir())if p.is_file()}
(Path(__file__).parent/'recomputed.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items()if k not in ['input_sha256','pr151','pr159','pr162','pr166_qwen8b02','pr166_qwen14b02']},indent=2))
