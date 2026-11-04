> Update, 2026-11-04: The title error identified in this review was corrected in PR #181 at commit 4861bb410a5e9faaa5206c44b9cbc7ad6fbebbb7. The review below retains the original finding for audit history.

# Independent skeptical review: HeteroSpec research position

Review snapshot: 2026-11-04, approximately 11:35 UTC.

## Executive judgment

The present evidence is not yet a convincing IEEE TPDS submission. The direction remains viable, but “MMA wins” is neither necessary nor sufficient. A numerical acceptance probability would be invented.

Scope of this review: PR descriptions for #171/#174/#177 and #178–181; fixed-head roadmap, research, and experiment documents; direct primary papers and repositories. This was a research review, not native GPU replication or a full source-code audit. No repository branch was changed.

## 1. A proposition worth testing

Can we accelerate an already-deployed quantized inference implementation while preserving its existing numerical behavior and committed state, rather than replacing it with a newly chosen deterministic implementation?

A defensible contract fixes the reference executable, model weights, quantization, toolchain, device configuration, and sampler. It specifies the reference’s logical state and numerical realization, not only dtype and tensor shape. It requires equality of requested full logits and live logical KV values at committed boundaries, with correct restoration or rejection when a candidate cannot satisfy the contract.

The evaluation asks whether independent-output scheduling, quantizer reuse, packing, or exact integer leaf replacement improves complete service cost against the strongest implementation satisfying that same contract.

This is narrower than generic deterministic inference. It is not automatically novel: existing-reference emulation and equivalence-constrained optimization already exist.

## 2. Who actually needs an existing trajectory?

Credible users are a subset of inference users:

- Maintainers optimizing an installed runtime without invalidating regression artifacts. Existing logits, continuations, caches, and bug reproductions can be contractual assets. Preserving them separates performance changes from behavioral changes.
- Researchers replaying previously generated runs. A new canonical implementation cannot recreate an old numerical trajectory merely because both are deterministic.
- Deployments retaining state across upgrades or alternative execution paths. Numerical compatibility could avoid discarding expensive prefix state, provided compatible reuse actually occurs and saves more than qualification and isolation cost.
- External replay or auditing systems, where the reference is prescribed by computation already performed rather than selected by the verifier. Bit-Exact AI Inference Verification explicitly studies replaying existing hardware behavior [S4].

The strongest concrete adjacent example is llama_reproducible [S3]: its CPU shadow emulates a particular GPU path. Its README reports that deterministic prefill became sufficiently slow to shelve daily use, including approximately 1,385 to 129 tok/s for its 27B case. These are authors’ measurements, not our replication.

Missing HeteroSpec evidence: a case study measuring the consequence of changing R. Different bits establish incompatibility, but not why someone should pay to avoid it. Show a preserved regression corpus, replay workflow, expensive retained state, or consumer that demonstrably requires the old result.

Avoid “RL needs exactness, therefore RL needs our scalar reference.” RL-Kernel [S5] supports aligning rollout and training arithmetic, but replaces operators on both sides. It does not establish that a historical scalar path is preferable to a new shared canonical path.

Also avoid claiming bitwise reproducibility is inherently more accurate, safer, or legally required. It can faithfully preserve an old implementation’s errors.

## 3. Closest prior art and claim boundaries

### Vosti [S1]

It specifies full-logit determinism and verifies engine/cache invariants plus relational kernel contracts under fixed deployment assumptions. It ties live KV values to causal prefixes. Its discussion explicitly identifies equivalence across distinct kernels as an extension opportunity. HeteroSpec needs a useful cross-implementation compatibility result, not another descriptor or provenance registry. Vosti does not prove cross-hardware/compiler agreement or functional correctness.

### Taming Bitwise Behavior [S2]

The verified full title is “Taming Bitwise Behavior in GPU Kernels with Tensor Core: Black-Box Reconstruction, Compiler Enforcement, and Static Verification.” It already reconstructs existing cuBLAS arithmetic, optimizes within bitwise-equivalence classes, and integrates static checking with tuning. Appendix E uses masked k8-within-k16 groups. Neither preserving an existing reduction descriptor nor masked MMA is novel by itself. A quantized integer/scale transformation still needs a precise comparison with its supported arithmetic and checker.

### LLM-42 [S6]

Its fixed-shape verifier establishes its own numerical trajectory and replaces verified-window KV even when tokens match. Verify/rollback and the insufficiency of token-only comparison are prior art. Preserving an immutable old scalar trajectory is a different target, but its utility must be demonstrated.

### llama_reproducible [S3]

Direct implementation competition includes four-column deterministic loops, portable shadow arithmetic, and DP4A experimentation. Its support is explicitly deployment/model/quantization bounded. PR180 is an essential control, not optional related work.

### RL-Kernel [S5]

Competes on numerical contracts, cross-engine operators, runtime execution provenance, and exact selected-token logprob comparison. Its selected-logprob results must not be equated with full-logit/full-KV equality or identical bits across every supported backend.

State mechanisms have close precedents in Preserving Provenance [S7], Aborted but Not Forgotten [S8], and Execution-State Capsules [S9]. Metadata, restore APIs, and test volume do not independently establish research novelty.

## 4. What current HeteroSpec experiments establish

- PR171: a real, bounded operator improvement. Old/new QB=1.0417x means approximately 4.00% less service time, not a 4.17% reduction. Four natural inputs are covered. The new path mainly benefits prefill and is shared by QB/WB. The 23-to-2 kernel observation is not a general speedup theorem.
- PR174: no registered AUTO benefit; all primary intervals cross 1. This is not an equivalence result.
- PR177: simpler WB-rechunk removes the claimed QB append advantage in the conditioned eight-root study. Complete-service session directions reverse.
- PR179: valuable safety infrastructure and CPU recovery evidence. CUDA qualification and realistic GPU-state costs remain open.
- PR180: the correct adversarial baseline. If loop4 explains the gain, ordinary backend scheduling/quantizer reuse accounts for it.
- PR181: actual compilation and machine-instruction evidence, but no numerical GPU execution or timing. High, architecture-dependent register pressure is a warning, not a predicted performance result.

The scientific story should follow these outcomes rather than require QB, AUTO, or tensor cores to win.

## 5. Full logits and KV: realistic, but bounded

Exactness is realistic on a sufficiently restricted deployment when equal inputs execute matching value-relevant arithmetic and state transitions. It is not established by kernel names, dispatch metadata, finite capture matches, or seeing the intended instruction in SASS.

For the Q8 experiment, integer products and sufficiently short integer sums can be exact without overflow while the original floating-point scaling and reduction graph remain unchanged. Verification must cover:

1. Actual F32-to-Q8 activation bytes, not only prequantized inputs.
2. Original FMA versus unfused rounding, FTZ/subnormals, signed zero, tail handling, scales, and casts.
3. The actual frozen kernel, not only a reconstructed W4 model.
4. Attention, normalization, positional operations, committed state, and continuation.

Define equality over live logical state. Raw allocator padding, unused slots, or process-specific metadata should not accidentally become the scientific contract.

A universal supported-input guarantee needs a sound argument/checker within explicit assumptions or actual reference computation at runtime. Finite testing supplies empirical qualification, not a universal proof. Runtime reference replay may consume the intended savings.

## 6. Competing hypotheses and decisive experiments

### H1: Preserving old R has practical value

Competing explanation: the legacy trajectory is an arbitrary experimental constraint.

Falsification: in an actual workflow, replacing it with a new canonical implementation changes no required artifact and creates no meaningful migration or recomputation cost. Evidence needed: retained baseline artifacts, replay obligations, or state whose compatibility saves real work.

### H2: Packing exposes a valuable parallel opportunity

Competing explanation: all benefit comes from eliminating a weak graph/concat implementation.

Decisive experiment: frozen R, graph tiles, backend-loop4, packed, and optimized wide-DP4A on identical operands and complete service workloads. If loop4 matches or wins, acknowledge that simpler scheduling accounts for the improvement.

### H3: Exact MMA can outperform the best exact scalar-core implementation

Competing explanation: masking, layout conversion, synchronization, and register pressure dominate integer throughput gains.

Decisive experiment: numerical qualification first, followed by matched timing against the best DP4A implementation, including quantization and integration. Losing MMA should remain an informative candidate result rather than trigger outcome-driven tuning of the paper’s objective.

### H4: The contract predicts safety before execution

Competing explanation: the registry only labels previously observed successes.

Decisive experiment: freeze predicates before unseen cases; inject unsupported layouts, wrong residency, stale bindings, failed restores, asynchronous errors, and incompatible cached state. Test rejection and restoration separately. Finite absence of false acceptance is not a universal proof.

### H5: State machinery has positive net value

Competing explanation: checkpointing, conservative isolation, and lost cache hits exceed optimization savings.

Decisive experiment: full lifecycle/memory accounting over cold and warm requests, reuse diversity and failures; compare simple reject/recompute and original qualified paths. Do not time only the successful fast path.

### H6: The method generalizes

Competing explanation: it is one deployment-specific patch.

Decisive experiment: a second model family and architecture with independently pinned references, plus explicit unsupported cases. Per-platform reference preservation is not a claim of common cross-platform numerical output.

Do not select more roots or tune policies merely to reverse existing negative findings.

## 7. Publishable directions even if MMA loses

Most promising: a general quantized compatibility method with a modest but robust DP4A/packing improvement. It should explain which transformations preserve a legacy realization, identify their limits, and predict where they pay. Tensor cores become one evaluated candidate, not the thesis.

Potentially valuable but harder: sound translation validation for quantized kernels spanning integer leaves, scales, floating reduction, and compiler lowering. It needs an advance beyond Taming’s checker, not an independently rebuilt subset.

Possible systems direction: safe switching among independently qualified implementations while maintaining live numerical state, with a real workload and low net overhead. Present checkpoint/provenance components alone are too close to prior art.

If everything loses: a compatibility/performance frontier and negative result can still be useful, but need general explanatory findings. Many passing tests plus a slower optimization are not enough for TPDS.

## 8. Changes that would materially improve submission prospects

1. Demonstrate one external, concrete reason to retain old R.
2. State one main contribution; demote AUTO and generic checkpoint infrastructure.
3. Run the strong frozen-reference comparison instead of another weak-baseline campaign.
4. Establish actual GPU numerical equivalence, including quantizer and state integration.
5. Produce a general rule or analysis with explicit failure cases.
6. Replicate net service benefit across a second meaningful deployment and independently reproduce at least one.
7. Retain negative evidence and report complete costs.
8. Correct titles and distinguish preprints, repositories, authors’ measurements, and independently verified results.

## 9. Venue judgment

TPDS scope includes GPU/thread-level parallelism, so multi-node experiments are not inherently required [S10]. Meaningful parallel-systems insight and evidence are required.

For a narrowed kernel/compiler compatibility contribution, ACM TACO is the best alternate fit, not an easier acceptance guarantee. Its current publication record includes architecture-aware tiling and compiler optimization [S11, S12]. If the result remains a narrow negative deployment study, a focused systems/compiler workshop is more credible than relabeling it as a finished journal contribution.

TOMS becomes a possible fit only if the outcome is general, well-engineered numerical software rather than a collection of deployment-specific LLM patches. Its charter still requires novelty, practical value, and comparison with strong alternatives [S13].

## 10. PR181 title audit

Fixed head: a886576af0ea781187b3e85529919f26a53f9eff.

All 13 changed files were fetched through the GitHub connector and searched for “Taming” and “2609.11356.” Exactly one changed-file match was found:

- File: experiments/masked_q8_mma/README.md
- Actual line: 31
- Wrong link text: “Taming Numerical Variation, Appendix E”
- Exact line: The mapping derives from the separate CPU model in `heterospec-q8-mapping`: exact eight-product leaves, preserved four-warp K stream and ordered floating-point graph. [Taming Numerical Variation, Appendix E](https://arxiv.org/html/2609.11356v1) already describes embedding k8 groups in masked k16 MMA. No algorithmic novelty is claimed.
- Fixed-head permalink: https://github.com/leecdiang/HeteroSpec/blob/a886576af0ea781187b3e85529919f26a53f9eff/experiments/masked_q8_mma/README.md#L31

The PR181 description also uses “Taming Numerical Variation” in its “Prior art / fair controls” section. It is separate from the file correction. No branch or PR was edited.

Correct title: Taming Bitwise Behavior in GPU Kernels with Tensor Core: Black-Box Reconstruction, Compiler Enforcement, and Static Verification.

## Sources

S1. Vosti: Specifying, Implementing, and Verifying Deterministic LLM Inference. https://arxiv.org/html/2609.38981v1

S2. Taming Bitwise Behavior in GPU Kernels with Tensor Core: Black-Box Reconstruction, Compiler Enforcement, and Static Verification. https://arxiv.org/html/2609.11356v1 ; abstract/title https://arxiv.org/abs/2609.11356

S3. amiller/llama_reproducible. https://github.com/amiller/llama_reproducible

S4. Bit-Exact AI Inference Verification Without Performance Tradeoffs. https://arxiv.org/html/2606.00279v2

S5. RL-Align/RL-Kernel. https://github.com/RL-Align/RL-Kernel ; execution provenance discussion https://rl-align.github.io/RL-Kernel/blog/2026-09-18-rl-kernel-amd-vime-qwen3-8b-train-rollout-bitwise-consistency/

S6. LLM-42: Enabling Determinism in LLM Inference with Verified Speculation. https://arxiv.org/html/2601.17768v2

S7. Preserving Provenance in Shared KV Caches for LLM Serving. https://arxiv.org/abs/2609.38706

S8. Aborted but Not Forgotten: KV-Cache Retention Breaks Rollback Consistency in Language Agents. https://arxiv.org/abs/2608.15939

S9. Execution-State Capsules: Graph-Bound Execution-State Checkpoint and Restore for Low-Latency, Small-Batch, On-Device Physical-AI Serving. https://arxiv.org/abs/2606.20537

S10. Official TPDS scope. https://www.computer.org/digital-library/journals/td/cfp-parallel-distributed-systems

S11. A Decoupled Analytical Model for Tile Size Selection in Affine Programs, TACO. https://doi.org/10.1145/3806056

S12. Using Task Graph Caching to Accelerate TVM Code Generation, TACO. https://doi.org/10.1145/3810246

S13. TOMS editorial charter and information for authors. https://www.cs.kent.ac.uk/projects/toms/Charter.html ; https://www.cs.kent.ac.uk/projects/toms/Authors.html

Additional primary background: Defeating Nondeterminism in LLM Inference. https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ ; cuBLAS reproducibility documentation https://docs.nvidia.com/cuda/cublas/index.html#results-reproducibility

## Internal repository evidence

- PR171: https://github.com/leecdiang/HeteroSpec/pull/171 ; results https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/RESULTS.md ; existing review https://github.com/leecdiang/HeteroSpec/pull/171#issuecomment-6605817171
- PR174: https://github.com/leecdiang/HeteroSpec/pull/174 ; results https://github.com/leecdiang/HeteroSpec/blob/aa7ff4e64752be3de0d7974febbce453ae3a96c0/benchmarks/rtx_prefix_reuse_v1/execution/RESULTS.md
- PR177: https://github.com/leecdiang/HeteroSpec/pull/177
- Roadmap: https://github.com/leecdiang/HeteroSpec/blob/4bbd322de1411be9f7998def4042dafabb4df669/docs/research/reference_parallelism_roadmap_20261104/ROADMAP.md
- PR179 research: https://github.com/leecdiang/HeteroSpec/blob/7e02a870d90396fe0d91be98d49161a5ebd8bc3c/docs/research/reference_contract_20261104/RESEARCH.md
- PR180 experiment plan: https://github.com/leecdiang/HeteroSpec/blob/c4ae8ef2f04dfbab4509843303ec8a11f53afbfe/docs/research/backend_loop4/EXPERIMENT_PLAN.json
- PR181 README: https://github.com/leecdiang/HeteroSpec/blob/a886576af0ea781187b3e85529919f26a53f9eff/experiments/masked_q8_mma/README.md
