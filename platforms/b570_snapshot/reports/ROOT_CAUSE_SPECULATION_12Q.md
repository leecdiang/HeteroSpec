# Speculative Decoding Root-Cause Diagnostic (12 Questions)

## Decision

The 420-question holdout was not opened. A 12-question diagnostic control set was drawn from the completed pilot: two questions from each of the six official task groups. Within each group, the two shortest completed B0 inputs were selected using input length only, before observing RTX-assisted results. The output cap was 64 tokens and `k=1` was frozen because it was the best pilot configuration.

The result separates three effects:

1. The current CPU/OpenVINO heterogeneous implementation is materially slower than RTX-only decoding.
2. Moving the draft to the RTX without changing the custom harness makes performance worse, not better; cross-device transfer alone is therefore not the dominant explanation.
3. Transformers native assisted generation recovers almost all overhead through integrated assistant KV-cache and scheduling, but produces only a marginal and inconsistent net gain on this 8B target.

## End-to-end results

| Configuration | Implementation | Geometric mean speedup | Faster questions | Exact output |
|---|---|---:|---:|---:|
| A: RTX 8B baseline | Cached/custom or Transformers native paired baseline | 1.000x | - | reference |
| B: CPU 0.6B -> RTX 8B | OpenVINO draft + custom verifier | 0.733x | 1/12 | 12/12 |
| C1: RTX 0.6B -> RTX 8B | Same custom verifier and full-prefix draft proposal | 0.611x | 0/12 | 12/12 |
| C2: RTX 0.6B -> RTX 8B | Transformers native assisted generation | 1.015x | 5/12 | 12/12 |

For C2, the ratio of aggregate baseline time to aggregate assisted time was 1.031x, while the median per-question speedup was 0.973x. The sign of the small result is therefore workload-dependent and is not evidence of a robust production speedup.

## Custom-harness time decomposition

| Draft placement | Baseline total | Spec total | Draft time | Target verify/correct time | Residual bookkeeping | Rounds | Acceptance |
|---|---:|---:|---:|---:|---:|---:|---:|
| CPU/OpenVINO | 59.31 s | 85.22 s | 17.45 s | 61.82 s | 5.95 s | 474 | 66.7% |
| RTX/PyTorch | 57.75 s | 100.92 s | 23.66 s | 71.07 s | 6.19 s | 470 | 68.3% |

Mean per-round draft/target times were 36.8/130.4 ms for CPU/OpenVINO and 50.3/151.2 ms for RTX/PyTorch. The RTX draft contends with the target for the same GPU and is slower in this latency-oriented, batch-1 path. The custom OpenVINO path also resubmits the complete prefix on every proposal round rather than preserving draft KV state across rounds. The residual column includes Python control flow, token/list conversion, cache operations, and synchronization; this experiment does not claim a separately measured CPU-to-CUDA transfer time.

## Root-cause interpretation

The evidence does not support the simple claim that cross-device copy overhead alone destroys speculative decoding. The stronger interpretation is:

- The custom heterogeneous path loses time to repeated draft prefill, cross-runtime orchestration, verification/correction, and Python/KV bookkeeping.
- Co-locating both models on the RTX does not help under the same inefficient orchestration because it adds GPU contention.
- A mature integrated implementation removes most of those implementation losses.
- After those losses are removed, the remaining algorithmic benefit for a fast NF4 Qwen3-8B target on an RTX 5070 Ti Laptop is approximately break-even at `k=1`, not a stable acceleration.

Thus both hypotheses contribute, but at different layers: the present heterogeneous harness accounts for a large additional slowdown, while the 8B target leaves too little fundamental latency headroom for native draft-model speculation to deliver a convincing gain.

## Safety

No crash occurred. Peak NVML use was 10,558.1 MB for native RTX-assisted generation and 11,908.1 MB for the same-harness RTX draft. The latter remains uncomfortably close to the known near-capacity failure region, so no larger RTX-draft run is authorized from this diagnostic.

## Next scientific question

The most informative next experiment is a bounded target-size crossover study, not the 420-question holdout. It should first estimate target token latency and VRAM at one or two larger quantized targets, then proceed only if the model fits with a conservative memory margin. The current 12 GB GPU and repeated near-capacity hypervisor failures make blind 14B/20B loading inappropriate.

## Evidence

- `logs\phase5-cpu-rtx-root-cause-12q-20260906.json`
- `logs\phase5-rtx-rtx-same-harness-12q-20260906.json`
- `logs\phase5-rtx-assisted-root-cause-12q-20260906.json`
- `logs\phase5-rtx-assisted-canary-20260906.json`

