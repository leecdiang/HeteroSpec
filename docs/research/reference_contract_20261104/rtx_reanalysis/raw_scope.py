from pathlib import Path
import json,zipfile,hashlib,math,statistics as st,collections as co
ROOT=Path(__file__).parent;D=ROOT/'data';Z=ROOT.parent/'historical-timing-evidence'
pins={1:'732a3bce85050698facf48df324387a889ed98bb5c0af671a7b2a84654c4d131',2:'4a3a3dac9eb4be318d3300024378277b4ea43afc9f038319222aa96713f161f4'}
p=D/'pr151-native-projection.json'
projection=json.loads(p.read_text())
assert projection['source_commit']=='29511ed91eb9f3d9773cfdda53e3554b0f4ad08b'
assert {int(x['name'].split('day')[1].split('-')[0]):x['sha256']for x in projection['archives']}==pins
r=projection['records']
assert len(r)==672 and len({x['slot']['slot_id']for x in r})==672
G=co.defaultdict(dict)
for x in r:
 s=x['slot'];G[(s['family'],s['date_slot'],s['session_slot'],s['input_id'])][x['arm']]=x
assert len(G)==96 and all(len(v)==7 for v in G.values())
old=json.loads((D/'pr151-analysis.json').read_text())['results'];bykey={}
for fam,rr in old.items():
 for x in rr['input_session_effects']:bykey[(fam,x['date_slot'],x['session_slot'],x['input_id'])]=x['log_effects']
flat=[];maxerr=0
for key,a in G.items():
 s={k:x['service_seconds']for k,x in a.items()}; e={'D_GS':math.log(s['M_GS']/s['C_GS']),'D_PQ':math.log(s['M_PQ']/s['C_PQ']),'D_QB':math.log(s['M_QB']/s['C_QB']),'C_QB_over_C_PQ':math.log(s['C_QB']/s['C_PQ']),'M_QB_over_M_PQ':math.log(s['M_QB']/s['M_PQ'])}
 for k,v in e.items():maxerr=max(maxerr,abs(v-bykey[key][k]));assert abs(v-bykey[key][k])<1e-12
 m,c=a['M_QB'],a['C_QB']; tp=lambda x:x['target_phases'].get('PREFILL',0);dp=lambda x:x['draft_phases'].get('PREFILL',0)
 # Each component is host elapsed, not exclusive device time or proven disjoint critical paths.
 cyc=c['cycle_accounting']; accepted=cyc['accepted']; proposed=cyc['proposed']
 flat.append({'family':key[0],'date':key[1],'session':key[2],'input':key[3],'prompt_tokens':c['prompt_tokens'],'output_length':c['length'],'D_QB':s['M_QB']/s['C_QB'],'M_seconds':s['M_QB'],'C_seconds':s['C_QB'],'draft_extra_total_s':s['C_QB']-s['M_QB'],'draft_prefill_s':dp(c),'target_prefill_C_minus_M_s':tp(c)-tp(m),'nonprefill_net_savings_s':(s['M_QB']-tp(m))-(s['C_QB']-tp(c)-dp(c)),'acceptance':accepted/proposed if proposed else None,'cycles':cyc['cycles'],'accepted':accepted,'proposed':proposed})
summary={}
for family in ['Qwen','SmolLM2']:
 for domain in ['CodeContests','GSM8K']:
  rr=[x for x in flat if x['family']==family and x['input'].startswith(domain)]
  summary[family+'/'+domain]={'n_blocks':len(rr),'D_QB_gm':math.exp(st.mean(math.log(x['D_QB'])for x in rr)),**{k:st.mean(x[k]for x in rr) for k in ['M_seconds','C_seconds','draft_extra_total_s','draft_prefill_s','target_prefill_C_minus_M_s','nonprefill_net_savings_s','acceptance','cycles']},'amortization_failure_blocks':sum(x['draft_extra_total_s']>0 and x['nonprefill_net_savings_s']>0 for x in rr),'draft_losing_blocks':sum(x['D_QB']<1 for x in rr)}
result={'native_records':len(r),'matched_input_session_blocks':len(G),'max_contrast_recompute_absolute_error':maxerr,'days':[1,2],'summary':summary,'per_block':flat,'warning':'Phases are host elapsed, not exclusive GPU critical path. Nonprefill net savings is an accounting residual, not measured decode-only causal gain; no future outcome feature may be used at admission.'}
(ROOT/'raw_scope_recomputed.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k!='per_block'},indent=2))
