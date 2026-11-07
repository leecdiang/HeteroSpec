"""Paper-ready finite-cohort conclusions from completed independently checked results."""
import json
from prepare import ROOT,STUDY,save,now
import verify_joint

def main():
    verified=verify_joint.all_reached(ROOT)
    a=json.loads((STUDY/'A_trajectory/REPORT.json').read_text(encoding='utf-8'))
    b=json.loads((STUDY/'B_matched_cost/REPORT.json').read_text(encoding='utf-8'))
    if not a.get('execution_complete') or not b.get('execution_complete'):
        raise RuntimeError('Complete fixed A/B schedules required for this paper draft')
    n=a['distinct_prompts'];den=3*n
    assert n==b['distinct_prompts']==19 and a['valid_complete_runs']==285 and b['valid_complete_runs']==171
    labels={'UB2_live':'Target-only UB2','H2_live':'Independent per-round P/R','R_ONLY_live':'Fresh R-only replay','reference_live':'Target reference UB1'}
    lines=['# Paper evidence draft: RTX V4 / A19_B19','',
           'This is a proposed paper addition derived from the independently verified new study. The frozen manuscript is unchanged. Earlier V3 terminal prefixes are excluded from every denominator below.','',
           '| A comparison against native batched live | Exact full-array pairs | Entirely exact prompts |',
           '|---|---:|---:|']
    for k,label in labels.items():
        v=a['comparisons'][k];lines.append(f"| {label} | {v['exact_pairs']}/{v['total_pairs']} | {v['wholly_exact_prompts']}/{n} |")
    diverg=a['reference_divergent_prompts'];stable=all(a['repeat_stability'].values())
    lines+=['',f"A completed all 285 planned conditions. {len(diverg)} of {n} prompts have at least one full-array disagreement between the UB1 reference and native batched live. All five A conditions are repeat-stable: {stable}. H2 and fresh R-only agree on {a['comparisons']['H2_R_ONLY']['exact_pairs']}/{den} pairs. Exact first-divergence indices and IDs remain in the full report.",'',
            '| B path against reference | Exact full-array pairs | Qualification | Speedup (reference/candidate) | 95% paired bootstrap CI |',
            '|---|---:|---|---:|---|']
    names={'B_BATCHED_K2_UB2':'Native batched k=2, UB2','B_SERIALIZED_K2_UB1':'Native serialized k=2, UB1'}
    for k,v in b['paths'].items():
        speed='null' if v['speedup'] is None else f"{v['speedup']:.6f}"
        ci='null' if v['CI'] is None else f"[{v['CI'][0]:.6f}, {v['CI'][1]:.6f}]"
        lines.append(f"| {names[k]} | {v['exact_pairs']}/{v['total_pairs']} | {v['status']} | {speed} | {ci} |")
    lines+=['','B completed all 171 new conditions. It shares the 19 task IDs with A, while all B observations are fresh. The three-repeat median is computed per prompt; qualified speedups are the geometric mean of reference/candidate ratios. The 10,000 bootstrap draws resample paired prompts using frozen seed 2026100204. The interval describes resampling uncertainty within this exposure-conditioned finite cohort.','',
            '## Suggested manuscript paragraph','',
            f"We conducted a prospective RTX study on all {n} remaining exposure-audited HumanEval prompts, with three repetitions per condition. Before any native batched live run, we froze and fully retrieved all 228 pre-live arrays and proposal tapes. Independent replay reproduced the per-round P/R outputs on all {den} pairs. Native batched live then completed {den} fresh runs; the UB1 reference differed from it on {len(diverg)} prompts."]
    for k in ['UB2_live','H2_live']:
        v=a['comparisons'][k];status=a['candidates'][k]['status']
        claim={'MATCH_DISCRIMINATING':'matches every native live array and also distinguishes the observed reference-divergent cases','MATCH_NONDISCRIMINATING':'matches every native live array, although this cohort contains no reference-divergent case','PARTIAL_MATCH':'does not predict every native live array'}[status]
        lines.append(f"The predefined {labels[k]} candidate matches {v['exact_pairs']}/{den} complete-array pairs across {v['wholly_exact_prompts']}/{n} wholly exact prompts and {claim}.")
    for k,v in b['paths'].items():
        if v['status']=='QUALIFIED':
            lines.append(f"In a separate matched-cost schedule, {names[k]} passed all {den} output-equivalence pairs and achieved an instrumented post-prefill latency ratio of {v['speedup']:.6f} (reference/candidate; 95% paired-prompt bootstrap interval [{v['CI'][0]:.6f}, {v['CI'][1]:.6f}]).")
        else:lines.append(f"In a separate matched-cost schedule, {names[k]} matched {v['exact_pairs']}/{den} full-array pairs and failed the complete-cohort qualification requirement; its speedup and interval are therefore withheld (null). Retained timings for this path are diagnostic observations only.")
    lines+=['','## Scope of supported claims','',
            'The cohort consists of the entire remaining unexposed pool after conservative exclusion of 145 tasks. It is not a random sample from HumanEval or a representative population. There are 19 distinct prompts; 456 formal conditions and three repeated runs per condition are not 456 independent samples. A and B do not form independent prompt cohorts.','',
            'The results concern two predefined trajectory candidates on one frozen model/runtime/device configuration. Complete agreement supports finite-cohort empirical sufficiency only; disagreement rejects universal sufficiency on that cohort. Neither outcome establishes necessity, uniqueness, minimality, a theorem, or cross-backend generalization.','',
            'Cost intervals exclude loading, initial prefill and teardown, and include the retained instrumented execution, logging, responses and synchronization inside the timer boundary. Observer on/off checks establish output stability on engineering inputs; clock-call tests do not bound total logging overhead. These measurements support instrumented request latency only, with no throughput, energy or unrestricted deployment claim. A qualified ratio above one means the candidate is faster; an interval including one does not resolve the direction within this bootstrap calculation.','',
            'All complete arrays, first divergences, native logs, per-round proposal tapes, timers, device observations, source snapshots, process ledger and F0/F1/F2/B_START retrieval proofs are preserved in the author evidence capsules. Anonymous capsules permit derived offline recomputation with explicit privacy and chronology limits.','']
    (STUDY/'PAPER_EVIDENCE_DRAFT.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    save(STUDY/'PAPER_EVIDENCE_LINKAGE.json',{'status':'PASS','utc':now(),'A_conditions':285,'B_conditions':171,'distinct_prompt_count':19,'original_manuscript_modified':False,'old_V3_prefix_included':False,'independent_result_status':verified['status'],'exact_author_reports':['A_trajectory/REPORT.json','B_matched_cost/REPORT.json'],'draft':'PAPER_EVIDENCE_DRAFT.md'})
    print('Paper evidence draft PASS',flush=True)
if __name__=='__main__':main()
