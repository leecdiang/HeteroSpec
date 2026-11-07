# Windows HumanEval llama.cpp replication

## Verdict

**CLOSED — the matched native CUDA replication is correctness-blocked; exact serialized controls are decisively slower.**

The frozen 30 HumanEval prompts, three paired repetitions, Qwen3-8B Q8_0 target, Qwen3-0.6B Q8_0 draft, greedy decoding, 128-token cap, and fixed `k=2` were retained. The intended batched CUDA run was stopped when both CPU-draft and RTX-draft conditions diverged from their paired baseline on HumanEval/106. Because token equality was the hard gate, those timings are invalid for performance claims.

Setting `ubatch=1` restored exactness and was run as a clearly labelled diagnostic control: all 270 generations completed and both speculative conditions matched their paired baseline in 90/90 cases.

| Exact diagnostic | Geomean speedup | 95% prompt-bootstrap CI | Median | Faster prompts | Acceptance | Accepted/round | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|---:|
| CPU 0.6B → RTX 8B | 0.404× | [0.390, 0.418] | 0.399× | 0/30 | 91.31% | 1.821 | 8688.1 MB |
| RTX 0.6B → RTX 8B | 0.650× | [0.629, 0.673] | 0.637× | 0/30 | 91.21% | 1.819 | 9746.1 MB |

The unit of analysis is the prompt. Each prompt value is the geometric mean of its three paired speedups; the reported aggregate is their geometric mean. Confidence intervals use 10,000 prompt bootstrap resamples with seed 20260910.

## What failed, and what it means

The two speculative placements produced the same divergent output at the same point on the failing prompt. Changing Flash Attention, forcing cuBLAS, and forcing MMQ did not recover equality; reducing the verification micro-batch to one did. This isolates the hard failure to the CUDA target's batched verification/numerical path rather than CPU↔GPU transfer, draft placement, or tokenization.

This is consistent with upstream llama.cpp reports that quantized CUDA computations can be batch-dependent, violating the lossless equivalence required by speculative decoding. The result is therefore not evidence that an incorrect faster CUDA path is useful; it is a backend correctness boundary.

Relevant upstream records include llama.cpp's [speculative decoding contract](https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md), the open [SM120 CUDA batch-invariance issue](https://github.com/ggml-org/llama.cpp/issues/28111), an earlier [quantized-target speculative divergence report](https://github.com/ggml-org/llama.cpp/issues/25618), and broader [CUDA batch-dependent output](https://github.com/ggml-org/llama.cpp/issues/3014) and [Q8_0 repeatability](https://github.com/ggml-org/llama.cpp/issues/7228) reports. These reports support plausibility; the local ablations are the direct evidence for this machine/build.

## Mechanism results

- High acceptance was not sufficient. Acceptance exceeded 91% in both exact controls, slightly above the reported M4 aggregate, while speed remained far below 1×.
- Cross-device overhead was not the sole cause. Moving the draft onto the RTX improved 0.404× to 0.650×, but still accelerated none of the 30 prompts.
- Serialization exposes the verification cost. `ubatch=1` is a diagnostic correctness control, not a practical optimized configuration; it removes the batching benefit that speculation needs.
- The default Windows CUDA path cannot be compared fairly on speed because it fails the preregistered exactness gate.

Acceptance-versus-speed correlations were moderate, not determinative: Pearson/Spearman were 0.471/0.387 for CPU→RTX and 0.409/0.461 for RTX→RTX. Accepted-tokens/round correlations were similar.

## Energy and telemetry limitation

NVML verified stable residency and peak VRAM, but the 1 Hz trace covers the entire short-lived process, including model loading. CPU package energy and decode-window boundaries were not captured. Reporting those process-window values as J/output-token would be misleading, so no formal energy ratio is claimed. This is a declared missing measurement, not a favorable imputation.

## Artifacts

- Pair-level table: `HUMANEVAL_LLAMA_REPLICATION.csv`
- Machine-readable summary: `windows_humaneval_summary.json`
- Raw exact control: `logs/windows-humaneval-replication-30q-ub1.json` (local/ignored)
- Aborted primary attempt: `logs/windows-humaneval-replication-30q.json` (local/ignored)
- Reproduction manifest: `benchmarks/windows_humaneval_replication_30q/manifest.json`

**Stop criterion reached. No prompt was excluded, no 420-task expansion was run, and the old custom harness was not used to rescue the result.**
