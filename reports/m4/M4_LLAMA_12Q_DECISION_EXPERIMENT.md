# M4 llama.cpp Metal 12Q Decision Experiment

## Decision

**POSITIVE SIGNAL: `k=2` PASSES THE INITIAL M4 ARCHITECTURE-CONTROL GATE.**

The frozen root-cause 12Q matrix completed all 48 generations with exact-token
agreement. The Qwen3-8B Q8_0 target and Qwen3-0.6B Q8_0 draft ran through
llama.cpp 0.4.0 on Metal with greedy decoding and a 64-token cap. Condition
order was shuffled within each question using frozen seed `20260903`.

| Condition | Exact | Geomean decode speedup | Geomean prefill+decode speedup | Questions faster | Mean package J/output-token | Package-energy improvement |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 12/12 | 1.000x | 1.000x | reference | 0.932 | reference |
| `k=2` | 12/12 | **1.350x** | **1.288x** | **11/12** | **0.834** | **1.162x** |
| `k=4` | 12/12 | 0.948x | 0.963x | 6/12 | 1.275 | 0.748x |
| `k=6` | 12/12 | 0.820x | 0.849x | 5/12 | 1.480 | 0.641x |

Here, an energy-improvement ratio above one means baseline consumed more
energy. Package is Silemetry's CPU + GPU + ANE aggregate and excludes its
separately reported DRAM domain. Energy was trapezoid-integrated over the
runtime request window (prefill plus generation), excluding model load.

`k=2` clears the predeclared strong-positive threshold (>1.10x and faster on
most questions). Its arithmetic mean package energy per output token is 10.6%
lower than baseline; the paired geometric energy ratio is 1.162x. `k=4` is
slightly below break-even, while `k=6` is clearly negative.

## Speculation behavior

| Condition | Drafted tokens | Accepted tokens | Weighted acceptance | Verification rounds |
|---|---:|---:|---:|---:|
| `k=2` | 578 | 353 | 61.1% | 292 |
| `k=4` | 919 | 412 | 44.8% | 235 |
| `k=6` | 1,196 | 440 | 36.8% | 207 |

The deeper configurations reduce verification rounds but waste progressively
more draft work. That tradeoff explains why `k=2` is robust while `k=4/6`
become strongly prompt-dependent.

## Memory and thermal checks

All 48 runs passed the composite memory gate: no run entered WARN or FAIL and
no throttled pages were observed. Sampled process peak RSS ranged from 14,200
to 17,567 MiB; this is process RSS, not an additive physical-memory measure on
unified memory.

The ten full-length baseline generations averaged 12.07 tok/s in the first
five and 11.95 tok/s in the last five, a 1.0% decline. `pmset` reported no
thermal or performance warning after the matrix. Silemetry's private sensor
stream recorded rising temperatures, but its hottest-channel maxima are not
treated as calibrated junction limits. The stable baseline rate and absence of
OS thermal warnings do not support a material late-run throttling confound.

## Measurement notes

- Completion time and tok/s use llama.cpp's reported target evaluation time.
- TTFT is retained as a prompt-evaluation proxy because this CLI does not emit
  a separate first-token latency field suitable for this subprocess protocol.
- Draft/acceptance counts and verification rounds come from llama.cpp's own
  speculative statistics at debug verbosity.
- Silemetry uses private IOReport/AppleSMC interfaces; energy claims apply to
  this fixed M4/macOS build and are not cross-device power calibration.
- Questions 164 and 239 reached EOS after nine runtime output tokens; paired
  comparisons use the same exact output length.

The subsequent mechanism diagnosis found a cheap two-token verification ratio
and strong acceptance/speedup correlation, but a two-prompt paired recheck did
not reproduce the original per-question magnitudes: high-acceptance Q438
remained positive at 1.169x geomean, while low-acceptance Q395 was negative at
0.704x. Therefore 1.350x is retained as an initial positive signal rather than
a replicated effect-size estimate. See `M4_SPECULATION_MECHANISM_DIAGNOSIS.md`.

The result authorizes a bounded full paired replication of the `k=2` condition
if tighter estimates are needed. It does not authorize 60Q, 420Q, 14B or ANE.
