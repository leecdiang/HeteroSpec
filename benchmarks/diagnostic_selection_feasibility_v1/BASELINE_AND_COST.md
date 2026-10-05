# Baselines and cost break-even

No qualified latency saving is measured. Counts below are retained model-record equivalents requested through a CPU-only replay. Repeats assess stability; workloads are the diagnosis units. The strongest available baseline is ordinary reference fallback for reference compatibility, or direct verification of the single native B570 action if retaining speculation is required. Reference fallback is exact by construction within the retained reference contract, not a new inference or functional-accuracy result.

All comparators receive the same paid reference/baseline observation budget: 114 records for RTX19, 144 for B57024, 144 for the separate MBPP24 supplement. Previously stored data costs only CPU reads here; prospective acquisition is separately accounted. The fixed reference is never changed. Actual full-action output comparison supplies final verification; adding a fresh independent replication would add the same explicit validation term to every selected action.

The shared-acquisition table conditions on having performed the diagnostic audit. A standalone ordinary reference fallback can skip native baseline diagnosis and all candidate/proxy runs: its cold cost is simply `C_reference_execution + C_reference_validation` (or valid retained-reference reuse). Thus equal common O in the table is conservative to fallback, not evidence that a selector is required to access reference behavior. Retaining speculation requires a separate declared operational reason.

| Main context / comparator | Repair / baseline deviations | New deviations / matching controls | Persistent deviations | Workload decision | Additional available records after common acquisition |
|---|---:|---:|---:|---|---:|
| RTX19 no change | 0/2 | 0/17 | 2 | Fail | 0 |
| RTX19 reference fallback | 2/2 | 0/17 | 0 | Reference-compatible by definition | 0 (reference already acquired) |
| RTX19 U2 | 1/2 | 1/17 | 1 | Fail | 57 |
| RTX19 N1 | 1/2 | 1/17 | 1 | Fail | 57 |
| RTX19 enumeration N1,U2 | No selected repair | No selected regression | Baseline retained | Abstain | 114 |
| RTX19 enumeration U2,N1 | Same | Same | Same | Abstain | 114 |
| RTX19 P2 H1-screen then U2 | No selected repair | No selected regression | Baseline retained | Abstain; N1 unqueried | 114 (57 H1 + 57 U2) |
| B57024 no change | 0/4 | 0/20 | 4 | Fail | 0 |
| B57024 reference fallback | 4/4 | 0/20 | 0 | Reference-compatible by definition | 0 |
| B57024 ordinary U2 | UNKNOWN | UNKNOWN | UNKNOWN | Unknown: all 72 cells missing | 0 (72 requested but unavailable) |
| B57024 enumeration N1 | 4/4 | 0/20 | 0 | Select N1 | 72 |
| B57024 P2 T1 then N1 | 4/4 | 0/20 | 0 | Select N1 | 144 (72 T1 + 72 N1) |

No post-hoc per-task mixture is permitted. RTX could repair /15 by N1/U2 and retain /25 by N0 only by selecting per task after knowing labels; that is not a feasible configuration-level policy. The MBPP supplement has N0/N1 reference matches 22/24, no repaired task, no newly divergent control, two persistent deviations. Its U2 remains UNKNOWN on 72/72 cells. Both enumeration orders and P2 abstain with unknown coverage. This supplement is not merged into the main contexts or disguised as a new holdout.

## What numerical work was actually observed

RAW_WORK_INVENTORY.json directly counts all 114 restored bridge native traces and all 171 bound result records. For **each** of N0 and N1 (57 runs): target prefill 57 decode calls evaluating 10,287 tokens; draft prefill 57 calls/10,287 tokens; target continuation 1,710 calls/5,118 tokens; draft continuation 5,118 calls/8,526 tokens. Target-continuation occupied shapes are 1,704 occurrences of 2 tokens plus 1,710 of 1 for N0, versus 5,118 occurrences of 1 for N1. Per-call graph-token sums equal caller token counts. These are observed forward-shape occurrences, not unique kernel launches or latency estimates.

Both conditions have 57 transfers, summing 1,517,053,989 serialized payload bytes each. This is a state-format payload sum, not measured PCIe traffic, time or VRAM reduction. Committed output counts are N0 4,830; N1 and U2 4,839 each. U2 has 57 ordinary target-only processes, no draft and no handoff; detailed U2 graph-forward counts are unavailable. Native target work totals 15,405 evaluated caller tokens per condition; draft totals 18,813. A mere reduction of native run count cannot be equated with avoiding this numerical work.

Four old H1 spot records have separately bound P/R wire streams and draft/target request activity. The RTX proxy is a two-worker draft-plus-target verification execution, not a free token predictor. B570 T1 removes the draft, but full prefill/continuation target execution and state transfer remain. Detailed comparable B570 work counts are not reconstructed here; its inherited qualified source/verification receipts establish the path, not a speed advantage. CPU parser/test durations and instrumented run timestamps cannot establish GPU savings.

## Symbolic comparison with strong baselines

Let O include fixed-reference and baseline observation costs, P_j a proxy workload execution, N_j actual native candidate execution, U ordinary U2, S selector/setup cost, and V comparable independent verification. Use

`C_method = C_setup + C_observation + C_probes + C_selection + C_validation`.

For the observed B570 success, enumeration costs `O + N + V`; P2 costs `O + S + P + N + V`. For nonnegative added work, P2 adds `S + P` and has no selection-cost advantage on this successful one-action workload. Future early rejection cannot justify today's accepted-case saving. For observed RTX rejection of N1 plus rejection of U2, enumeration in either order costs `O + N + U + V_E`; P2 costs `O + S + P + U + V_P`. It can beat enumeration only if `P + S + (V_P−V_E) < N`, while accepting its potentially false proxy-rejection risk. This is an unmeasured possibility, not an established gain. Against just U2, the proxy cannot improve the measured output result; it adds P. Against reference fallback, no demonstrated retained-speculation benefit has been established.

For a one-action prospective distribution with proxy acceptance probability p, screening has cost `S + P + p*N + V_P`, enumeration `N + V_E`; screening wins only if `S + P + (V_P−V_E) < (1−p)*N`. For two actual actions, replace the right side by the cost of actual candidate execution **avoided at the same success/risk contract**; no artificial large search space is assumed. A cheap partial probe is not currently qualified as a replacement for full-workload verification.

Plausible regime (purely illustrative assumptions, no measurements): `P=0.2N`, `p=0.1`, negligible extra selection/validation; rejecting most unsuccessful candidates could help. Unfavorable regime: `P≥N`, or `p≈1`, or extra validation/false-rejection risk erases avoided N. B570 observed screening acceptance is 1/1 workload; RTX H1 repeats substantial native numerical work, so cheap-proxy assumptions have no measured support. These ratios are symbolic examples, not latency values.

For m genuinely independent uses with stable qualified configurations, `C_setup/m + C_per_use` can amortize one-time parser/tool setup. Reference/baseline acquisition, workload-dependent probes and validation still recur unless the exact workload/configuration remains reusable. Initial proxy qualification and raw-capture machinery must be amortized only over applicable configurations. No deployment volume m is assumed. Memorizing a decision on the same exposed workload also amortizes enumeration; it is not new generalization.

No historical RTX V4 0.677351, 358H ceiling or M4 timing enters this accounting. If the engineer later supplies a concrete reason to retain speculation, the smallest cost check is a same-boundary comparison of P, N, U/reference, setup and required validation on that declared use case. It is not authorized or executed here, and current evidence does not justify launching it automatically.
