# Draft Micro-Latency Qualification

## Result

**PASS. CPU selected as the primary synchronous draft device.**

The test approximates the small candidate bursts used by speculative decoding. It does not measure target verification, acceptance rate, end-to-end speedup, or energy.

## Frozen configuration

- Model: Qwen3-0.6B symmetric INT4 OpenVINO artifact
- Input: identical 64-token tokenized context
- Candidate burst sizes: `k = 1, 2, 4, 8`
- Per cell: 5 warm-ups and 30 measured calls
- Device binding: explicit `CPU`, `GPU.0`, or `NPU`; no `AUTO`/`MULTI`
- Generation: greedy, EOS ignored
- NPU compiler: `PREFER_PLUGIN`, static maximum prompt length 64

## Results

| Device | k | Runs | Mean ms | P50 ms | P95 ms | CV | Unique hashes |
|---|---:|---:|---:|---:|---:|---:|---:|
| CPU | 1 | 30 | 10.78 | 10.57 | 11.85 | 5.03% | 1 |
| CPU | 2 | 30 | 21.15 | 21.01 | 22.61 | 3.55% | 1 |
| CPU | 4 | 30 | 42.76 | 42.50 | 44.44 | 2.10% | 1 |
| CPU | 8 | 30 | 84.82 | 84.44 | 86.80 | 1.60% | 1 |
| GPU.0 | 1 | 30 | 14.87 | 14.31 | 16.55 | 6.39% | 1 |
| GPU.0 | 2 | 30 | 30.29 | 30.21 | 33.13 | 5.98% | 1 |
| GPU.0 | 4 | 30 | 59.34 | 58.76 | 61.24 | 2.11% | 1 |
| GPU.0 | 8 | 30 | 121.51 | 119.54 | 152.08 | 7.82% | 1 |
| NPU | 1 | 30 | 140.33 | 140.37 | 141.52 | 0.45% | 1 |
| NPU | 2 | 30 | 168.98 | 168.76 | 170.54 | 0.45% | 1 |
| NPU | 4 | 30 | 224.54 | 224.26 | 228.95 | 1.03% | 1 |
| NPU | 8 | 30 | 330.69 | 330.11 | 332.79 | 0.43% | 1 |

## Correctness checks

- Successful measured calls: 360/360
- Exact requested token count: PASS
- Within-cell repeatability: PASS; one token hash per cell
- Cross-device equality: PASS; CPU, GPU.0, and NPU produced the same token sequence for each corresponding `k`
- Runtime fallback: forbidden by explicit device enumeration and binding

## Interpretation

At this batch-1, short-burst workload, CPU is 1.38x to 1.43x faster than Intel GPU.0. The NPU has exceptionally low timing variance, but its approximately 112 ms fixed call cost makes it 3.9x slower than CPU at `k=8` and 13.0x slower at `k=1`. That fixed overhead dominates the synchronous propose/verify loop.

This does not disqualify the NPU hardware. It disqualifies the current OpenVINO GenAI NPU path as the primary low-latency synchronous proposer. It remains eligible for asynchronous, batched, energy-focused, or future-runtime experiments.

## Decision for the correctness prototype

1. Implement `CPU draft -> RTX target verification` first.
2. Start correctness coverage with `k=1,2,4,8`, without claiming an optimal `k`.
3. Keep GPU.0 as a secondary comparison.
4. Keep NPU as a qualification/energy branch rather than the primary performance path.
5. Require target-side verification of every candidate; draft hash equality is never assumed.

## Evidence

Raw files follow the pattern:

`logs\phase1-draft-micro-{CPU|GPU0|NPU}-k{1|2|4|8}-20260905.json`

Harness:

`scripts\phase1_sym_draft_matrix.py`
