#!/usr/bin/env python3
"""No inference. Count two specified k=3, no-EOG trajectories and naive retention."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--prompt-tokens',type=int,default=512);p.add_argument('--output-cap',type=int,default=128);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.prompt_tokens<=0 or a.output_cap<=0:raise ValueError('positive sizes required')
r=[]
for mode in ('all_accept','reject_j0'):
    base=a.prompt_tokens;emitted=1;lengths=[base];commits=[base];cycles=0
    while emitted<a.output_cap:
        lengths.extend(base+j for j in range(1,5))
        remaining=a.output_cap-emitted
        accepted=min(3,remaining) if mode=='all_accept' else 0
        added=accepted if mode=='all_accept' and remaining<=3 else accepted+1
        emitted+=added;base+=1+accepted;commits.append(base);cycles+=1
    leaf_lengths=[max(lengths)] if mode=='all_accept' else ([a.prompt_tokens] if not cycles else [a.prompt_tokens+i+4 for i in range(cycles)])
    for fam,v,bpt in [('Qwen',151936,144*1024),('SmolLM2',49152,192*1024)]:
        r.append({'family':fam,'scenario':mode,'prompt_tokens':a.prompt_tokens,'output_cap':a.output_cap,'cycles':cycles,
          'target_vector_uses_including_initial':len(lengths),'naive_fresh_reference_scalar_token_evaluations':sum(lengths),
          'fresh_maximal_path_jobs':len(leaf_lengths),'maximal_path_reference_scalar_token_evaluations':sum(leaf_lengths),
          'maximal_path_max_live_prefix_tokens':max(leaf_lengths),
          'ideal_single_copy_committed_KV_MiB_if_all_old_prefix_chunks_unchanged':max(commits)*bpt/2**20,
          'paired_candidate_reference_logits_MiB':2*len(lengths)*v*4/2**20,
          'naive_duplicated_paired_active_KV_GiB':2*sum(commits)*bpt/2**30,
          'notes':'Modeled no-EOG trajectory, not observed timing or obligatory storage. Counts initial plus each commit. Dense full duplication excludes metadata, free-run/R-repeat evidence, hidden backend state and model loading. Chunking/dedup/streaming can reduce retained bytes without skipping live comparisons.'})
with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
