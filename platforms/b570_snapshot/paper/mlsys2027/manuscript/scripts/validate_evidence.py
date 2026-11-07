#!/usr/bin/env python3
"""Independent replay from frozen raw/pair records. Outputs only manuscript QA."""
from pathlib import Path
from collections import defaultdict
import csv,json,math,random,statistics,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parents[2]/'evidence'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def csvread(p):return list(csv.DictReader((ROOT/p).open(encoding='utf-8-sig')))
def gm(x):return math.exp(statistics.fmean(math.log(v) for v in x))
def bootstrap(v,n,seed,lo,hi):
 rng=random.Random(seed);b=sorted(gm([rng.choice(v) for _ in v]) for _ in range(n));return [b[lo],b[hi]]
checks=[]
def check(label,actual,expected,tol=1e-12):
 if isinstance(actual,(list,tuple)):
  assert len(actual)==len(expected),(label,actual,expected)
  error=max(abs(a-b) for a,b in zip(actual,expected))
 else:error=abs(actual-expected)
 assert error<tol,(label,actual,expected,error)
 checks.append({'check':label,'actual':actual,'expected':expected,'max_absolute_error':error,'pass':True})
# M4: reconstruct paired ratios and exact token comparisons from archived runs.
for tag,p,summ,cond,taskfield,order,n,seed,lo,hi in [
 ('M4-24','work/m4/llama_confirmatory_24q.json','analysis/m4_confirmatory_summary.json','k2','question_id',None,10000,20260907,249,9749),
 ('M4-HE','artifacts/m4_humaneval_code_conditioned/results.json','analysis/m4_humaneval_summary.json','fixed_k2','task_id',None,100000,20260910,2500,97499)]:
 d=read(p);s=read(summ);order=d['selection']['question_ids'] if tag=='M4-24' else d['preregistration']['dataset']['task_ids']
 if tag=='M4-HE':s=s['conditions']['fixed_k2']
 by={(r[taskfield],r['repetition'],r['condition']):r for r in d['runs']};v=[];ev=[];exact=0
 for t in order:
  sr=[];er=[]
  for rep in [1,2,3]:
   b=by[t,rep,'baseline'];a=by[t,rep,cond];sr.append(b['metrics']['decode_ms']/a['metrics']['decode_ms']);exact+=b['tokens']==a['tokens']
   er.append(b['metrics']['energy_per_output_token']['package_j_per_token']/a['metrics']['energy_per_output_token']['package_j_per_token'])
  v.append(gm(sr));ev.append(gm(er))
 key='geomean_speedup' if tag=='M4-24' else 'prompt_geomean_speedup';ci='bootstrap_95_ci' if tag=='M4-24' else 'prompt_bootstrap_95_ci'
 check(tag+' speed',gm(v),s[key]);check(tag+' CI',bootstrap(v,n,seed,lo,hi),s[ci]);check(tag+' token exact',exact,s['exact_pairs']);check(tag+' faster prompts',sum(x>1 for x in v),s['faster_prompts'])
 if tag=='M4-HE':
  check(tag+' energy',gm(ev),s['prompt_geomean_energy_efficiency_ratio']);check(tag+' energy CI',bootstrap(ev,n,seed,lo,hi),s['energy_bootstrap_95_ci'])
  # Registered secondary energy in appendix.
  ev=[]
  for t in order:
   ev.append(gm([by[t,r,'baseline']['metrics']['energy_per_output_token']['package_j_per_token']/by[t,r,'k2_pmin_0.9']['metrics']['energy_per_output_token']['package_j_per_token'] for r in [1,2,3]]))
  sec=read(summ)['conditions']['k2_pmin_0.9'];check('M4 secondary energy',gm(ev),sec['prompt_geomean_energy_efficiency_ratio']);check('M4 secondary energy CI',bootstrap(ev,n,seed,lo,hi),sec['energy_bootstrap_95_ci'])
# RTX: retained committed pair-level data, frozen numeric task sort.
rr=csvread('reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.csv')
for s in read('reports/5070ti/windows_humaneval_summary.json')['summaries']:
 groups=defaultdict(list);r=[x for x in rr if x['condition']==s['condition']]
 for x in r:
  ratio=float(x['baseline_decode_ms'])/float(x['spec_decode_ms']);check(s['condition']+' pair '+x['task_id']+' '+x['repetition'],ratio,float(x['paired_speedup']));groups[x['task_id']].append(ratio)
 v=[gm(groups[k]) for k in sorted(groups,key=lambda x:int(x.split('/')[1]))]
 check(s['condition']+' GM',gm(v),s['geomean_speedup']);check(s['condition']+' CI',bootstrap(v,10000,20260910,249,9749),[s['ci95_low'],s['ci95_high']]);check(s['condition']+' exact',sum(x['exact_match']=='True' for x in r),s['exact_pairs']);check(s['condition']+' faster',sum(x>1 for x in v),s['faster_prompts'])
# B570: original archived pair insertion order, NOT sorted prompt CSV.
p='artifacts/b570_backend_control/exact-fallback-v1-20260912-222617/exact_fallback/processed/humaneval30_exact_fallback.json';d=read(p);s=read('analysis/b570_exact_fallback_summary.json')
for field,stat,point in [('speedup','performance','prompt_geometric_mean_speedup'),('board_energy_ratio','energy','prompt_geometric_mean_efficiency_ratio')]:
 groups={}
 for x in d['pairs']:groups.setdefault(x['task_id'],[]).append(x[field])
 v=[gm(x) for x in groups.values()];check('B570 '+field,gm(v),s[stat][point]);check('B570 '+field+' CI',bootstrap(v,10000,20260910,250,9750),s[stat]['bootstrap_95_ci'])
runs={r['run_id']:r for r in d['runs']};exact=sum(runs[p['baseline_run_id']]['tokens']==runs[p['speculative_run_id']]['tokens'] for p in d['pairs']);check('B570 actual token arrays exact',exact,60)
check('B570 wholly exact prompts',sum(all(p['exact'] for p in d['pairs'] if p['task_id']==k) for k in groups),20)
# Direct 358H processed observations and complete round traces.
r=csvread('analysis/358h_phase3_prompt_summary.csv');rounds=csvread('analysis/358h_phase3_rounds.csv');s=read('analysis/358h_phase3_summary.json')
for dev in ['CPU','NPU']:
 group={};xs=[x for x in r if x['condition']==dev+'_DRAFT_K2']
 for x in xs:group.setdefault(x['task_id'],[]).append(float(x['baseline_end_to_end_ms'])/float(x['end_to_end_ms']))
 v=[statistics.median(g) for g in group.values()];a=np.asarray(v);draw=np.random.default_rng(20260919).choice(a,(10000,len(a)),replace=True);ci=[float(np.quantile(np.exp(np.mean(np.log(draw),axis=1)),q)) for q in [.025,.975]]
 check('358H '+dev+' GM',gm(v),s['performance'][dev]['geometric_mean_speedup']);check('358H '+dev+' CI',ci,s['performance'][dev]['bootstrap_ci95']);check('358H '+dev+' exact flags',sum(x['exact']=='True' for x in xs),90);check('358H '+dev+' faster',sum(x>1 for x in v),0)
 rr=[x for x in rounds if x['device']==dev];committed=sum(int(x['C']) for x in rr);c=committed/len(rr);check('358H '+dev+' direct C',c,s['acceptance'][dev]['mean_committed_tokens_per_round_C'])
 total=sum(float(x['end_to_end_ms']) for x in xs);base=sum(float(x['baseline_end_to_end_ms']) for x in xs);tb=base/committed
 terms=[]
 for f,k in [('draft_replay_proposal_ms','draft_replay_plus_proposal'),('verification_ms','target_verification'),('orchestration_residual_ms','orchestration_residual')]:
  component=sum(float(x[f]) for x in xs);check('358H '+dev+' '+k+' fraction',component/total,s['decomposition'][dev]['fractions_of_speculative_time'][k]);terms.append(component/len(rr)/tb)
 check('358H '+dev+' accounting identity',c/sum(terms),base/total)
# Forward microbenchmarks and immutable vendor/data lineage.
for x in csvread('reports/5070ti/WINDOWS_EXACT_VERIFICATION_COST.csv'):check('RTX micro '+x['path']+' depth '+x['context_depth'],float(x['pp2_median_ms'])/float(x['pp1_median_ms']),float(x['T_verify2_over_T_decode1']))
for c in read(str((E/'published_values.json').relative_to(ROOT)))['claims']:
 for p,digest in c['sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest,p
vendor=E.parent/'manuscript/vendor'
for line in (vendor/'SHA256SUMS').read_text().splitlines():
 h,p=line.split('  ',1);assert hashlib.sha256((vendor/p).read_bytes()).hexdigest()==h,p
(E/'NUMERICAL_QA.json').write_text(json.dumps({'status':'PASS','checks':checks,'count':len(checks),'method':'Independent read-only replay; original estimator, bootstrap order, RNG, endpoint conventions retained. Source arrays or committed derived records used as indicated; no new experiments.'},indent=2)+'\n')
print(f'PASS: {len(checks)} numerical comparisons; source hashes and untouched official style verified.')
