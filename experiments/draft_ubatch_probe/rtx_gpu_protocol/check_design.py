#!/usr/bin/env python3
"""Check this unbound planning draft and arithmetic only; never load/run a model."""
import argparse,json
from pathlib import Path

def need(x,msg):
    if not x:raise ValueError(msg)
def count_reject0(prompt,cap,bpt,vocab):
    cycles=cap-1
    queried=[prompt]+[prompt+i+j for i in range(cycles) for j in range(1,5)]
    committed=[prompt+i for i in range(cap)]
    leaves=[prompt+i+4 for i in range(cycles)] if cycles else [prompt]
    return {'prompt_tokens':prompt,'cap':cap,'trajectory':'every_cycle_rejects_j0_no_EOG','cycles':cycles,
      'target_vector_uses':len(queried),'commit_snapshots':len(committed),'maximal_reference_jobs':len(leaves),
      'reference_tokens_excluding_H_and_free_R':sum(leaves),'free_R_tokens_excluding_H':prompt+cap-1,
      'paired_repeated_active_KV_GiB':2*sum(committed)*bpt/2**30,
      'paired_target_logits_MiB':2*len(queried)*vocab*4/2**20,
      'excludes':'raw serialization/canonical duplication, H, repetitions, metadata, hidden state, process/setup and runtime measurements'}
def check(root):
    p=json.loads((root/'BENCHMARK_PLAN.json').read_text())
    need(p['status']=='NOT_READY_FOR_GPU' and p['execution_authorized_in_this_task'] is False,'this checker only accepts non-executing design drafts')
    phases={x['name']:x for x in p['phases']};totals={}
    for name in ['G1','G2','G3']:
        x=phases[name]
        main=x.get('main_free_and_control_requests_max',0)+x.get('heavy_requests_max',0)+x.get('provisional_timed_requests_max',0)
        refs=x.get('forced_and_internal_oracle_jobs_max',x.get('forced_reference_jobs_max',0))
        n=main+refs+x['autonomous_R_runs_max']+x['stability_runs_max']
        need(n==x['setup_count_bound'],'setup bound mismatch '+name)
        totals[name]={'setup_max':n,'H0_priming_max':0,'H1_priming_max':n}
    samples=[]
    for fam,bpt,v in [('Qwen3-8B_nominal_F16',144*1024,151936),('SmolLM2-1.7B_nominal_F16',192*1024,49152)]:
        for prompt,cap in [(32,8),(128,16),(512,16)]:samples.append(dict(family=fam,**count_reject0(prompt,cap,bpt,v)))
    need(samples[0]['reference_tokens_excluding_H_and_free_R']==273,'small reference count')
    need(samples[0]['target_vector_uses']==29 and samples[0]['commit_snapshots']==8,'small capture count')
    blockers=['GPU adapters/extractor not implemented or qualified','old-R bridge identity and budget unbound','H recipe and primary family unbound','device output/model/executable paths not verified','host RSS/peak GPU/disk/time limits and worst storage bound unbound']
    return {'status':'DRAFT_ARITHMETIC_CHECKED_NOT_READY_FOR_GPU','new_native_or_GPU_executions':0,'phase_setup_bounds':totals,'modeled_cases':samples,'remaining_blockers':blockers,'not_claimed':'GPU runtime readiness, qualification, time/FLOP prediction, guaranteed completion within proposed budgets'}
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
    with args.output.open('x') as f:json.dump(check(args.root),f,indent=2);f.write('\n')
