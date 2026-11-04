"""Counterfactual accounting sensitivity only; not a cache implementation or prediction."""
from pathlib import Path
import json,math,statistics as st,collections as co,csv
ROOT=Path(__file__).parent;r=json.loads((ROOT/'raw_scope_recomputed.json').read_text())['per_block']
def gm(xs):return math.exp(st.mean(math.log(x)for x in xs))
def grouped(rows,fn):
 d=co.defaultdict(list)
 for x in rows:d[fn(x)].append(x)
 return d
for x in r:
 P=x['draft_prefill_s'];Delta=x['C_seconds']-x['M_seconds'];eq=x['M_seconds']-(x['C_seconds']-P)
 assert abs((P-Delta)-eq)<1e-12
 x['fraction_prefill_to_remove_for_parity_h0']=Delta/P
 x['fraction_prefill_to_remove_with_10ms']= (Delta+.010)/P
 # Hypothetical identical-state n-use sharing: cost C-P+P/n+h. Not measured cache behavior.
 x['ideal_n_strictly_above_for_gain_h0']=P/(P-Delta)if P>Delta else None
 x['ideal_n_strictly_above_for_gain_10ms']=P/(P-Delta-.010)if P>Delta+.010 else None
rows=[]
for key,v in grouped(r,lambda x:(x['family'],x['date'],x['session'])).items():
 totalM=sum(x['M_seconds']for x in v);totalC=sum(x['C_seconds']for x in v);P=sum(x['draft_prefill_s']for x in v)
 rec={'family':key[0],'date':key[1],'session':key[2],'inputs':len(v),'M_sum_s':totalM,'C_sum_s':totalC,'P_sum_s':P,'C_over_M_sum':totalC/totalM,'C_over_M_gm':gm(x['C_seconds']/x['M_seconds']for x in v),'net_saving_s':totalM-totalC,'threshold_fraction_sum_cost_h0':(totalC-totalM)/P,'losing_inputs':sum(x['C_seconds']>x['M_seconds']for x in v)}
 rec['fixed_fraction_sensitivity']={str(f):{'counterfactual_C_over_M_sum':sum(x['C_seconds']-f*x['draft_prefill_s']for x in v)/totalM,'profitable_inputs':sum(x['C_seconds']-f*x['draft_prefill_s']<x['M_seconds']for x in v)}for f in [0,.1,.25,.5,.75,1]}
 rows.append(rec)
perinput=[]
for key,v in grouped(r,lambda x:(x['family'],x['input'])).items():
 perinput.append({'family':key[0],'input':key[1],'prompt_tokens':v[0]['prompt_tokens'],'blocks':len(v),'threshold_fraction_h0_min':min(x['fraction_prefill_to_remove_for_parity_h0']for x in v),'threshold_fraction_h0_max':max(x['fraction_prefill_to_remove_for_parity_h0']for x in v),'C_minus_M_mean_s':st.mean(x['C_seconds']-x['M_seconds']for x in v),'draft_prefill_mean_s':st.mean(x['draft_prefill_s']for x in v)})
res={'analyzed_scope':'QB only, M_QB versus C_QB; not GS/PQ amortization estimates.','formula':'Measured C, M, P=draft-prefill. Hypothetical Cnew=C-f*P+h; strict gain iff f>(C-M+h)/P. f in [0,1] includes actually reusable fraction, realized hit rate and realized speedup; h is total additional synchronization/maintenance/allocation overhead. Not causal prediction.','alternative_formula':'For identical-state n-use sharing only, ideal Cnew=C-P+P/n+h; strict gain iff n>P/(P-(C-M)-h), with positive denominator. Model does not establish cache validity, natural hit rates, or avoided work.','coverage':'Days1/2 only (2026-10-31/2026-11-01); two sessions each; each model12fixed previously exposed inputs. Repeated inputs/sessions not independent date populations.','per_session':rows,'per_input':perinput,'per_block':r}
(ROOT/'amortization_recomputed.json').write_text(json.dumps(res,indent=2)+'\n')
with (ROOT/'amortization_per_block.csv').open('w')as f:
 w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r)
print(json.dumps({'per_session':[{k:v for k,v in x.items()if k!='fixed_fraction_sensitivity'}for x in rows],'per_input':perinput},indent=2))
