# PR123 RTX dispatch intervention — actual result

302 native hosts, 9228 explicit graph calls. UUID `hs123-57d3eed0-c107-4358-bc4a-ac1008a06e28` permanently closed. SOFTWARE_FIRST/HOLD.

Both separately started sessions and all8 planned blocks completed for eligible paths. 208/256 clean slots qualified; the other48 were never started because six cell/arm combinations failed their two-host exact-reference qualification. No scientific retry or replacement. Twelve native qualification exits3 are retained finite-output mismatches, not CUDA launch/sync failures.

## Reference-constrained physical intervention

| Logical L | Physical S | Two values × two fresh hosts | Clean eligibility |
|---|---|---|---|
| 1023 | 1023 | 4/4 exact | admitted |
| 1023 | 1024 | 0/4 exact | INFEASIBLE_EXACT_REFERENCE |
| 1023 | 1025 | 4/4 exact | admitted |
| 1024 | 1024 | 4/4 exact | admitted |
| 1024 | 1025 | 0/4 exact | INFEASIBLE_EXACT_REFERENCE |
| 1024 | 1026 | 0/4 exact | INFEASIBLE_EXACT_REFERENCE |

All 12 failed ordinary occurrences are retained with complete bytes, mismatch word count, max absolute error, signed ULP distance and first differing word in results/NUMERICAL_MISMATCHES.csv. Inputs, placement, finite values, actual node support and compute/sync returns passed. No intermediate QK/softmax/AV diagnostics were added: first internal divergence and backend cause remain UNKNOWN.

The only qualified padding L1023→S1025 is tested against BOTH unpadded QB controls. Padding that reaches S1024 did not preserve this reference contract, so its clean speedup is undefined. No padded serial reference replaces the unpadded two-capture-per-query reference.

## Actual matched clean costs

Primary B0 is completed graph; primary T0 is one copy/transpose→Q upload/sync→replay/full sync→ordinary readback QPC interval. Host means equally weight the two values and8 blocks. Units µs.

| Geometry | Arm | Primary | Resident graph | Resident call | CPU Q | Q upload/sync | Readback |
|---|---|---:|---:|---:|---:|---:|---:|
| B0-1023 | native_A | 113.234 | 113.234 | 147.096 | N/A | N/A | 33.862 |
| B0-1023 | native_B | 113.215 | 113.215 | 147.194 | N/A | N/A | 33.979 |
| B0-1023 | pad_2 | 114.924 | 114.924 | 148.715 | N/A | N/A | 33.790 |
| B0-1024 | native_A | 50.324 | 50.324 | 84.953 | N/A | N/A | 34.629 |
| B0-1024 | native_B | 50.224 | 50.224 | 84.820 | N/A | N/A | 34.597 |
| T0-2 | QB_A | 89.500 | 45.766 | 80.009 | 0.794 | 8.678 | 34.243 |
| T0-2 | QB_B | 88.949 | 45.375 | 79.627 | 0.805 | 8.504 | 34.252 |
| T0-2 | QH_compact | 89.694 | 45.764 | 80.070 | 0.916 | 8.692 | 34.306 |
| T0-2 | QH_permuted | 89.683 | 46.162 | 80.290 | 0.811 | 8.568 | 34.129 |
| T0-4 | QB_A | 118.625 | 66.162 | 104.528 | 1.340 | 12.742 | 38.365 |
| T0-4 | QB_B | 118.322 | 66.144 | 104.355 | 1.292 | 12.661 | 38.211 |
| T0-4 | QH_compact | 118.816 | 66.074 | 104.312 | 1.944 | 12.545 | 38.239 |
| T0-4 | QH_permuted | 119.823 | 67.001 | 105.565 | 1.531 | 12.713 | 38.564 |

Setup allocation, initialization, graph construction, source materialization, full initial upload and buffer bytes are in COST_BOUNDARIES.csv. B0 padding materialization CPU wall is in raw INPUT_PROVENANCE.json; it includes generation/verification and is not a deployment latency estimate. K/V/mask are resident in T0; targets preallocated; actual Q copy/transpose is charged each call. Original model-Q production remains UNKNOWN. Compute-return may already include backend synchronization; explicit subsequent full-device sync is disjoint. Neither host interval is called kernel latency.

## Paired estimates and prospective screen

| Geometry | Numerator / denominator | Ratio [95% block interval] | Δ µs | A/A scale µs | Screen |
|---|---|---|---:|---:|---|
| B0-1023 | AA | 1.000189 [0.997101, 1.003205] | 0.019 | 0.442 | False |
| B0-1023 | pad_2/native_A | 1.014783 [1.008791, 1.023742] | 1.690 | 0.442 | False |
| B0-1023 | pad_2/native_B | 1.014974 [1.006371, 1.025399] | 1.709 | 0.442 | False |
| B0-1024 | AA | 1.001958 [0.995605, 1.008982] | 0.101 | 0.322 | False |
| T0-2 | AA | 1.006066 [0.984530, 1.028574] | 0.551 | 2.346 | False |
| T0-2 | QH_compact/QB_A | 1.002216 [0.978504, 1.027650] | 0.194 | 2.346 | False |
| T0-2 | QH_compact/QB_B | 1.008295 [0.988981, 1.029729] | 0.745 | 2.346 | False |
| T0-2 | QH_compact/QH_permuted | 1.000014 [0.985009, 1.015535] | 0.012 | 2.346 | False |
| T0-2 | QH_permuted/QB_A | 1.002202 [0.982208, 1.019768] | 0.183 | 2.346 | False |
| T0-2 | QH_permuted/QB_B | 1.008281 [0.988917, 1.027728] | 0.734 | 2.346 | False |
| T0-4 | AA | 1.002565 [0.997416, 1.007736] | 0.304 | 0.939 | False |
| T0-4 | QH_compact/QB_A | 1.001598 [0.995238, 1.007214] | 0.190 | 0.939 | False |
| T0-4 | QH_compact/QB_B | 1.004167 [0.999294, 1.009306] | 0.494 | 0.939 | False |
| T0-4 | QH_compact/QH_permuted | 0.991659 [0.982389, 1.000395] | -1.007 | 0.939 | False |
| T0-4 | QH_permuted/QB_A | 1.010022 [1.000932, 1.020110] | 1.197 | 0.939 | False |
| T0-4 | QH_permuted/QB_B | 1.012613 [1.005842, 1.019770] | 1.501 | 0.939 | False |

Full per-value/per-session signs and leave-one-block-out estimates are in execution/ANALYSIS.json. Whole blocks are bootstrapped within actual sessions; arms and values stay paired, values equal weight. Inner30 calls are technical repeats. Two sessions are not independent devices or dates. No B0/T0 pooled speedup. PRACTICAL_CANDIDATE requires all8 blocks, both values and sessions in the saving direction against BOTH controls, upper interval<1 and saving>max(2% baseline,1µs,matched A/A scale).

Screen outcome: `{"B0-1023": {"pad_1": "NOT_ESTABLISHED", "pad_2": "NOT_ESTABLISHED"}, "B0-1024": {"pad_1": "NOT_ESTABLISHED", "pad_2": "NOT_ESTABLISHED"}, "T0-2": {"QH_compact": "NOT_ESTABLISHED", "QH_permuted": "NOT_ESTABLISHED"}, "T0-4": {"QH_compact": "NOT_ESTABLISHED", "QH_permuted": "NOT_ESTABLISHED"}}`. No interpretation of a tiny positive point estimate as stable acceleration.

## Actual path and ON evidence

24 profiled attempts, including failed qualification paths. Actual successful capture/end/instantiate and each formal replay verified for every admitted signature; six alternating-input capability hosts verify both values for q2/q4 and both Q representations. Clean hosts do not load CUPTI and inherit mode eligibility only through exact graph/runtime signature matching. Profile timing is never pooled with clean timing. Failed paths can have only first-call direct execution evidence, not qualified steady replay. See TRACE_SUMMARY.csv and raw API/activity records.

SOURCE_LINK_UNKNOWN: candidate source mmvf even-dimension/alignment predicates and softmax launch specialization were inspected and hashed; the staged CUDA DLL lacks an authenticated source/link correspondence. Trace signatures support representation/path observations only. Padding changes work as well as dispatch. Kernel count is not traffic, occupancy, busy-time union, Tensor Core utilization or isolated causal attribution.

## Accounting, failures and reproducibility

Native exit0 290, exit3 12; profiles 24/24. Native command-wall sum 377.668s; stage-controller wall sum 497.948s; scoped native/helper/controller conservative owned upper 1253.284s. Peak native Job commit 651067392B, per-Job cap8GiB. Combined full-task OS peak not certified. Explicit endpoint SMI queries 27; all8 blocks environment-qualified. Endpoint quiet is not continuous exclusivity. Invalid/odd clock telemetry stays UNKNOWN and is not used to normalize costs.

Budget6h with final45min reserve; native120s,8GiB owned memory/output and10GiB headroom. Actual302 hosts/9228 calls are below350/11448 specifically planned and358/11732 overall caps. No models, decoder, actor, RTL, FPGA, B570, paper, main, release or automation changes.

Pre-graph failures preserved: missing build-library path, missing header path, and verifier mapping import-library/PDB names outside build/. The verifier correction was committed/frozen before any GPU query; native bytes unchanged. Initial and repair F0 both retained. No GPU startup failure or scientific retry. CPU13 unit tests,8 actual-evidence corruption negatives and4 signed-ULP diagnostics tests passed. Diagnostic signed zero-crossing ordering was corrected in an explicit offline wrapper; admission bitwise checks, frozen timing and statistics did not change. A short CPU fault-injection audit overlapped session0; all samples retained, no result-based exclusion.

Initial F0 `df35b72fc00e1e2189a1d9e4264f99efaf4838ebab7510e304fcef38cd95638c`; tool-repair freeze `fe3ee728f7cb227cdc3e7314dd5dc78888d0b94e2635dbe5a9fc9f18887a8184`; admission `72bca69b2153119bee52a0ea8e9b8b5d798773a2486c98915a4b050eacd48c1a`.

Raw: `D:\hs123-57d3eed0-c107-4358-bc4a-ac1008a06e28`. ZIP: `D:\hs123-57d3eed0-c107-4358-bc4a-ac1008a06e28-archive\raw.zip`; 7860 members, 67118323B; SHA256 `2e69ad5cc8a32944781a1da643ea2116f11575aee14fc12c25eff997f22dcfd3`. Member manifest SHA256 `066fde9a3e3946f8949ab4e18fa049f7d5aa01b8a6a144848ecd1799d59573b7`. Fresh restore enumerated/hash-verified every member; a new interpreter recomputed all scientific exports byte-exact. Local verification only: raw not uploaded, no external independent review. Compact Git artifacts receive separate actual remote-byte readback.

## Decision

No T0 candidate meets the predeclared practical screen against both QB controls. Close the compact-QH optimization branch for these fixed inputs; no further precision hunting. The reference-preserving representation opportunity is constrained: reaching the cheap1024 path by padding does not preserve the required bytes for these inputs. The remaining admissible padding has its own matched cost estimate. T0 answers the charged ON conversion question on fixed q2/q4 synthetic inputs; follow the both-control screen and retain negative/discordant outcomes. No selector, decoder or hardware GO follows. Keep QB as the strong software baseline; software-first/HOLD remains.
