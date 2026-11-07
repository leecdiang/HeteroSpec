# Figure and typography review — 2026-11-01

## Scope and disposition

Editing input: the author-delivered 31-page `HeteroSpec_Revision_20261101.pdf` and its source ZIP. Repository ancestry: PR145 at `a97f97925e55ce29d8ce06a208c58b8e52664ad4`; added evidence remains pinned to RTX PR151 `29511ed91eb9f3d9773cfdda53e3554b0f4ad08b` and B570 PR152 `022babfabb3d1b6f4f2a2830dca04b2654d193f9`.

This pass reviews figure-to-claim fit, numerical encodings, reading order, grayscale redundancy, and TeX layout. It is one assistant's multi-pass editorial review, not multiple independent agents or external peer review. No experiments, references, estimator weights or scientific outcomes were changed.

## Initial review, before editing

| Figure | Judgment | Disposition |
|---|---|---|
| Main 1 / design | Directly distinguishes GS/PQ/QB and runtime obligations. Its schematic tiles are labelled as logical views. | Retain; no decorative redraw. |
| Main 2 / three-date scope | Shows draft value well, but the headline interaction is only a number in each title. Date identity is available only in the caption. | Redraw: add a separate interaction panel and on-figure date/range legend. |
| Main 3 / E2 sessions | Raw session marks and named bootstrap intervals answer the local-layout question. | Retain; do not substitute bars or new uncertainty. |
| Main 4 / operator correspondence | A discrete matrix is appropriate for counts of bitwise correspondence. | Retain all counts and q1-control explanation. |
| Main 5 / state composition | Endpoint categories and same-prefix continuous scores are correctly separated. | Retain; its additive prediction must remain distinct from observations. |
| Main 6 / producer matrix | All 48 cells are present, but tiny single-column labels hide the main fixed-reference switches. | Redraw full-width: keep every cell/order, highlight the two prealgebra rows, and explain their unchanged C1 reference in an adjacent panel. |
| Main 7 / mapping boundary | Qualification and missing qualified cost are categorical. | Retain the evidence table; a performance bar for a failed path would be misleading. |
| Supplement S1/S2 | Matched seven-arm and task contrasts preserve the complete historical comparison. | Retain, including negative draft results. |
| Supplement S3/S4 | Partition and state-cross schematics state their finite scope. | Retain. |
| Supplement S5 | Displays both PQ/R and QB/R, A/A and every measured block. | Retain; no attribution of total drafting benefit to QB. |

The full argument is visible across this figure set: method → repair economics → local correspondence → state/producer conditions → paid transaction. The new visuals improve access to already-supported conclusions; they do not introduce a new result.

## Applied changes

1. Figure 2 now has A/B same-scale draft-value panels and C for `Gamma=D_QB/D_GS`. Each of the three dates is an open circle/triangle/square; the equal-log-weight pooled value is a filled diamond. Horizontal segments show observed date ranges, explicitly not confidence intervals. All 24 original date/pooled draft-value marks remain; eight interaction date/pooled marks are added from the unchanged reconstruction.
2. Figure 6 retains the original eight-input order and all 48 strict-R cells. Shading identifies the two existing fixed-R switches. The adjacent summary explicitly uses each input's own R and includes KV plus initial logits. The arrow compares conditions, not a temporal repair procedure. GSM8K/1184 remains visible as a distinct case. `48 completed` is separated from `39 match R`.
3. Captions name what each panel encodes and keep the qualification, causal and statistical boundaries that affect interpretation.
4. The E2 absolute-cost table fills the column with normal-size type instead of leaving an uneven narrow table rule. The generator and its saved output agree.
5. One introduction sentence is shortened to avoid a one-line spill into the next page; the producer/consumer qualification claim is unchanged.
6. Bibliography uses ragged-right line setting and keeps each entry together, avoiding stretched spacing and a reference split across columns. The discovered 1.32pt vertical overflow was removed. Normal final-section white space is not filled with oversized leading or unrelated content.

## Final challenge pass

- Could a reader confuse interaction with profitable drafting? Separate panels and distinct axis definitions prevent this; Smol remains below draft parity.
- Could date ranges be mistaken for confidence intervals? The on-figure legend and caption both say otherwise.
- Were failure cells, inputs or outliers hidden? No. All matrix cells, all displayed dates and historical plots remain.
- Does panel B imply one common R for two different inputs? No; it states each input retains its own reference.
- Does the producer arrow imply an online recovery algorithm or KV-only causality? No; the caption explicitly denies temporal recovery and identifies both state components.
- Does the visual narrative require a new hardware or performance claim? No.
- Does the compact generated-summary serialization change reconstruction? No. The complete original reconstruction dictionary is equal to the previous implementation's dictionary; detailed source CSVs and executable checks remain. The redundant check-name list/static receipt is kept in the QA delivery rather than duplicated in the publication tree.

No unresolved visual/typographic blocker was identified in the inspected artifact. This judgment is not a guarantee of acceptance or a full native-data replication.

## Workflow provenance

K-Dense scientific-visualization v1.4, source blob `44ea38c24fb5015535254bfd9b5ae9a856195408`, was read and applied for honest encoding, raw-data preservation, redundant visual cues and actual-size inspection. Existing Humanizer and anti-defensive-writing editing remains intact; this pass changed captions and one equivalent sentence, not the scientific narrative. No AI-authorship detection claim is made.
