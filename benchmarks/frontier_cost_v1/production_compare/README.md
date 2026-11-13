# Original-entry paired request preparation

This module prepares a finite experiment on the original Linux M2 production
entry. It does not establish a 5% improvement. `performance_admitted` is always
`false`: historical scalar-R qualification and a full-vector/state bridge to the
clean timing path remain open.

The local validation compiled all four executables against the unchanged CPU
libraries, but ran none of them. The two clean executables are byte-identical to
PR221's previously compiled original guarded-entry binaries. Ten host-only tests
cover input immutability, API versus physical work, failed/partial runs, path
rejection and the original two-file terminal-capture format. No new model or GPU
request was made. A successful link is not CUDA runtime qualification.

## What the original interface actually supplies

The native CLI remains `ENTRY JOB.json FRESH_OUT`. Neither `entry.cpp`,
`worker.cpp`, the GPU-required gate, nor the numerical source is modified.
Dependencies are the exact PR221 source bytes at
`d6053addcd973e503ebeaae495b3326d6bf99bd4`.

| Observation | Capture mode | Clean mode |
|---|---|---|
| Every actual target/draft sampling vector | Complete vocabulary F32 files written by the original worker | Unavailable |
| Target initial/commit/terminal active sequence | Original sequence files | KV position bounds only |
| Draft active sequence and native head/extent guards | Additional read-only link wrappers at reset/trim/terminal | Unavailable |
| Original `service_seconds` | Includes heavy observation, so excluded from performance | Recorded diagnostic clock |
| Original `request_seconds` | Instrumented | Prefill through final synchronization |
| Model/pool setup and complete process wall time | Recorded separately | Recorded separately |

`service_seconds` starts before resident reset/setup and ends at worker return.
It includes actual prefill, target verification, draft work, CPU sampling,
planning, synchronization and worker teardown bookkeeping. It excludes model
load, pool construction, the subsequent receipt-file write, text tokenization,
networking and queueing. This is a complete worker request interval, not an
entire deployed service's response latency. Original model-load/pool timings and
the owned child-process wall clock remain in the raw receipts.

The capture binaries link the unchanged entry with GNU `--wrap` observers for
model load, context initialization, memory clear, sequence trim and context free.
They record real native bytes; they do not substitute outputs, alter sampling,
change decode widths or patch native libraries. Before the next target clear,
both previous terminal states are captured. Both final terminal states are
captured before the first context free. The footer explicitly says
`OBSERVATIONS_CLOSED_NOT_ENTRY_QUALIFIED`; process success and the complete entry
receipts must also pass. Any ambiguous/partial lifecycle is rejected.

Worker initial/commit captures have `capture.txt`; the original entry's terminal
capture has only `frontier.f32` and `sequence.bin`. The comparator follows those
distinct original formats. No missing metadata is fabricated.

Active sequence serialization is not a whole-context image: inactive KV,
padding, stale logits and all private backend state are outside its scope.
The unused eager last-draft logits are not made into a new consumer. The two
required bridges cannot be inferred from equal token IDs, equal bounds, this
module's PASS-like diagnostic statuses, or old S3 receipts.

## Fixed plan and independently checked budget

The input generator verifies the entire original PR213 job-manifest SHA and
selects the first two lexicographic test roots of session0 LOCAL-loop4-k7.
These are full original prompts: APPS/train/169 (151 tokens) and APPS/train/199
(117 tokens). They are already exposed diagnostic inputs, not a new confirmation
set. The original cap96 is explicitly reduced to cap16; there is no extra
primer, retry, replacement root or automatic panel expansion.

The plan is k7, LOCAL, live proposals, target reserve8/ubatch32, draft ubatch4,
context1024 and two CPU threads. It runs a capture pair, then two clean pairs,
reversing arm order in the second clean pair. Each of the six fresh processes
contains both requests in the same order. Model/pool setup happens in each
process. The second request exercises the original resident reset.

For prompt length P and observed cycle count C, target API calls are
`ceil(P/32)+C`. Draft API calls are `1+8C` for eager and `1+7C+R` for deferred,
where R is the actual number of all-seven-retained cycles. Draft prefill is one
API call, but `ceil(P/4)` physical microbatches. Target prefill has `ceil(P/32)`
API calls and physical microbatches. Both roles consume P prefill token rows.
Actual continuation rows and histograms are reconstructed from the literal
cycles and checked against the original native counters.

Since each cycle emits at least one token after the initial token, `C <= 15`.
These are fixed worst-case limits, not predictions of natural acceptance:

| Total across the six processes | Ceiling |
|---|---:|
| Requests | 12 |
| Frontend context creations | 12 |
| Model loads | 12 |
| Target `llama_decode` calls | 234 |
| Draft `llama_decode` calls | 1,452 |
| Target physical microbatches | 234 |
| Draft physical microbatches | 1,848 |
| Target token rows | 3,048 |
| Draft token rows | 3,048 |

The context count is checked against the original entry's observed API counter
and the capture wrapper's actual contexts. Each process has a fixed 1,800-second
limit. Only its owned child can be killed and reaped on timeout; partial output
is retained and no later process runs.

Storage ceilings use the authenticated Qwen structures: target36/draft28 layers,
1024 K and 1024 V elements per layer, F16 KV, the maximum active position and
maximum checkpoint counts. They include 1 MiB metadata allowance per state and
16 MiB per-request JSON allowance, plus every original F32 consumer/checkpoint
vector. Actual state sizes exceeding this bound fail. The plan records the
computed disk requirement; the raw size is checked before progressing to the
next process. This is not a small synthetic-model storage estimate.

## Commands

Use a fresh checkout of the eventual committed source. Supply authenticated
source-kit/frontend/library paths from the parent preparation workflow. Build
outputs and run outputs should be outside the committed source subtree.

```sh
export PYTHONDONTWRITEBYTECODE=1

python build_production.py \
  --core "$HETEROSPEC_CORE" --frontend "$HETEROSPEC_FRONTEND" \
  --lib-dir "$HETEROSPEC_LIBS" --out "$HETEROSPEC_WORK/build_fresh"

python run_production.py --out "$HETEROSPEC_WORK/plan_fresh"

# Only on the real allocated host, after committing this module:
python run_production.py --execute \
  --build "$HETEROSPEC_WORK/build_fresh" \
  --public-root "$HETEROSPEC_CHECKOUT/benchmarks/frontier_cost_v1" \
  --target-model "$HETEROSPEC_TARGET_MODEL" \
  --draft-model "$HETEROSPEC_DRAFT_MODEL" \
  --gpu-index "$HETEROSPEC_ALLOCATED_GPU_INDEX" \
  --experiment-commit "$HETEROSPEC_EXPERIMENT_COMMIT" \
  --out "$HETEROSPEC_WORK/run_fresh"

python verify_production.py "$HETEROSPEC_WORK/run_fresh" \
  --out "$HETEROSPEC_WORK/replay_fresh.json"
```

The execute path requires the real frozen target and draft GGUF SHA values, a
fresh CUDA build, a clean committed experiment subtree and the exact committed
module. It reuses PR221's hash-pinned PCI/MIG/physical-GPU0 exclusion and visible
CUDA-device checks. It refuses an occupied device and records free VRAM. A
whole-weight-file-size plus 1 GiB margin is a resource-admission check, not an
OOM guarantee. Allocation failures remain failures. No SSH endpoint or GPU was
available locally, and this module launches neither by itself.

All jobs are written before the first native process. Native input names include
the run ID and process name. Returned files, owned-child logs, binary identities,
module identities, complete request counts and capture footer are bound before
comparison. Failed qualification stops clean jobs. A clean logical endpoint
match remains an endpoint check; it does not supply missing clean vectors.

`verify_production.py` is a diagnostic offline replayer, not an independent
authenticator of an arbitrary directory. Its run/source manifests must be pinned
by the externally frozen experiment and artifact identity. It never accepts an
external PASS string as historical-R, clean-vector or 5% authorization.

## What the next observations would support or rule out

1. **Preservation comes first.** On the actual model and CUDA identity, any
   target/proposal full-vector, active-state, native geometry, output or
   lifecycle difference rejects this lazy-tail implementation for that scope.
   A successful instrumented pair establishes only the recorded pair's scope.
2. **Measure the specific mechanism.** Record actual omitted/recovered draft
   calls and physical rows. If both requests omit no tail calls, this scope
   provides no opportunity for this mechanism. Saving calls alone is not a
   latency result and does not establish a universal cost per call.
3. **Separate a small baseline repair from a new route.** This module isolates
   the last draft q1 optimization. A later adaptive verification route must be
   compared with a baseline that already has the same lazy-tail/cap treatment.
   Its extra decision overhead and changed target physical widths belong in the
   complete worker service clock. The earlier CPU q2 qualification failure is
   not repaired by these same-width eager/deferred pairs.
4. **Close the two open bridges before performance admission.** Obtain authentic
   fresh historical-R compatibility and full-vector/state evidence for the clean
   path under the actual source/build/model/device identities. The current
   original entry cannot supply the latter without another observed bridge.
   This module keeps the gate closed even if its clean clocks look favorable.
5. **Test the 5% and generality claims on a new fixed scope.** After those gates,
   preregister paired complete-request measurements on a separate confirmation
   panel, report the paired reduction and uncertainty, and retain per-family,
   prompt-length, acceptance and architecture results. Two exposed code prompts
   and two repeats cannot establish generality or statistical support for 5%.
   A gain confined to low acceptance or one launch-sensitive GPU supports a
   conditional architecture result; a broad claim requires the corresponding
   independent model/task/device evidence. Unfavorable cells must remain in the
   analysis rather than being replaced or averaged away without disclosure.

The useful result of this module is a concrete falsifiable next experiment and
the precise observation gaps. It is not evidence that the requested 5% goal has
already been achieved.
