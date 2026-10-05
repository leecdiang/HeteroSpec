"""Readable final reports from independently verified numerical tables."""
from common import *
def main():
    s=load(DOC/'RESULTS.json');facts=load(DOC/'DIAGNOSTIC_FACTS.json');freeze=load(DOC/'FREEZE_RECEIPT.json');assert s['status']=='PASS' and s['formal']==171
    def write(name,text):(DOC/name).write_text(text,encoding='utf-8',newline='\n')
    pairs='\n'.join(f"| {p} | {v['array_equal']}/57 | {v['endpoint_equal']}/57 | {v['joint_equal']}/57 | {v['all_three_equal_tasks']}/19 |" for p,v in s['comparisons'].items())
    changed=[r['task'] for r in s['task_table'] if r['N0_N1_changed']]
    tails=facts['raw_post_endpoint_sample_tails'];tailids=sum(map(len,tails.values()))
    write('STUDY_REPORT.md',f'''# RTX matched-configuration target-only bridge

**{s['outcome']}**. All **171/171** fresh formal runs passed independent raw verification. Engineering: 12; additional diagnostic generations: 0; failed attempts: 0; retries: 0; formal restarts: 0.

This study is based on PR #54 at `{PIN}` and is stacked on `codex/manuscript-intervention-reconstruction-v010`. The pre-formal implementation/protocol freeze is `{freeze['commit']}`. PR #53/#54, all inherited evidence, and the manuscript are unchanged.

## Question and execution

Does ordinary draft-free target-only U2 reproduce native intervention N1 under matched current RTX settings, and how does its agreement differ from N0? The retrospective lead was recomputed: historical U2=N0 51/57; U2=N1 57/57. Historical U2 actually used 12 threads. The present comparison uses 24 generation and 24 batch threads, including explicit supported draft settings on N paths. This is an exposed cohort, not a discovery on unseen tasks or a thread-causality experiment.

All 19 prescribed HumanEval tasks ran in three conditions and three fresh-process repetitions. Condition orders were N0/N1/U2, N1/U2/N0, U2/N0/N1. One GPU queue, no warmup, no process/KV reuse; the OS file cache was not flushed. Exact argv, effective settings and input bindings are retained per run.

N0 uses the existing qualified native UB2 prefill/draft, k=2 and UB2→UB2 sham. N1 preserves the same first-pending sample/accept and handoff while changing target continuation to UB1. U2 is the released ordinary CLI with global UB2, its own initialization/prefill/continuation, and no draft model, transplant, proposal tape or supplied answer. Target-only caller grouping was observed rather than changed to force agreement.

Hardware: RTX 5070 Ti Laptop GPU, 12,227 MiB, UUID `GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd`; driver 616.92; Windows 11 build 26300; Python 3.11.9. Target Qwen3-8B-Q8_0 and draft Qwen3-0.6B-Q8_0 hashes match the specified assets. Runtime b10839 is pinned to `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`. All 54 released runtime files and the prior native frontend match their hashes; post-execution readback passes all 80 asset bindings. Raw logs confirm CUDA0 target 37/37 layers and N draft 29/29, 24-thread numerical pools, ctx=4096, batch=2048, F16 KV and FA off. HTTP housekeeping uses 23 threads and is separate.

Twelve local engineering runs passed independent capture/input/config/handoff checks on /15, /25, /18 and /31. Unchanged instrumentation reuses its prior qualified 120-array/30-sham evidence; that larger campaign was not rerun. Seven meaningful negative verifier tests passed. U2=N1 and N0=N1 were never qualification gates.

## Fresh results

| Pair | Full arrays | EOS/limit endpoints | Joint equality | All three equal task units |
|---|---:|---:|---:|---:|
{pairs}

N0, N1 and U2 each have 19/19 stable tasks across all three repetitions. Tasks are the scientific units; the 57 pairs are repeated observations, not independent samples. Full arrays include the terminal EOG ID, or all 128 committed IDs at the cap. Endpoint equality compares EOS/limit separately; lengths and terminal IDs remain in the array comparison.

Changed N0/N1 tasks: {', '.join(changed)}. Both changed tasks agree with U2 in all three repetitions (6/6 observations). The other 17 tasks are output no-ops. Predicting N1=N0 achieves 17/19 tasks and 51/57 observations, compared with U2's 19/19 and 57/57. These finite exposed-case differences do not establish a general predictive method. COMPARISONS.json gives every length, zero-based first divergence and endpoint; unequal-length difference count is positional substitutions over the common length plus the absolute length difference, divided by max length for its fraction.

| Case | N0 / N1 / U2 lengths | First N0/N1 divergence | Old UB1 reference relationship |
|---|---|---|---|
| /15 | 25 / 28 / 28 | index 15: 9147 → 4199 | U2=N1 restores reference; N0 differs |
| /25 | 75 / 75 / 75 | index 4: 1406 → 271 | N0 matches reference; U2=N1 moves away |
| /18 | 69 / 69 / 69 | none | all three still differ from reference |

There are no new U2/N1 mismatches or instabilities. Fresh N0 and N1 each match their pinned historical counterpart in 57/57 arrays/endpoints. Fresh U2 at 24 threads matches historical U2 at 12 threads in 57/57; this is an observational bridge. Old-reference agreement remains 51/57 for each current condition. Reproduction fidelity does not erase /25's failed restoration objective.

The runtime logs contain zero committed IDs beyond the contract endpoint. The traces additionally retain {tailids} uncommitted target samples beyond the committed prefix in {len(tails)} native records; full sampled lists, decisions and tails remain inspectable and are excluded from equality. No raw tail was silently discarded.

## Diagnosis and decision

Existing formal captures suffice for the bounded exploratory /15, /25, /18, /31 selection; no extra generations were needed. For these cases, N0/N1 first-pending source KV and full pending logits are byte-equal. At /15 and /25, the first divergent target decision flips the top candidate while the native caller still contains three tokens. Captured continuation occupied tokens are [1,2] for N0 and [1] for N1; U2 post-first-commit batch dumps have length 1 despite UB2 capacity. U2 graph tensors and live KV/logits are unobserved. These observations are consistent with a caller/occupied-shape numerical explanation, but do not uniquely prove causation or equal later prefix state. DIAGNOSTICS.md preserves exact scores and alignment limits.

Ordinary U2 is sufficient to reproduce N1 on this matched exposed cohort. This weakens the novelty of the complex RTX P/R predictor for that objective. The result is consistent with ordinary deterministic greedy re-execution using the shared numerical backend; it does not rule out that simple explanation or establish an equivalence theorem. **Stop pursuing a new-method novelty claim or more 57/57 checks through this route.** A later study would need a concrete useful decision and a frozen construction rule tested against ordinary target-only and the no-op baseline on new tasks/configurations. No demonstrated utility here justifies launching that study now.

No speedup, energy benefit, actual VRAM reduction, functional accuracy, reference restoration in general, bitwise state equality or cross-platform generality is claimed.

## Evidence and limits

The independent CPU verifier imports no controller/capture/comparison helper, reparses all 171 selected raw records, verifies 1,596 per-run file bindings, recomputes all tables and reparses 114 restored historical native logs. A separate settings audit covers 183 engineering/formal records and 122 handoffs. Hashes establish supplied content consistency, not independent authentication of omitted weights/runtime binaries, physical execution or absolute time. Opaque sampler state and live U2 internals remain unavailable.

Compact arrays, task tables, protocol/input/asset/freeze bindings and reports are reviewable directly in Git. Full raw evidence uses Git-backed CAS parts under `artifacts/rtx_target_only_bridge_v1`. REPRODUCIBILITY.md gives restoration commands. Final archive/readback/delivery receipts are later Git objects, outside the archive snapshot they describe; see their exact coverage before claiming delivery complete.
''')
    diag='''# Bounded exploratory diagnostics

The full 171-run matrix completed before exploratory selection. The frozen rule selected /15, /25, /18 and /31; no new U2/N1 mismatch or instability took priority. Additional diagnostic generations: 0/12. Existing formal N captures already contain the available detailed state witnesses; repeating the same paths would not provide richer U2 state.

| Path / phase | Observed caller lengths | Callback occupied tokens |
|---|---|---|
| N0 target continuation | 1, 3 | 1, 2 |
| N1 target continuation | 1, 3 | 1 |
| N0/N1 draft continuation | 1, 3 | 1, 2 |
| U2 after first commit | logged batch dumps: 1 | unavailable |

U2's UB2 capacity is not an observation of two occupied graph tokens. Its logger includes caller and split-batch dumps; those counts are distinct from N tensor callback dimensions. For all four selected cases, the first U2 prefill dump spans the complete input (91, 151, 111, 129 tokens respectively), with additional split dumps of sizes 1/2. Grouping was not replaced or forced to match N.

'''
    for t,d in facts['selected'].items():
        v=d['comparisons']['N0/N1'];diag+=f"## {t}\n\nN0/N1 lengths: {v['left_length']} / {v['right_length']}; endpoints: {v['left_endpoint']} / {v['right_endpoint']}. U2=N1: {d['comparisons']['U2/N1']['joint_equal']}. Original first-pending source KV equality: {d['first_pending_source_bytes_equal']}; full pending-logit equality: {d['first_pending_logits_bytes_equal']}. These are captured live initial states, not a new prefill of a later shared prefix.\n\n"
        if v['first_divergence'] is None:diag+='No divergent committed decision exists. /18 remains different from the old reference; /31 is the unchanged cap-128 control. Equal outputs do not prove equal internal continuation states.\n\n'
        else:
            diag+=f"First divergence: zero-based index {v['first_divergence']}, IDs {v['left_id']} / {v['right_id']}.\n\n| Condition | Selected ID | Top 1 (score) | Top 2 (score) | Caller length / UB | Positions / logits index |\n|---|---:|---|---|---|---|\n"
            for c in ['N0','N1']:
                dec=d[c+'_first_divergent_decision'];sample=dec['sample'];batch=dec['preceding_live_decode'];diag+=f"| {c} | {sample['selected_id']} | {sample['top1']} ({sample['top1_score']:.6f}) | {sample['top2']} ({sample['top2_score']:.6f}) | {batch['caller_batch']} / {batch['ub_capacity']} | {batch['positions']} / {sample['logits_index']} |\n"
            diag+='\nBoth native paths have the same committed prefix at this sampled decision ordinal. The original caller tokens, positions/masks, actual proposals, rollback endpoints and selected scores remain in DIAGNOSTIC_FACTS.json and raw traces. Full live KV at this later point was not serialized. Speculative lookahead must not be conflated with the committed-prefix state. A correlated score/shape difference is not unique causal identification.\n\n'
    diag+=f'''## Interpretation and unavailable state

N0/N1 preserve initial handoff state while changing observed target continuation capacity/graph shape. The first output divergences associate with different target top candidates. U2's ordinary single-token continuation agrees with N1 at every formal endpoint; shared greedy numerical execution and occupied shape are plausible explanations. Equal outputs cannot establish identical KV, logits, sampler or kernel execution, and accumulated numerical differences remain an alternative.

Unavailable: live U2 KV/logits/sampler/occupied graph tensors; complete serialized KV at the later divergent N decision; opaque sampler bytes. No fresh prefix was presented as an original live state, and no major runtime intervention was built. The {tailids} recorded uncommitted target samples in {len(tails)} native runs are retained independently of committed arrays. Diagnostic records never replace formal arrays or change the denominator.
'''
    write('DIAGNOSTICS.md',diag)
    print(json.dumps({'status':'REPORTS_RENDERED','formal':171,'raw_uncommitted_samples':tailids}),flush=True)
if __name__=='__main__':main()
