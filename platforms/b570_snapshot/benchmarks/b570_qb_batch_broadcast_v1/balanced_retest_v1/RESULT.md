# PR128 balanced QB_A/QB_B/QH_C retest

Result: all nine coordinate screens and the fixed q2/q4 panel are UNRESOLVED. This retest does not establish a QH_C advantage or disadvantage beyond the preregistered A/A noise boundary. It does not prove performance equivalence.

## Fixed scope and execution

Parent scientific commit: a970dbe33083a42877f7f142d27e0eded9de6eea (Draft PR128). No backend or shader changes in this retest. Actual Vulkan DLL SHA256 remains 79b0031bea367da64a8f580f1b00fe1108c83cc2ab73e893739d9740e4408423. Device: Intel Arc B570, driver 32.0.101.9034.

Three serial fresh OS process sessions each constructed a new backend and graph allocations. Sessions ran on one device and date, within 24 seconds; they are not independent devices, independent dates, or evidence of long-term stability. Three fixed input sets were reused across sessions: the original dyadic pattern, small counter-hashed dyadic values, and a different counter-hashed input with larger magnitude. D=Dv=128, H=Hkv=8, compact F32 Q, F16 K/V, exact key 1023/1024/1025, q=1/2/4 and query-specific causal masks remain fixed.

QB_A and QB_B use exactly the same graph factory branch with separate allocations. Canonical graph metadata equality is asserted. Original K/V objects remain unchanged, with no REPEAT nodes. Each session first passed all 81 support slots, then all 81 FP64 QK/softmax/AV/final numerical slots and arm-output byte checks before any timing. All input readbacks were retained. Every post-block final was required byte-identical to the qualified output.

Three sessions completed 243 numerical slots, 486 paired timing blocks, 43,740 measured graph calls, and 46,656 total graph calls including numerical, warmup and primer calls. Calls are technical repeats, not independent statistical samples.

## Balanced design and frozen analysis

Each session/input/coordinate has six blocks. Every block executes all six permutations of QB_A/QB_B/QH_C, each arm twice at each ordinal position. Each arm visit contains five timed calls, hence 30 calls per arm per block. Coordinate/input traversal and permutation starting order rotate by session/block. Measurement-file writes occur outside timed calls. No observations or outliers were removed.

Timing is host steady-clock graph compute plus explicit backend synchronization on resident inputs. Backend Q staging remains included. Explicit upload/readback, allocation, numerical reference, setup and logging are outside the measured call but inside cumulative native-process wall accounting. No GPU timestamp, replay, model latency or complete input-production cost claim is made.

The frozen analysis uses paired block means. It resamples three session clusters and blocks within each fixed input, keeping all arms paired and sharing resampling indices across coordinates. There are 54 paired blocks per coordinate but only three process-session clusters. Twenty thousand bootstrap replicates use seed 20261020. Nine coordinate claims plus one predeclared q2/q4 panel use 99.5% per-claim intervals (Bonferroni family adjustment over ten claims). With only three clusters, these are descriptive conditional intervals, not population-level confidence guarantees.

A directional screen requires its full paired difference interval to lie beyond max(1 us, 2% mean QB time, 95th percentile absolute QB_B-QB_A block difference), direction agreement in all three sessions and all three inputs, and point differences beyond the threshold against each QB arm. Any q1 raw screen would mark the observer uncalibrated and disable all mapping conclusions. No q1 screen triggered. This only passes that negative-control check; it does not certify two-percent measurement resolution.

## Coordinate results

Difference is QH_C minus the mean of QB_A and QB_B, in microseconds. A/A noise is the 95th percentile absolute paired block difference QB_B-QB_A.

| key | q | difference | 99.5% paired interval | A/A noise | screen |
|---|---:|---:|---|---:|---|
| 1023 | 1 | +0.44 | [-3.03, +3.48] | 8.87 | UNRESOLVED |
| 1023 | 2 | -0.70 | [-2.15, +0.71] | 10.57 | UNRESOLVED |
| 1023 | 4 | -0.73 | [-2.38, +0.77] | 12.14 | UNRESOLVED |
| 1024 | 1 | -0.84 | [-3.22, +1.13] | 6.28 | UNRESOLVED |
| 1024 | 2 | -0.25 | [-1.78, +1.32] | 11.74 | UNRESOLVED |
| 1024 | 4 | -0.96 | [-2.84, +1.04] | 11.78 | UNRESOLVED |
| 1025 | 1 | -0.22 | [-1.50, +1.20] | 9.91 | UNRESOLVED |
| 1025 | 2 | -1.01 | [-2.51, +0.97] | 8.46 | UNRESOLVED |
| 1025 | 4 | -2.52 | [-9.43, +1.06] | 16.52 | UNRESOLVED |

The predeclared equal-weight q2/q4 panel has QB_A mean 125.496 us, QB_B mean 125.273 us and QH_C mean 124.357 us. QH_C minus dual-QB mean is -1.028 us, with interval [-2.177,+0.067] us. Its paired geometric ratio is 0.991897, interval [0.984106,1.000356]. Panel A/A noise is 3.445 us and dominates the screen threshold. No stable advantage passes the declared screen.

The earlier single-input pilot's QH_C-higher median ordering is not established by this balanced retest. Inputs, sessions and ordering changed together, so this is not an isolated causal attribution to ordering. Retain both results. Current evidence supports keeping QB as the existing software baseline, without a selector or hardware claim. It does not establish that no finer difference exists.

## Numerical and raw-data recheck

All per-session FP64 checks and exact cross-arm final checks passed. An additional CPU-only NumPy recheck of saved operands and actual GPU outputs passed:
- 2,430 stage checks, including all six post-block outputs per graph;
- 2,916 actual input-readback identities;
- 1,458 post-block exact-output identities;
- 162 cross-arm exact-output identities.
Maximum final absolute error against NumPy FP64 was 1.672460842039314e-8 in every session. No GGML/GPU backend is loaded by the CPU analysis/recheck scripts.

## Process receipts and cumulative budget

| session | PID | charged parent wall (s) | exit |
|---|---:|---:|---:|
| 0 | 43132 | 8.8882332 | 0 |
| 1 | 38580 | 7.0738920 | 0 |
| 2 | 11636 | 7.1192354 | 0 |

All three processes exited, complete stdout/stderr capture was observed, normal backend cleanup returned and no deadline kill was requested. This retest charges 23.0813606 seconds. Prior charge stays 4.7601167 seconds. Cumulative charge is 27.8414773 / 300 seconds, leaving 272.1585227 seconds. There were no GPU retries or further GPU runs.

A CPU compilation initially found a duplicate session variable; that declaration was removed before GPU launch. Both failed and successful build logs are retained. Runtime, preregistration, source and analysis hashes were fixed before the first session and reverified afterward.

## Evidence and reproduction

The evidence root is C:/hs/b570-qb-aa-balanced-20261020065000. All 7,296 raw result files (4,351,349,322 bytes) are retained locally. FINAL_MANIFEST.json hashes the raw results and selected source, binary, receipts and analysis files; its gzip copy and hash receipt are supplied in Git. Old PR128 pilot and unsupported-run directories are unchanged.

NATIVE_EVIDENCE.zip preserves the exact three session result.json/timing.jsonl files, stdout/stderr, process receipts and build logs without the large tensors. Expanding this ZIP beside analyze.py provides the original directory structure needed for a CPU-only analysis rerun. BLOCK_MEANS.csv exposes all 486 paired block means for inspection. Reproducing verify_raw.py additionally requires the local raw tensor files listed in the manifest; Git delivery is not external validation of those tensors.

RUN_ALL.ps1 is the historical launcher and refuses an existing ledger. Its historical starting charge must never be reused to reset accounting. A future run needs new evidence and must start from 27.8414773 cumulative seconds.

No models, actor, RTL or CPU8 execution; no CPU8 framework expansion; no merge.
