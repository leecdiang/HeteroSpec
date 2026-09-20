# Actual figure comparison and narrative selection — v0.3

Base: `1a11361f8526ec361e20dd6878d6e67352fb7bbd`. Branch: `paper/mlsys2027-figures-v0.3`. This review supersedes the provisional v0.2 recommendations. Experiments are closed; no experiment was rerun. No manuscript prose, figure wrapper, or scientific source was changed.

The main sequence establishes an observation before diagnosing two measured failures of translation from local opportunity to realized gain. Correctness and state-interface cost are bounded diagnoses, not a universal thesis or exhaustive theory. M4 workload dependence remains a first-class observation.

## Actual decisions

| Role | OLD manuscript source | Decision | Selected placement |
|---|---|---|---|
| 1 · empirical puzzle | `01_framework.tex` | **REDESIGN BOTH** | Main, 6.75 in. Replace both accounting-first designs with a categorical local-measurement/outcome overview. |
| 2 · correctness diagnosis | `03_verification.tex` | **TAKE NEW** | Main, 6.75 in. Retain v0.2 path rows, explicit context and qualification, redundant status encoding. |
| 3 · same-platform contrast | `02_m4.tex` | **HYBRID** | Main, 3.25 in. OLD forest-plot economy plus NEW exact estimates, intervals and exactness counts; height reduced from 2.90 to 2.40 in. |
| 4 · stateful integration | `04_358h.tex` | **TAKE NEW** | Main, 6.75 in. Both versions already use absolute time; NEW adds baseline, totals, CIs and separately labeled prompt-GM speedups. |
| 5 · regime inventory | `05_regimes.tex` | **TAKE NEW — APPENDIX** | Appendix A1, 6.75 in. Keep the complete inventory; remove it from the recommended main sequence to avoid duplicating Figure 1. Asset ID remains `figure5` for provenance. |

Four main figures are recommended, not five. Synthesis is carried by the Figure 4 caption and optional appendix inventory; no extra diagram is needed merely to preserve the previous count.

## Comparison protocol and evidence

[OLD_NEW_COMPARISON.pdf](comparison/OLD_NEW_COMPARISON.pdf) contains ten pages: OLD versus committed v0.2 candidate, then OLD versus selected v0.3 asset, for each figure. Every pair has the same physical width, independently verified from the placed PDF forms. Print at 100%, without fitting to the proof page.

[OLD_NATIVE_WIDTH.pdf](comparison/OLD_NATIVE_WIDTH.pdf) preserves the five OLD artworks at their actual checkpoint widths. OLD Figures 1 and 5 were single-column; the equal-width comparison enlarges them by 2.077× to the proposed double-column width. This is labeled explicitly and is not presented as their original typography.

OLD is an exact vector crop of the committed `manuscript/output/manuscript-v0.1.pdf`, not a recreation from pixels. Crop coordinates, source pages, filenames and hashes are in [comparison_lock.json](comparison/comparison_lock.json). Captions were read directly from TeX and assessed below; artwork crops omit captions. The checked-in template sets text width 6.75 in and column gap 0.25 in, giving 3.25 in per column. Numeric TeX filename prefixes differ from actual manuscript numbering; the role mapping above follows the compiled PDF.

Color and grayscale were inspected at final physical sizes. [comparison_validation.json](qa/comparison_validation.json) reconciles OLD/NEW source numbers: M4 estimates/CIs and 358H values agree at full precision; all eleven micro cells agree to the OLD source precision (B570 fast uses four decimals). No correction to the closed scientific results is proposed.

## Figure 1 — REDESIGN BOTH

OLD is the more compact accounting explanation: its single-column gate, denominator and dashed proxy box are clear. The prior candidate adds definitions and a failed-gate branch, at a greater vertical cost. Neither establishes the new empirical story.

The replacement uses four annotated categorical cases. M4's shared-path micro evidence is explicitly from a separate study; it is not presented as measured separately on HumanEval and 24Q. Both M4 outcomes appear. RTX has no admissible speedup value. The NPU row contrasts isolated tok/s with a separately qualified speedup without equating their units. Figures 2–4 carry uncertainty and detailed conditions. Accounting remains in the untouched framework subsection; a second main accounting diagram is unnecessary.

Tradeoff: the overview takes double-column space and repeats selected outcomes. It earns that space by presenting the puzzle before its diagnoses; moving the full regime inventory to the appendix prevents a second overview in the main paper.

## Figure 2 — TAKE NEW

OLD is compact (about 2.14 in high, excluding caption), already uses open/filled markers, and correctly warns in its caption about unmatched contexts and the incomplete proxy. Those strengths are retained. Its nearby cells overlap, serialized paths have no distinct shape, and B570 serialized qualification depends heavily on caption/table lookup.

NEW uses 3.58 in of height to show context, numeric range and status on each row. Filled/open markers, circle/square shapes and solid/dashed range segments remain distinct in grayscale. Ranges span contexts, not confidence intervals. B570 60/90 remains visibly inadmissible; RTX serialization is labeled an exact secondary control. The added height is justified by a self-contained correctness diagnosis. Neither version establishes a hardware ranking or full target-side cost.

## Figure 3 — HYBRID

OLD already has the right forest plot and clear 1× reference. Its compactness is valuable. The prior candidate adds exact counts and direct numerical intervals but expands to 2.90 in. The selected hybrid reduces height to 2.40 in, retains those useful annotations and moves the token-equality/pass@k caveat from the artwork into the caption. The simple forest structure, single quantitative axis and clear 1× line are preserved; heavy grid lines are unnecessary.

The revised caption asks whether the tested platform/runtime exposes opposite regimes. It does not imply a statistically paired between-workload comparison or workload-only causality. Workloads and session conditions differ; both frozen campaigns remain primary evidence.

## Figure 4 — TAKE NEW

Actual OLD inspection resolves the previous uncertainty: OLD already uses absolute stacked times. It does not hide total-duration differences with 100% normalization. Its connected throughput points show the widening median device gap, and its two panels are compact (about 2.72 in high).

NEW is selected for its explicit 13.25 s / 27.54 s totals, 9.58 s baseline and separately labeled 0.734× / 0.352× prompt-GM headlines. Isolated CIs and exactness counts are explicit. CPU/NPU marker shapes and component hatching survive grayscale. NEW costs 3.75 in of height; this central mechanism merits that information density.

The bars are arithmetic mean post-prefill seconds/request, not whole-request latency. Their ratios must not reconstruct prompt-GM headlines. Replay and proposal share one timer. Tiny residuals retain their true width and are labeled in milliseconds, not enlarged. The evidence supports the measured state-interface diagnosis, not an intrinsic NPU defect or an unmeasured persistent-state remedy.

## Figure 5 / appendix A1 — TAKE NEW

OLD's four boxes are readable in one column, but categories overlap (NPU appears twice), B570 serialized appears only in the caption, and mechanisms and outcome regimes are mixed. NEW separates correctness/profitability categorically, retains evidence classes, and includes both B570 diagnostic paths.

With the new Figure 1, this inventory is unnecessary in the main sequence. Select it only for the appendix. Mechanism rows organize tested cases; they are not an exhaustive taxonomy, continuous correctness score, or newly established causal mechanism. An empty cell is not evidence of impossibility.

## Claims to bound during subsequent prose integration

1. Lead with the tested failure of favorable local indicators to translate robustly into realized gain. Two diagnosed mechanisms do not establish a universal or exhaustive theory.
2. Describe opposite regimes in two separate M4 studies, without workload-only causality or unified-memory attribution.
3. Scope correctness blocking to the frozen RTX/B570 paths and workloads; do not generalize to all CUDA/Vulkan implementations.
4. Attribute the NPU cost to measured replay plus proposal in the current OpenVINO interface. Replay-only time and a state-persistent intervention are unmeasured.
5. Qualify E2E as post-prefill decode under the campaign boundary. Whole-request latency and energy gains are not established.

## Integration boundary

This branch supplies selected assets, caption suggestions, a figure-only inclusion file, comparison proofs and validated provenance. It does not silently substitute a new concept for `fig:framework`: existing prose refers to accounting. The manuscript owner must relocate the overview and reconcile old framework/regime references during the narrative rewrite. [Integration notes](integration/FIGURE_INTEGRATION.md) identify the locations. No automatic merge is performed.
