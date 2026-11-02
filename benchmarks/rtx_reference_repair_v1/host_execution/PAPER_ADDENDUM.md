# Addendum: mechanism-led Qwen3-14B Q8 reference repair

This standalone addendum reports the RTX reference-repair successor to PR156.
It does not modify the existing manuscript or erase the original failed pilot.
The deployment reference remains the original PR156 UB1 worker and its numerical
DLL cohort, using the same Qwen3-14B Q8 target, Qwen3-0.6B Q8 draft, tokenization,
greedy/EOG contract, cap128, F16 KV and fixed partial offload.

Canonical UB1 prefill and state transfer alone did not remove the counterexamples.
The first complete 96-request development matrix retained failures, including a
new divergence of the canonical-prefill C path on GSM8K/test/111. Same-boundary,
same-seed localization with explicit logical-row alignment and trace/no-trace
controls found a discrepancy after identical normalized K operands. The scheduler
assigned K RoPE to CPU for the original single-token path and CUDA for the batched
path. Captured RoPE outputs differed in 851 of 1024 F32 elements, with maximum
absolute difference 2.3126602172851562e-05. Eight native exact-operand replays
reproduced both own paths and their cross-backend counterparts. Layer10 was the
first captured layer-output discrepancy, not a proven globally earliest operator.

The mechanism was a row-count-dependent offload preference for Q/K head-normalization
scaling, with assignment propagation to RoPE. The repair queries the original
preference on a read-only one-token geometry copy for this operator class in scoped
target calls with two to four token rows. Actual tensor shapes, data and arithmetic
remain intact; R/q1, inactive draft and other operators retain their original path.
No task, token, layer-number or logit-margin exception is used. The scheduler's
static component changes, while the 21 numerical DLLs remain unchanged and the
optional Q8 rowwise matmul primitive stays disabled. The selected candidate uses
native prefill and retains useful batched/speculative execution.

After intervention, the eight-request ablation matched R at all 40 captured layer
outputs and final logits on the mapped row. All 96 development requests preserved
the fixed reference, with 48 stable observer pairs. The original 12-input Qwen3-8B
regression completed 144 requests with reference preservation. The Llama regression
matched its historical endpoints, transactions and 2356 saved full vectors; its
known CodeContests/valid/108 C-path counterexample remains a failure against R.
A failed fresh-context capture attempt and its full 24-request reservation were
retained before an ordinary lifetime fix and a new native regression build.

The candidate was frozen before any 14B output on the preselected confirmation
panel. The original PR156 binary produced 24 heavy/off references for the same 12
inputs, followed by 120 candidate qualification requests. All required endpoints
and observer pairs agreed. Four separately loaded process sessions then completed
all 288 measurements and 288 matched warmups with no dropped or repeated blocks.

Complete resident-request cost includes reset, prefill, repair dispatch, decode,
verification, reconciliation, synchronization and result assembly. Model loading
and pool provisioning are recorded separately, and heavy observation is absent
from timing. Across all 48 equally weighted input/session blocks, the geometric
mean C_QB/R cost ratio was 0.32045134 and M_QB/R was 0.45681960. The same-layout
M_QB/C_QB and M_PQ/dual-C_PQ ratios were 1.42555060 and 1.40338759, respectively.

The primary QB/mean(PQ_A,PQ_B) ratio was 0.97388972, a 2.611% reduction. Although
every session mean favored QB, the maximum input-aggregate absolute A/A imbalance
was 3.384%. Thus the preregistered practical-layout screen, requiring a reduction
above max(2%, A/A imbalance), **did not pass**. Reference repair and lower request
cost than R do not establish a separately resolved practical QB-over-PQ advantage.
All reversals and slow blocks remain in the complete results.

The new study conservatively charged 1140 of 1200 slots, including 420 of 480
development/recovery/regression slots; original PR156's 40 requests remain separate.
Finite-panel reference preservation is not a universal greedy-equivalence theorem.
This is one host and one fixed panel, without a population confidence interval or
cross-study pooling. Scheduler assignments do not establish kernel occupancy.
Independent decoding/hash/cost recomputation is performed on the same host and is
not independent-laboratory replication. See [execution results](RESULTS.md) for
the complete accounting, internal-path correspondence, raw evidence and delivery
verification.
