# Mechanism figure review v0.5

Exact stacked base: `paper/mlsys2027-figure-style-v0.4` at `974e84540b5193b416e20920629260ff320f759d`.

**Select Candidate B as PUBLICATION-CANDIDATE.** Candidate A is a scientifically valid, empirically anchored alternative. There are exactly two layouts; the root `mechanism.pdf`, `mechanism.svg`, and `mechanism.tex` are byte-identical copies of B, not a third design.

## Scientific question and role

How can favorable local indicators fail to translate into qualified integrated post-prefill decode gain in the tested configurations? The figure organizes two bounded diagnoses: correctness qualification removes a cheap path in the RTX case and remains unsatisfied by B570 diagnostics; the measured state interface erases the isolated 358H NPU drafting advantage. M4 is a separate outcome contrast, not an example assigned to either diagnosis. This is an explanatory schematic of measurement boundaries, not a universal performance theory or hardware ranking.

Later placement: after the opening paragraph of Section 5, before the correctness diagnosis. Suggested future label: `fig:translation`. This task changes neither manuscript prose, wrappers, numbering, nor existing figures. The recommendation to remove the prior overview remains an editorial decision for later integration.

## A versus B

| Criterion | A: evidence anchors | B: minimal alternative |
|---|---|---|
| Scientific precision | Explicit RTX range, bounded B570 count, isolated/realized NPU values, M4 point estimates. Additional caption preserves CIs, estimators, and denominator. | Same stages, gate, accounting, timing, and bounded diagnoses. Numeric detail is delegated to the existing evidence figures and the retained evidence ledger. |
| Narrative usefulness | Can stand alone as an empirical reminder. | Focuses the reader on the two diagnoses at the start of Section 5. |
| Visual restraint | Four short evidence lines under each relevant stage; still a scientific schematic, but denser. | Two or three text lines per relevant stage; the conceptual flow dominates. |
| Native-size readability | Pass at 6.75 in; numeric anchors require sustained reading. | Pass at 6.75 in; fewer competing details. |
| Redundancy | Repeats values already visible in the M4, verification, and 358H data figures. | Names those cases without replaying their quantitative results. |
| Decision | Retain as alternative; not selected. | **PUBLICATION-CANDIDATE**. |

Both resemble a scientific systems-paper schematic rather than a slide or infographic: Times-compatible typography, only two thin boundary boxes, small normal arrows, no title inside artwork, no card backgrounds, no vendor colors, no logos, and no common quantitative scale. The single muted-blue mark indicates the admissible continuation. A filled mark and solid continuation contrast with a gray open endpoint and dashed blocked branch; text labels preserve the distinction in grayscale.

A is not rejected for numerical weakness or illegibility. Its anchors remain subordinate in the artwork. B wins for this specific manuscript placement because the surrounding figures already establish the numerical evidence, and retaining A's numbers responsibly adds substantial caption context. More data does not improve this figure's particular job.

## Measured page footprint

| Layout | Nominal width | Artwork height | Artwork area | Height with proposed caption | Area with caption |
|---|---:|---:|---:|---:|---:|
| A | 6.75 in | 2.40 in | 16.20 in² | 4.45 in | 30.02 in² |
| B | 6.75 in | 2.10 in | 14.17 in² | 3.54 in | 23.89 in² |

B saves 0.30 in of artwork height and approximately 0.91 in including the proposed caption (about 20% of the captioned block). This is a physical block comparison, not a prediction of manuscript pagination. A's caption is longer because its point estimates need uncertainty, estimator and denominator context. Proofs use 9-pt captions and no figure number; final float spacing is not included. TeX's fixed-point output measures width as 6.7499165 in, within 0.0001 in of the 6.75-in specification. Exact dimensions are in `mechanism_v05/qa/page_cost.json`.

## Scientific wording constrained by evidence

- The minimal RTX callout was narrowed to **RTX batched**, avoiding a suggestion that all tested RTX paths fail. The exact serialized secondary controls remain qualified; their micro range is independently rechecked in the audit.
- B570's legacy `V2_exact` source key is never a publication-facing label. A says **60/90 exact; globally inadmissible**; B and its caption retain qualification failure and the insufficient effect of serialization.
- The NPU statement is **isolated advantage lost at the measured state interface**, not intrinsic NPU compute weakness. Replay and proposal remain one timed call; no replay-only number or measured state-persistence intervention is claimed.
- M4 remains **separate Metal studies; opposite observed outcomes; neither diagnosis assigned**. The caption explicitly retains differing workload/session conditions.
- No `S = C/(D+R+X)` equation is added to the artwork: the four accounting terms identify existing measurement boundaries, with costs and output progress separated by a thin rule. No new model or sufficient-condition claim is introduced.
- The optional CPU 358H numeric anchor is omitted for space, not contradicted or reclassified. Its 0.734× speedup and 87.34% complete target-side fraction were independently confirmed in the evidence audit.

No new discrepancy changes an experimental number or classification. These are scope safeguards, not changes to the closed scientific results.

## QA and reproducibility

Both layouts pass separate source/number validation and native-size color/grayscale inspection. PDFs contain only vector graphics and embedded fonts; SVGs contain vector glyph outlines and no images. Main labels are 8–9.2 TeX pt; mathematical subscripts/superscripts are approximately 5.98 PDF pt. Lines are 0.45 bp; arrowheads are 3 bp. No overfull TeX boxes, clipped text, text/mark overlap or color-only status distinction remains. The sparse blank space below local indicators is intentional: no local indicator is given an invented common scale or cross-platform causal assignment.

Native 96- and 180-dpi color/grayscale PNGs, independent SVG raster previews, and caption proofs were inspected. The PDFs preserve 100% physical scale; no physical printer test or final manuscript pagination is claimed. Print without fit-to-page scaling.

Files: [candidate index and reproduction](mechanism_v05/README.md), [scientific validation](MECHANISM_FIGURE_VALIDATION.md), [A proof](mechanism_v05/qa/proof_a.pdf), [B proof](mechanism_v05/qa/proof_b.pdf), [proposed captions](mechanism_v05/CAPTION_SUGGESTIONS.md).
