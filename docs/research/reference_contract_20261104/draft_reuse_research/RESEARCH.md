# QB draft startup and reuse: prior art, scope controls, and a falsifiable next step

Research checked 2026-11-04. Read-only web/source inspection and CPU-only recomputation; no device execution. This is a research assessment, not a new measured acceleration or a claim of exhaustive novelty search.

## Decision

The QB-specific historical finding supports a different bottleneck question: can the draft become useful soon enough? It does not support presenting prefix caching, paired target/draft caches, lazy catch-up, draft KV compression, or generic overlap as new ideas. All have close prior art, including work released in October and November 2026.

The narrowest potentially interesting implementation direction under a strict frozen-draft numerical contract is **cold prefill that processes known prompt tokens together while preserving each UB1 row's arithmetic and cache state**. This would attack first-use cost instead of depending on an unobserved cache-hit distribution. It is an unproven hypothesis, not established novelty. If only target output/distribution must remain exact, ordinary larger-ubatch draft prefill is a mandatory and potentially decisive simpler baseline.

## What the project evidence actually establishes

The pinned [PR151 worker](https://github.com/leecdiang/HeteroSpec/blob/29511ed91eb9f3d9773cfdda53e3554b0f4ad08b/scripts/experiments/rtx_scope_transfer_v1/worker.cpp) clears both caches on each request, prefills target and then draft sequentially, and synchronizes each phase before recording host wall time. Draft ubatch is 1, scoped target ubatch is 4, context 1024, both KV types F16, flash attention disabled, fixed greedy k=3. Models remain resident within the family session. Cache-hit claims cannot be inferred from these cold requests.

The local historical report independently reconstructs 96 input/session blocks, 672 formal arm records across two days. Within **QB only**, all 56 draft-losing blocks have a positive non-prefill accounting residual. This does not generalize across scopes: GS has 86 losing blocks and all 86 have negative residuals; PQ has 56 losing blocks, of which one has a negative residual. This includes host logic and synchronization, not isolated GPU decode benefit. Four Smol QB sessions require removing 66.7–73.2% of total draft prefill before any new overhead, equivalent to about 3.0–3.7x faster prefill if every other component is unchanged. Individual losing blocks require as much as 97.39% removal. Prompt reuse alone has no observed hit-rate evidence here.

A new CPU-only sensitivity calculation, with the headline restricted to QB, asks how much sequential startup could disappear if target and draft prefill overlapped perfectly without contention or overhead. It subtracts min(target_prefill, draft_prefill) from each measured speculative service cost. All 56 QB losses would disappear under this zero-overhead counterfactual ceiling. The same calculation leaves 83 GS losses and one PQ loss. Negative residual and failure after deleting only draft prefill are distinct tests: all 86 GS losers have negative residuals, but 83 remain losses after deleting draft prefill while preserving observed target-prefill differences. Across all Qwen QB blocks, sum(C)/sum(M) changes from 0.8922 to 0.7155; Smol QB changes from 1.2808 to 0.8793. This is a useful ceiling, not a predicted speedup. Same-GPU contention can erase it completely.

Reproducible publication: `reproduce.py`, `source_projection.json`, `SOURCE_MANIFEST.json`, and `RESULTS.json` beside this report. The 186 KB projection preserves raw selected values for all 288 GS/PQ/QB pairs plus archive/member SHA256 provenance. Default reproduction needs no download; optional `--archives` verifies both original ZIP hashes, all 672 formal records, within-block endpoints, and byte-for-byte reconstruction of the projection. It creates no GPU work.

The fixed-M sensitivity formula only removes draft startup from C. It is **not** a complete prefix-cache intervention: a fair deployed comparison must also give target-only M the same legal target-prefix reuse. The published source counts repeat the same twelve previously exposed inputs across four sessions per family and are not 96 independent workloads.

## Closest prior art and implementation status

### Persistent dual caches and exact boundary handling are already implemented

[Efficient Speculative Decoding for Llama at Scale (Meta, August 2025), §3.4](https://arxiv.org/html/2508.08192v1) explicitly keeps persistent base and draft KV caches, reuses matching prefixes, coordinates hits and evictions, and handles EAGLE's first-token feature/token alignment. It also addresses CPU/GPU synchronization. This is a direct novelty collision for “cache both models and synchronize their lifecycle.” Its EAGLE dependence on target hidden features differs from HeteroSpec's independent full draft model.

[vLLM PR61589](https://github.com/vllm-project/vllm/pull/61589), merged October 26, 2026, adds lookahead block hashes for EAGLE/EAGLE3/MTP prefix caching. A boundary draft KV value can depend on the successor token, so the cache key includes finalized lookahead; local hits are limited accordingly. The merged change concerns local cache reuse, with KV-connector compatibility handled separately. This preserves the inputs needed for cold-equivalent draft state; it is not a proof of arbitrary-kernel bitwise numerical parity. [vLLM's general APC design](https://docs.vllm.ai/en/latest/design/prefix_caching/) already chains block hashes and includes metadata such as model adapters and cache salts.

Current [llama.cpp server-task.cpp](https://raw.githubusercontent.com/ggml-org/llama.cpp/master/tools/server/server-task.cpp) stores target and draft sequence-state blobs together in its RAM prompt-cache path and restores each into its own context. That is a strong implementation baseline. Do not infer that every on-disk slot/checkpoint path has identical support or lifecycle semantics.

[exo PR2576](https://github.com/exo-explore/exo/pull/2576), opened November 3, 2026 and still open when checked, implements a separate valid draft frontier after target-only turns, draft catch-up on partial/exact hits, deep-copy/trim isolation and draft-byte accounting in eviction. The author reports acceptance checks for incorrect draft state and also reports target near-tie differences from chunked verification. This is unusually close to an “independent draft frontier” design, but is an unmerged implementation report on Apple Silicon, not evidence of performance or fixed-reference exactness on this project.

### Lazy catch-up and removal of draft history are known

[WhiFlash, June 2026, §3.4 and Table 5](https://arxiv.org/html/2606.07710v1) catches up an inactive EAGLE drafter only when switching back. Its KV-only prefill skips MLP/head work because the AR drafter is a single transformer layer fed by target features. That trick does not transfer wholesale to full Qwen3/SmolLM2 drafters: deeper-layer K/V require the preceding layers' MLP outputs. At most, work after the last required K/V can be removed, and graph pruning may already do so. Published Qwen3-8B memory figures are 15.26 GB without SD and 18.41 GB for WhiFlash; these are not demonstrated 12 GB/10 GB deployments. Reported principal performance metrics exclude prefill.

[DLite, October 16, 2026](https://arxiv.org/html/2610.23787v1) removes historical draft KV altogether by conditioning a trained local drafter on target hidden states. Its [official implementation](https://github.com/SJTU-DAI-Sys/DLite) has Qwen3 checkpoints, including 8B, but not SmolLM2. This directly anticipates “history-free draft startup.” It changes the drafter architecture/training, requires extracting target features, and is not a drop-in preservation of the historical full-draft execution. The repository explicitly notes its throughput benchmark does not compare the generated tokens against target-only outputs. The paper's agentic tests also include independent long prompts rather than demonstrating natural paired-cache hit rates across turns. A Q8 deployment within this project's memory limit still needs qualification.

[RIFT, October 22, 2026](https://arxiv.org/html/2610.31098v1) compresses and refreshes draft KV to reduce long-generation cost. Exact target-distribution sampling does not imply identical draft logits/KV. Compression after computing prefill does not by itself remove cold prefill work. Its rescoring overhead study includes projected latency from measured components rather than an entirely integrated end-to-end measurement. It is relevant negative evidence against treating a smaller draft cache as automatic startup elimination.

[MemSpec, LCTES 2026](https://arxiv.org/abs/2608.10362) already predicts draft usefulness and manages a resident working set of draft models under edge-memory constraints. Its main concern is avoiding reactive model-loading overhead. It further narrows novelty for generic memory-aware draft selection, although this is not identical to per-prefix KV admission.

### Overlap is not a new mechanism, and published hardware matters

[Saguaro/Speculative Speculative Decoding, ICLR 2026](https://arxiv.org/html/2603.03251v3) speculates on likely verification outcomes while verification runs, then looks up the matching prepared continuation or falls back. It proves distributional exactness. The main configuration uses four H100s for the target plus another H100 for the draft; throughput excludes prefill, and radix caching is disabled. Its [implementation](https://github.com/tanishqkumar/ssd) is useful for branch/rollback design, not evidence that same-device startup becomes free.

[PEARL](https://arxiv.org/abs/2408.11850) and its [nano-PEARL implementation](https://github.com/smart-lty/nano-PEARL) overlap draft/verify execution on distinct device groups. ParallelVLM's [CVPR2026 paper](https://openaccess.thecvf.com/content/CVPR2026/papers/Kong_ParallelVLM_Lossless_Video-LLM_Acceleration_with_Visual_Alignment_Aware_Parallel_Speculative_CVPR_2026_paper.pdf) explicitly overlaps target/draft prefill, using a pruned visual draft input. Neither makes overlap novel or establishes same-GPU reference-exact performance for the present independent text models.

### Baselines that eliminate neural-draft prefill entirely

[SuffixDecoding](https://suffix-decoding.github.io/) with [Snowflake ArcticInference](https://github.com/snowflakedb/ArcticInference) uses suffix trees over prompts and prior outputs, then target verification. This is a practical low-memory comparator for repeated code/edit/agent loops, with poor coverage on genuinely new continuations. A proposal should beat this where repetition is its claimed advantage, not only beat a cold neural draft.

[LayerSkip](https://arxiv.org/html/2404.16710v4) shares computation/KV between trained early-exit drafting and verification. It does not allow copying arbitrary Qwen target KV into the separately trained Qwen0.6B draft. [SpecPrefill](https://arxiv.org/html/2502.02789v1) sparsifies the target prompt computation and is not a strict frozen-target-reference substitute.

## Actual model and memory feasibility

The original PROCESS.json records specify Qwen3-8B-Q8_0 plus Qwen3-0.6B-Q8_0, and SmolLM2-1.7B-Instruct-Q8_0 plus SmolLM2-135M-Instruct-Q8_0. Model-file byte totals are not resident VRAM measurements.

Using official configurations and the worker's F16 K/V, nominal per-token cache bytes are 2 × layers × KV heads × head dimension × 2 bytes:

- [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json): 144 KiB/token; [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B/blob/main/config.json): 112 KiB/token. One target/draft pair is 256 MiB at 1K context or 2 GiB at 8K, before scratch, alignment and speculative slots.
- [SmolLM2-1.7B](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct/blob/main/config.json): 192 KiB/token; [SmolLM2-135M](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct/blob/main/config.json): 22.5 KiB/token. A pair is 214.5 MiB at 1K, about 1.676 GiB at 8K.

The Qwen draft is small in weights but its KV costs about 78% of target KV per token. The small Smol target uses full multi-head KV and is more expensive per cached token than the Qwen8B target. Parameter count is therefore a poor cache-capacity proxy.

Historical provisioning reports 1,927,282,688 bytes free for Qwen (1.795 GiB), versus 8,728,346,624 bytes for Smol (8.129 GiB), after creating four target and three draft context pools on the RTX 5070 Ti Laptop, at n_ctx=1024. These are historical measurements with those pools, not current free memory or a capacity guarantee for a redesigned server. The 48 GB host RAM can hold spill snapshots, but restore/transfer/synchronization cost must be charged. The B570 10 GB is a separate environment, not an additional assumed 10 GB on the same host or a verified Qwen pair placement.

## One falsifiable non-cache candidate

**Hypothesis:** Independent known prompt tokens can be processed layer-major with several rows in flight, retaining the UB1 per-row operation/reduction graph, while reusing weights and reducing launch overhead. The row's quantization, accumulation order, causal visible-key extent, padding/position treatment and K/V encoding must stay fixed. This is not permission to substitute ordinary GEMM, FlashAttention, or a wider reduction tree.

A practical prototype would use a bounded row tile, produce each layer's K/V for the prompt tile, and execute each causal attention row with its original extent. Parallelize independent work across rows, not reductions within a row. Avoid materializing full T×T attention; cap temporary activation/storage by tile. Only then attempt weight-tile reuse. This is an architectural feasibility argument, not a proven faster kernel. Thread/stream concurrency also requires auditing instrumentation and global layout settings; the historical serial worker is not a ready-made concurrent harness.

**Why it could matter:** Unlike caching, the same optimization applies on the first novel prompt and eviction misses. Unlike learned hidden-state drafters, it retains the existing full draft and could satisfy a stronger contract.

**Why it may fail:** Exact row arithmetic might prevent enough fusion/reuse; register/shared-memory pressure may reduce occupancy; launch overhead may already be removed by graphs; attention work still grows with context; the last-layer graph may already avoid unnecessary projections; the attainable reduction may fall far short of Smol's 67–73% session threshold. If ordinary wide-ubatch drafting is permitted and faster, the stronger fixed-draft guarantee may have insufficient practical value.

## Reproduce the bounded accounting

Run `python reproduce.py --output /tmp/draft-reuse-results.json` from this directory. With the two release ZIPs downloaded from the URL and checked against hashes in `SOURCE_MANIFEST.json`, run `python reproduce.py --archives /path/to/archives --output /tmp/draft-reuse-from-raw.json`. The two outputs must match `RESULTS.json` exactly. The script rejects overwriting any existing published evidence file. No inference, package installation, GPU, or device access is involved.

## Minimum experiment and rejection criteria

1. State the required guarantee separately: target distribution, greedy output equality, or full reference logits/KV/proposals and rollback. Papers proving the first do not prove the last. A cache can reproduce the mathematical state while changed chunk geometry changes floating-point results.
2. Compare equal resources: strongest same-scope target-only; frozen UB1 draft; ordinary larger-ubatch draft as a practical outside-frozen-draft baseline; graph-replayed baseline; plain paired-prefix caching; the candidate. If the use case is repeated code, include suffix/ngram drafting. Cross-engine comparisons need a distinct end-to-end track because changing engine/precision is not the same numerical contract.
3. Validate prompt-boundary K/V and continuation state, not only accepted tokens: every append, reject, correction/bonus, rollback, early stop, reset, eviction, partial hit and interleaved session. Test identical-length wrong prefixes and earlier-prefix edits. For coupled hidden-state drafters, include successor-token lookahead and pending boundaries.
4. Use new inputs crossed by domain, input length, and output budget. Separate truly cold, controlled repeated-prefix, partial-prefix, natural multi-turn and pressure/eviction traces. Give target-only the same legal prefix reuse. Do not advertise controlled perfect hits as a measured natural workload.
5. Count complete service including capture/warmup allocation in its proper deployment window, cache lookup/state checks, restoration, catch-up, synchronization, miss/fallback and memory pressure. Report total user waiting time, per-input ratios, TTFT and tails, not only decode tok/s.
6. Freeze admission using pre-request features and prior calibration. Never admit based on that request's future acceptance, completed output length, or hindsight cost. For adaptive catch-up, include the wasted speculative work and remaining-output uncertainty.
7. Stop the claim if numerical qualification fails, if overhead-adjusted achievable savings cannot cross the measured threshold, or if the candidate loses to the strongest practical target-only/cached/wide-draft baseline. The historical upper bound is a screening tool, not permission to omit these failures.

Negative cases are central: cold unique prompts; edits near the prefix beginning; short answers; a hot target with cold draft; low acceptance despite a warm prefix; memory-induced evictions; CPU/GPU contention; remote copy cost; cancellation before amortization; and long-context settings not represented by the historical 1024-token context. A useful result may be a precise boundary where draft startup cannot be repaid, rather than an always-on optimization.
