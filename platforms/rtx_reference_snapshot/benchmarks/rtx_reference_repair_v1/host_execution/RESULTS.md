# RTX reference repair: native execution results

The Qwen3-14B Q8 reference counterexamples were repaired by stabilizing the
scheduler's offload preference for target Q/K head-normalization scaling. The
original PR156 reference, model, numerical DLL cohort, prompts and panels were
preserved. Native development, regressions, 120-request unseen-input qualification,
and all four timing sessions completed. **The separate practical QB-over-PQ layout
benefit screen did not pass:** the measured reduction was 2.611%, below the
3.384% A/A threshold. This negative performance-screen outcome is retained.

The starting Draft PR158 head was verified as
`798ba41c09ac503faa690f134e618df96bfa2063`. This result is a separate successor;
PR158 and earlier PRs are not merged. The original PR156 forty-request failure
and its placement correction remain separate historical evidence.

## Native mechanism and intervention

The first roles=0 build passed capacity admission but its complete 96-request
development matrix failed. Canonical UB1 prefill fixed some paths while making
GSM8K/test/111 C/reference diverge at output index16; native M paths retained the
old index16/82 failures and native C retained the GSM120 index82 failure. Reverse
PQ/QB producer-to-R controls also retained failures. No failed cell was removed.

Same-state first-seed localization on exposed GSM111 used the same serialized
boundary KV, pending token and absolute position92. R ordinary row0 and C verify
row0 were explicitly mapped. Trace/no-trace controls preserved full decision
vectors, endpoints, transactions and states. The first captured layer-output
discrepancy was `l_out-10`; this is not a claim about the globally earliest
unobserved intermediate difference.

The aligned normalized K operands matched, but K RoPE was scheduled on CPU for
R and CUDA0 for C. Its output differed in 851/1024 F32 elements, maximum absolute
difference `2.3126602172851562e-05`. Eight native operator replays reproduced both
own paths and crossed the exact captured operands between CPU and CUDA: CPU on
four-token operands reproduced R's first row, while CUDA on one-token operands
reproduced C's first row. Repeats agreed. Actual scheduler assignments establish
the observed backend distinction; CUDA_Host buffer ownership is not used as a
substitute, and no kernel occupancy or bottleneck fraction is inferred.

The pinned CUDA preference threshold is 32 rows. Eight K heads cross it at four
tokens, whereas forty Q heads already cross it at one token. Scheduler propagation
changes the following RoPE backend. `repair_offload.hpp` therefore queries the
original predicate with a read-only one-token geometry copy for scoped-target
Q/K normalization MUL operations with 2..4 token rows. Actual graph shapes, tensor
data and arithmetic operations remain intact. R/q1, inactive draft and unrelated
operations retain their original predicate. There are no task, answer-token,
layer-number or margin exceptions. The Q8 rowwise matmul primitive remains disabled.

The selected policy was native prefill, prospectively selected before epoch03
outputs. It does not route every request through a canonical serial producer.
The repaired eight-request ablation matched R at all 40 captured layer outputs and
final norm/logits; all natural endpoints and observer controls agreed. The full
96-request development matrix then preserved R in all 48 heavy/off pairs, including
sham and reverse-producer controls. See the frozen [mechanism record](MECHANISM.json),
[operator replay](EPOCH02_ROPE_REPLAY_AUDIT.json),
[ablation](EPOCH03_ABLATION_AUDIT.json) and
[development audit](DEVELOPMENT03_AUDIT.json).

## Validation and retained failures

| Stage | Requests/reservations | Actual outcome |
|---|---:|---|
| Initial roles=0 development |96| Failed reference cells retained; all observer pairs stable |
| Same-state localization and operand capture |20| Paired observations and logical-row mapping retained |
| Native RoPE operator replay |8 conservative charges;0 model requests| Own-path and cross-backend reproduction |
| Repaired ablation |8| All40 layer checkpoints and final logits match R on mapped row |
| Repaired development |96| All recipes preserve R;48 stable observer pairs |
| Original Qwen3-8B regression |144| All preserve pinned R;72 stable observer pairs |
| Failed Llama regression attempt |24 reserved|15 complete records,16th active without final record; entire reservation charged |
| Fresh corrected Llama regression |24| All match historical behavior and 2356 full vectors; known four C-path failures against R remain |
| Original PR156 held-out references |24|12 stable heavy/off pairs from unchanged original EXE/DLLs |
| Frozen candidate qualification |120| All preserve original R;60 stable observer pairs |
| Four timing sessions |576|288 measured plus288 matched warmups; complete Cartesian panel, all endpoints preserve R |

The first Qwen8B admission failed before generation because a regression adapter
incorrectly bound 32 layers instead of the authenticated 36. The corrected adapter
and a fresh epoch retain that failure. The first Llama attempt exposed diagnostic
state capture after fresh-context destruction (`c0000005`). A new Llama build
captures live state into owned bytes before teardown and writes it afterward,
outside service timing. Its natural decode/acceptance loop is byte-identical.
All failed partial artifacts remain failure evidence, not qualification.

The original Llama CodeContests/valid/108 C_PQ/C_QB counterexample is still a
counterexample (four heavy/off requests against R). Historical-behavior equivalence
is not relabeled reference preservation. The two Llama controls and original R/sham
remain preserved. CPU/source tests support the engineering changes but do not
replace the native builds, admissions, model requests or vector audits.

Candidate freeze occurred at `2026-11-01T18:10:41.484276Z`, before held-out exposure
at `18:11:31.702110Z`. The exact original 12 inputs were used; no failed panel or
reference was replaced. The frozen mechanism's journal hashes are as-of freeze;
immutable prefix snapshots accompany the subsequently appended shared journals.

## Complete request cost

Primary results use all 48 input/session blocks, with equal log weights. PQ is the
arithmetic mean of its two identical A/B implementations within each block.
Warmups are retained but never promoted to measurements. Ratios below1 indicate
lower request cost for the numerator, except M/C, which is the measured speedup
from adding the C speculative path to the same-layout M path.

| Ratio | Geometric mean |
|---|---:|
| C_QB / mean(C_PQ_A,C_PQ_B) |0.9738897151|
| M_QB / C_QB |1.4255505980|
| M_PQ / mean(C_PQ_A,C_PQ_B) |1.4033875923|
| C_QB / R |0.3204513415|
| M_QB / R |0.4568196014|
| C_PQ_A / C_PQ_B |1.0178535217|

QB/PQ session means were 0.9716008284,0.9649689581,0.9772948731 and0.9817756985.
All four favor QB, but its pooled 2.61102849% reduction is below
`max(2%,3.38351626%)`. **Practical layout gain: false.** This is the predeclared
finite-panel engineering screen, not a population confidence interval. No slow
block, reversal, input or session was dropped and no timing request was rerun.

Service time includes resident-context reset, native prefill, decode/verification,
reconciliation, synchronization and result assembly, including repair dispatch.
The selected policy has no canonical producer/bridge. Heavy observation and state
writing are absent from timing. Model loads are separately 4.9105082,4.8307592,
4.8383671 and4.8402953 seconds; resident-pool provisioning is separately 0.0870152,
0.0788848,0.0731159 and0.0722341 seconds.

## Host, accounting and evidence

RTX5070Ti Laptop12GB (`GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd`), driver 616.92,
Ultra9 275HX, 48GB RAM, 24 threads; target GPU-layer setting 24 and draft setting 999.
Qwen3-14B Q8 target, Qwen3-0.6B Q8 draft, F16 KV, context1024, cap128/natural EOG,
k3 and the original prompt/token/greedy contract were preserved. The selected
worker SHA256 is `55cc7e9fecefc209ea0b17f1c787f906ff8fe8760a8e43a18a0e3b04ee6e6b15`.
The 21 numerical DLLs are unchanged; the repaired scheduler is statically linked,
and static-component hashes are separately retained.

All four process sessions completed with zero active Job processes and released
locks. Their native wall times were 4232.906,4196.485,4257.797 and4198.313 seconds.
Passive power samples all report AC and the original Balanced scheme. Sampled
available RAM stayed at least14,497,140,736 bytes and GPU free memory at least 1916MiB;
maximum sampled GPU temperature was 80°C. Sampling is approximately ten-second,
not a continuous peak guarantee. The final resource sample precedes the last
session END by 4.677526 seconds; the power monitor covers all session boundaries.

The final cumulative charge is **1140/1200**, including **420/480 development** and
720 confirmation/timing reservations. Remaining total/development reserve is 60.
The 1123 retained complete model records include 15 from the failed Llama attempt;
one additional slot started without a complete record, eight failed-stage slots
have no record/start evidence, and eight operator replays were conservatively
charged. No failed reservation was refunded. Cumulative native process time is
27,796.908 seconds, including non-generating admissions/operator execution. Original
PR156's 40 requests are separate and unchanged. No further experiment is queued.

## Independent raw reconstruction

The separate auditor reconstructed all 1123 retained complete records,
decoded 48162 full-vocabulary vectors (including orphan failure
artifacts), rehashed 390 complete-record final states and checked
259 available matrix heavy/off pairs. It uses struct-based F32
decoding, finite/first-argmax checks, the authenticated original transaction-checker
Git blob and independent fmean/log cost aggregation, without importing the candidate
auditor or runner. The 42 historical/development
reference mismatches remain recorded outcomes, not removed audit rows: 24 initial
development, 10 pre-repair diagnostic requests, and four known Llama failures in
each of the failed and recovered regression attempts. Partial
Llama artifacts have no reconstructed qualified endpoint.

All 576 timing/warmup coordinates and endpoints were rechecked; cost recomputation
agrees with the primary means within 1e-12 relative tolerance. Additional geometric
ratios are M_QB/M_PQ=0.9892698734, dual-C_PQ/R=0.3290427412,
and M_PQ/R=0.4617745003. All 48 blocks and 12 input aggregates are retained
in [COST_RECOMPUTATION.json](COST_RECOMPUTATION.json).

Internal correspondence is reported separately from endpoint qualification:

| Comparison | Endpoint | Transactions/KV bounds | Full saved vectors | Final state hashes |
|---|---:|---:|---:|---:|
| M PQ vs QB | 12/12 | 12/12 | 12/12 | 12/12 |
| C PQ vs QB | 12/12 | 12/12 | 12/12 | 12/12 |
| Original R vs candidate R | 12/12 | 12/12 | 12/12 | 12/12 |

Thus the retained qualification comparisons show matching logical work and bytes
for both layouts on this panel. This correspondence does not override the negative
practical-benefit screen or extend to untested inputs.

These counts apply to the frozen qualification panel. They do not erase the initial
failed candidate or imply equality for every possible input. The compact
[independent summary](INDEPENDENT_AUDIT_SUMMARY.json) pins the complete raw audit,
which is included in the archive. This is independent implementation on the same
host, not third-party scientific replication.

## Delivery

All raw data remain locally, including initial failures and partial artifacts.
The published release, raw access index and successful fresh all-member remote
readback receipts are documented in [DELIVERY.md](DELIVERY.md). No existing paper or old PR is
merged or rewritten.
