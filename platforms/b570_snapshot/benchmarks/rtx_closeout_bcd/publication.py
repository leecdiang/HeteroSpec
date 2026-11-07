"""Prepare a derived-only review payload; raw evidence stays in the local archive."""
import hashlib,json
from close_base import HERE,EOG,read,save,sha

OUT=HERE.parent.parent/'outputs'
PUBLIC='benchmarks/rtx_closeout_bcd/'

def main():
    audit=read(HERE/'generated/POST_AUDIT.json');assert audit['status']=='PASS'
    b=read(HERE/'generated/B_RESULTS.json');c=read(HERE/'generated/C_RESULTS.json');d=read(HERE/'generated/D_RESULTS.json')
    pilot=read(HERE/'generated/C4_PILOT_RESULTS.json');sel=read(HERE/'generated/C4_SELECTION.json')
    four=read(HERE/'generated/C4_RESULTS.json') if sel['status']=='RUN' else None
    long=read(HERE/'generated/C4_LONG_RESULTS.json') if four else None
    diag=read(HERE/'generated/C_BOUNDARY_DIAGNOSTICS.json')
    summary={k:v for k,v in diag.items() if k not in ['state_comparisons','crossings']}
    summary['source_evidence_sha256']=sha(HERE/'generated/C_BOUNDARY_DIAGNOSTICS.json')
    summary['state_comparisons']=[{'pair':x['pair'],'cut':x['cut'],'sampler_contract_equal':x['sampler_contract_equal'],
        **{k:x['comparison'][k] for k in ['layers','prompt_kv_equal','different_tensor_count','first_different_position']},'KV_tensor_count':len(x['comparison']['tensors'])} for x in diag['state_comparisons']]
    summary['crossings']=[]
    for x in diag['crossings']:
        item={k:v for k,v in x.items() if k not in ['native_call_tokens','decisions']}
        item['native_caller_token_count']=len(x['native_call_tokens'])
        item['decisions']=[{'donor':y['donor'],'current_query_batch':y['current_query_batch'],
           'EOS_in_local_decision':any(t in EOG for t in y['sampled_ids']),'accepted_proposals':y['accepted_proposals']} for y in x['decisions']]
        summary['crossings'].append(item)
    save(HERE/'generated/C_BOUNDARY_SUMMARY.json',summary)
    public_d={'stage':'D','qualified':d['qualified'],'requests':d['requests'],'warmups':d['warmups'],'reset_proof':d['reset_proof'],
       'source_evidence_sha256':sha(HERE/'generated/D_RESULTS.json'),
       'panels':{name:{k:v for k,v in p.items() if k!='details'} for name,p in d['panels'].items()}}
    save(HERE/'generated/D_PUBLIC_RESULTS.json',public_d)
    patch_summary={}
    for label,file,delta in [('C','C_PATCH_IDENTITY.json','changed_from_phase2'),('cross','CROSS_PATCH_IDENTITY.json','changed_from_C')]:
        p=read(HERE/'generated'/file)
        patch_summary[label]={'full_inventory_sha256':sha(HERE/'generated'/file),'source_files':len(p['source_inventory']),'changed_files':p[delta]}
    save(HERE/'generated/NATIVE_PATCH_SUMMARY.json',patch_summary)
    counts={'complete_generations':audit['all_complete_generation_requests'],'nonwarm':audit['panel_requests'],'warmups':audit['excluded_warmups'],'auxiliary_decodes':audit['paid_auxiliary_target_decode_calls']}
    result={'status':'FINITE_RTX_CLOSEOUT','B':b['qualification'],'C_passes':[{'k':x['k'],'ub':x['ub'],'cap':x['cap']} for x in c['configurations'] if all(x['qualification'].values())],
       'C_failed_task':'MBPP/229 at k5/UB6 and k7/UB8, all three caps and both repetitions',
       'additional_old_probe_failure':'HumanEval/18 target-alone and speculation at UB6/8; original-reference qualification fails',
       'D_k3_UB4':d['qualified'],'C2':read(HERE/'generated/C2_SELECTION.json'),'C3':read(HERE/'generated/C3_SELECTION.json'),
       'C4_pilot':pilot['qualification'],'C4_selection':sel,'C4_main':four['qualification'] if four else None,
       'C4_long':[{k:v for k,v in x.items() if k!='details'} for x in long['configurations']] if long else None,
       'C4_costs':four['costs'] if four else None,'costs_B':b['costs'],'costs_D':d['panels']['d']['costs'],'counts':counts,
       'closed_questions':['Prospectively unused project-task validation','Finite width and requested-length boundary','Original-profile persistent request reset','Natural-state local crossing','Fixed-UB lookahead isolation'],
       'limit':'One RTX/model/runtime/sampler/single-sequence finite panel. No functional correctness, universal optimality, unique operator, production throughput, new held-out C4 tasks or B570 results.'}
    save(HERE/'generated/CLOSEOUT_SUMMARY.json',result)
    def speed(x):return f"{x['generation']['task_median_geomean_speedup']:.4f}x generation / {x['wall']['task_median_geomean_speedup']:.4f}x whole request"
    lines=['# RTX B/C/D finite closeout','',
      'Widening native speculative calls can change the past state and lose the original scalar reference even when a matched target control passes. This study continues the manuscript and Phase 1/2 diagnosis with prospective task validation, width/length qualification, natural-state crossings, persistent requests, and a bounded fixed-microbatch amendment. The final result is a finite configuration boundary with measured costs.','',
      '## Results','',
      '- **B:** all 24 locked, previously unused sanitized MBPP tasks match repeated paid scalar references under all four conditions (384 requests + 16 warmups). Target scopes / matched target: '+speed(b['costs'][0])+'. Target scopes / all scopes: '+speed(b['costs'][2])+', below the predeclared 3% extra-generation gate.',
      '- **C:** k1/UB2 and k3/UB4 qualify at all three requested caps (128/256/512). MBPP/229 fails under k5/UB6 and k7/UB8 in every cap/repetition; all failures and costs remain. The topology probe HumanEval/18 also fails its original reference under UB6/8 in target-alone and speculative modes. Actual long reference lengths reach 261, not 512 tokens.',
      '- **Natural state crossing:** at 47 committed tokens of MBPP/229, two genuine donor states are crossed with two current UB6 query layouts. Both same-path shams per boundary pass. Swapping state changes the local EOS decision; swapping the current layout changes floating-point scores without changing that decision. This is local state evidence, not a unique operator or full-continuation proof.',
      '- **D:** the original k3/UB4 profile matches all 24 task references in two resident cycles in both capture-enabled reset qualification and separate timing runs. '+speed(d['panels']['d']['costs'])+'. D does not test higher k.',
      '- **Original optional C2/C3:** skipped by their frozen output gates. More constrained scopes failed to repair both selected wider cases. No failed outputs were replaced.','',
      '## Final parameter isolation','',
      'Original C changes k and UB together. C4 was declared after primary B/C/D and before all C4 forwards: fix numerical UB=4 and target scopes, test k3/5/7 on all 24 B tasks plus four old probes, two repeats. All three profiles pass complete-array/EOS qualification; actual k7 caller batches reach 8 while occupied microqueries remain 1–4 and constrained multiquery paths stay active. Capture costs are excluded.','']
    if four:
        extra=next(x for x in four['costs'] if x['denominator']=='anchor_speculation')
        lines += [f"Highest output-qualified k={four['selected_k']} was frozen before 448 independent balanced cost requests and 16 warmups. The same 28 pilot tasks are reused; no held-out or new unused-task claim.",'',
          '| Comparison | Costs | Full-reference qualified |','|---|---|---|']
        lines += [f"| {x['numerator']} / {x['denominator']} | {speed(x)} | {x['qualified']} |" for x in four['costs']]
        lines += ['',f"Predeclared extra-generation gate versus k3 (full reference, >=1.03x generation, >=1x whole request, >=3/4 faster repetitions): **{'PASS' if extra['practical_decode_gain'] else 'FAIL'}**.",'',
          'Final independent 11-task long validation pays scalar, matched target, and selected speculation at caps 256/512 with two repeats (132 + 6 warmups).','']
        lines += [f"- cap{x['cap']}: qualification {x['qualification']}; {speed(x['cost'])}; cost qualified {x['cost']['qualified']}." for x in long['configurations']]
    else:lines += ['No higher lookahead qualified; both confirmation panels were skipped.']
    lines += ['', 'No further RTX profile search follows this bounded amendment. Failed qualifications and failed speed gates are retained.','',
      '## Evidence and reproducibility','',
      f"Post-audit PASS: {counts['complete_generations']} complete generations ({counts['nonwarm']} nonwarm + {counts['warmups']} warmups), plus {counts['auxiliary_decodes']} paid auxiliary target decodes. The two bound models, 33 published DLLs, prior private/native sources and binaries, and exact request-runner identities remain verified. One offline C summary key-set error was corrected without any model rerun; its record is retained.",'',
      'Initial protocol/inputs were frozen before new B inference in private commit 7b8c6fb. C4 is explicitly a later bounded amendment, never a replacement of original C negatives. Public pre-output commits: 4c34dfc (C4 pilot) and 0ba7912 (selected C4 main/long manifest). Protocol, inputs and source identities retain their original hashes.','',
      'This PR adds only `benchmarks/rtx_closeout_bcd/` and leaves the manuscript and previous studies to the ongoing integration. `results/` and `tables/` contain derived summaries; the local full archive contains raw outputs, traces, exact private native source/binaries, corpus identity, frozen references and Git history. No weights, runtime binaries, raw telemetry, native token arrays or float dumps are committed here. Public B_INPUTS contains descriptions/prompts and zero-forward vocabulary tokenization, never solutions/tests.','',
      'Review artifacts: [Chinese report](REPORT.md), [closeout summary](results/CLOSEOUT_SUMMARY.json), [width/length](figures/width-length.svg), [qualified costs](figures/costs.svg), [state crossing](figures/state-crossing.svg).','',
      'Rehydrate the delivered CAS ZIP into a **new** directory using the included `rehydrate.py`; verify dependencies separately. Configure `HETEROSPEC_PHASE1_ROOT`, `HETEROSPEC_PHASE2_ROOT`, `HETEROSPEC_ASSET_ROOT`, and `HETEROSPEC_RTX_STUDY_ROOT`. `restore_runtime.py` checks and places the bound private executables and installed published DLLs. Python 3.11 is used; NumPy/Matplotlib are needed only for score analysis/figures. Models, the exact bound released runtime, and previous Phase 1/2 archives must already be available. The public code alone is not a portable CUDA rebuild.','',
      'Archived experiment runners intentionally refuse to overwrite run directories and require frozen clean Git heads. Evidence review/rehydration is separate from new model reruns: create a new checkout from `generated/FROZEN_HISTORY.bundle`, configure its dependencies, and preregister new output destinations before inference. Do not rerun exposure selection after these tasks have been executed.','',
      'The RTX closeout is scoped to this GPU, model pair, runtime, greedy seed, FA-off, single sequence, and finite tasks/configurations. It does not claim functional task correctness, universal losslessness, globally optimal k/scopes, unique operator causality, production throughput or cross-platform speed. B570 is the next separate platform study; its paid native reference and required scopes must be identified independently.','']
    (HERE/'README.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    entries=[]
    def add(path,content):entries.append({'path':PUBLIC+path,'mode':'100644','type':'blob','content':content})
    for p in sorted(HERE.glob('*.py')):add(p.name,p.read_text(encoding='utf-8'))
    for name in ['README.md','PROTOCOL.md','B_INPUTS.json','B_MANIFEST.json','SOURCE_BINDINGS.json','C_MANIFEST.json','D_MANIFEST.json','C2_PREOUTPUT_PLAN.json','C3_PREOUTPUT_PLAN.json','C4_PREOUTPUT_PLAN.json','C4_PILOT_MANIFEST.json','cross_block.h.txt']+(['C4_MANIFEST.json'] if four else []):
        add(name,(HERE/name).read_text(encoding='utf-8'))
    generated=['B_RESULTS.json','C_RESULTS.json','D_PUBLIC_RESULTS.json','C_BOUNDARY_SUMMARY.json','C_LOGIT_WITNESSES.json','C_TOPOLOGY_OUTPUT_COMPARISONS.json','C2_SELECTION.json','C3_SELECTION.json','C4_SELECTION.json','C4_PILOT_RESULTS.json','POST_AUDIT.json','CLOSEOUT_SUMMARY.json','C_BUILD_IDENTITY.json','CROSS_BUILD_IDENTITY.json','NATIVE_PATCH_SUMMARY.json','C_BRIDGE.json','C_ENGINEERING.json','ANALYSIS_FAILURE_01.json','HELPER_FAILURE_02.json','EXPOSURE_SUMMARY.json']+(['C4_RESULTS.json','C4_LONG_RESULTS.json','C4_WORK_COUNTS.json'] if four else [])
    for n in generated:add('results/'+n,(HERE/'generated'/n).read_text(encoding='utf-8'))
    add('REPORT.md',(OUT/'HeteroSpec_RTX_闭环_实验报告.md').read_text(encoding='utf-8'))
    for p in sorted(OUT.glob('HeteroSpec_RTX_闭环_*.csv')):add('tables/'+p.name,p.read_text(encoding='utf-8-sig'))
    for label,name in [('width-length','适用范围'),('costs','实际速度'),('state-crossing','状态交叉诊断')]+([('fixed-ub','固定UB速度')] if four else []):
        add('figures/'+label+'.svg',(OUT/f'HeteroSpec_RTX_闭环_{name}.svg').read_text(encoding='utf-8'))
    assert len({e['path'] for e in entries})==len(entries)
    save(HERE/'generated/PUBLISH_FINAL.json',entries)
    save(HERE/'generated/PUBLISH_EXPECTED_GIT_BLOBS.json',{e['path']:hashlib.sha1(b'blob '+str(len(e['content'].encode())).encode()+b'\0'+e['content'].encode()).hexdigest() for e in entries})
    body=['Wider native speculation can lose the original scalar reference even when its matched target control passes. This additive study completes the remaining RTX task, length/width and persistent-request gates from #60, then tests a bounded fixed-microbatch amendment derived from the state diagnosis. It retains the original negative boundaries and separates output qualification from practical extra speed.','',
       '**Results:** B qualifies all 24 pre-output exposure-audited MBPP tasks under four conditions and four balanced repeats. Original C qualifies k1/UB2 and k3/UB4 at caps128/256/512; MBPP/229 fails k5/UB6 and k7/UB8 at every cap/repeat. The topology probe HumanEval/18 also fails its original reference under UB6/8 in target-alone and speculative modes. D qualifies the original k3/UB4 profile in two resident cycles with separate reset capture and timing.','',
       '**Local state evidence:** naturally aligned MBPP/229 donor states at 47 committed tokens are crossed with two current UB6 layouts. All four same-path shams and source-unchanged checks pass. State swapping changes the local EOS decision; current-layout swapping changes scores without changing that decision. The two caps expose the same task/boundary, not independent cases. This is not a unique operator or full-continuation proof.','',
       '**Final fixed-UB amendment:** declared before C4 outputs and explicitly after primary B/C/D. Fixing UB4 qualifies k3/5/7 on all28 pilot tasks; actual k7 callers reach8 while occupied microqueries remain<=4. Highest qualified k7 is selected by outputs only, then checked in independent balanced sessions. The same tasks are reused, without a held-out-task claim.','']
    if four:
        extra=next(x for x in four['costs'] if x['denominator']=='anchor_speculation')
        body += ['| Complete-reference comparison | Generation | Whole request |','|---|---:|---:|']+[f"| {x['numerator']} / {x['denominator']} | {x['generation']['task_median_geomean_speedup']:.6f}x | {x['wall']['task_median_geomean_speedup']:.6f}x |" for x in four['costs'] if x['qualified']]
        body += ['',f"k7's practical extra-speed gate versus original k3 is **{'PASS' if extra['practical_decode_gain'] else 'FAIL'}**. All three constrained/target modes match full references; ordinary k7/UB4 fails MBPP/229, MBPP/274, HumanEval/25 and HumanEval/18, so its costs stay diagnostic. The independent cap256/512 scalar/target/selected confirmation is reported in the long results. No further RTX retuning follows.",'']
    body += [f"**Validation and scope:** {counts['complete_generations']} complete generations ({counts['nonwarm']} nonwarm, {counts['warmups']} warmups) plus {counts['auxiliary_decodes']} paid auxiliary target decodes. Post-audit PASS verifies both model identities, 33 released DLLs, prior source/binary assets, frozen runners, full counts and output endpoints. All failures, the offline zero-model summary correction, exact private source and raw records are retained in a separate content-addressed local archive. Original C2/C3 confirmation gates are skipped. No new reliable acceleration from relaxing draft scopes or increasing lookahead is claimed.",'',
       'Read `benchmarks/rtx_closeout_bcd/README.md`, `REPORT.md`, `results/CLOSEOUT_SUMMARY.json`, and the tables/figures. Only this additive directory is changed; the manuscript and earlier PRs remain in the user integration workflow. Weights, runtime binaries, raw telemetry and native output/float arrays are excluded from GitHub.','',
       'RTX closeout means the frozen questions have finite answers, including failures. It does not mean universal losslessness, functional code correctness, production throughput, globally optimal widths/scopes, journal acceptance or cross-platform validity. B570 is not run in this tranche and needs its own paid native reference and platform-specific qualification.','']
    (HERE/'generated/PR_BODY.md').write_text('\n'.join(body),encoding='utf-8',newline='\n')
    print({'public_files':len(entries),'characters':sum(len(e['content']) for e in entries),'counts':counts},flush=True)

if __name__=='__main__':main()
