#!/usr/bin/env python3
"""Deterministic post-data analysis for the frozen 358H Phase-3 campaign."""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]

def digest(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
 return h.hexdigest()
def gm(xs): return float(math.exp(np.mean(np.log(xs))))
def ms(x): return x/1e6
def boot(vals,seed=20260919,n=10000):
 rng=np.random.default_rng(seed); a=np.asarray(vals,float); samples=rng.choice(a,(n,len(a)),replace=True)
 return [float(np.quantile(np.exp(np.mean(np.log(samples),axis=1)),q)) for q in (.025,.975)]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--campaign-dir',type=Path,required=True); ap.add_argument('--analysis-dir',type=Path,default=ROOT/'analysis'); a=ap.parse_args()
 raw=a.campaign_dir/'observations.resolved.json'; rows=json.loads(raw.read_text(encoding='utf-8'))
 status=json.loads((a.campaign_dir/'FORMAL_PHASE3_STATUS.json').read_text(encoding='utf-8'))
 if not status.get('complete') or len(rows)!=270: raise RuntimeError('campaign is incomplete')
 base={(r['task_id'],r['repetition']):r for r in rows if r['condition']=='TARGET_BASELINE'}
 if len(base)!=90: raise RuntimeError('expected 90 baselines')
 a.analysis_dir.mkdir(exist_ok=True)
 prompt_out=[]; round_out=[]; summary={'schema':'heterospec.358h.phase3.summary.v2','status':'COMPLETE','campaign_directory':str(a.campaign_dir),
  'formal_phase3_data_seen':True,'protocol':{'runner_sha256':status['runner_sha256'],'driver_sha256':status['driver_sha256'], 'dataset_sha256':status['dataset_sha256'], 'output_cap':128,'k':2,'bootstrap':{'resamples':10000,'seed':20260919,'unit':'HumanEval prompt; input is each prompt median paired speedup'}},
  'correctness':{},'performance':{},'acceptance':{},'decomposition':{},'energy':{'CPU_DRAFT_K2':'NOT_CLAIMED: no qualified end-to-end boundary','NPU_DRAFT_K2':'NOT_ADMISSIBLE'}}
 for device in ('CPU','NPU'):
  cond=f'{device}_DRAFT_K2'; spec=[r for r in rows if r['condition']==cond]
  exact=[r for r in spec if r['exact_vs_baseline']]
  by_task=defaultdict(list); divergences=[]; speedups=[]
  for r in spec:
   b=base[(r['task_id'],r['repetition'])]; sp=b['timing']['end_to_end_ns']/r['timing']['end_to_end_ns']; speedups.append(sp); by_task[r['task_id']].append((r,sp))
   if not r['exact_vs_baseline']: divergences.append(r['first_divergence'])
   prompt_out.append({'task_id':r['task_id'],'repetition':r['repetition'],'condition':cond,'formal':True,'admissible':bool(r['exact_vs_baseline']),'exact':r['exact_vs_baseline'],
    'generated_token_ids_sha256':hashlib.sha256(json.dumps(r['generated_token_ids'],separators=(',',':')).encode()).hexdigest(),
    'baseline_end_to_end_ms':ms(b['timing']['end_to_end_ns']),'end_to_end_ms':ms(r['timing']['end_to_end_ns']),'speedup':sp,
    'draft_replay_proposal_ms':ms(r['timing']['draft_replay_proposal_ns']),'verification_ms':ms(r['timing']['target_verification_ns']),'orchestration_residual_ms':ms(r['timing']['orchestration_residual_ns']),
    'proposed_tokens':r['proposed'],'accepted_draft_tokens':r['accepted'],'rounds':len(r['rounds']),'realized_c':sum(q['C'] for q in r['rounds'])/len(r['rounds'])})
   for q in r['rounds']:
    round_out.append({'task_id':r['task_id'],'repetition':r['repetition'],'device':device,'round_id':q['round_id'],'prefix_before':q['prefix_before'],'proposals':len(q['proposals']),'accepted':q['accepted'],'C':q['C'],'correction':q['correction'] is not None,'bonus':q['bonus'] is not None,'initial_target_only':q['native_initial_target_only'],'draft_replay_proposal_ms':ms(q['draft_replay_proposal_ns']),'target_verification_ms':ms(q['target_verification_ns'])})
  prompt_medians=[float(np.median([sp for _,sp in values])) for values in by_task.values()]
  all_rounds=[q for r in spec for q in r['rounds']]; gen=sum(len(r['generated_token_ids']) for r in spec); base_gen=sum(len(r['generated_token_ids']) for r in base.values())
  timings={k:np.array([r['timing'][k] for r in spec],float) for k in ('end_to_end_ns','draft_replay_proposal_ns','target_verification_ns','orchestration_residual_ns')}
  base_ns=np.array([base[(r['task_id'],r['repetition'])]['timing']['end_to_end_ns'] for r in spec],float)
  accepted=sum(r['accepted'] for r in spec); proposed=sum(r['proposed'] for r in spec); committed=sum(q['C'] for q in all_rounds); rc=Counter(q['accepted'] for q in all_rounds)
  summary['correctness'][device]={'status':'PASS' if len(exact)==90 else 'FAIL','exact_pairs':len(exact),'total_pairs':90,'exact_prompts':sum(all(r['exact_vs_baseline'] for r,_ in v) for v in by_task.values()),'total_prompts':30,'mismatch_pairs':90-len(exact),'mismatch_prompts':sum(not all(r['exact_vs_baseline'] for r,_ in v) for v in by_task.values()),'first_divergences':divergences}
  summary['performance'][device]={'claim_status':'CORRECTNESS_ADMISSIBLE','geometric_mean_speedup':gm(prompt_medians),'median_prompt_speedup':float(np.median(prompt_medians)),'bootstrap_ci95':boot(prompt_medians), 'faster_prompts':sum(x>1 for x in prompt_medians),'total_prompts':30,'faster_pairs':sum(x>1 for x in speedups),'total_pairs':90,'baseline_ms_per_token':float(np.sum(base_ns)/base_gen/1e6),'speculative_ms_per_token':float(np.sum(timings['end_to_end_ns'])/gen/1e6),'baseline_tok_s':float(base_gen/(np.sum(base_ns)/1e9)),'speculative_tok_s':float(gen/(np.sum(timings['end_to_end_ns'])/1e9))}
  summary['acceptance'][device]={'drafted_tokens':proposed,'accepted_draft_tokens':accepted,'weighted_acceptance_rate':accepted/proposed,'total_speculative_rounds':len(all_rounds),'rounds_by_accepted_draft_tokens':{str(k):rc[k] for k in (0,1,2)},'bonus_rounds':sum(q['bonus'] is not None for q in all_rounds),'correction_rounds':sum(q['correction'] is not None for q in all_rounds),'committed_output_tokens':committed,'mean_committed_tokens_per_round_C':committed/len(all_rounds)}
  summary['decomposition'][device]={'units':'ms per request, arithmetic mean across 90 paired observations','baseline_end_to_end_ms':float(np.mean(base_ns)/1e6),'speculative_end_to_end_ms':float(np.mean(timings['end_to_end_ns'])/1e6),'draft_replay_plus_proposal_ms':float(np.mean(timings['draft_replay_proposal_ns'])/1e6),'target_verification_ms':float(np.mean(timings['target_verification_ns'])/1e6),'orchestration_residual_ms':float(np.mean(timings['orchestration_residual_ns'])/1e6),'fractions_of_speculative_time':{'draft_replay_plus_proposal':float(np.sum(timings['draft_replay_proposal_ns'])/np.sum(timings['end_to_end_ns'])),'target_verification':float(np.sum(timings['target_verification_ns'])/np.sum(timings['end_to_end_ns'])),'orchestration_residual':float(np.sum(timings['orchestration_residual_ns'])/np.sum(timings['end_to_end_ns']))},'limitation':'Replay-only and proposal-only are not separable: one synchronous OpenVINO LLMPipeline call performs both.'}
 def csvwrite(path, fields, data):
  with path.open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(data)
 csvwrite(a.analysis_dir/'358h_phase3_prompt_summary.csv',list(prompt_out[0]),prompt_out)
 csvwrite(a.analysis_dir/'358h_phase3_rounds.csv',list(round_out[0]),round_out)
 dec=[]
 for d,x in summary['decomposition'].items():
  dec.append({'device':d,**{k:v for k,v in x.items() if k not in ('fractions_of_speculative_time','limitation')},**{f'fraction_{k}':v for k,v in x['fractions_of_speculative_time'].items()}})
 csvwrite(a.analysis_dir/'358h_phase3_decomposition.csv',list(dec[0]),dec)
 (a.analysis_dir/'358h_phase3_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
