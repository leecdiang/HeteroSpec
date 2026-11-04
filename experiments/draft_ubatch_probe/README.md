# Draft microbatch study candidate (cloud-only draft)

This is a source-pinned derivative and CPU validation fixture, not a new qualified
RTX result. Historical experiments and all their attempts remain untouched.
Only the draft context physical microbatch capacity changes from 1 to 2 or 4. Draft output reserve stays1, avoiding a second output-capacity intervention.
No additional threading, prefill reordering, cache, skipped initial-EOG draft
prefill, adaptive retry, target arithmetic or target scope change is included.

## Source-level intervention

Frozen worker: [PR151 fixed head](https://github.com/leecdiang/HeteroSpec/blob/29511ed91eb9f3d9773cfdda53e3554b0f4ad08b/scripts/experiments/rtx_scope_transfer_v1/worker.cpp).
Its exact GitHub file SHA256 is 4423bf687de4d652809c3ffad9cd9bf31770c2019c383fb54bd7abd24858b124.
The earlier local archival copy adds one newline; the stager deliberately refuses
that different input. `frozen-worker.cpp` is the exact retrieved text.

`stage.py` passes a separate draft-only physical width to both resident and fresh draft constructors. The shared Context defaults it to1 and uses `istarget ? ub : draft_physical` only for `n_ubatch`; both output reserve fields still use the original `ub=1` for draft. Target callers are unchanged. A single executable
has one immutable draft ubatch, verifies it in each slot, family binding, plan
and resident context, and records it. It requires a distinct study ID, so old
registered slots cannot run silently. All source/executable/module/model hashes,
output retention, fresh output requirement and host admission remain. The pool
is process-local and single-width; no cross-executable context reuse is allowed.
The Context differs only in this draft-only parameter and assignment; removing those two edits recovers its exact original bytes. Target constructor calls and the entire request accept/reject/bonus/trim algorithm are checked byte-for-byte unchanged by `test_stage.py`.

The Windows native worker is NOT COMPILED here. The generated patch is an
implementation candidate, not a runnable approved RTX protocol. A future study
needs separately frozen worker builds, budget, slots, bindings, controls and
qualification. No old source or binding should be edited in place.

## Actual CPU fixture, and limits

`test_native.cpp` links the same unmodified PR171 source-kit candidate runtime for all
three arms. It uses each synthetic Q8 or F32 model as both target and draft, separately; this is not the original two-model Qwen/Smol pairing or original #151 numerical library. It tests
actual prefill, proposal, rejection at each j=0/1/2, all-accept bonus, cap1/2/5/9,
synthetic EOG predicates at each output index, trim, continuation, and reset.
Every target verification vector is compared bitwise with an independent fresh
scalar forced-prefix replay. Endpoint greedy tokens are independently replayed. Serialized committed sequence bytes are compared to a fresh scalar replay, separately from pending/last-logit behavior; serialization is not proof of all hidden backend padding. Each case writes STARTED/COMPLETED to a fresh append-only journal so partial failure is retained.
The synthetic stop predicate tests the protocol branch, not real tokenizer EOG
classification. Native model EOG semantics still require actual-model testing.

This target fixture uses ordinary unscoped target ubatch1 with output reserve4
(to retain four requested verification rows), while each scalar oracle has
ubatch1/output reserve1. It does NOT exercise PR151 scoped QB target ubatch4 or
pretend its reserve differs only in harmless metadata. The direct comparison
establishes only the recorded CPU cases. The first exploratory test incorrectly
reserved1 for a four-output caller and aborted; its log is retained. No attempt
is silently retried as a numerical success. A fresh library build initially
OOMed at j2; the same build resumes j1 and that failure is retained separately.

The all-output harness is an offline validator, not an uncharged production
oracle/cache. Its checks and fresh replays are deliberately costly. No timings
from it are claimed as service speedups. Reported expected microbatch counts are
arithmetic expectations, NOT observed GPU launches. Draft wider ubatch may
change initial logits, KV, proposals, acceptance, target call histories and total
cost; equality of draft bytes is not the target contract and not assumed.

For a new CUDA arm, compare every target decision vector against old R at the
same forced token prefix, then separately test committed KV/pending/initial
logits, subsequent continuation, endpoint, reset and known failures. Changed
draft proposals cannot inherit the old finite set of target qualifications.
Trim is not a generic numerical state rollback. A mismatch aborts qualification;
no repair/retry is discarded or relabeled. No optimized target admission follows
from these CPU tests.

## Prior art and interpretation

[llama.cpp common.h](https://github.com/ggml-org/llama.cpp/blob/master/common/common.h)
already exposes an independent draft n_ubatch; its default0 follows the target.
This is an implementation/configuration study, not a novel batching algorithm.
[Leviathan et al., ICML2023](https://proceedings.mlr.press/v202/leviathan23a)
provides speculative decoding with an approximation model and exact target
sampling under its assumptions. That mathematical target guarantee is not a
proof that hardware-dependent finite-precision batch verification equals this
repository's frozen scalar deployment. Here #151 uses strict greedy acceptance,
not the stochastic rejection-sampling algorithm.

Keep no-draft M_QB, unchanged ub1 and candidate ub2/4 controls, equal cache policy,
all exposed failures and all attempted requests. Do not infer a net speedup by
subtracting draft prefill time from old records: proposal and target work can
change. A later affordable trial needs independent budget approval.

## Reproduction

```sh
python test_stage.py
python stage.py --worker frozen-worker.cpp --draft-ubatch 2 --output /fresh/arm2
cmake -S /verified/source-kit/candidate -B /fresh/cpu-build -G Ninja \
  -DGGML_CUDA=OFF -DGGML_NATIVE=OFF -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_TOOLS=OFF \
  -DLLAMA_BUILD_COMMON=OFF -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build /fresh/cpu-build --target llama -j1
python validate.py --source /verified/source-kit/candidate \
  --library-dir /fresh/cpu-build/bin --model /synthetic/llama-q8.gguf \
  --output /fresh/validation
```

`validate.py` records commands, model/source/library/implementation hashes, logs
and all attempts. It instruments only the test executable with UBSan, not the
runtime libraries. This is not a full runtime sanitizer claim. The synthetic
model must be separately pinned; these results do not qualify an arbitrary GGUF.

## Review-driven isolation correction

The initial local derivative changed draft `ub` directly, which also increased
its output reserve from1 to2/4. This was identified during independent review.
The final isolated derivative keeps output reserve1 and varies only the physical
microbatch field. The initial code, arms and CPU runs remain in local archival
files named bundled/v1 or early/final-validation; they are not results for this
final isolated intervention. Final receipts are `release-q8/RECEIPT.json` and
`release-dense/RECEIPT.json`. Earlier isolated runs are retained too. Subsequent DRAFT_SYNC and each PROPOSE remain one
token per caller, so this patch does not reduce their per-cycle caller count.
It may still change allocation, graph selection and draft state; it is not a
proof that only prompt computation time changes.

Independent review also found that the initial fixture could accept a mutant
that stopped every request after one token: its oracle compared only the produced
length. The final fixture independently asserts the requested cap/stop length,
nonzero cycles whenever length>1, and exact first-cycle accept/correction/bonus
branch for forced proposals. Old passing receipts are retained but superseded
for coverage by v3 and the subsequent independent-frontier fix; the mutant rejection is independently rechecked.

A second review mutant discarded all final generated KV while resetting the
fixture's own history to the prompt. The earlier state check compared against
that same mutable history. The corrected test independently derives the final
committed prefix from the emitted endpoint and terminal branch: accepted stop
includes the last token; correction/bonus/initial stop excludes the pending last
token. It checks history, base, both KV positions, serialized target sequence and
continuation against this independent prefix. Earlier receipts remain retained.

## History-sensitive synthetic stress models

Independent review demonstrated that the original Q8 fixture's next logits were
identical for six different histories ending in the same token. Original F32
history effects were only around1e-9. Therefore their continuation checks alone
were weak evidence, even though sequence-byte checks caught discarded state.
Those fixtures and results remain unchanged.

`make_stress_fixture.py` requires the exact original synthetic F32 model hash
and writes a new GGUF: only five RMS norm weight arrays become1, all other bytes
remain identical. It records each changed byte range and resulting hash. The
independent history probe then observed changes in126/128 Q8 or128 F32 logits
for nontrivial history changes (max about6.66e-4 /1.16e-4). Identical-token repeated
histories remain a documented degenerate control. This is still untrained
synthetic data, not a production target model. `stress-q8` and `stress-dense`
receipts each contain75 passing protocol cases on these new fixtures.

```sh
PYTHONPATH=/verified/source-kit/candidate/gguf-py python make_stress_fixture.py \
 --input /synthetic/llama-dense.gguf --output /fresh/stress/dense.gguf
# Build quantize_fixture.cpp with the same llama include/library flags used by validate.py.
./quantize-fixture /fresh/stress/dense.gguf /fresh/stress/q8.gguf
# Run validate.py separately for both generated models, with new output directories.
```

Original synthetic models came from the frozen source's `test-llama-archs -a
llama -s178 -o <dir>` and `quantize_fixture.cpp`; generator toolchain matters and
exact input hashes are required, not presumed. The stress change is diagnostic
data generation, not a change to the frozen reference/model or production
quantizer. No GPU device was used.

The strengthened model does NOT make every adversarial continuation visible in
logits: the review's final-state-discard mutant still had all75 Q8 continuation
vectors match, while57 serialized-sequence checks correctly rejected it. The
nonzero generic history probes and this particular blind spot are distinct
facts. Serialized-state comparison is essential in this fixture; do not claim
that continuation logits alone detect all lost KV or establish a universal
floating-point target guarantee.
