# Native admission checkpoint: not admitted, not implemented by this census

N0 closed its supplied-history cut-opportunity branch before GPU work. No N1
reference, context, qualification or timing was executed. No N2 cohort is frozen.
The original3072-request/12M-row bounds and PR218 consumption provide no allowance
for this successor. An idle GPU is not a new allocation. The current result does
not recommend spending GPU budget under the unchanged N0 contract.

## Source and deployment findings

The exact existing Qwen3-8B-Q8_0 is8,709,518,112bytes, SHA256
408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6.
Its actual GGUF says36 layers,32 query heads,8 KV heads,128-wide K/V heads,
151936 vocabulary entries. C4096/F16 KV alone is603,979,776bytes; reserve32
full F32 output rows add19,447,808bytes. These metadata estimates exclude graph,
workspace/driver/allocator costs and do not establish admission or placement.

The inspected original Linux reference frontend explicitly rejects context
capacity!=1024 (this is separate from the response-generation cap128)
and clears memory before each input/case. Passing n_ctx4096 in JSON cannot make
that binary an N reference. Reuse its fixed arithmetic/source foundation in a
separate versioned descendant; preserve the old reference and bind an independent
N sequential producer before candidate outputs. A convenient cold whole-prefix
rerun is not an independent sequential resident reference.

The inherited PhaseContext SIMPLE planner is insufficient if an outer caller
first fixes32-row chunks: head205/append84 can still become[32,19,13,20].
Strong whole-rechunk must receive the complete append and actually emit
[32,19,32,1]; LOCAL outer is[32,32,20]. These are static examples, not observed
native heads or execution proofs. All four arms receive the same legal lifecycle
and output-ownership changes; loop4/packed is kept orthogonal to cut policy.

## Requirements before any model execution

1. Establish an unanswered question and a prospective history-serialization
   contract. The present canonical nonthinking template rewrites the old empty
   think stub on every supplied-history continuation. A cache-preserving renderer
   or a different sequential free-producer contract is a new version, not a repair
   retroactively applied to this result. Do not select an alternate policy by speed.
2. Bind latest Linux source/build/dependencies/modules, actual model/tokenizer and
   template bytes, C4096, F16, output masks/reserve32, capability echo and all four
   ordered native paths. Unknown/ignored job fields fail. Bind placement including
   any declared host embedding storage, output and KV; do not infer it from flags.
3. Reconfirm an explicitly allocated UUID, confirmed quiet start/end/last-worker
   times, two CPU cores, RAM/disk/VRAM safety reserves and finite timeouts. Protect
   company services; no reset, sudo, driver/power change, foreign signals or second
   card. A single study coordinator and existing allocation locks apply.
4. Freeze a distinct finite N1 allowance from an exact operation manifest. The
   accompanying proposal is not authority;16 unused failure slots never authorize
   automatic retries. Every failed/rejected/warm/control/model request is charged.
5. Freeze the new independent sequential R first. One context persists through a
   session. Native turn receipts must report stable context identity, prompt IDs,
   actual head, pending ID/position, materialized ranges and rebuild reason.
6. Compare token-ID prefix before state mutation. Materialize a pending token and
   any template suffix exactly once. A mismatch triggers the identical predeclared
   reset/full rebuild for R and every method, with full costs. End-of-session reset
   and new-session emptiness are checked. No per-turn cold restart disguised as
   append; naturally required rebuilds remain explicit.
7. Four source-only development conversations are listed, never executed. Check
   natural EOG/cap1/cap128, pending, requested full vectors and owned outputs,
   active KV/frontier across all36 layers, capacity/tails/reset and actual physical
   calls. Heavy and clean bridges have distinct checking depth and cost records.
   Preserve failures and requalify general source changes in new epochs.

Only after all of these and a supported census question may an independent N2
episode protocol be frozen. Separate teacher-forced replay from natural free
sessions. Its primary unit is the whole conversation, including initial prefill,
append, responses, state work and necessary rebuilds. Freeze all four equally
optimized controls and complete requests/rows; no tuning roots/offsets/rounds to
obtain5%, no borrowing S3/8B allowance, and no automatic confirmation panel.

The proposed N1 envelope covers one prospectively selected history-producer
mode. Running both teacher-forced replay and free sequential generation needs a
new exact manifest and separately accounted allowance; they cannot both consume
the same256-request envelope or be pooled as independent evidence. The proposed
250GiB disk value is a minimum floor, not a computed complete raw-capture bound.
Compute the actual state/vector capture and archive/safety bound before admission.

The successful CPU corpus/schedule tests and saved-data checks do not satisfy any
native numerical or state-lifecycle gate above.
