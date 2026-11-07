"""Reviewer-authored retained-record arithmetic; no author code, bootstrap, or inference."""
from pathlib import Path
from collections import defaultdict, Counter
from statistics import median
import json,csv,math,hashlib,argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('package_root',type=Path,help='Frozen packet directory, or extracted anonymous scientific-package root')
parser.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
args=parser.parse_args();P=args.package_root.resolve();O=args.output_dir.resolve();O.mkdir(parents=True,exist_ok=True)
def src(rel):
 p=P/rel
 if p.is_file():return p
 if rel.startswith('science/'):return P/rel[len('science/'):]
 return p
def read(p):return json.loads(src(p).read_text())
def gm(v):return math.exp(sum(math.log(x) for x in v)/len(v))
def first(a,b):return next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)) if len(a)!=len(b) else None)
def quantile(v,q):
 s=sorted(v);t=q*(len(s)-1);i=int(t);return s[i]+(s[min(i+1,len(s)-1)]-s[i])*(t-i)
def stable(rows,arrayfn):
 groups=defaultdict(list)
 for r in rows:
  for condition,array in arrayfn(r).items():groups[(r['task_id'],condition)].append(array)
 return all(len(v)==3 and all(a==v[0] for a in v) for v in groups.values())
R={'method':'Independent Python standard-library direct arithmetic. No supplied analyzers/verifiers, bootstrap reruns, raw archive retrieval, or inference.'}
b=read('science/evidence/B570_original_H1.json')['rows'];print('B570 array keys',list(b[0]['arrays']))
keys=list(b[0]['arrays']);pred=next(k for k in keys if k!='reference' and k!='live');live='live'
if live not in keys:live=next(k for k in keys if 'live' in k)
R['B570_H1']={'rows':len(b),'prompts':len(set(x['task_id'] for x in b)),'predictor_live_equal':sum(r['arrays'][pred]==r['arrays'][live] for r in b),'reference_live_equal':sum(r['arrays']['reference']==r['arrays'][live] for r in b),'repeat_stable':stable(b,lambda r:r['arrays']),'lengths':sorted(set(len(a) for r in b for a in r['arrays'].values())),'divergences':[]}
for r in b:
 a=r['arrays']['reference'];l=r['arrays'][live];i=first(a,l)
 if i is not None and r['repetition']==1:R['B570_H1']['divergences'].append({'task':r['task_id'],'index':i,'common_length':min(len(a),len(l)),'positions_different':sum(x!=y for x,y in zip(a,l)),'positions_after_first':sum(a[j]!=l[j] for j in range(i+1,min(len(a),len(l))))})
R['B570_H1']['distinct_nonreference_positions']=sum(x['positions_different'] for x in R['B570_H1']['divergences'])
R['B570_H1']['strictly_after_first']=sum(x['positions_after_first'] for x in R['B570_H1']['divergences'])
f=read('science/evidence/B570_live_intervention.json')['rows'];scores=[(a,b) for r in f for a,b in zip(r['primary_scores'],r['alternate_scores'])];deltas=[b['top1_score']-a['top1_score'] for a,b in scores]
R['B570_fork']={'runs':len(f),'score_rows':len(scores),'reachable_decisions':sum(len(r['paired_decisions']) for r in f),'changed_score_runs':sum(r['primary_scores']!=r['alternate_scores'] for r in f),'raw_top1_changed_rows':sum(a['raw_top1_id']!=b['raw_top1_id'] for a,b in scores),'changed_immediate_decisions':sum(e['native']['committed_id']!=e['alternate']['committed_id'] or e['native']['accepted_proposal']!=e['alternate']['accepted_proposal'] for r in f for e in r['paired_decisions']),'continuation_changed_runs':sum(r['primary_ids']!=r['alternate_ids'] for r in f),'continuation_changed_prompts':len(set(r['task_id'] for r in f if r['primary_ids']!=r['alternate_ids'])),'abs_delta_median':median(abs(x) for x in deltas),'abs_delta_p95':quantile([abs(x) for x in deltas],.95),'abs_delta_max':max(abs(x) for x in deltas),'min_primary_margin':min(a['margin'] for a,b in scores),'min_alternate_margin':min(b['margin'] for a,b in scores),'projected_state_checks_all':all(r['state']['serialized_kv_equal'] and r['state']['source_unchanged'] for r in f),'later_cases':[]}
for r in f:
 i=first(r['primary_ids'],r['alternate_ids'])
 if i is not None and r['repetition']==1:R['B570_fork']['later_cases'].append({'task':r['task_id'],'fork_index':r['checkpoint_output_index'],'first_difference':i,'distance':i-r['checkpoint_output_index']})
v=read('science/evidence/RTX_V4.json');a=v['A'];lc='A_NATIVE_BATCHED_LIVE';conditions=list(a[0]['conditions']);R['RTX_V4_A']={'rows':len(a),'prompts':len(v['tasks']),'arrays':sum(len(r['conditions']) for r in a),'repeat_stable':stable(a,lambda r:{c:x['ids'] for c,x in r['conditions'].items()}),'agreements':{c:sum(r['conditions'][c]['ids']==r['conditions'][lc]['ids'] for r in a) for c in conditions},'failure_extents':[]}
for r in a:
 if r['repetition']!=1:continue
 l=r['conditions'][lc]['ids']
 for c in ['A_REFERENCE_UB1','A_TARGET_ONLY_UB2']:
  p=r['conditions'][c]['ids'];i=first(p,l)
  if i is not None:R['RTX_V4_A']['failure_extents'].append({'task':r['task_id'],'candidate':c,'index':i,'own_id':p[i] if i<len(p) else None,'live_id':l[i] if i<len(l) else None,'own_length':len(p),'live_length':len(l),'differences_common_extent':sum(x!=y for x,y in zip(p,l)),'extra_own_ids':max(0,len(p)-len(l))})
all_v4_arrays=[x['ids'] for r in a for x in r['conditions'].values()]+[r['ids'] for r in v['B']]
R['RTX_V4_A']['all_A_and_B_endpoints_valid']=all(0<len(ids)<=128 and not any(t in v['eog_ids'] for t in ids[:-1]) and (len(ids)==128 or ids[-1] in v['eog_ids']) for ids in all_v4_arrays)
R['RTX_V4_A']['hindsight_best_complete_array_prompts']=sum(any(r['conditions'][c]['ids']==r['conditions'][lc]['ids'] for c in ['A_REFERENCE_UB1','A_TARGET_ONLY_UB2']) for r in a if r['repetition']==1)
bb=v['B'];bg=defaultdict(list);ar={}
for r in bb:
 t=r['timer'];ms=1000*t['qpc_delta']/t['frequency'];assert abs(ms-t['milliseconds'])<1e-8;bg[(r['task_id'],r['condition'])].append(ms);ar[(r['task_id'],r['repetition'],r['condition'])]=r['ids']
cs=sorted(set(r['condition'] for r in bb));ref='B_TARGET_REFERENCE_UB1';ser='B_SERIALIZED_K2_UB1';m={k:median(x) for k,x in bg.items()};ratios=[m[(task,ref)]/m[(task,ser)] for task in v['tasks']]
R['RTX_V4_B']={'runs':len(bb),'gate_counts':{c:sum(ar[(task,j,c)]==ar[(task,j,ref)] for task in v['tasks'] for j in [1,2,3]) for c in cs},'reference_repeat_stable':all(ar[(task,1,ref)]==ar[(task,2,ref)]==ar[(task,3,ref)] for task in v['tasks']),'serialized_prompt_GM':gm(ratios),'serialized_faster_prompts':sum(x>1 for x in ratios),'reciprocal_relative_GM':1/gm(ratios),'order_position_counts':{c:[sum(s['order'][j]==c for s in v['schedule']) for j in range(3)] for c in cs},'timer_consistency_max_ms':max(abs(1000*r['timer']['qpc_delta']/r['timer']['frequency']-r['timer']['secondary_milliseconds']) for r in bb),'prompt_median_latency_seconds':{c:[quantile([m[(task,c)]/1000 for task in v['tasks']],q) for q in [0,.25,.5,.75,1]] for c in cs}}
rows=list(csv.DictReader(src('science/derived/358h_phase3_prompt_summary.csv').open()));R['358H']={}
for c in sorted(set(r['condition'] for r in rows)):
 z=[r for r in rows if r['condition']==c];pg=defaultdict(list);sg=defaultdict(list)
 for r in z:
  B=float(r['baseline_end_to_end_ms']);T=float(r['verification_ms']);D=float(r['draft_replay_proposal_ms']);X=float(r['orchestration_residual_ms']);assert B>0 and T>0 and D>=0 and X>=0
  assert abs(T+D+X-float(r['end_to_end_ms']))<=.01
  pg[r['task_id']].append(B/T);sg[r['task_id']].append(B/float(r['end_to_end_ms']))
 U=gm([median(x) for x in pg.values()]);Bt=sum(float(r['baseline_end_to_end_ms']) for r in z);Tt=sum(float(r['verification_ms']) for r in z);Dt=sum(float(r['draft_replay_proposal_ms']) for r in z);Xt=sum(float(r['orchestration_residual_ms']) for r in z);L=sum(int(r['rounds']) for r in z);N=sum(round(float(r['realized_c'])*int(r['rounds'])) for r in z);tb=Bt/N
 R['358H'][c]={'runs':len(z),'prompts':len(pg),'committed_IDs':N,'rounds':L,'realized_C':N/L,'D_normalized':Dt/(L*tb),'Rtarget_normalized':Tt/(L*tb),'X_normalized':Xt/(L*tb),'actual_prompt_GM':gm([median(x) for x in sg.values()]),'actual_pooled_total':Bt/(Tt+Dt+Xt),'prompt_GM_zero_other_cost_ceiling':U,'pooled_zero_other_cost_ceiling':Bt/Tt,'uniform_target_reduction_budget':1-U,'max_prompt_median_ceiling':max(median(x) for x in pg.values()),'prompt_median_ceilings_at_least_one':sum(median(x)>=1 for x in pg.values()),'individual_ceilings_at_least_one':sum(x>=1 for vv in pg.values() for x in vv),'max_component_sum_error_ms':max(abs(float(r['verification_ms'])+float(r['draft_replay_proposal_ms'])+float(r['orchestration_residual_ms'])-float(r['end_to_end_ms'])) for r in z),'exact_flags_all':all(r['exact']=='True' for r in z)}
inp=read('science/derived/inputs.json');mr=inp['M4'];groups=defaultdict(list)
for r in mr:groups[(r['workload_family'],r['task_id'],r['condition'])].append(r['end_to_end_ns'])
meds={k:median(vals) for k,vals in groups.items()};tasks=sorted(set((r['workload_family'],r['task_id']) for r in mr));mg=[];ma=[];mo=[];target_faster=[];fam=defaultdict(list)
for f,t in tasks:
 tar=meds[(f,t,'TARGET_ONLY')];al=meds[(f,t,'ALWAYS_SPEC_K2')];gu=meds[(f,t,'GUARD_K2')];mg.append(gu/al);ma.append(tar/al);mo.append(al/min(tar,al));fam[f].append(gu/al)
 if tar<al:target_faster.append({'family':f,'task':t,'target_seconds':tar/1e9,'always_target':al/tar,'guard_target':gu/tar,'all_three_guard_fallbacks':all(r['fallback_triggered'] for r in mr if r['workload_family']==f and r['task_id']==t and r['condition']=='GUARD_K2')})
R['M4']={'observations':len(mr),'prompts':len(tasks),'all_original_medians_match':all(meds[(r['workload_family'],r['task_id'],c)]==r[k] for r in inp['M4_original_medians'] for c,k in [('TARGET_ONLY','target_median_ns'),('ALWAYS_SPEC_K2','always_median_ns'),('GUARD_K2','guard_median_ns')]),'target_always_speedup_GM':gm(ma),'guard_always_latency_GM':gm(mg),'guard_faster_prompts':sum(x<1 for x in mg),'always_faster_prompts':sum(x>1 for x in mg),'always_oracle_GM':gm(mo),'two_fixed_mode_reduction_fraction':1-1/gm(mo),'guard_fallback_count':sum(r['fallback_triggered'] for r in mr if r['condition']=='GUARD_K2'),'family_guard_always_GMs':{k:gm(v) for k,v in fam.items()},'target_faster_subset':target_faster}
for file,label in [('science/evidence/RTX_H2.json','RTX_V2'),('science/evidence/RTX_H1_discovery.json','RTX_H1_discovery')]:
 d=read(file);z=d['rows'];keys=list(z[0]['arrays']);live='RTX_BATCHED_K2';R[label]={'rows':len(z),'prompts':len(set(r['task_id'] for r in z)),'agreements':{c:sum(r['arrays'][c]==r['arrays'][live] for r in z) for c in keys},'repeat_stable':stable(z,lambda r:r['arrays'])}
files=['manuscript-v0.9.0.pdf','appendix-v0.9.0.pdf','overleaf-diagnostic-revision-v0.9.0.zip','anonymous-evidence-index-v0.9.0.zip','REVIEW_RUBRIC.txt','FIXED_PACKET.json','manuscript-v0.9.0.pdf.txt','appendix-v0.9.0.pdf.txt','science/README_V090.txt','science/INDEX_V090.json','science/SHA256SUMS_V090.json','science/INDEX.json','science/evidence/B570_original_H1.json','science/evidence/B570_live_intervention.json','science/evidence/RTX_V4.json','science/evidence/RTX_H2.json','science/evidence/RTX_H1_discovery.json','science/evidence/RTX_matched_latency.json','science/derived/inputs.json','science/derived/358h_phase3_prompt_summary.csv']
R['input_hashes']={f:hashlib.sha256(src(f).read_bytes()).hexdigest() for f in files if src(f).is_file()}
if src('FIXED_PACKET.json').is_file():
 expected=read('FIXED_PACKET.json')['files'];assert all(R['input_hashes'][f]==d['sha256'] for f,d in expected.items())
(O/'EVIDENCE_INDEPENDENT_CALCULATIONS.json').write_text(json.dumps(R,indent=2)+'\n')
print(json.dumps({k:v for k,v in R.items() if k!='input_hashes'},indent=2))
