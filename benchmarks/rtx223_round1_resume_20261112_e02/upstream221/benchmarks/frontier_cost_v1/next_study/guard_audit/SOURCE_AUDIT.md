# CUDA Q8 recipe / guard source audit

## Decision

The pinned implementation contains concrete dense-cache, output-ownership, graph-reuse and backend-loop4 guards. **The packed Q8 path does not inherit the backend-loop4 guard contract.** It creates an unmarked grouped matmul and uses the ordinary CUDA dispatcher. In addition, the placement observer is enabled only during heavy capture; the original RTX observer does not select `frontier_packed_*` projection nodes. These are two specific gaps between a broad reading of the method description and the audited implementation. They are not evidence that the frozen measured configuration produced incorrect outputs.

The useful TPDS revision is to publish the actual predicates and qualification scope, and then qualify a narrowly defined packed descriptor admission rule. This audit adds no timing result, no model execution, no GPU execution, and no claim that a general 5% gain has been achieved.

## Exactly what was inspected

The method text is pinned to [PR #222 commit e8a4981](https://github.com/leecdiang/HeteroSpec/blob/e8a4981ef7db8f05cff7144fd4edc6e5a4109343/papers/reference_compatible/20261111_tpds_mainline_rewrite/sections/03_method.tex). The implementation is the public [RTX phase-1 source release](https://github.com/leecdiang/HeteroSpec/releases/download/tpds-phase1-rtx-review-v2-evidence-20261107/rtx-phase1-source.zip), SHA-256:

`57cbfbfe43ae1c4b4ed5ba3f5261412daa2b5c14b712e76d868da55f4f8a4101`

The archive contains independently identifiable `loop4` and `packed` cores. The source manifest and every audited member were checked against their bytes. `native/STAGED.json` records base commit `a28f3474acac793d07b6e6f462cb70bbccfa6ceb`; that ancestry is not a claim that all modified release members equal that Git tree. The archive/member hashes are the effective identities. Old intermediate source-staging receipts are not substituted for the release manifest.

The reconstructed Linux M2 candidate frontend is listed separately in `GUARD_MATRIX.json`, with its own file hashes and reconstruction status `RECONSTRUCTED_NOT_NATIVE_QUALIFIED`. It is useful for determining what the later frontend actually changes; it is not presented as the historical executed RTX binary. The numerical cores were not modified.

The matrix records 10 obligations, 20 source-file identities and 35 exact source regions. Each guard has an explicit predicate, failure timing, fallback behavior, supported scope, static observation and missing native qualification. Full source SHA-256 values are in the machine-readable file; short names below refer to its source IDs and guard IDs.

## Actual guard matrix

| ID | Live implementation and predicate | Failure / fallback behavior | Scope the paper can safely describe |
|---|---|---|---|
| G01 | `PhaseContext::decode` plus `phase_append_requirements`: dense cache; one stream; no SWA/shift; physical head, occupancy and logical prefix agree; capacity fits; each occupied cell contains sequence 0; F16 K/V | Before the first decode of this phase, unsupported metadata gives empty extents and an exception. No new phase execution has occurred. | Dense, nonwrapping sequence-0 profile. `seq_has(0)` is not an arbitrary shared-cell exclusivity proof. |
| G02 | SIMPLE groups equal extent and `arithmetic_class`, max 32. LOCAL takes max-32 outer chunks. Frontend class encodes K/V types only. Original all-output reserve is 4; reconstructed M2 changes it to a bound reserve of 8. | Invalid SIMPLE descriptors/unknown lowering/output reserve reject before execution. No automatic reference replay. | Existing fixed deployment and all-or-last output mask; not a general per-operator recipe selector or arbitrary sparse-mask API. |
| G03 | Packed `build_lora_mm`: Q8_0/F32, outer q=5..32, singleton higher activation dimensions; packing needs contiguous activation, singleton weight batch dimensions and q≥8. Complete groups become `[K,4,g]`; tails stay ≤4 columns. | Packed node is unmarked and enters generic CUDA dispatch. Failed packing predicates use graph-level tiles; failed outer predicate uses ordinary wide matmul. The path does not emit a typed recipe-unsupported outcome. | Source-backed CUDA Q8 mapping for the bound profile. General correctness of out-of-scope fallback is not established by this source audit. |
| G04 | Marked backend-loop4 explicitly checks dtype, all tensor contiguity, shape agreement, q=5..32, int offset limits, same-device actual CUDA buffers, NVIDIA warp32, no unsafe padded compute view, and MMVQ selection for every old tile; IDs/fusion rejected. | Failure throws before this operator’s quantizer/kernel, **inside** `llama_decode`. Earlier operations may already have run; the target phase catches and poisons. No marked fallback. | Strong control path only; these checks cannot be attributed to the unmarked packed node. |
| G05 | Attention checks ordered one-sequence causal non-Flash groups, prefix counts, dtype/head/transpose descriptor, supported LLAMA/QWEN3 shapes; constructs per-extent K/V/mask views; materializes mask contiguity. | Generic branch if grouping condition is false. Some unsupported conditions are `GGML_ASSERT` and terminate the process; they are not recoverable preflight statuses. | Dense fixed attention recipe, not SWA, wrapping, paged, Flash, MoE or MLA coverage. |
| G06 | Actual reuse compares active/layout policy, full per-row prefix vector, ubatch/sequence/output counts and a rotary-head placement key. Output indices are refreshed from the current mask. | Mismatch rebuilds the graph. | More than outer-shape reuse is implemented. The unused frontend `refplan::Identity` is not the live graph key, and a literal phase label or general projection recipe object is not compared. |
| G07 | Synchronize after each native group; copy every requested full vector into owned storage before the next group; require requested pointer and append end; reject absent output slots. | Failures inside the target decode catch poison the owner. | Real output ownership, not a run-time comparison of values/KV to reference. `OutputRows` helper is not the live storage implementation. |
| G08 | Target group catch sets `poisoned`; reset/decode reject poisoned state. Commit uses accepted frontier, trims to `base+1+accepted`, and carries correction/bonus pending tokens. | Trim, draft decode and sample failures are outside that catch; the CLI exits on them. Assertions abort. | Current process lifetime contract. A reusable API whose caller catches errors needs a wider transaction-invalid flag. |
| G09 | `phase_observe=owner.capture`. Clean callback returns immediately. Original capture selects `kq*` / `hs_*` and requires a “5070” device description; M2 additionally selects all MUL_MAT nodes and checks GPU device type. | Heavy observation fails after execution. Clean `need(!obs.bad)` alone does not attest placement. | Heavy diagnostic coverage and cheap clean guards are distinct. No CPU fallback in measured clean runs is asserted here. |
| G10 | Diagnostic capture checks binary32/little-endian, finite requested full vector and complete native sequence export; marks active-KV extraction as required. Original snapshots cover initial/first commit; M2 broadens capture points. | Capture failures terminate the worker; clean requests do not perform this export. | Evidence collection, not equality verification. Each independent R comparison and case coverage still has to be bound to the actual binary. |

### Finding 1: packed and loop4 have different rejection contracts

The graph files differ exactly where the arithmetic groups are exposed. `loop4/src/llama-graph.cpp` marks a contiguous wide node with `hs_loop4::mark`. The packed version makes an ordinary `[K,4,g]` view and `ggml_mul_mat`, then reshapes its result. The shared `ggml-cuda.cu` checks the marker before applying the strict loop4 guards. With no marker, the same file follows its ordinary dispatch tree, including the bad-padding-to-cuBLAS branch. This is a real control-flow distinction, not a hypothetical interpretation of the paper. [G03, G04]

The packed mapping preserves four columns at the graph descriptor level. The MMVQ source also contains a case-4 specialization and channels in the launch descriptor. Those facts support the proposed mechanism, but they do not by themselves prove that every admitted device/layout reaches that specialization with the same activation quantization, offsets, reduction and state update. There is no reproduced counterexample in the frozen profile in this audit. The correct conclusion is **missing general recipe admission evidence**, not “the reported packing results are wrong.” [G03]

### Finding 2: observer coverage is not clean runtime admission

In the release frontend, `Observer::bad` starts false and reset reconstructs the observer. The callback immediately returns when `phase_observe` is false, and target decoding assigns that flag from `capture`. Consequently a clean postcheck of `!obs.bad` does not independently validate device placement. It can coexist with other protections: loop4 has actual buffer checks, and the entry selects a single GPU. Those protections have their own narrower scopes. [G04, G09]

The original observer also filters by tensor name. `frontier_packed_*` is outside its `kq*` / `hs_*` filter. The reconstructed Linux M2 frontend expands observation to MUL_MAT nodes, but that later change must not be projected backward onto the original RTX capture coverage. Offline operator replay or other host evidence may provide additional qualification; that evidence must be cited and bound separately. [G09]

### Finding 3: invalidation is partly an API rule and partly process termination

Target phase execution is protected by `catch (...) { poisoned=true; throw; }`, and later `clear`/`decode` reject a poisoned context. This supports the paper’s target-group failure statement. `Context::trim`, draft decode and finite-logit sampling lie outside that catch. Their failures cause the published entry to exit, so the audited worker does not resume another request. An embedding application that catches those errors and retains the object would need an explicit transaction-level invalidation contract. A graph assertion terminates the process and cannot be described as caught poison or a safe retry. [G07, G08]

### What the graph-reuse source really supports

The suspected “shape-only reuse” problem is **not** supported: actual reuse does compare the prefix vector, active/layout policy and head-placement choices. The documentation issue is more precise. The generic frontend `Identity` helper is unused; actual reuse depends on the core predicates, fixed model/context identity and refreshed input indices. The table should list those checks, and treat deployment/recipe binding separately. [G06]

## Minimal next qualification, with no new numerical claim

`PACKED_QUALIFICATION_DESIGN.json` defines a focused follow-up around the packed path. It is deliberately an unexecuted experiment design. It requires captured real projection operands and their dtype/shape/stride/buffer descriptors; the exact loaded module/build/model identity; the selected MMVQ specialization and channel/offset descriptors; old-tile own-path replay; packed-versus-loop4 full output comparisons; and full-model original-reference state checks where applicable.

The first cases should be q=4/5/7/8/9/11/12/31/32, actual physical-boundary splits, and one violation of each missing packed-admission condition. The width sweep distinguishes no-packing, two-group entry, tail behavior and maximum supported width. Unsupported-descriptor cases need an explicit expected result—reject before native execution or use an independently qualified fallback. For a failure injected after execution begins, the expected result is invalidation with no successful reuse. These outcomes cannot be combined into a single generic “test passed” cell.

No numerical-core patch is submitted as a fix by this audit. A proposed always-on packed guard must first be checked against the frozen measured descriptors, then measured in the service path so its cost is not hidden. This is the smallest evidence path from the static scope gap to a defensible runtime recipe contract. It also protects the later search for 5% incremental benefit from accidentally relaxing the numerical contract.

## Suggested replacement text for the method section

> For the evaluated CUDA Q8 deployment, dense-cache ownership, output reservation and planning are checked before each phase. Local attention and projection lowering additionally use descriptor conditions in the graph builder and backend. The backend-loop4 control has explicit shape, stride, placement and dispatch rejection checks; the packed projection uses a separate graph mapping and ordinary backend dispatch, whose supported descriptor set must be explicitly bound to the available deployment-specific qualification evidence. Table X distinguishes these runtime checks from capture-only observations and from conditions not yet covered by qualification. Graph reuse compares the prefix vector and active/layout policy in addition to existing graph parameters and head-placement checks. Target-group exceptions invalidate the resident owner; other worker-level failures terminate the process.

This wording preserves the conditional induction argument while making its premises reviewable. If the authors wish to retain the stronger statement that every packed recipe is dynamically admitted by descriptor guards, the dedicated packed admission and negative-case evidence need to be completed first.

## Reproduction and evidence boundary

Run the verifier against the public release ZIP. Supplying the separate reconstructed M2 frontend and pinned method file verifies those identities too:

```bash
python verify_source_bindings.py \
  --source-zip /path/to/rtx-phase1-source.zip \
  --candidate-frontend /path/to/reconstructed/candidate_frontend \
  --paper-method /path/to/03_method.tex \
  --out /new/path/static_binding_receipt.json
```

The verifier reads source bytes and exact source regions; it never imports native libraries, compiles, loads a model, uses a GPU or performs reference replay. Its receipt is **source identity validation only**. It does not turn static branches into measured runtime outcomes. Q4_K/Q6_K and the paper-specific Vulkan recipe are excluded because their independent implementation was not audited here; a file name containing “q4” for four query columns is not Q4_K evidence.
