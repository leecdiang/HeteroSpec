# Independent experiment review — 2026-11-03

Reviewed fixed heads: RTX PR162 `e11d2b75d82422409ba2b701aa38c59f36acc50b`; B570 PR163 `10a70566ce01ab707dbdcc57d8270c1434088f07`. Author-authorized developmental review; this is not an editor's decision or a new native reproduction.

## Finding

The quoted review is substantially supported: both platforms identify and repair a physical KV-prefix effect; Vulkan additionally needs the scalar-reference activation-precision path. The shared prefix rule is a concrete reusable mechanism. The present evidence supports mechanism-led repair and retained batching in the admitted implementation domain, but does not yet demonstrate an automatically inferred, cross-family runtime policy.

The most important wording correction is the meaning of target-only batching. `M_PQ/M_QB` execute ordinary greedy generation, without teacher-forced tokens or a hidden draft. Their target contexts admit four-row microbatches for prompt prefill, while generated tokens are still decoded one at a time. Therefore `M_QB/R` is a full-request comparison with a UB1 numerical reference, including prefill and context/path differences. It does not show four-token parallel autoregressive generation, nor isolate the new prefix rule's speedup.

## Source-supported execution semantics

- B570 `scripts/experiments/b570_llama_companion_v1/worker.cpp`, lines 139–157: arm decoding, target capacity `mode ? 4 : 1`, natural prompt prefill, and one-token ordinary generation. Lines 158–177 execute real proposals, verification, correction/bonus, and KV trimming only for C arms. Lines 147–181 include context construction and destruction in the service clock. Both target and draft model files are loaded before arm execution; M arms do not instantiate a draft context.
- RTX `scripts/experiments/rtx_llama_repair_v1/schedule.py`, lines 5–18: M has target capacity 4 and `draft=False`; C has real draft k3. Its pinned ancestor `scripts/experiments/rtx_scope_transfer_v1/worker.cpp` at `29511ed91eb9f3d9773cfdda53e3554b0f4ad08b`, line 144, performs single-token natural ordinary decode. The source transforms preserve that loop. The independent cost reconstruction explicitly rejects teacher forcing and diagnostic observation.
- Prefix grouping source computes physical extents from actual slot head, occupied cache, padding, and contiguous append; it does not use input identifiers, expected tokens, or output positions. CUDA and Vulkan both split a 765–768 consumed-position example into extents `[768,768,768,1024]`, making groups of three and one rows.
- B570 `source.py` still admits a specific native layout domain: head dimension 128, Q heads 32, KV heads 8, q2/3/4, key extents 256/512/768/1024, dense causal nonflash attention. A general-purpose planner does not itself expand the validated backend domain.

## Cost reconstruction

`recompute_costs.py` independently recomputes every ratio in all 144 saved blocks per platform, using all 864 published measured time values per platform. Arithmetic dual-PQ block denominators, equal log weights, all six period means, and A/A thresholds agree to 1e-12. This is a complete arithmetic reanalysis of the committed block reports, not a fresh restoration of all raw request/vector files.

| Geometric mean | RTX | B570 |
|---|---:|---:|
| C_QB / arithmetic-dual C_PQ | 0.9755308329694600 | 0.9505485305997169 |
| M_QB / M_PQ | 1.0043665337928351 | 0.8993003831218389 |
| M_QB / C_QB | 0.9736070498242494 | 0.3342545882301661 |
| C_QB / R | 0.4589845741084981 | 1.6287866913580917 |
| M_QB / R | 0.4468706171126144 | 0.5444294248346735 |
| A/A practical threshold | 2.9831566748046656% | 2.9418325005226675% |
| Practical C-layout screen | does not pass | passes |
| Blocks with slower C_QB | 38/144 | 2/144 |
| Blocks with slower M_QB | 73/144 | 0/144 |

The M_QB/M_PQ contrast is useful existing evidence: ordinary scoped QB is approximately 0.437% slower on RTX and 10.070% faster on B570. This quantity is a post-hoc descriptive reconstruction, not a newly passed prospective screen. There is no phase-specific timing decomposition sufficient to attribute all of it to prefill, even though the ordinary decode loop is single-row and the main layout opportunity is prefill.

## Complete-vector evidence

- RTX qualification report: 48 immutable-reference requests, 240 candidate requests, 23,080 saved complete vectors. Its 120 committed-vector comparisons contain 13,810 committed candidate rows with no hash differences. The 120 comparisons include 24 candidate-R cells. Non-R vector equality is an additional descriptive reconstruction, not a retrospectively invented prospective gate.
- B570 qualification report: 288 total requests, 23,718 saved complete vectors, 14,555 committed candidate rows; all complete reference-vector hashes agree. This count also includes candidate R.
- The comparisons use whole-file SHA256 equality, not only final tokens or top-1. The saved reports and auditor source substantiate these counts; this review did not re-download and decode the full raw vector corpus.

## Policy coverage

`COVERAGE_MATRIX.json` provides a machine-readable matrix. Main distinctions:

1. CUDA Qwen3-14B: PR159 causally repairs normalization-dependent scheduler placement that propagates to RoPE; 12-input confirmation passed before the Llama prefix work. PR162 adds the shared prefix implementation to a combined-policy build and passes a 192-request old-panel regression plus 32 immutable-R requests. Do not rename that regression a new unseen cross-family confirmation of prefix causality.
2. CUDA Qwen3-8B: the combined head-normalization plus prefix policy is enabled and a 144-request regression plus 24 immutable-R requests passes. The inspected summary does not establish how many prefix splits actually fired. This is meaningful combined-policy compatibility coverage, not a new causal repair.
3. CUDA Llama: active prefix repair, ablation, and 24-input confirmation; the compiled head-normalization policy does not trigger because those Q/K normalization nodes are absent.
4. CUDA SmolLM2: prior PR151 layout/scope results exist; the PR159/162 combined numerical rules have not been evaluated on this family in these inspected records.
5. Vulkan Qwen3-8B: the old adapter calls only `hs_b570_set_layout`; `reference_q8` and `prefix_extent` remain false. Its twelve requests establish compatibility of the old path.
6. Vulkan Llama: both new switches are true; controlled factors and separate reversals support the two-factor repair; 24 unseen inputs pass.

## Delivery and editorial detail

B570 `DELIVERY_COMPLETE.json` and `REMOTE_RECONSTRUCTION.json` report a fresh authenticated download, 145,342 logical files / 46,976 objects, and byte-identical reconstruction of three scientific reports from 39,473 restored files. This is same-host remote reconstruction. RTX still has no final remote delivery pass at the inspected head. Its RESULTS opening says confirmation is incomplete, while its later confirmation section records completion; that opening is stale and should be corrected when the result branch is finalized.

## Three next research actions

1. Make the planner and backend policy extraction executable, including graph cache identity. Distinguish the implemented shared prefix planner from a future extractor of arithmetic and dispatch requirements; a table of contracts alone is insufficient. Validate changed graph reuse in the host handoff.
2. Run a focused active-policy transfer on the existing Vulkan Qwen producer–consumer examples. The two strongest fixed-R cases are MATH500 prealgebra 1865 and 1804: P1+C1 and P4T+C1 preserve R, P1+PQ/QB fail, and P4T+PQ/QB already pass. A success must repair the failing P1 path without swapping producer or oracle. Include GSM8K/1184, where P4T changes natural C1 too, to determine whether the method controls the producer as well as the consumer. An enabled rule that never triggers is reported separately.
3. Show useful parallelism/cost under the structural rule at predicted boundaries, using the existing two hosts. A boundary sweep or structurally distinct configuration selected before output is more informative than another random panel or a rerun to beat the RTX noise screen. Record which groups execute and why; then use a short held-out confirmation only for the frozen new candidate.

No further full-panel Llama timing, duplicated archival audit, or larger prompt count is needed to establish the already demonstrated mechanisms. The remaining research question is whether the structural policy predicts and fixes another numerical path while preserving useful computation.

## Files

`SOURCE_MANIFEST.json` lists 39 inspected source files with exact repository commits, paths, Git blob SHAs and URLs. Local source copies normalize CRLF to LF for reading. `RECOMPUTED_COSTS.json` and `COVERAGE_MATRIX.json` can be used directly to generate the revised manuscript tables.
