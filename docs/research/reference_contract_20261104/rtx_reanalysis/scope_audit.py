"""Scope-explicit negative controls for draft prefill accounting; no new measurement."""
from pathlib import Path
import json,collections as co,statistics as st
P=Path(__file__).parent
r=json.loads((P/'data/pr151-native-projection.json').read_text())['records']
g=co.defaultdict(dict)
for x in r:
 s=x['slot'];g[(s['family'],s['date_slot'],s['session_slot'],s['input_id'])][x['arm']]=x
assert len(g)==96
rows=[]
for scope in ['GS','PQ','QB']:
 for key,a in g.items():
  m,c=a['M_'+scope],a['C_'+scope]
  M,C=m['service_seconds'],c['service_seconds'];mp=m['target_phases'].get('PREFILL',0);tp=c['target_phases'].get('PREFILL',0);dp=c['draft_phases'].get('PREFILL',0)
  residual=(M-mp)-(C-tp-dp)
  measured=sum(v for k,v in m['target_phases'].items()if k!='PREFILL')-sum(v for k,v in c['target_phases'].items()if k!='PREFILL')-sum(v for k,v in c['draft_phases'].items()if k!='PREFILL')
  rows.append({'scope':scope,'family':key[0],'date':key[1],'session':key[2],'input':key[3],'M_seconds':M,'C_seconds':C,'C_minus_M':C-M,'draft_prefill_s':dp,'target_prefill_C_minus_M_s':tp-mp,'nonprefill_accounting_residual_s':residual,'synchronized_nonprefill_decode_sum_saving_s':measured,'unassigned_host_gap_difference_s':residual-measured})
summary=[]
for scope in ['GS','PQ','QB']:
 for fam in ['all','Qwen','SmolLM2']:
  rr=[x for x in rows if x['scope']==scope and (fam=='all'or x['family']==fam)];losers=[x for x in rr if x['C_minus_M']>0]
  summary.append({'scope':scope,'family':fam,'blocks':len(rr),'losing_blocks':len(losers),'losers_still_losing_after_ideal_full_draft_prefill_removal':sum(x['C_minus_M']-x['draft_prefill_s']>0 for x in losers),'losers_positive_accounting_residual':sum(x['nonprefill_accounting_residual_s']>0 for x in losers),'losers_positive_synchronized_decode_saving':sum(x['synchronized_nonprefill_decode_sum_saving_s']>0 for x in losers),'accounting_residual_range_losers_s':[min(x['nonprefill_accounting_residual_s']for x in losers),max(x['nonprefill_accounting_residual_s']for x in losers)],'synchronized_decode_saving_range_losers_s':[min(x['synchronized_nonprefill_decode_sum_saving_s']for x in losers),max(x['synchronized_nonprefill_decode_sum_saving_s']for x in losers)]})
out={'scope':'All three fixed repair scopes, day1/day2 only. Phase sums are synchronized host decode elapsed, not exclusive GPU critical-path or causal speedup.','correction':'Original report summary omitted that all-56 positive nonprefill residual statement applied only to QB. GS and PQ counterexamples invalidate universalization.','summary':summary,'per_block':rows}
(P/'scope_audit_recomputed.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(summary,indent=2))
