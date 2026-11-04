# Frozen-reference runtime qualification and committed-state execution

Research/design artifact, 2026-11-04. This directory adds documentation and CPU-only abstract tests to the existing research branch. No native runtime source was modified and no GPU was used for this work. This document is a conditional design and source audit, not a formal verification result or a performance result.

## 1. Findings that change the implementation plan

1. A deployment identity alone does not define a canonical result if its frozen reference is shape/chunk dependent. Define an exact reference transition schedule, or retain the producer schedule in cache provenance. Do not infer cold-prefill equivalence from a scalar reference.
2. `mctx->apply()` changes KV metadata before graph allocation. A graph-level guard cannot provide request-level atomicity on its own.
3. The scheduler copies and launches one split at a time. A CUDA split-level veto can happen after earlier CPU or device splits have executed. All splits and transfers need a prelaunch plan.
4. CUDA launch/synchronization failures use a fatal `GGML_ABORT` path. The current checkpoint wrapper's C++ catch blocks are not a general device-error recovery mechanism.
5. KV storage starts zero-filled. For a strictly owned, dense, append-only context, maintaining a zero-free-tail invariant permits bounded rollback without a full KV snapshot on every successful call.
6. Merely masking future KV is an additional numerical proof obligation. A conservative full native path can avoid it: per layer, compute qualified pure projections in parallel, but insert query j's K/V and run its unchanged scalar attention before inserting query j+1. This preserves the entire padded attention input, including unused bytes.
7. Current staged contract mode explicitly disables graph reuse, CUDA capture and fusion. A low-overhead qualification cache is a new integration step, not a description of the staged implementation.
8. Successful implementation still depends on actual kernel equivalence evidence. Registry flags, matched hashes and finite replay do not establish it. Without a suitable certificate, the production gate remains closed.

The proposed first full-path milestone is therefore **qualified pure-operator batching plus exact-input attention scheduling, owned zero-tail storage, and atomic output publication**. It is deliberately narrower than general masked batching, shared-prefix caches, arbitrary native state mutation or heterogeneous multi-GPU execution. It can be end-to-end native without comparing against a second runtime on the hot path. It has no promised speedup.

## 2. Evidence and reproducibility

The inspected source is the staged native source corresponding to the recorded hashes. Use `HETEROSPEC_NATIVE_SOURCE` or `verify_source_manifest.py --source` to name a local copy; no machine-specific path is required.

The input source kit has SHA256 `b1926827029e0bb8e219861901f2ca3538b330a44f9c6093b5267157dbfcd1ac`. Individual inspected file hashes are in `source_manifest.json`. Line numbers below refer to this staged source, not latest upstream or an arbitrary subsequent PR revision. At publication preparation, #179 head was `5e63429220ef43b33d15ea5f7dadc2383a3e7592`; every overlapping staged-file digest in that head's NATIVE_VALIDATION.json matched this inspection manifest. The stage manifests themselves label the execution contract unqualified and the CUDA audit source uncompiled. Separate later validation may establish newer compilation evidence, which must be reported separately.

Relevant reference artifacts:

- Frozen PR179 implementation description: https://github.com/leecdiang/HeteroSpec/blob/d694011de1065701b25840f30e25cc532c27f52d/docs/research/reference_contract_20261104/IMPLEMENTATION.md
- Source-kit origin: https://github.com/leecdiang/HeteroSpec/blob/aa7ff4e64752be3de0d7974febbce453ae3a96c0/benchmarks/rtx_prefix_reuse_v1/execution/evidence/native-source-kit.zip
- Related repository plan: [`../REFERENCE_PARALLELISM_RESEARCH_PLAN.md`](../REFERENCE_PARALLELISM_RESEARCH_PLAN.md).

### Source anchors

| File and lines | Observed behavior | Required design consequence |
|---|---|---|
| `src/llama-context.cpp:794-826,1747-1777` | `memory_update(false)` precedes `init_batch`; preparation failure may call `memory_update(true)`. `init_update`/apply can consume or execute pending work. | Enter the transaction before decode preprocessing. Use a pure pending-update query; do not call a mutating initializer just to test eligibility. Reject shift/copy/optimization in the first fast domain. |
| `src/llama-kv-cache.cpp:745-750` | `init_update` moves `sc_info`. | Even an apparent inspection can consume update metadata. |
| `src/llama-context.cpp:1336-1401` | `mctx->apply()` precedes graph parameters, reuse test, graph construction, allocation, inputs and compute. | Shadow metadata or a complete reversible metadata log must already exist. |
| `src/llama-kv-cache.cpp:753-816` | Preparation temporarily applies ubatches and restores selected cell metadata/heads. | Useful planning structure, not a KV-byte snapshot or a proof covering purge side effects. |
| `src/llama-kv-cache.cpp:1099-1187` | Overwriting a cell can purge earlier positions and move heads. | First domain requires genuinely empty fresh slots. A target-slot-only log is insufficient for occupied-slot operation. |
| `src/llama-kv-cache.cpp:278-295` | Newly allocated KV buffers are cleared to zero to avoid padding NaNs. | Establish and maintain a zero-free-tail invariant rather than silently relying on unspecified free bytes. |
| `src/llama-kv-cache.cpp:1252-1282` | Physical attention extent is padded to at least 256; scalar-prefix extents are computed separately. | Live-token length is not the physical read extent. Preserve per-query extent and padded contents. |
| `src/llama-kv-cache.cpp:1337-1425,1495-1541` | K and non-transposed V use row writes. Transposed V uses scalar scatter and may pad embedding dimensions. | Derive typed physical write sets separately for K and each V layout. |
| `src/llama-graph.cpp:2996-3011,3021-3063` | The current graph emits all K/V writes before grouped attention views. | Prefix extents alone do not establish equality of masked future contents to the scalar execution. The conservative schedule is a real graph change. |
| `ggml/src/ggml-backend.cpp:1637-1647,1995-2011` | Allocation can relocate tensors; split assignment and allocation happen before compute. | Bind physical addresses/generations only after allocation, and pin them through completion. |
| `ggml/src/ggml-backend.cpp:1663-1805` | Splits are copied and launched sequentially; a later split can return failure after earlier work. | Prepare every split and transfer before any launch or candidate persistent write. |
| `ggml/src/ggml-backend.cpp:1668-1697,1785-1796,1840-1843` | Existing event/copy dependencies and ring-copy ownership matter. | Qualification includes copies, scratch reuse, `cur_copy` and completion dependencies, not just kernels. |
| `src/llama-context.cpp:1836-1863` | Failure cleanup removes failed ubatch positions. | This is not whole-logical-batch rollback. |
| `src/llama-context.cpp:2505-2522` | Logical batched calls select batch CPU thread counts/threadpools. | Retaining a scalar-shaped CPU node is insufficient unless CPU execution settings also match R or are separately qualified. |
| `ggml/src/ggml-backend.cpp:1806-1848` | An eval callback can stop the remaining nodes while the function later returns success. | Reject this callback path initially; a success status alone does not prove complete planned-node coverage. |
| `src/llama-context.cpp:1880-1892,2040-2043` | Logits are copied asynchronously and decode returns without explicit final sync. | Decode success is submission success, not a commit event. Output-copy completion belongs in the final fence. |
| `src/llama-graph.cpp:506-521` | An active reference contract/packing binding disallows attention graph reuse. | Replace this conservative rejection only after a bound-plan reuse protocol exists. |
| `src/llama-graph.h:820-898`; `src/llama-graph.cpp:1465-1495` | Existing graph reuse tests topology-related parameters and input compatibility. | A topology-reuse decision is not a numerical or transactional qualification. |
| `ggml/src/ggml-cuda/ggml-cuda.cu:2595-2638` | CUDA graph cache is keyed by first-node pointer; equal nonzero graph UID bypasses property comparison. | Do not treat pointer or UID equality as a proof token. Attach independent handle/allocation/qualification generations. This observation alone does not demonstrate a bug in the existing topology cache. |
| Same file `:4139-4145,4329,4424-4438,4454,4524` | A fused RMSNorm/multiply/RoPE operation can write KV; audit disables fusion/capture/concurrent plans, and enforcement rejects CUDA splits. | A write manifest must include fused writes. An audit-policy trace does not automatically qualify the original frozen policy. |
| Same file `:99-108,2423-2427,2548-2551,4399,5596-5598` | CUDA errors pass through a noreturn abort handler; launch and completion checks are distinct. | Fault recovery/availability requires error propagation or a supervisor and pre-existing recovery state. |
| `ggml/src/ggml-cuda/mmvq.cu:1435-1452` | MMVQ may clear temporary source padding and allocates/quantizes backend-pool scratch during execution. | Preparation must cover backend-internal memory operations and allocations, not just scheduler-visible tensors. |
| `ggml/src/ggml-cuda/common.cuh:130-140,1576-1591,1658-1683` | PDL has explicit dependency synchronization and can use extended launch attributes on one stream. | Verify actual PDL wait/trigger semantics and include launch attributes in the executable manifest; stream identity alone is insufficient. |
| `ggml/src/ggml-cuda/set-rows.cu:30-65,139-171` | Index-to-address calculations have no destination bounds check; stores are plain stores, not atomics. Flattened indices narrow to 32 bits. | Prove/check bounds, arithmetic width, destination uniqueness and aliasing before execution. |
| `src/execution_contract.hpp:112-145,174-219,222-259` | Qualification records and assumption callbacks are trusted; `execute_operator` is a stateless callback boundary and taints on failure. | This is an admission protocol, not an engine or kernel proof. Generic callbacks must not be the source of the clean-state capability. |

## 3. Exact reference semantics

Use the notation `R = (deployment, transition program, observation contract)`.

Deployment contains model and tokenizer identity; weight/adapter/control-vector versions; exact backend binaries and libraries; compiler and math-mode choices; the supported device/driver domain; tensor/KV formats; relevant environment knobs; placement/fusion/capture policy; CPU thread count, threadpool, floating-point environment and other value-relevant execution settings. A package or source hash is an identity check, not semantic evidence about that binary.

The transition program specifies batching, prefix extents, selected routes and sampling behavior. Two important choices must not be conflated:

- **Scalar recurrence reference:** append one supplied token at a time using a frozen route and cache policy. A q-token reference operation is the ordered composition of these one-token transitions.
- **Frozen request-recipe reference:** preserve a particular existing q-token/chunk schedule, possibly shape-dependent. The canonical value then depends on that recipe/trajectory unless additional equivalence is established.

This design's conservative schedule is stated against the first choice. If the user's deployment reference is instead the second, instantiate the theorem with that transition DAG and recheck every rescheduling/fusion step. Choosing a convenient new scalar reference after benchmarking is not preserving the old deployment.

Define observable state explicitly:

- Committed input-token history and positions, sequence ownership and metadata.
- Bit patterns of every committed layer K/V element.
- The physical padding/free-byte invariant needed for future reads.
- Committed output rows, their ordering and access metadata.
- Any pending-token/acceptance state and explicit sampler state that the supported API exposes.

Timing, scratch allocation addresses and performance counters are not numerical observations here. API failure codes, crash durability and exactly-once network delivery are separate contracts. There is no claim that the optimized path reproduces every reference failure timing.

A theorem about outputs alone is weaker than a theorem about historical KV. A theorem about KV alone does not establish sampler equivalence.

### Canonical cache warning

A prefix key consisting only of model and token sequence is unsound if R's numerical result depends on the producer's chunking or route. Either:

1. Define canonical production by the fixed scalar recurrence and prove every admitted producer refines it; or
2. Include the producer recipe/trajectory in identity, allowing cross-recipe reuse only under an explicit equivalence relation.

This is independent of storage corruption checks. A perfectly intact cache entry can still have the wrong numerical provenance.

## 4. Minimum viable full native domain

Admit initially only:

- One owned context, one sequence, one caller transaction at a time; no raw context mutation outside its owner. Model/adapter buffers have shared read leases excluding mutation by other contexts, and eval/abort/cancellation callbacks are rejected unless their completion and side-effect semantics are explicitly modeled. In particular, reject the eval callback path that can skip nodes yet return scheduler success.
- A dense causal transformer with independently owned layer KV storage. Reject layer-KV aliases/reuse, recurrent state, MoE, SWA, multimodal/external embedding input, cross-attention and unsupported auxiliary output.
- Dense append to contiguous slots that have never been committed and whose reference-zero contents are established; no holes, deletion, shift, compaction, wrapping, pending copies or occupied-slot overwrite.
- Exact frozen KV dtype and layout. For the staged non-FA reference, support its transposed V layout rather than switching to FA. F16 K/V is a useful first proof domain if it matches the chosen R; it is not permission to convert a different R.
- One logical batch fitting one ubatch, with explicit rejection when it does not. No implicit native optimize/retry branch inside the fast transaction. Reusing a formerly tentative slot after a complete checked zero restoration is allowed; "fresh" does not mean it has never physically been written.
- Immutable supplied tokens/positions, not tokens that require mid-batch external sampling. Backend samplers remain off. Greedy or other sampling is a separate staged transition after verified logits, with explicit state if enabled later.
- One GPU plus the exact unchanged host/CPU staging or arithmetic paths required by R. Every CPU/GPU split is included in planning. Additional GPUs/backends require their own certificates and dependency semantics.
- Existing scalar kernel/fusion bundles retained unchanged where no equivalence certificate exists. Batch only pure regions for which an actual certificate applies.

"Full native" here means the whole requested transition executes and commits without a reference rerun, full-logit comparison or full-state serialization. It does not mean every kernel is batched or every deployment is admitted.

The current packing admission targets widths 8-32. This milestone does not imply an improvement for a four-row speculative verification request. Measure that workload independently and do not hide a zero applicable-hit rate.

## 5. Exact-input scheduling: remove one hard numerical premise

For each layer l and each query j in increasing logical position:

1. The input hidden state is the same as the scalar reference's input at that layer/token.
2. Run certified pure projection regions over several j values into transaction-owned scratch. Retain the scalar route for unqualified regions.
3. Insert only K[l,j] and V[l,j].
4. Run the original scalar attention with its original prefix extent, mask bits, backend, kernel/fusion route and arithmetic.
5. Only after that attention's reads complete may K/V for j+1 be inserted into that layer.
6. Finish that layer's pure output/FFN regions under the same certificate rules, then proceed to the next layer.

Explicit control/anti-dependency edges are required:

`write_KV(l,j) -> attention(l,j) -> write_KV(l,j+1)`.

The second edge is easy to miss: scalar attention physically reads padded slots that the following write would change, even where its mask says "drop". A graph scheduler that models only logical valid-prefix reads may reorder this incorrectly. For the first implementation use a fully ordered execution stream per participating backend and explicit cross-backend events; do not rely on textual graph insertion order if optimizer/concurrent-stream passes can reorder operations. A single CUDA stream is not automatically fully ordered when Programmatic Dependent Launch (PDL) is active: inspect the actual dependency waits, their position before conflicting accesses, and captured graph edge attributes. Keep the frozen PDL policy or separately prove any change equivalent. The [NVIDIA PDL specification](https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/programmatic-dependent-launch.html) explicitly permits overlapping dependent kernels on the same stream and requires synchronization for dependent memory accesses.

This schedule preserves every physical input bit read by unchanged attention. It therefore needs no new claim that `0 * NaN`, `0 * Inf`, signed zeros or online normalization are harmless. It also avoids defining a mathematical attention function that silently differs from the deployment implementation.

It does not magically preserve a fusion that crosses the proposed boundary. If R fuses RMSNorm/multiply/RoPE/SET_ROWS, retain that exact scalar composite and batch only preceding certified pure work, or prove equivalence of the replacement composite. Disabling the fusion globally establishes a different policy unless separately proved equivalent.

Layer-major scheduling is permissible only if the full dependency DAG supports it. For ordinary independent-layer KV, each token's layer l+1 consumes its own layer l result and the layer l+1 prefix, not another layer's later-token cache. Shared layer KV, side-effectful callbacks and hidden state invalidate that argument. The checked template must encode this fact.

### Why all-KV-first needs more evidence

Suppose a padded attention implementation evaluates `sum(mask[i] * V[i])`. The reference processes query 0 while a future slot contains zero. A batched path first writes infinity into that future slot. Even with mask zero, `0 * infinity` is NaN, so the first output can change. The same issue affects rollback: deleting cell metadata does not remove the infinity from physical memory.

Finiteness can remove that specific example, but alone is not a universal bitwise proof. The actual reduction, signed-zero behavior, masked loads and normalization must be accounted for. A masked-noninterference lemma can justify a faster all-KV-first schedule later, but it is not required for the exact-input MVP.

## 6. Zero-free-tail storage and bounded rollback

Define the storage invariant at every committed boundary:

- Slots `[0,n)` contain exactly the reference K/V bytes.
- All element storage in free slots `[n,capacity)` is positive-zero bit pattern.
- Unused per-row or variable-embedding padding that can be read has its prescribed reference bytes, initially zero.
- Context metadata describes exactly the dense committed prefix, with no untracked aliases or pending mutation.

The source's initial buffer clearing supports the base case. Ownership and each successful/aborted transition must preserve the invariant. Merely observing maximum position n-1 is insufficient to establish it for an arbitrary imported context.

For a proposed append of q tokens, let W be the exact physical write footprint of their K/V stores, including compiler-visible widened stores and padding writes. Require `W` to be disjoint from all old committed KV bytes and from other owners' storage. Candidate scratch and outputs are separate owned resources.

After a successful fully completed transition, the q new rows become committed and the rest remains zero. On a **nonfatal failure with known bounded writes and known completion**, clear W to its pretransaction zero bits, discard private outputs/shadow metadata, and return to the old committed state. There is no successful-call full KV backup or whole-cache hash.

This zero restoration is not sound for deleted/reused slots with arbitrary old bytes, a shared prefix, unknown writes, device faults, or an asynchronous operation still able to write. Those cases require a journal, copy-on-write, a trusted checkpoint/replay, or rejection.

### Exact write-set formulas for a simple F16 domain

For layer l with capacity C, old prefix n, append q, K width Dk and transposed V width Dv:

- K: byte range `[Kbase + 2*Dk*n, Kbase + 2*Dk*(n+q))`.
- Transposed V: union over `d = 0..Dv-1` of `[Vbase + 2*(d*C+n), Vbase + 2*(d*C+n+q))`.

Use each layer's actual base, strides and allocated width. If the implementation pads V to a maximum width, Dv is that actual stored width, not a nominal per-layer head width. A broad bounding interval for transposed V contains old rows; the write-set representation must support strided rectangles or explicit disjoint ranges.

For recovery, K can use a checked contiguous memset and transposed V can use a checked 2D memset with pitch `2*C`, width `2*q`, height Dv, beginning at `Vbase+2*n`. These library operations and their range/lifetime semantics are part of the trusted backend contract. This is a design, not an implemented optimization.

General quantized K/V needs block granularity, rounding and read/modify/write treatment. It should not be silently admitted by the F16 rule.

### Speculative accepted-prefix extension

The initial theorem commits all supplied q tokens. A speculative verifier that commits only m <= q must additionally stage its acceptance/RNG decision and clear `[n+m,n+q)` after all reads/writes complete, before publishing m. Rejected-suffix zeroing may be an ordinary successful-call cost, not just an error cost. Including this extension requires a precise sampler/acceptance transition and its own tests. Full q-token decode equality does not by itself establish the speculative protocol.

## 7. Three qualification objects plus a capture instance

### KernelQualification: cold path

A trusted, immutable record identifies:

- Exact reference and candidate code/binary/module identities and backend/device/math domain.
- Both invocation schemas, input/output correspondence and supported tensor/value domains.
- A relational statement: equal required input bits imply equal required output bits; writes stay within the declared frame; there are no unsupported races or externally visible side effects.
- Arithmetic details: quantizer, accumulator, reduction tree, rounding, FMA/casts, instruction semantics and tail behavior.
- All premises and how each is established: statically, by owned invariant, by runtime guard, or merely assumed.
- Evidence artifact and checker version, with level `empirical`, `conditional structural` or `proved within stated model`.

The production "proved" mode must not upgrade empirical evidence. The code generator/compiler/GPU model may remain trusted; say so. An unverified callback returning true is not an independent proof of an input-dependent premise.

Unchanged nodes may use identity/reflexivity only when they really invoke the same selected code with equal inputs and deterministic semantics. Same operation name or dtype is insufficient. In this runtime, a logical ubatch with more than one token switches CPU thread count/threadpool to batch settings even for a scalar-shaped node. Preserve the scalar settings for such unchanged nodes, or certify that the alternative settings preserve the required bits. Include threadpool/math-state binding and any shared-backend mutation in resource leases.

### PlanTemplate: prepare once, reuse within its domain

Contains the complete graph, including fused nodes, transfer operations, explicit anti-dependencies and backend partition; symbolic buffer roles and alias constraints; exact route/template family; supported shape/stride/alignment domains; per-query scalar-prefix extent pattern; and qualifications for every node whose behavior changed.

The plan constructor must first split/allocate or produce an equivalent immutable allocation plan, then run a **pure backend prepare** operation for every split. Backend route selection must return a closed executable description. Execution must consume that description without independently rerunning a selector that can choose another algorithm.

The manifest must be nonempty for a nonempty request, cover the expected full operation/transfer sequence exactly, and reject omissions, duplicates and unaccounted execution. The existing launch-time CUDA route observer is too late for this purpose. Implement preparation and execution from one shared dispatch definition so they cannot silently disagree. If a route depends on unavailable tensor contents, either stage that decision before persistent writes with its own dependencies or reject it. First-domain dense projections should not need data-dependent route selection. Scheduler allocation alone does not reserve all backend resources: the inspected MMVQ path allocates Q8_1 scratch and issues quantization and sometimes a source-padding memset inside execution. Prepare must include these operations, reserve the needed pool/workspace resources, and bind their lifetimes. Lazy allocation/initialization or library algorithm selection after an earlier persistent write must not escape the plan.

The key is a canonical structural identity, not a stringified tensor name. It includes reference/qualification version, model/adapter versions, exact graph/fusion policy, placement, supported q, types/strides, route-affecting dimensions and prefix-extent pattern. It can use parametric ranges only when the qualifications actually quantify over those ranges.

### PlanBinding: check every request

Holds current context epoch and clean-state capability; exact append positions/slot range; immutable tokens, masks and indices; buffer allocation IDs plus nonreused generations; actual base/size/offset/stride mappings; ring-copy slot; stream/event dependencies; output destinations and lifetimes; and the qualification epoch being leased.

Dynamic checks are mandatory on a template hit. Do not place every physical address and exact token position in the template key, then advertise no-miss reuse. Conversely, removing them from all checks creates a stale-address vulnerability.

Dense host-generated SET_ROWS indices can be checked from the formula and locked immutable inputs, without downloading them from GPU on every invocation. An arbitrary caller-supplied device index tensor is outside this shortcut.

### CapturedExecutable: allocation-specific instance

Separately identify the CUDA graph instance, its template ID, capture policy, captured launch manifest, buffer generations/addresses, ring slot and graph-exec generation. A template can be reused while a capture instance must be rebound or rebuilt.

Capture and ordinary launch both must execute the same prepared manifest. Replaying a graph can bypass per-kernel launch observers, so validation must happen at the graph-exec boundary. Failed graph-exec update/reinstantiation invalidates the old instance lease before any reuse.

Current `cgraph->nodes[0]`, graph UID and cached tensor properties are useful implementation aids but do not constitute this numerical/state binding. The staged audit also disables capture/fusion, so its recorded trace cannot be reused as evidence for an unobserved captured/fused execution.

### Reuse example

With physical prefix padding 256 and q=8, many append positions have extent pattern `[256,256,256,256,256,256,256,256]`. Their topology template can match while positions, masks, indices and state epoch are rebound. Near a boundary a mixed pattern appears, then the stable `[512,...,512]` pattern. Exact extent signatures must be checked, not inferred from the first or last position alone.

### Invalidation and TOCTOU

Invalidate/rebind on allocation replacement, graph rebuild, ring-copy change, KV mutation, dtype/stride/alignment change, route threshold crossing, model/adapter/control-vector update, backend/driver/math change, policy change or qualification revocation. Raw address reuse is not allocation identity.

Hold exclusive context and resource/qualification leases from validation through completion/publication. A generation comparison without preventing mutation between comparison and launch does not close TOCTOU. All counters are nonwrapping or reject before wrap.

## 8. Precise transaction timing and pseudocode

This is an API design, not a patch against the supplied files.

```text
append_fast(owner, request):
    acquire exclusive owner lease
    require owner is Clean, no operation is in flight, request ID is eligible
    validate immutable request and whole-logical-batch domain
    require pure pending-update query says none
    require no external mutation since owner's invariant was established
    reserve epoch; reject on counter overflow

    tx = reserve shadow metadata, output storage, input storage, event storage
    tx.slots = dense fresh range [n, n+q)
    derive per-query reference prefix extents/masks
    # Do not call native memory_update or mutating apply on committed metadata.

    template = lookup structural template
    if miss:
        construct exact-input dependency graph, including alias anti-dependencies
        split and allocate without persistent-data mutation
        prepare every CPU/GPU split, transfer, fusion and launch route
        verify all certificates and static bounds
        cache immutable template only after complete success

    binding = bind actual allocation generations, ranges, ring slot and streams
    validate current dynamic bounds, aliases, indices, epoch and certificate lease
    if rejected:
        release tentative resources
        return RejectedClean, or enter a separately valid reference transaction
        # Ordinary native decode is not an automatic invariant-preserving fallback.
        # Unsupported-domain fallback invalidates fast admission until I is restored.

    mark owner Tentative; no native state observer may bypass owner
    prepare owned inputs and exact reference mask bits
    submit immutable prepared plan
    record final completion covering every participating device, auxiliary stream,
        transfer and output copy, including work submitted before any later failure

    if any failure:
        if write frame and completion are both known, and backend remains usable:
            wait/drain every submitted operation
            clear exact fresh write set to zero; wait for clearing to complete
            restore/discard shadow metadata and output descriptors
            return owner to Clean with a fresh epoch
            optionally enter the same owner-protected reference transaction
            account for all failure/recovery work and its state transition
        else:
            mark owner Poisoned; quarantine resources and all dependent cache entries
            recover only from prior trusted checkpoint or deterministic token replay
        do not publish candidate outputs

    wait for full completion, check asynchronous errors and establish complete planned-node coverage
    verify resource/qualification leases still valid
    # No full logits/KV equality check here: semantic certificates and invariants
    # are what justify omitting that audit, not a belief that the data look normal.
    publish metadata, output descriptors, history and explicit sampler state once
    issue Clean capability tied to new epoch and provenance
    release resource leases only when their consumers have also completed
```

Allocation failures during planning must not mutate committed state. Host allocation needed for commit should happen before submission, so the publication section can be nonthrowing. `clean=true` is an owner-issued capability following a successful protocol, never a caller-set boolean accepted at face value.

The linearization point is the owner-protected publication of a complete committed descriptor. In the in-place zero-tail design, **every reader must be excluded for the whole transaction**, including GPU readers launched earlier; a reader lease lasts until its device work finishes. An immutable-descriptor release-store alone is not enough: an old descriptor can still reference the same padded KV bytes that a candidate is modifying. A pointer-publication design additionally needs generation-isolated/COW storage or the same full reader-exclusion discipline. Borrowed native pointers cannot outlive their valid read lease. Deep-copy output snapshots can be retained independently, but old raw KV descriptors cannot be safely reused after publication. Native getters that bypass this discipline would expose tentative or cross-generation state.

Multiubatch support needs a complete preplan and reservation for all ubatches, or a higher-level transaction that rolls back all earlier successful ubatches. First-domain rejection is simpler and honest.

### Fallback is itself a state transition

A prelaunch candidate rejection leaves the old state intact; an ensuing fallback does not automatically do so. It must run the exact R schedule under an owner/completion/staging protocol that preserves I. Merely invoking ordinary native decode and labeling it scalar is insufficient: native metadata mutation, multiubatch partial failure, queued shifts and dirty freed slots remain possible. If fallback is outside the invariant-preserving domain, revoke the fast-path capability and do not reissue it until I is independently re-established. A failed ordinary fallback requires restore/poison handling, not the claim that the initial rejection was a stuttering step. The theorem below calls only the candidate veto itself a rejected stutter; a successful fallback is an R transition, and its failure is analyzed separately.

### Asynchronous errors and availability

There are three distinct milestones: accepted submission, completed work, and published state. They must not be collapsed.

The current CUDA backend's fatal error handler can terminate the process at launch-error checking or synchronization. A `try/catch` around `llama_decode` will not generally catch that. The proposed in-process abort path is valid only for errors represented by a usable backend with known completion/write scope. Illegal-address/device-loss/unknown completion poisons the context; a supervisor can recover from an already retained checkpoint or token history, but this is a separate availability design. Do not promise recovery by taking a checkpoint after a fatal failure.

A final event on one stream is sufficient only when every other stream/backend has been joined into it. Existing scheduler events may be absent or may only cover a successful split. Record a transaction-level submitted-work ledger before moving to the next split and ensure failure draining includes the last partially submitted split and pending output copies.

## 9. Conditional safety theorem and proof obligations

### Theorem statement

Let R be the explicitly fixed deterministic scalar transition program. Let the candidate owner start in a state related to an R state by relation I: committed metadata/history/output/sampler bits agree; committed KV bytes agree; free/padded storage obeys the prescribed reference bytes; and there are no outstanding writes or untracked owners.

Assume:

A1. Every unchanged operation executes the same deterministic selected semantics as R on equal required input bits.

A2. Every changed operation has a sound relational qualification for the actual invocation, including equal outputs and its physical write frame. All certificate premises hold.

A3. The prepared plan preserves all value dependencies and all conflicting physical-memory dependencies, including padded-read anti-dependencies. Allocator/lifetime/event bindings are faithful and stable through completion.

A4. All persistent writes are within the admitted fresh set W; old committed KV and other owners are untouched. No externally visible sampler/output side effect occurs before publication.

A5. Completion/error classification is sound. A recoverable abort drains all work and restores W plus any tentative metadata/output state exactly. Unknown faults do not return a clean capability.

A6. Publication is atomic for all allowed observers, and reference/qualification/ownership identities cannot change unnoticed during the transaction.

Then:

- A successful q-token transaction emits exactly the reference's q-token output bit patterns and ends in a state related by I to `R^q` applied to the old state.
- A rejected prelaunch transaction is a stuttering step on the committed numerical state.
- A recoverably aborted transaction is a stuttering step after restoration, although its internal epoch advances.
- A poisoned transaction publishes no candidate result and is not eligible for continued execution/cache admission until independently restored.
- By induction on successful committed transactions, every exposed committed prefix matches the corresponding R trace. This is a safety theorem, not a guarantee of eventual completion or crash recovery.

### Proof outline

**Base case.** Context initialization uses the prescribed model/configuration and establishes identical zero-initialized KV allocation, empty history and initial sampler state. A trusted restore must establish the same relation; maximum-position checks alone do not suffice.

**Pure nodes.** Equal inputs imply equal outputs by A1 or A2. Copies are modeled as bit-preserving operations with exact byte ranges and dependencies, not ignored.

**Attention at layer l, query j.** Earlier token rows in that layer have already been written with equal values. The current row is equal by the K/V production contracts. Later rows still contain their pretransaction reference bytes because of the explicit read-before-next-write edge. The per-query physical prefix, mask and selected route match R. Thus every physical input read by attention is equal, and its outputs are equal by A1. Independent-layer storage and the hidden-state DAG justify the layer-major topological order.

**Commit.** All new rows and outputs are equal, old rows are unchanged, and all writes/copies have completed. The still-free tail is unchanged zero. A6 publishes the entire new logical state together, establishing I for the next committed boundary.

**Abort.** A4 confines writes to W plus private scratch/output. The pretransaction value of W is known zero. A5 waits for all writers and restores that exact value, while shadow metadata/output/sampler state is discarded. Thus the previous numerical state is restored; the new epoch only prevents stale-plan reuse.

**Induction.** Compose successful transitions and delete stuttering rejected/aborted steps. Poisoned execution has no admitted successor until I is independently re-established.

### What is not proved today

The inspected source does not implement the full prepare/execute split, exact-input schedule, atomic publication protocol or the above proof. Its registry accepts trusted evidence, and the CUDA enforcement path refuses execution. The bounded Python model checks a finite state family under imported projection equivalence; it does not verify C++, CUDA, compiler lowering, the driver or the certificate checker.

The main open proof obligations are:

| ID | Obligation | Minimum evidence before enabling |
|---|---|---|
| K1 | Candidate projection preserves quantization, reduction, FMA/cast and tails for every admitted input. | Mechanized relation, or an explicitly conditional structural argument bound to the actual binaries; replay alone remains empirical. |
| K2 | Every kernel/store/copy stays in its declared physical region; no unsupported races. | Index/alignment/overflow analysis plus compiled-code or trusted lowering correspondence. |
| K3 | Packed columns do not mix logical inputs and cover outputs exactly. | Universal mapping/coverage proof or checked parametric construction. |
| G1 | Plan includes every executed node, fusion, transfer and route. | Shared pure dispatcher; execution consumes its immutable output; capture manifest checks. |
| G2 | Physical alias and read-before-write constraints survive scheduler/allocator optimization. | Alias/lifetime checker and explicit control edges with tests. |
| S1 | Owned state starts valid and no native API mutates it outside the owner. | Encapsulation and provenance, not just a clean boolean. |
| S2 | Zero-free-tail survives commit, abort, import and accepted-prefix trimming. | Range-exact stores/clears and an inductive state argument. |
| S3 | Commit observers cannot see mixed metadata, KV or output generations. | Full reader exclusion, or generation-isolated storage plus linearizable descriptor publication. |
| E1 | Completion covers all submitted asynchronous work and errors. | Backend completion API, submitted-work ledger, injected late failures. |
| C1 | Reused plan/capture/cache entries are bound to current identities and lifetimes. | Generation leases, stable key checks, invalidation coverage and race tests. |

Any uncheckable premise is either a declared trusted assumption or a reason to reject. Calling the entire system formally verified would be inaccurate.

## 10. Bounds, atomics, taint and cache details

### Bounds must match the implementation's integer widths

The SET_ROWS source narrows the flattened index to `uint32_t`, and its launch grid count is an `int`. A host predicate checking only 64-bit tensor size is insufficient.

For a conservative first domain:

- Check every dimension/product/addition/stride offset with widened arithmetic before narrowing.
- Bound the flattened scalar element domain to `UINT32_MAX` and every divisor passed as 32-bit to a positive supported range. This is conservative rather than a maximal bound.
- Bound grid dimensions by both host integer representation and actual device limits.
- Check index tensor size/type, every generated index, row width and physical destination range.
- Reject duplicate destinations and overlapping vector/block stores, including conflicts induced by strange strides or aliases.
- For quantized stores, validate block size/alignment and the whole quantization read/write block. Do not apply scalar-element bounds unchanged.
- Prove that weights, index tensors and read-only inputs are not aliases of scratch/output/KV write destinations.

The kernel's plain SET_ROWS stores are not atomics. Duplicate indices are a race even if a high-level scatter operation appears deterministic. Floating-point atomic reductions would require an exact ordering contract or exclusion; the mere presence of atomics is not always disqualifying, since disjoint integer bookkeeping can have independent proofs. Host atomic publication likewise is not a numerical reduction proof.

### Taint is scoped, but must be contagious where dependencies exist

Track separate states such as Clean, Tentative, Recovering and Poisoned. At failure, taint every allocation/cache object whose provenance depends on potentially incomplete or unknown writes. Do not taint unrelated devices by default if a sound isolation boundary is known, but do not assume a stream boundary isolates an illegal-address or device-level fault.

A model/source identity match does not restore clean state. Neither does changing graph policy or recomputing just the next token. Restoration must establish the state invariant, not merely produce one matching logit vector.

### Cache interfaces

Keep execution-plan caches distinct from KV-result caches:

```text
lookup_prefix(known logical identity and required provenance)
admit_prefix(identity, immutable payload, producer capability)
validate_storage(entry, version/integrity policy)
materialize(entry, destination layout/ownership/zero-tail contract)
```

A caller should not have to compute the expected full KV and logits to perform a prefix lookup. A hash is an index, not logical equality: verify the canonical key on collision, or explicitly include collision resistance in the trust assumptions. Integrity checks protect stored bytes; qualification/provenance establishes their semantics. The first result cache may remain strict-recipe and single-owner.

Do not admit tentative or poisoned entries. A cache entry needs an immutable payload version, valid ownership/lifetime and producer lineage. Reusing a pointer after free is not a hit. A post-admission mutation requires invalidation or copy-on-write. If an ancestor's semantic qualification is revoked, descendants relying on it cannot remain trusted merely because their checksums match.

On import into the zero-tail MVP, use a newly initialized owned context, materialize only the qualified live prefix, and establish that every other read-relevant byte remains the prescribed zero. Broader imports require their own evidence or remain on the audit path.

## 11. Prior-work boundary

[Vosti](https://arxiv.org/html/2609.38981v1), inspected 2026-11-04, already composes an engine invariant proof with relational kernel contracts and accounts for prefix-cache provenance. Its paper explicitly separates trusted launch/compiler/representation components and retains numerical premises, including a finite-values premise for masked attention reasoning. It pins runtime-independent configurations; equivalence-based alternative dispatch is described as future work. Consequently, "kernel contracts plus cache/state induction" is not a novel claim here. The possible distinction is retrofit compatibility with an externally fixed deployment trajectory, including its quantized kernels and failure/transaction boundary. That distinction needs evidence of practical value, not a stronger-verification slogan.

[Taming Bitwise Behavior](https://arxiv.org/html/2609.11356v1), inspected 2026-11-04, already studies reduction structure, precision/fusion/rounding, static equivalence classes and equivalence-constrained tuning, including a caller-provided reference. A registry of reduction signatures or searching only equivalent configurations is therefore not a new general mechanism. The proposed contribution would need to be the concrete legacy-runtime integration and a net-beneficial compatible execution path. Unsupported arithmetic must remain unknown rather than being collapsed into a common opaque label.

These are mechanism comparisons, not reproductions of either paper's artifact or cross-system throughput measurements. Neither paper supplies a certificate for the inspected HeteroSpec CUDA binary.

## 12. Adversarial test plan and release gates

### Tier 0: executable design checks, completed here

`check_transaction_model.py` is an intentionally small Python binary64 model. It assumes pure projection equivalence and tests two-layer scalar-versus-layer-major scheduling, zero-tail recovery, prelaunch guards and selected counterexamples.

Results in `transaction_model_results.json`:

- 54 successful schedule/full-state comparisons.
- 648 injected nonfatal abort positions, including after partial K or V writes.
- 648 stale-generation/allocation/count/unsupported-split, incomplete-manifest, aliased-storage, tainted-state or dirty-tail rejections.
- Five reproduced counterexamples: masked future V infinity, future K infinity before a -Inf mask, late write after rollback, 32-bit index narrowing and a later-split rejection after earlier mutation.

The model assumes no observers inside a transaction and immediate known completion; it does not test observer linearizability or asynchronous runtime completion. Its full-array assertions are ghost verification checks, not proposed hot-path scanning. Its named stage manifest is schematic, not a native launch manifest. These checks are neither exhaustive nor native/GPU tests. Their value is that the proposed protocol has an executable, falsifiable model and clear premises.

### Tier 1: host-side predicates and scheduler integration

- Prefix/slot cases at 0, 1, 255, 256, 257, capacity-1, capacity, q=1/4/7/8/9/31/32/33, and extent-boundary crossings.
- Empty request, invalid tokens, negative/overflowing positions, wrong sequence IDs, noncontiguous inputs, holes, SWA and pending updates.
- Multiubatch requests must explicitly reject in the first domain before any committed mutation.
- Artificial late unsupported split: assert no candidate kernel or persistent-data copy was launched anywhere.
- Allocation failure after metadata planning: old cells/heads/outputs must be unchanged.
- Forced buffer relocation, same-address/new-generation allocation, ring-copy rotation, policy/adapter change and qualification revocation.
- Overflow cases around INT32/UINT32/INT64/SIZE_MAX without allocating giant tensors.
- Transposed-V rectangle boundaries, variable-width padding, quantized block tails, duplicate indices, aliases and misalignment.
- A scheduler that tries to move future KV writes ahead of current attention must be rejected or constrained by explicit dependencies.
- Reject empty, missing, duplicated or reordered required manifest entries for nonempty requests. Include MMVQ scratch allocation, quantization, padding memsets and PDL attributes.
- Hold an old raw descriptor while a transaction tries to write its padded read region: the owner must block the writer or provide generation-isolated storage. A pointer swap alone must fail this test.

### Tier 2: actual native correctness, requires authorized hardware later

- Exact frozen-R versus candidate full logits, every layer's live KV and required free/padded bytes, not just tokens/top-1.
- Fresh context and long continued history. Run the next successful append after every injected abort, not only the immediate rollback check.
- Signed zero, subnormals, large finite values, NaN/Inf where the qualified domain permits them; extreme quantization blocks and tails.
- Same reference fusion/capture policy, including steady-state CUDA graph replay and graph-exec update/rebuild.
- Compare observing and non-observing executions to detect audit-induced route changes.
- Error injection before first launch, after K only, after V, after each split, during output copy, after submission but before final event, and after completion but before publication.
- Exercise callback-false after an intermediate node: a scheduler success code must not authorize commit of an incomplete graph.
- Force n_threads/n_threads_batch and threadpool/threadpool_batch to differ; unchanged scalar CPU nodes must retain the exact reference settings or be rejected.
- Check that clearing W happens after all writers, and cannot touch committed prefix bytes.
- Simulate fatal/error-unknown classification: no clean capability, no cache admission, no scalar retry in that context.
- Deliberate concurrent invalidation and observer calls must respect owner leases.
- If enabling accepted-prefix commit, test all m from 0 to q, suffix zeroing, RNG rollback, acceptance decisions and next-step equivalence.

### Tier 3: performance, with the same service outcome

Report separately cold preparation, warm hit, capture rebuild, guard rejection, recoverable abort, poisoned recovery and accepted-prefix cleanup. Include:

- Planning/cache lookup/dynamic binding CPU time.
- Input staging, graph construction/allocation and all transfers, including actual mask construction/copies that can scale as q times padded prefix length.
- Required stream/event waits and lost overlap.
- Projection, KV writes, attention and other compute.
- Required result transfer, publication, zeroing/journaling and cache materialization.
- Request p50/p95/p99, full-session time and throughput, peak KV/scratch/output memory, eligible-hit rate and fallback rate.

Use the same frozen R for all comparisons. Include the strong backend four-column loop baseline, not only graph tile-plus-concat; fixed-width packed and unbatched reference alternatives; and the existing full-snapshot audit path as an overhead baseline, not the main performance baseline.

For q appended tokens and L layers, a structured binding/write-set descriptor can be O(L+q), while scalar index materialization or naive scatter checking can cost O(L*q*D). Zero restoration touches O(q*sum(Dk+Dv)*element_size) bytes and belongs only to failure/trim paths under the zero-tail invariant. Plan memory/scratch and final output transfer can be substantial. This does not bound total input preparation: dense mask materialization can scale as O(q*P) for padded prefix P, and the executed graph has its own per-layer/per-query work. No O(1) whole-model guarantee is justified.

The conservative schedule adds ordering and possibly launches. It may lose to the strong four-column loop despite a kernel-level projection gain. If so, report the negative result and do not relax proof assumptions to manufacture a win.

### Concrete break cases

| Break | Why naive approach fails | Expected response |
|---|---|---|
| Same prompt, different chunk/route producer | Prefix identity does not imply same numerical KV. | Strict recipe miss or proved cross-recipe relation. |
| Later CUDA split refuses after CPU/GPU split 0 | Per-split prelaunch is not per-request prelaunch. | Whole-plan preparation before submission. |
| All future KV written before earlier padded attention | Masked raw bytes may influence arithmetic. | Exact-input schedule or explicit masked-noninterference proof. |
| Metadata-only rollback after NaN/Inf write | Free dirty bytes can be read later. | Quiesce and zero exact W, or restore trusted bytes. |
| Clear while an asynchronous kernel is still running | Late store dirties the supposedly restored state. | Completion proof before clear and clear completion before reuse. |
| Duplicate SET_ROWS indices or overlapping strides | Plain stores race or overwrite other state. | Reject before launch. |
| Flattened index wraps at 2^32 | 64-bit size check misses the kernel's narrowing. | Check the actual narrowing domain. |
| Same buffer address reused for another allocation | Pointer cache hit binds the wrong owner/lifetime. | Allocation ID plus generation lease. |
| Old descriptor survives release-store publication | In-place padded KV bytes change under its reader. | Full reader leases through device completion or isolated storage. |
| Empty/incomplete all-split manifest | `all(empty)` or a partial scan can vacuously pass. | Exact expected coverage and nonempty-plan checks. |
| Warm plan omits backend-internal scratch/memset | Lazy resources fail or writes escape the scheduler-level manifest. | Include backend resource and memory-operation plan. |
| Same stream treated as fully serialized under PDL | Conflicting accesses may overlap before dependency synchronization. | Check wait/trigger placement and graph dependency attributes. |
| Capture replay bypasses launch observer | Old plan can run despite new policy/qualification. | Validate captured-exec manifest and generation at replay boundary. |
| Audit disabled the original fusion | Collected trace belongs to another execution policy. | Observe without changing policy or label a distinct R. |
| Fatal CUDA synchronize aborts process | C++ catch does not perform rollback. | Poison/supervisor recovery, no in-process recovery claim. |
| LoRA changes at stable pointer | Topology/address key can remain unchanged. | Explicit content/version identity and invalidation. |
| Eval callback stops nodes but scheduler reports success | Submission status is not complete manifest execution. | Reject unmodeled callbacks or prove completed-node coverage. |
| Logical batch silently switches CPU threadpool | Same node/shape can run a different numerical implementation. | Bind exact CPU execution settings or qualify the change. |
| Sampler/RNG advances before commit | Same KV/logits does not restore next token distribution. | Stage sampler state or reject sampler path. |
| Accepted only m of q but tail retained dirty | Next read sees rejected speculative bytes. | Clear suffix and publish only accepted-prefix state. |
| Rejection falls through ordinary native decode then keeps Clean | Reference route may mutate/partially fail outside the fast invariant. | Transactional reference fallback or revoke/re-establish fast capability. |
| Full snapshot restored but free padding differs | Live KV equality may not imply future equality. | Restore or re-establish the full read-relevant padding invariant. |

## 13. Implementation sequence and stopping criteria

1. Freeze the actual reference transition and observation contract; decide whether it is scalar recurrence or an existing shape-dependent recipe. Record all value-relevant policy choices.
2. Implement a pure all-split prepare/execute interface and closed launch manifest. Fail closed for missing routes, unsupported fusions or unbound data dependencies.
3. Add the exclusive owner, shadow state, immutable input/output resources and completion ledger. Reject unsupported native mutation before it happens.
4. Implement the exact-input per-layer schedule while retaining every unqualified scalar composite. Add precise F16 transposed-V writes/clears if that is the frozen layout.
5. Establish the zero-free-tail invariant and nonfatal bounded rollback. Keep fatal-device recovery out of any catch-and-retry promise.
6. Bind one real kernel relation to deployed code; do not enable the optimized production gate until that relation's premises are enforceable.
7. Add template/capture reuse with allocation and qualification generations, then validate steady-state correctness and cost.
8. Benchmark against the strong frozen-reference backend loop and report applicability, overhead and negative cases. Only then consider masked parallel attention, wider batching, shared prefixes, more backends or automatic selection.

A sufficient first milestone is one genuinely admitted native end-to-end path with full-state equivalence on authorized hardware, no hot reference rerun/full serialization, fault-injection recovery coverage, and a measured improvement over the strong baseline. It is not a universal proof, and none of the current evidence establishes that milestone yet.
