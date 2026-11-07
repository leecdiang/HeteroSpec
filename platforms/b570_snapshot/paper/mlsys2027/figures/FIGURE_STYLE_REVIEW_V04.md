# Scientific figure style review v0.4

Exact base: `paper/mlsys2027-narrative-v0.2` at `afda6a192f3e9359eb5f5d7d24d3313bf59ef2f3`.

This is a presentation refactor of already validated science. No experiment, estimator, CI, classification, measurement boundary, source pointer, manuscript prose, or manuscript figure wrapper is changed. Existing assets and source/provenance records remain intact. All proposed replacements live in `style_v04/`.

## Decisions

| Current role | Decision | Candidate / rationale |
|---|---|---|
| Figure 1 overview | **REMOVE FROM MAIN** | The introduction already states all four cases. A restrained figure and a smaller booktabs alternative are supplied, but neither adds a distinct graphical comparison. Removal is recommended, not applied. |
| M4 forest plot (`figure3` asset) | **RESTYLE** | Minimal two-row forest, one parity line, thin original CIs, compact labels; exactness and numerical intervals remain in the unchanged source caption. |
| Verification (`figure2` asset) | **RESTYLE** | Conventional horizontal cells/ranges, execution-path y labels, one 1× line and short monochrome status annotations. No duplicate endpoint table inside artwork. |
| 358H (`figure4` asset) | **RESTYLE** | Retain two panels, original CIs and absolute component widths; replace baseline stub with a valid shared vertical reference, simplify annotations. |
| Appendix inventory (`figure5` asset) | **REPLACE WITH TABLE** | Booktabs inventory preserves all eight cases, evidence classes, exactness, classifications and two displayed mechanism percentages. Appendix-only. |

Asset IDs are preserved for provenance; they are not a proposed renumbering of manuscript floats.

## Figure 1: A versus B, including page cost

A is a monochrome, table-like vector figure with column labels and thin rules. It has no internal headline, arrows, colored prose, bold outcomes or explanatory footer. It preserves all four local indicators, the three qualified speedups, exact counts and blocked/negative/profitable distinctions. Heterogeneous indicators retain their units and have no common quantitative axis.

B recommends removing the overview float and using the current introduction plus the detailed evidence figures. `sections/01_introduction.tex` already summarizes the M4 positive/negative outcomes, RTX qualification failure and 358H NPU result. The detailed figures retain the quantitative evidence. Therefore removal need not add another paragraph. An optional short replacement paragraph and a genuine LaTeX booktabs table are supplied for editorial choice; neither is inserted into the manuscript.

Measured physical footprints, including the same inherited overview caption for the current figure, A and the table:

| Option | Width | Artwork/body height | Height including caption | Area including caption |
|---|---:|---:|---:|---:|
| Current overview | 6.75 in | 3.63 in | 4.93 in | 33.28 in² |
| A: restrained table-like figure | 6.75 in | 1.60 in | 2.90 in | 19.58 in² |
| B: optional booktabs table | 6.75 in | 1.11 in | 2.41 in | 16.26 in² |
| B: optional replacement prose | 3.25 in | 1.69 in | 1.69 in | 5.49 in² |
| B: remove float, reuse existing introduction | — | 0 incremental | 0 incremental | 0 incremental |

These are measured blocks, not predicted final page counts. They use the same 9-pt caption convention; float spacing and page breaks depend on the manuscript integration. Full precision is in `style_v04/qa/page_cost.json`. The prose alternative includes the four indicators/outcomes and their measurement limits and refers readers to detailed uncertainty; it is a replacement option, not an additional paragraph to append to the current introduction.

Scientific clarity favors removal: neither A nor the table provides an interpretable shared axis, a new contrast or extra evidence beyond the introduction and detailed figures. A remains useful if a visual overview is editorially required. If exact overview lookup must remain, the booktabs table is more compact and signals honestly that this is categorical tabulation. Redesigning it as a common hardware plot would be misleading. The removal recommendation is not a claim that A is numerically or scientifically wrong.

## M4 forest plot

The same two estimates and original asymmetric CIs remain at the same numeric positions. The internal title, direct numeric labels and exactness labels leave the artwork; the source caption already contains 0.842× [0.809, 0.877], 1.387× [1.351, 1.422], 72/72 and 90/90, the preregistration scope, and the separate-study caveat. Two compact y labels and one dashed 1× line carry the visual comparison. This reduces artwork from 2.40 to 1.55 in at single-column width without replacing uncertainty with prose. No between-workload paired comparison or workload-only causality is implied.

## Verification plot

Execution paths are ordinary y-axis categories. All eleven context cells and the same range endpoints remain plotted. Filled/open marks encode qualification, circle/square marks encode fast versus serialized execution, and solid/dashed segments reinforce status. Annotation text stays black. The 1× line is a reference in baseline target-decode units, not profitability parity. Both B570 rows explicitly remain diagnostic and inadmissible; RTX serialization remains an exact secondary control.

Removed endpoint labels and per-row context paragraphs duplicated the neighboring manuscript table. The caption handoff preserves the context sets, overlapping-cell caveat, range-not-CI meaning and `V_2^micro != complete R_target` boundary. Ranges still span tested contexts; no CI or matched cross-platform comparison is invented. Artwork height is 2.12 in, down from 3.58 in.

## 358H two-panel plot

Panel (a) uses black CPU circles and muted-blue NPU diamonds with the original six medians and CIs. Small horizontal offsets separate device marks at each categorical context; the caption discloses this purely visual offset. Panel (b) retains the original stacked arithmetic-mean seconds and the true residual widths, including the subpixel residuals. Replay plus proposal is muted blue, complete target work is light gray with hatch, and residual is dark gray.

The vertical dashed baseline is valid: the frozen CPU and NPU rows have the identical 9.577611905555555 s arithmetic-mean baseline and the same post-prefill timing boundary. It is drawn at that exact coordinate, labeled 9.58 s, and never used to recompute the distinct prompt-GM speedups. Total times and prompt-GM headlines remain above the bars. Detailed component percentages, residual milliseconds and headline speedup CIs move to the caption handoff. Replay and proposal remain inseparable. Initial prefill remains excluded. Artwork height falls from 3.75 to 2.65 in.

## Appendix inventory

A conventional booktabs table provides clearer lookup than categorical boxes or a sparse infographic matrix. Each of the eight cases has explicit qualification, outcome, evidence class and the same case annotation. The two RTX serialized controls remain grouped and secondary; both B570 paths remain globally inadmissible diagnostics. The 358H rows retain P/M and the original 87.34% target-side / 58.35% replay-plus-proposal labels. The table remains appendix-only and makes no new causal taxonomy. Its body is 2.23 in high, compared with 4.10 in for the current artwork.

## Style and validation

The palette is ink `#222222`, one accent `#4C6E9E`, mid gray `#777777`, light gray `#D9DDE2` and rule gray `#D0D3D6`. Prose labels remain monochrome. No gradients, shadows, decorative arrows, dashboard headlines or color-only status distinctions remain. Matplotlib exports use embedded STIX TrueType fonts; LaTeX tables use embedded Times-compatible fonts. SVGs use vector glyph outlines.

All seven candidates have PDF and SVG exports. Independent validation reads the frozen CSVs without importing rendering helpers, checks coordinates and CI endpoints read back from actual artists, checks actual component widths and baseline position, inspects compiled table text, and verifies output hashes, vector-only content, embedded fonts and text bounds. Twenty-seven input/provenance/manuscript files are byte-locked against the exact base. All six plotting tables pass scoped completeness/uniqueness checks. No statistical estimate is recalculated and no experiment is replayed.

Color and grayscale were inspected at 3.25/6.75-in native widths using 96/180-dpi renders; captioned proofs were also inspected. Corrections included preventing the baseline from crossing the CPU annotation, eliminating an awkward table word break and adding a 1-pt LaTeX inset to prevent a superscript touching the cropped PDF boundary. All candidates pass within this reviewed scope. Final manuscript pagination and wrapper integration are deliberately not claimed.

## Review artifacts

- [Current/style comparison](style_v04/qa/STYLE_COMPARISON.pdf)
- [Native-width candidates with caption handoff](style_v04/qa/STYLE_PROOF.pdf)
- [Candidate files and reproduction](style_v04/README.md)
- [Caption handoff](style_v04/CAPTION_HANDOFF.md)
- [Independent validation](style_v04/qa/validation.json)
- [Frozen input lock](style_v04/frozen_inputs.json)
- [Output manifest](style_v04/STYLE_MANIFEST.json)

The manuscript owner can select A, the booktabs table or removal after review. This branch does not apply any of those prose/wrapper changes and does not merge automatically.
