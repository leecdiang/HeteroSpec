# B570 evidence closure for the mapping-cost chapter

This document integrates the completed B570 micrograph study into the paper's existing research chain. It does not replace the historical model experiments, change their reference contracts, or certify the whole B570 platform.

Research chain: **reference semantics → admitted mappings → strong software baseline → charged cost boundary → remaining hardware opportunity**.

The chapter structure follows the merged [RTX evidence synthesis](https://github.com/leecdiang/HeteroSpec/blob/9b8cdba784b34a5aa3e8981073223c451bbaaf54/docs/research/rtx_evidence_synthesis_20261018/CHAPTER_DRAFT.md). B570 extends its evidence scope with a separately qualified Vulkan experiment, not a controlled hardware comparison.

## Evidence and decision

| Step | B570 evidence | Supported statement | Boundary |
|---|---|---|---|
| Reference semantics | Serial FP64 stage oracle, exact cross-arm ordinary finals, actual input readbacks, 243 prior-reference continuity checks | These exposed inputs preserve the prescribed bytes across the representation change | No universal equivalence or token-level qualification |
| Admitted mapping | Original q2 QB support rejection preserved; scoped batch-3 support repair uses existing broadcast shader; all 9 coordinates pass | A concrete backend admission gap can be repaired without REPEAT or K/V replication | Hq=Hkv=8 and frozen F16/F32 geometry; not general GQA |
| Strong baseline | Separate QB_A/QB_B allocations executing the same graph factory; 3 inputs, 3 fresh processes, balanced orders | The pilot's apparent ordering is not a sufficient basis for selecting QH_C | Sessions are one device/date; small cluster count |
| Resident cost | Prior q2/q4 panel difference -1.028 us, interval [-2.177,+0.067] us | No practical QH_C benefit established in the resident compact-Q window | No upload, natural producer or final readback in that window |
| Charged representation | New continuous copy/transpose + upload + graph + full readback panel difference -1.518 us, interval [-4.168,+0.916] us | No practical benefit established after producing the candidate layout from common host Q | K/V/mask resident; no model producer, cache update or request critical path |
| Hardware opportunity | No calibrated physical bottleneck or request critical-path fraction | Keep the hardware decision SOFTWARE_FIRST/HOLD | This is insufficient evidence for an accelerator, not a theorem that no opportunity exists |

The current branch is closed with a useful negative result: **retain QB on the tested B570 backend**. Do not build a selector from post-hoc fastest points, continue sampling until a favorable result appears, or turn the remaining GPU budget into an experiment quota. Reopening requires a different, concrete hypothesis.

## Manuscript-ready passage

We separately examined the same mapping question on an Intel Arc B570 Vulkan
backend. The original backend rejected multi-query QB at operator admission,
although its existing matrix-vector shader implemented the required broadcast.
A narrowly scoped admission repair enabled the tested equal-head F16/F32
geometries without replicating K/V or substituting a repeated-query graph.
For key extents 1023, 1024 and 1025 and query counts 1, 2 and 4, all tested
outputs passed the serial FP64 stage checks and exact cross-mapping final
comparison. These results establish admissibility only for the exposed inputs
and frozen runtime.

The initial short pilot was followed by balanced experiments using two arms
with the same QB implementation, three fixed input sets, and three fresh
process sessions. In the resident compact-Q window, the fixed q2/q4 panel's
QH_C-minus-dual-QB difference was -1.028 microseconds, with a descriptive
family-adjusted interval of [-2.177, +0.067]. We then charged the representation
transaction continuously, beginning with common permuted host Q and including
copy or transpose, Q upload, graph completion, and complete final readback.
K/V and the mask remained resident, and targets were preallocated.
The corresponding difference was -1.518 microseconds
[-4.168, +0.916]; the paired geometric QH_C/QB ratio was
0.992244 [0.979908, 1.004691]. No coordinate or the fixed panel cleared the
predeclared practical-effect screen against both QB controls. All 243 final
outputs in the transaction study retained the preceding reference bytes.

We therefore retain QB for this tested B570 branch. The result does not prove
equivalence or exclude smaller effects: the A/A screen is conservative, the
study has only three process clusters on one device and date, and the inputs
are synthetic. Its value is to constrain the optimization claim before
proposing hardware. The transaction excludes natural Q production and ongoing
KV-cache updates, and the study does not measure a model-request critical-path
share or identify a calibrated physical bottleneck. Accordingly, it supports
neither an end-to-end speedup claim nor a new accelerator design.

## Placement, figure and source links

Place this passage after the RTX charged-representation subsection and before the hardware-implications discussion. Cite:

- Scoped backend repair and original nine-coordinate pilot: [PR128 a970dbe3](https://github.com/leecdiang/HeteroSpec/tree/a970dbe33083a42877f7f142d27e0eded9de6eea/benchmarks/b570_qb_batch_broadcast_v1).
- Balanced resident evidence: [PR128 73d07c32](https://github.com/leecdiang/HeteroSpec/tree/73d07c328da335cfdfc48ad0719181b69bd2e467/benchmarks/b570_qb_batch_broadcast_v1/balanced_retest_v1).
- Charged transaction: this directory's `PREREGISTRATION.json`, `ANALYSIS.json`, `RESULT.md`, `REFERENCE_CONTINUITY.json` and exact process receipts in `NATIVE_EVIDENCE.zip`.
- Figure: `MAPPING_COSTS.svg`; source `closeout.py`, with `RESIDENT_ANALYSIS.json` and `ANALYSIS.json`.

Suggested caption: “B570 mapping differences in two separately measured windows. Points are QH_C minus the mean of two identical QB controls; bars are 99.5% descriptive paired session/block-bootstrap intervals. Gray rows are q1 controls. Each coordinate has three fixed inputs and three fresh process sessions, with six paired blocks per input/session. All practical-effect screens remain unresolved. The panels change both layout and window; their absolute costs do not isolate transfer or packing overhead.”

Do not pool RTX and B570 timings or copy the RTX 8/3/8 kernel-count boundary onto B570. Hq/Hkv, runtime, execution mode and instrumentation differ. The shared conclusion is about the evidence required to justify a mapping optimization, not about relative hardware quality.

## Remaining work for the whole paper

Within the current model-free authorization, the support/correctness/baseline/transaction branch is ready for paper integration and artifact review. The existing untracked manuscript directories were not overwritten.

The following remain separate, unexecuted questions:

1. Natural-request relevance: identify a real admitted model path and measure this region's critical-path share, including Q production and KV updates. Model execution is outside the current authorization. Micrograph costs cannot supply this missing fraction.
2. Physical mechanism: only if a repeatable practical residual exists after the full software baseline, collect separately authorized device-level evidence for submission, memory or arithmetic limits. Kernel count alone is insufficient.
3. Hardware design: only after the first two gates, define a concrete module, numerical contract, resource budget and PPA evaluation. Actor and RTL remain outside authorization.
4. Formal platform delivery: CPU8/PR127 remains its own blocked qualification track; these micrograph passes do not establish F0 or any of the eight CPU8 acceptance items.

A future executor should first read the latest cumulative budget and preserve every preceding evidence root. The current starting charge is **53.7774511 seconds**, leaving **246.2225489 seconds**. No historical launcher may be reused to reset that charge. There is no authorized reason to spend it on another repetition of this closed comparison.
