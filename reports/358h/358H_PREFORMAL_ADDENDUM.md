# 358H pre-formal protocol addendum v1

This addendum was frozen before any formal latency, CPU-energy, target-baseline, or verification-timing observation existed. It cites the immutable original freeze `6cdb84fe7962c1871136fc316fd6d12e40b99271` and the preserved fail-closed preflight `314ba642be75dce5986044d1a827d1fcd9a5108b`. At creation: formal latency = 0, formal energy = 0, formal T_b = 0, formal V_2 = 0, and there had been no result-dependent parameter selection.

It fills only execution definitions that the original preregistration explicitly deferred. It does not change the frozen models, contexts (512/2048/8192), proposal width k=2, Phase-1 prompt semantics, output cap, thresholds, bootstrap, or GO/BORDERLINE/NO-GO rules.

## CPU Track E

Track E reuses the Phase-1 CPU workload exactly: context order 8192, 2048, 512; five repetitions; fixed token-ID inputs; greedy 128-token output; seed 123; ignore EOS; no chat template; CPU affinity 0-11. The direct PDH collector remains isolated on CPUs 12-15, samples `RAPL_Package0_PKG` at 1000 ms, timestamps each collection at its QPC midpoint, and uses linear boundary interpolation plus trapezoidal integration.

To prevent a short single generation from yielding too few interior 1000-ms samples, each predeclared energy window contains the minimum conservative structure of three back-to-back, otherwise identical 128-token generations. Output length was not increased. The integrated package energy is divided by 384 generated tokens. Duration is retained solely as an integration boundary and cannot replace Track-L latency. NPU energy remains `NOT_ADMISSIBLE`.

## Same-platform target controls

The frozen runtime is official llama.cpp b10839 (`0cae43063cf15170e91a2ff4d034da0ecef4a1b2`) with Vulkan on the physical Intel Arc B390 GPU. The qualification-only probe requested `Vulkan0`, reported `devices=Vulkan0`, offloaded 37/37 model layers, and placed every KV-cache layer on Vulkan0. AUTO, MULTI, HETERO, and silent CPU fallback are forbidden.

T_b follows the repository's existing target-only PP1 definition: after a matching prefix depth, one synchronized target `llama_decode` step is measured by llama-bench. Contexts are 512, 2048, 8192; five formal samples per context; warm-up is 3-5 attempts with the unchanged 5% stability rule. Model loading, allocation, prefix construction, and warm-up are outside the timing boundary.

V_2 reuses the existing M4/CUDA/B570 verification microbenchmark construction on the same target model/backend. It is the synchronized PP2/PP1 ratio at each matching prefix depth, with 20 repetitions, `ubatch=1`, flash attention off, explicit Vulkan0, and the same 3-5 warm-up stability rule. The previously observed fast batched path is forbidden because it was not token-exact.

Before V_2 timing is admissible, the immutable six-task HumanEval control runs three paired repetitions per task (18 pairs total), seed 123, k=2, cap 128. All generated token-ID sequences from target-only and `draft-simple` must match exactly. Both target and the byte-frozen canonical draft GGUF are explicitly assigned to Vulkan0. Any divergence makes verification inadmissible and triggers the original NO-GO rule.

The authoritative machine-readable protocol is `benchmarks/358h_threshold_validation/protocol_addendum_v1.json`; execution-critical files and hashes are recorded in `runs/358h/preformal_addendum_manifest.json`.

