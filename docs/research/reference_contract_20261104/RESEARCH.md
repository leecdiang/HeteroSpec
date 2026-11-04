# Research update informing the PR178 implementation

Search date: 2026-11-04. This is an implementation-oriented update to PR178's
broader map, not a claim of exhaustive coverage, independent experimental
replication or established novelty. Several close works below are recent
preprints; publication status and versions should be rechecked before submission.

## Closest overlaps that change the roadmap

| Primary source | Existing contribution that must be acknowledged | Consequence for this implementation |
|---|---|---|
| [Taming Bitwise Behavior in GPU Kernels with Tensor Core](https://arxiv.org/abs/2609.11356) | Reduction-order descriptors, reconstruction of cuBLAS behavior, PTX/GCN checks and tuning within bit-equivalence classes | Neither a reduction descriptor nor an equivalence-constrained optimizer is new by itself. Preserve the distinction between checked intermediate ISA and final SASS. Our registry does not implement their static checker. |
| [Vosti](https://arxiv.org/abs/2609.38981) | Relational kernel contracts, state invariants and batching/chunking/prefix constraints | Contract metadata and relational verification are direct prior art. A possible difference is a useful transformation relative to an existing deployed quantized scalar path, but native evidence is needed. |
| [Preserving Provenance](https://arxiv.org/abs/2609.38706) | Shared-KV descriptors, compatibility registries and lookup/store binding | Adding recipe/provenance metadata is not a new contribution. This candidate deliberately uses conservative exact-recipe isolation rather than claiming general cross-recipe compatibility. |
| [Aborted but Not Forgotten](https://arxiv.org/abs/2608.15939) | Stale KV following aborted execution and recovery concerns | Abort is not rollback. State must remain tainted until restoration and full readback succeed; the current mock protocol is not a native recovery result. |
| [Execution-State Capsules](https://arxiv.org/abs/2606.20537) | Capturing complete execution-buffer closure for replay | A KV-only snapshot is insufficient. Include independently held logits, positions and pending tokens. Token-level replay evidence must not be relabeled full-logit/state preservation. |
| [Bit-Exact AI Inference Verification](https://arxiv.org/abs/2606.00279) | Replaying existing hardware behavior through explicit execution information | Existing reference-relative replay is prior art. Logging a kernel name alone does not reproduce the arithmetic. |

The opportunity is therefore narrower than “introduce numerical contracts” or
“add KV provenance.” A defensible research question is whether an existing
quantized deployment admits useful independent-group transformations under
explicit reference-relative conditions, and whether their stateful lifecycle
can be managed with practical net cost. This PR implements protocol components;
it does not yet answer that performance question.

## Packing and scheduling background

- [NVIDIA strided batched matrix multiplication](https://developer.nvidia.com/blog/cublas-strided-batched-matrix-multiply/) already describes batches of independent GEMMs and shared operands. Independent-group batching itself is not novel. API legality and strides must be checked against the deployed CUDA version; old examples are not a universal contract.
- [CUTLASS grouped scheduler](https://docs.nvidia.com/cutlass/media/docs/cpp/grouped_scheduler.html) provides established grouped scheduling machinery. Changing scheduling or warp mapping can change arithmetic, so a fast grouped kernel cannot be admitted solely because its mathematical operation matches.
- [cuBLAS reproducibility documentation](https://docs.nvidia.com/cuda/cublas/index.html#results-reproducibility) binds guarantees to particular library/hardware/configuration conditions. Build/runtime/device identity belongs in the qualification scope, not a hardware-independent theorem.
- [ReproBLAS](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2016/EECS-2016-121.html) and [ExBLAS](https://github.com/riakymch/exblas) offer reproducible accumulation strategies, but a more reproducible or more accurate answer need not equal the existing deployed reference.

PR171 remains the implementation anchor: independent groups preserve its observed
four-column dispatch while avoiding repeated graph concat/launch work. It does
not permit arbitrary width, precision or device. Its q32 V-projection counterexample
shows why fewer kernels alone is not a sufficient performance metric.

## State and service background

- [LLM-42](https://arxiv.org/abs/2601.17768) uses fixed-shape verification and state repair. Verify/rollback is not unique to HeteroSpec; fixed verifier trajectory and preserving an arbitrary old scalar trajectory are different contracts.
- [Thinking Machines batch invariance](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) and [vLLM batch invariance](https://docs.vllm.ai/en/stable/features/batch_invariance/) demonstrate fixed numerical-path serving. Do not claim first deterministic inference on Intel or NVIDIA.
- [SGLang](https://arxiv.org/abs/2312.07104), [PagedAttention](https://arxiv.org/abs/2309.06180) and [BatchLLM](https://arxiv.org/abs/2412.03594) establish strong reuse and batching baselines. Exact recipe isolation may lose hits or increase fragmentation; that cost must be measured rather than hidden.
- [Hydragen](https://arxiv.org/abs/2402.05099) and [RelayAttention](https://aclanthology.org/2024.acl-long.270/) share attention work across prefixes, but mathematical exactness does not by itself preserve the deployed reduction sequence.
- [FlashInfer Autotuner v2](https://flashinfer.ai/2026/09/22/autotuner-v2.html) motivates independent selection/evaluation measurements and deployment-consistent timing. [Stream-K](https://arxiv.org/abs/2301.03598) motivates a strong robust fixed implementation before adding adaptive selection.

## Implementation decisions resulting from the survey

1. Separate deployment identity, numerical realization, state provenance and
   evidence scope. None can be reconstructed from only dtype and shape.
2. Make evidence explicit and finite empirical mode opt-in. Do not label matching
   metadata or a hash as a proof, and do not ship synthetic test receipts as a
   hardware qualification database.
3. Default to exact recipe isolation. An eventual cross-recipe relation needs
   independent bounded evidence or a sound proof within stated assumptions.
4. Reject before optimization when possible. A graph-layer failure may follow
   slot allocation; it requires abort/full restoration, not an in-place switch.
5. Keep old tiled lowering, original scalar fallback, and checkpoint replay as
   three distinct actions. They have different semantics and costs.
6. Keep all negative service results from PR174/175/177. Future comparison must
   include equally optimized WB-rechunk and the complete state/checkpoint cost.

## Submission implications

This update reduces two novelty risks in PR178: reduction-equivalence tuning and
shared-KV provenance are already close active topics. A larger implementation does
not itself solve that problem. TPDS relevance would require a meaningful parallel
method, demonstrated reference preservation in a bounded but useful domain,
comparison with these near neighbors, strong fixed baselines, and complete service
costs. The current CPU protocol tests improve auditability and failure handling;
they add no new GPU speedup or measured acceptance probability.

The next native study should be selected only after host extraction and complete
state adapters are implemented. It must distinguish:
- successful protocol execution from numerical equivalence;
- registered finite captures from unseen-input qualification;
- operator latency from full service latency;
- source portability from backend numerical portability;
- mock restoration from actual KV/logit/position restoration.
