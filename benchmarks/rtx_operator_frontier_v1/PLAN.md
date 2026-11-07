# RTX operator frontier: PR168 review and focused follow-up

Status: DESIGN / NATIVE NOT RUN. Author target: IEEE TPDS.

Base: PR168 at `9c79594f679ea4aad1956d8a385fdf6a7352d892`, on PR166. This independent branch adds planning and review only. Do not alter the frozen PR168 sources, references, records, criterion or input panel. B570 PR169 is running independently: do not change its branch, prompts, shared files or jobs.

## 1. Decision from the review

Run a bounded RTX follow-up now, rather than waiting idle for Vulkan. Do not repeat PR168 timing to turn its roughly 1% point estimate into a passing result. The unresolved RTX-specific questions are (a) whether blanket four-column Q8 projection/FFN lowering is necessary or avoidable, and (b) the cost of local versus whole-graph cuts when those cuts actually differ. Defer a broad new natural-workload campaign and redundant head-dimension/model expansion until the B570 result and these diagnostics are available.

### What PR168 established

- The frozen pilot retains scalar-reference compatibility for R and four methods on two natural inputs, evaluated separately at capacities 1024 and 1536. Its reported 2,560 committed-vector comparisons and 1,896 speculative branch comparisons overlap; they are not independent samples. Native stock paths have their own compatibility flags.
- Physical WB-cut is a genuine whole-target graph split driven by the KV allocator. It shares the same candidate numerical lowering as QB-local and is a serious comparator, not an intentionally slowed baseline.
- The wide caller graph is real, but its Q8 projections/FFN and attention are lowered into tiles of at most four columns/queries. A 32-row caller graph is not evidence for a reference-compatible elementary matmul of width 32.
- Head mappings 16/8, 32/8 and 40/8 are exercised within Qwen3; all reported head dimensions are 128. This is useful geometry coverage, not three new model families or a new head dimension.

### Cost reconstruction and interpretation

The authoring review independently recomputed the 64 measured service seconds transcribed from `benchmarks/tpds_parallel/evidence/cost.json`; all published service geometric means, ratios and session directions agree. No native inference or full raw-vector reconstruction was performed in the reviewer environment. Direct evidence downloads were unavailable there; the original host remains the source for raw tensor replay.

| Arm | Service geometric mean, seconds | Arm / QB-local |
|---|---:|---:|
| Timed ordinary R | 8.574332 | 2.072178 |
| S1 speculative | 11.265438 | 2.722543 |
| PQ-ext | 4.396870 | 1.062601 |
| QB-local | 4.137837 | 1.000000 |
| WB-cut | 4.180762 | 1.010374 |
| native32, not reference-compatible | 2.339648 | 0.565428 |
| native-full, not reference-compatible | 2.100309 | 0.507586 |

QB has 5.8913% lower time than PQ and 1.0267% lower time than WB on this fixed pilot. WB/QB session ratios are 0.984382 and 1.037052, and QB wins 5/8 blocks. The predeclared 3% plus consistent-session-direction criterion was not met. It is a descriptive engineering criterion, not a significance test or a TPDS requirement. Two inputs repeated across capacities and sessions are still two workloads.

The comparison has a precise structural explanation worth testing, not an excuse for rerunning it. With empty-cache starts, caller width 32 divides padding 256. Every full prefill chunk therefore stays in one extent; prompt tails 31 and 17 also stay in their current bucket. PR168 reports identical prefill physical width histograms for PQ/QB/WB and extra whole-graph WB cuts on only 2/158 verification calls. This is a useful low-cut-density control. It does not measure a broad high-cut-density serving workload.

Changing allocated capacity to 1536 does not itself establish a long active prefix: the natural prompts have lengths 255 and 593, and reported mechanism crossings are at 256 and 512. Boundary 1024 remains a meaningful untested coordinate under an already fixed context reference.

### TPDS implication

Keep the reference-preserving execution problem and the validated mechanisms. Do not claim general local-cut superiority, or attribute the common scalar-to-batched gain solely to QB. The stronger next contribution would be an operator-specific numerical execution rule with measured costs, or an accurately characterized boundary at which local graph organization helps. A simple WB implementation matching QB is a legitimate result and must remain visible.

Do not promote generic bitwise kernel equivalence itself as new. The September 2026 primary preprint *Taming Bitwise Behavior in GPU Kernels with Tensor Core: Black-Box Reconstruction, Compiler Enforcement, and Static Verification* (arXiv:2609.11356) already studies reduction descriptors, bit-compatible GEMMs and equivalence-constrained search. This follow-up remains about the existing quantized stateful runtime and its operator/graph mapping; it does not require implementing a new generic verifier or compiler.

## 2. Common execution rules

Restore the exact PR168/166 source bindings into new worktrees, binaries and output roots. Keep the existing RTX GPU placement, Q8 model bytes, F16 KV, non-flash attention and k3 natural speculative contract. Reuse the fixed scalar references at C1024/C1536. Do not redefine R to make a native-wide path qualify. A new implementation is a new candidate, not a retrospective reinterpretation of old measurements.

Scope activation and arithmetic policy stay fixed for each live request/state. For comparisons after a policy change, restore the identical canonical prefix in separate contexts; changing graph-cache identity alone does not undo a numerically changed KV state. Distinguish physical slot head from logical token length and require dense single-stream append for the current planner.

Use the existing exclusive GPU lock and finite process cleanup. Ordinary build, view, observer and runner defects can be fixed autonomously with the material change recorded. Diagnose resource or runtime errors rather than relabelling them numeric failures. Keep all completed and failed attempts. Avoid rebuilding a large audit framework: reuse the existing source and vector comparison machinery.

## 3. Experiment A: does each operator really require a four-column tile?

### Question and rival explanations

PR168's wide attempt changed the final logits and its blanket four-column Q8 lowering repaired the tested paths. This does not establish that every Q8 projection class needs the same restriction, that a four-column limit is fundamental, or how much time is spent on numerical arithmetic versus graph materialization.

Possible explanations to discriminate: activation quantization changes; reduction/accumulation organization changes; output/view/concat effects; placement changes; excessive launch/materialization overhead despite correct arithmetic. Do not assume the Vulkan Q8 activation mechanism is also the CUDA cause.

### Procedure

1. Reuse the retained 0.6B wide failure as a development witness and establish a Qwen8B witness under C1536. Keep the original failed attempt intact. Start with a noncrossing physical prefix so an attention extent change does not explain a projection difference.
2. Locate the first differing relevant operator using the actual input, weight bytes, tensor shape/stride and executing backend. Capture stable, owned operands before downstream aliasing. Require own-path replay to reproduce the captured output before interpreting interventions.
3. Inventory the actual classes reached by this graph: Q/K/V projection, attention output, FFN gate/up/down and vocabulary projection. Group genuinely identical arithmetic/dispatch descriptors; do not require a separate model run for every layer. Record each class's admitted route or untested status. Prioritize the first divergent class and one distinct high-cost class indicated by profiling; one graph-level failure is not evidence that all classes are equivalent.
4. On the same captured inputs compare scalar-column reference, existing <=4-column tiling, and native widths 8/16/32 (retain width 2/4 controls). Keep reduction operands and casts fixed; inspect actual activation precision, accumulation/reduction structure, backend selection, launch count and concatenation behavior. Compare full operator outputs, not just top-1. Fixed-width and native-wide paths are separate factors; use one-factor changes sufficient to identify the actual cause.
5. If the source/replay shows a concrete opportunity, implement one structural candidate: for example select a scalar-compatible existing wide route, batch independent output columns without changing each reduction, or remove redundant materialization while keeping the arithmetic. Selection must follow operator/tensor/backend descriptors, not model/input names or observed answer margins. Do not just remove a width guard, run a lucky sample, or assert that one failing route proves all wide implementations impossible.
6. Apply any improved arithmetic/lowering policy equally to QB-local and WB-cut. A faster new QB versus a deliberately obsolete WB would not isolate the grouping contribution. Preserve the old QB4 as a historical candidate and compare it with the new one where applicable.

Separate GPU execution, CPU planning/graph construction, launches, copies/concat and synchronization on a small diagnostic run. Native kernel identifiers or profiler traces are useful when available; scheduler tensor metadata alone is not a kernel trace. Profiling must not be mixed into primary clean timings.

### Deliverable and stop

Deliver an operator table: original descriptor, scalar route, native-wide route, observed equality, selected candidate action, cost and supporting source/replay. The result may be that existing <=4-column paths are the only routes established in this study. That is a bounded finding, not a mathematical ceiling. Do not start an unrelated kernel/compiler project or a repeated search for an advantageous percentage.

## 4. Experiment B: local versus whole-graph cuts under active boundaries

Use Qwen3-8B with C1536 and its already fixed scalar oracle; no C4096 expansion or new model is needed for this RTX question. Preserve k3 for any natural generation. Widths 8/32 below are known-token append diagnostics, not k7/k31 speculative decoding.

Freeze the following eight structural coordinates before new diagnostic timings. Read native padding P; the table assumes the existing P=256 and must be regenerated from actual metadata if the implementation differs.

| Boundary B | Append q | Noncrossing physical head H=B-q | Crossing physical head H=B-3 | Expected crossing extent groups |
|---:|---:|---:|---:|---|
| 256 | 8 | 248 | 253 | 3+5 |
| 256 | 32 | 224 | 253 | 3+29 |
| 1024 | 8 | 1016 | 1021 | 3+5 |
| 1024 | 32 | 992 | 1021 | 3+29 |

Use the same token fixture/prefix for all arms within a cell; build the prefix with scalar R and restore equivalent state for every run. A synthetic/teacher-input fixture is acceptable for this diagnostic and must be labelled as such. Do not edit natural prompts to manufacture a population speedup.

Primary paths are S1, frozen QB4 and frozen WB4. Report actual whole-graph calls, elementary projection/FFN widths, QK/AV widths, extents, copy/concat bytes, launches and graph-build/reuse counts. Under PR168's tile rule, crossing attention tiles should be 3+4+1 for q8 and 3+4+4+4+4+4+4+4+1 for q32. QB's projection tiles start from the caller group; WB's restart at the physical cut. Verify the actual native behavior rather than merely emitting this expected table.

Qualification precedes timing and compares every appended vocabulary vector with scalar R, plus the retained ordinary continuation where needed to check committed state. If the B1024 mapping reveals a new failure, retain it, resolve the responsible structural factor on development inputs, and freeze a new candidate without changing the oracle. Do not silently drop that row.

Default fixed diagnostic cost panel: eight cells x three paths x three paired blocks = 72 append measurements, each preceded by an equal same-arm warmup from the same canonical state. Fix balanced/rotated order before timing. Model loading, prefix generation and state restoration are excluded from the append interval and reported separately; this is append cost, not complete-request latency. Include actual planning, graph work, computation, necessary materialization and synchronization inside the append interval. Disable heavy observers and phase instrumentation during primary timing.

If Experiment A delivers a materially different candidate, add new-QB and new-WB symmetrically to this fixed matrix (120 measurements total); record that decision before the cost outputs. Do not enlarge the panel based on a timing sign. Report crossed and noncrossed cells separately, all blocks and both absolute and normalized costs. A diagnostic average over eight deliberately balanced coordinates is not a deployment-average speedup. The original aligned PR168 panel and its mixed session directions stay in the paper evidence.

## 5. Conditional natural confirmation, not an automatic large rerun

No new implementation: finish the diagnostic report and wait for B570 before deciding the final shared method and a broad evaluation. Do not rerun PR168's 64 costs for a different result.

Material implementation improvement: freeze its source, numerical mapping, context/reference, panel selection and cost order; then select four natural unseen Qwen8B inputs (two code, two math; varied feasible lengths) from authenticated existing pools, excluding earlier exposures. Keep C1536, native EOG/cap128, old k3, and the same registered caller width. First qualify full committed vectors against R and all candidate speculative branch vectors/transactions against the scalar k3 control. Failed qualification remains a reported counterexample; a repair needs a new frozen confirmation, not input replacement.

Default natural cost panel is four inputs x three arms (old QB4, new QB, new WB) x three sessions = 36 clean resident-service measurements with equal warmups. Freeze the arm set before outputs; no omitted alternative implementation chosen after measurement. If the development did not produce an eligible candidate, this phase is not run. Retain full service timing separately from profiler phases; include reset, both prefills where applicable, all draft/verify/reconciliation/sample work and synchronization, and report pool setup and model loading separately. Timed R and immutable numerical oracle remain distinct if R is later measured.

This small confirmation supports the changed implementation, not a population uncertainty claim or final TPDS evaluation completeness. No new 3% pass requirement is imposed. Improvement relative to old QB, and incremental new-QB versus equally improved WB, are separate estimates. Do not credit a common operator optimization only to local grouping.

## 6. Delivery and contribution decisions

Submit a separate RTX result PR stacked on this plan, without automatic merge or manuscript submission. Include compact reproducible source changes, source/operand identities, the operator table, eight-cell prediction-versus-observation table, clean costs and profiler cost attribution. Reuse existing evidence delivery; publish enough for the reported results without replaying every historical archive. Record exactly which checks were run on which host.

Interpret results as follows:

- A supported operator-specific mapping exposes wider/reorganized parallel work with lower full cost: integrate as a stronger runtime method, with its actual backend scope and equal treatment of WB.
- Local cuts help only at boundary-active coordinates: report a conditional benefit and its cut density; do not replace the neutral aligned workload evidence with a stress-only headline.
- WB matches or outperforms QB and no selective arithmetic improvement emerges: preserve that finding and consolidate with B570. Shared reference requirements may support multiple lowerings; QB need not be the universal winner.

Do not duplicate B570's ongoing d64/MHA study, force draft profitability, add a third device, change quantization/reference, or continue timing to cross the old pilot threshold. Final manuscript integration should wait for the B570 result; this independent RTX mechanism work need not.

## Source map

- [Reviewed results](../tpds_parallel/RESULTS.md), [protocol](../tpds_parallel/PROTOCOL.md), [cost records](../tpds_parallel/evidence/cost.json)
- [Actual lowering](../tpds_parallel/lowering.patch), [four-column projections](../tpds_parallel/wide_ops.py)
- [Physical WB-cut and diagnostic observation](../tpds_parallel/probe.cpp)
- [Service adaptation](../tpds_parallel/service_build.py), [natural oracle/qualification](../tpds_parallel/panel.py), [freeze and fixed execution](../tpds_parallel/study.py)
- [Artifact reconstruction implementation](../tpds_parallel/reproduce.py)
- Related-work boundary: https://arxiv.org/abs/2609.11356
