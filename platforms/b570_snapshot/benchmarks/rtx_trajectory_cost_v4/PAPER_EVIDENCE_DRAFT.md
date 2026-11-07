# Paper evidence draft: RTX V4 / A19_B19

This is a proposed paper addition derived from the independently verified new study. The frozen manuscript is unchanged. Earlier V3 terminal prefixes are excluded from every denominator below.

| A comparison against native batched live | Exact full-array pairs | Entirely exact prompts |
|---|---:|---:|
| Target-only UB2 | 51/57 | 17/19 |
| Independent per-round P/R | 57/57 | 19/19 |
| Fresh R-only replay | 57/57 | 19/19 |
| Target reference UB1 | 51/57 | 17/19 |

A completed all 285 planned conditions. 2 of 19 prompts have at least one full-array disagreement between the UB1 reference and native batched live. All five A conditions are repeat-stable: True. H2 and fresh R-only agree on 57/57 pairs. Exact first-divergence indices and IDs remain in the full report.

| B path against reference | Exact full-array pairs | Qualification | Speedup (reference/candidate) | 95% paired bootstrap CI |
|---|---:|---|---:|---|
| Native batched k=2, UB2 | 51/57 | BLOCKED | null | null |
| Native serialized k=2, UB1 | 57/57 | QUALIFIED | 0.677351 | [0.661653, 0.691812] |

B completed all 171 new conditions. It shares the 19 task IDs with A, while all B observations are fresh. The three-repeat median is computed per prompt; qualified speedups are the geometric mean of reference/candidate ratios. The 10,000 bootstrap draws resample paired prompts using frozen seed 2026100204. The interval describes resampling uncertainty within this exposure-conditioned finite cohort.

## Suggested manuscript paragraph

We conducted a prospective RTX study on all 19 remaining exposure-audited HumanEval prompts, with three repetitions per condition. Before any native batched live run, we froze and fully retrieved all 228 pre-live arrays and proposal tapes. Independent replay reproduced the per-round P/R outputs on all 57 pairs. Native batched live then completed 57 fresh runs; the UB1 reference differed from it on 2 prompts.
The predefined Target-only UB2 candidate matches 51/57 complete-array pairs across 17/19 wholly exact prompts and does not predict every native live array.
The predefined Independent per-round P/R candidate matches 57/57 complete-array pairs across 19/19 wholly exact prompts and matches every native live array and also distinguishes the observed reference-divergent cases.
In a separate matched-cost schedule, Native batched k=2, UB2 matched 51/57 full-array pairs and failed the complete-cohort qualification requirement; its speedup and interval are therefore withheld (null). Retained timings for this path are diagnostic observations only.
In a separate matched-cost schedule, Native serialized k=2, UB1 passed all 57 output-equivalence pairs and had a measured instrumented post-prefill latency ratio of 0.677351 (reference/candidate; 95% paired-prompt bootstrap interval [0.661653, 0.691812]).

## Scope of supported claims

At initial selection, the cohort comprised all 19 remaining unexposed prompts after conservative exclusion of 145 tasks. Continuation reuses the unchanged predictor observations rather than introducing another unexposed cohort. It is not a random sample from HumanEval or a representative population. There are 19 distinct prompts; 456 formal conditions and three repeated runs per condition are not 456 independent samples. A and B do not form independent prompt cohorts.

The results concern two predefined trajectory candidates on one frozen model/runtime/device configuration. Complete agreement supports finite-cohort empirical sufficiency only; disagreement rejects universal sufficiency on that cohort. Neither outcome establishes necessity, uniqueness, minimality, a theorem, or cross-backend generalization.

Cost intervals exclude loading, initial prefill and teardown, and include the retained instrumented execution, logging, responses and synchronization inside the timer boundary. Observer on/off checks establish output stability on engineering inputs; clock-call tests do not bound total logging overhead. These measurements support instrumented request latency only, with no throughput, energy or unrestricted deployment claim. A qualified ratio above one means the candidate is faster; an interval including one does not resolve the direction within this bootstrap calculation.

All complete arrays, first divergences, native logs, per-round proposal tapes, timers, device observations, source snapshots, process ledger and F0/F1/F2/B_START retrieval proofs are preserved in the author evidence capsules. Anonymous capsules permit derived offline recomputation with explicit privacy and chronology limits.


**Provenance note.** Completion is under a disclosed host-policy amendment after predictor capture. The original predictor observations and strict-host stop remain unchanged; fresh native and B observations follow the sealed prediction checkpoint. See [audit appendix](HOST_POLICY_AUDIT_APPENDIX.md) for the fan-policy adjustment, authorization, chronology and recorded timing scope.
