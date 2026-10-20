# B570: charged Q representation transaction

The tested QB/QH_C micrograph branch is complete. All nine coordinates pass support, FP64 numerical checks and exact reference-byte checks, but no coordinate or the fixed q2/q4 panel establishes a practical QH_C advantage under the preregistered A/A screen. Retain QB; close this optimization branch for these inputs. This does not establish equivalence or complete model/platform qualification.

## Why this experiment

The preceding resident-graph retest at PR128 commit `73d07c328da335cfdfc48ad0719181b69bd2e467` found no stable difference beyond its A/A screen. The paper's remaining question was whether a candidate remains useful when its input representation must be produced. This experiment measures that missing transaction, using the same patched Vulkan DLL and no additional backend change.

All arms start with identical preexisting permuted host Q `[q,H,d]`. QB_A and QB_B copy it to their separate staging buffers and expose the same permuted-Q graph. QH_C transposes it into compact `[H,q,d]`. One continuous steady-clock window includes copy/transpose, Q upload and synchronization, graph computation and synchronization, and complete final readback and synchronization. Host/device targets are preallocated; K/V/mask are resident. Original model-Q production, KV updates, compilation, allocation and reference checking are excluded. No CUDA-style capture/replay or GPU device timestamps are claimed.

The geometry remains Hq=Hkv=8, d=dv=128, key=1023/1024/1025 and q=1/2/4, with the original causal mask. This is not the RTX GQA geometry and cannot support a controlled device ranking. The q1 arms use the identical original graph and memcpy path.

## Design and qualification

Three fresh serial native processes each cover three fixed input sets, nine coordinates and three arms. Every session completes all support checks, all numerical checks and all actual transaction qualification checks before timing. QB_A/B canonical node metadata must match. Original K/V tensor identities are retained, and REPEAT nodes are forbidden.

Every paired block contains all six arm permutations; five calls per visit produce 30 observations per arm. Cell order and permutation starts rotate across blocks and sessions. Five warmups and one primer per arm precede measurements. Complete output bytes are checked after every transaction, outside its timed window. Input bytes are read back before/after qualification and after timing. No first failure occurred; no GPU retry was performed.

Results:

- 243/243 support slots, 243/243 numerical slots and 243/243 actual transaction qualification slots pass.
- All 243 complete finals also match the prior resident experiment's exact reference bytes, checked from saved files by `REFERENCE_CONTINUITY.json`. The representation change did not silently introduce a new reference.
- 486 paired blocks contain 43,740 measured transactions; 46,899 total graph computations include qualification, warmups and primers.
- CPU-only NumPy recomputation passes 2,430 stage checks, 2,916 input readback identities, 1,458 post-block final identities and 162 cross-arm identities.
- All frozen input hashes match after execution.

## Cost result

The analysis program was fixed before execution and reuses the preceding retest's estimator: 20,000 paired session/block bootstrap draws, nine coordinate claims plus one predeclared equal-weight q2/q4 panel, 99.5% per-claim intervals, and a practical screen requiring the interval to exceed max(1 us, 2% of QB mean, p95 absolute A/A block difference). Directions must agree across all sessions and inputs, and point differences must exceed the screen against both QB arms. q1 controls do not trigger the observer-invalid rule.

| Fixed q2/q4 panel | Value |
|---|---:|
| QB_A mean | 187.013 us |
| QB_B mean | 187.819 us |
| QH_C mean | 185.898 us |
| QH_C minus dual-QB mean | -1.518 us |
| Adjusted difference interval | [-4.168, +0.916] us |
| Paired QH_C / dual-QB geometric ratio | 0.992244 |
| Adjusted ratio interval | [0.979908, 1.004691] |
| A/A practical-screen threshold | 17.284 us |
| All nine coordinate screens / panel | UNRESOLVED |

The interval crosses zero, one session's direction reverses, and the observed difference is below the A/A threshold. These are sufficient reasons not to adopt QH_C on this evidence. Three process clusters on one device/date are not a population-level significance or equivalence result. A q1 control that does not trigger also does not certify two-percent measurement resolution.

`MAPPING_COSTS.svg` and the local PNG/PDF show the fixed intervals. The resident and transaction panels use different input layouts and measurement windows; their absolute costs must not be subtracted to estimate isolated transfer or packing costs. No phase-sum reconstruction was substituted for the continuous transaction.

## Process evidence and budget

| Session | PID | Parent wall charge | Exit |
|---|---:|---:|---:|
| 0 | 1712 | 9.8485258 s | 0 |
| 1 | 17440 | 8.0238481 s | 0 |
| 2 | 13060 | 8.0635999 s | 0 |

All processes returned normal backend cleanup, complete stdout/stderr capture and observed exit. No deadline kill was requested. New charge is 25.9359738 seconds, including initialization, reference work, raw I/O and cleanup. Prior charge 27.8414773 seconds remains unchanged. Cumulative charge is **53.7774511 / 300 seconds**, leaving **246.2225489 seconds**. This budget is a ceiling, not a requirement to spend the remainder.

The historical launcher refuses an existing ledger. It must not be restarted with its historical starting balance. Future authorized execution requires a new evidence root and starts from 53.7774511 cumulative seconds.

## Evidence delivery and limits

Evidence root: `C:/hs/b570-qb-transaction-20261020160400`.
The 7,782 raw result files occupy 4,356,096,428 bytes and remain local. Git includes source, frozen design, exact compact metadata ZIP, analysis, block means, continuity checks, summary and compressed full selected-artifact manifest. Raw tensors and DLLs are not uploaded. Hash verification of compact Git artifacts is not external validation of the full raw data.

Unzip `NATIVE_EVIDENCE.zip` beside `analyze.py` to recompute statistics without any GPU load. `verify_raw.py` requires the preserved raw tensors; `closeout.py` additionally requires the prior evidence root for reference continuity. Its figure and packaging work are CPU-only. Local absolute include/library paths and the frozen runtime remain prerequisites for rebuilding the native harness.

Device exclusivity, continuous clocks/power and a physical GPU bottleneck were not established. Repeated fixed inputs are technical repeats, not new workload samples. Exact bytes on the exposed tensors do not imply greedy-token or model-request qualification.

No model, actor, RTL, CPU8 execution or CPU8 framework extension occurred. PR127/F0 and all historical failures remain unchanged. Draft PR only; no merge.
