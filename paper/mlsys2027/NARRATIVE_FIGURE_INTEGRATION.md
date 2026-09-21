# Narrative v0.2 — selected publication-figure integration

Completed 2026-09-21 on `paper/mlsys2027-narrative-v0.2`. This record supersedes the temporary figure selection at the prose-only checkpoint. Scientific claims, estimators, evidence classes, timing boundaries and uncertainty are unchanged.

## Source sequence

1. Narrative baseline: `1a11361f8526ec361e20dd6878d6e67352fb7bbd`.
2. Coherent prose checkpoint: `249c31c986da180bfae2e3f5881c300ae220edfa`.
3. Fetched main used for integration: `575f7d3c2991bdf00915fa213a644cb9deeb0673` (PR #17), containing publication-figure source `6cf4924a796ce12ef9c52cb4ef0527cff0937702`; ancestry of both required commits was verified.
4. Main merged into the manuscript branch without resetting narrative edits: `37d2f32dfe6fc180d1c0856f049ec2f10ca22ac8`.
5. Selected assets integrated through manuscript wrappers, followed by build, evidence validation and visual review.

Authoritative guidance: `figures/FIGURE_REVIEW.md`, `FIGURE_MANIFEST.md`, `FIGURE_CAPTION_SUGGESTIONS.md`, `integration/FIGURE_INTEGRATION.md`, and `integration/selected_figures.tex`. The selected figure tree remains byte-identical to integration main. No quantitative figure was regenerated.

## Final order and dimensions

| Manuscript number | Semantic label | Immutable asset | Actual page | Native size (inches) |
|---|---|---|---|---|
| 1 | `fig:overview` | `figures/pdf/figure1.pdf` | main 2 | 6.75 × 3.63 |
| 2 | `fig:m4` | `figures/pdf/figure3.pdf` | main 4 | 3.25 × 2.40 |
| 3 | `fig:verification` | `figures/pdf/figure2.pdf` | main 6 | 6.75 × 3.58 |
| 4 | `fig:state` | `figures/pdf/figure4.pdf` | main 7 | 6.75 × 3.75 |
| A1 | `fig:regimes` | `figures/pdf/figure5.pdf` | appendix 3 only | 6.75 × 4.10 |

The M4 figure precedes the two diagnoses because results precede explanations in the new narrative. Asset filename numbers therefore differ from manuscript numbers for M4 and verification. All active prose and captions use semantic references. The fixed overview artwork's “Figures 2–4” range remains correct because those three figures supply its detailed evidence. No stale `fig:framework` reference survives in active sources or the compiled paper. Its historical, unused source is retained; accounting equations remain in Section 2.

The main hardware synthesis no longer inserts or refers to a main-text regime figure. It summarizes observed regimes in prose and points to the separate appendix inventory. Appendix Section F introduces Figure A1 as descriptive evidence, not an exhaustive taxonomy.

## Caption changes from the supplied integration kit

No scientific qualification was removed or relocated to save space.

- Overview: expanded the shared-path M4 caveat to say explicitly that the micro values were not independently measured in each workload. Added that the 8,192-token isolated NPU example is contextualized by all three contexts in the state figure. Replaced the literal figure-number range with semantic references.
- M4: retained the supplied caption verbatim, including both exact CI endpoints, independent-study/session qualification, paired within-study estimator and token-equality versus pass@k distinction.
- Verification: replaced the potentially misleading phrase “excludes complete realized target-side work” with “is not complete realized target-side cost.” This preserves the intended proxy-versus-complete-cost distinction without suggesting disjoint timing regions. Context ranges remain explicitly not CIs; RTX secondary and B570 diagnostic/global inadmissibility qualifications remain.
- State: made the timer limitation explicit: replay and proposal share one timed OpenVINO call, and replay-only time is not measured. Replaced the literal verification-figure number with its semantic label. All isolated-throughput versus post-prefill timing, arithmetic-mean versus prompt-GM, exactness and non-intrinsic-NPU qualifications remain.
- Appendix inventory: retained the supplied caption verbatim, including diagnostic/secondary status, non-exhaustiveness and no hardware ordering.

## Layout and visual review

Final main PDF: **10 main pages + 1 reference page**. Separate appendix: **3 pages**. The official style, page geometry, text sizes and spacing are unchanged. The runtime reservation spans approximately 1.5 pages across main pp. 8–9.

The actual PDF transformation matrices confirm 3.25-inch M4 width and 6.750135-inch wide figures, the latter differing from 6.75 only through normal TeX point conversion. No figure was scaled below its validated size. Normal top floats are used; the state wrapper is queued at the preceding paragraph boundary to keep its float with the state diagnosis on p. 7. Appendix A1 has a dedicated, vertically centered float page with spare space above and below. No caption is split from its figure or clipped.

All 11 main pages and all 3 appendix pages were rendered and visually inspected after the final build. Checks covered ordering, references, captions, columns, whitespace, equations, tables, section transitions and bibliography. The hardware-only build was also rendered, with its changed final pages inspected. Scratch renders are local verification material, not review artifacts.

## Scientific and artifact QA

- The unchanged original numerical validator passed **228/228** checks after integration. Its numerical report remains byte-identical to the baseline.
- The five figure validators independently replayed original timing cells, the two M4 campaign bootstraps, isolated-throughput summaries, Phase-3 prompt bootstrap/decomposition and categorical evidence inventory. All passed. Existing limitations are preserved: raw token arrays were not replayed; Phase-1 reciprocal TPOT replay corroborates summaries where separate raw throughput arrays are unavailable.
- All five asset hashes, native dimensions, current placements and actual insertion widths were checked. Source locks were checked across 40 records; the historical `WRITING_STATUS.md` entry is verified at the locked revision because that narrative document is intentionally updated here. Scientific data/source records are checked against working-tree bytes.
- Narrative checks passed for 89 protected file entries, all 57 prior prose numeric macros, allowed edit scope, unchanged ledger/tables and the selected figure tree. Counts can overlap and do not represent unique experiments.
- Both output PDFs match their checked build bytes. Font embedding is checked recursively through figure resources, including Type 0 descendant fonts. Anonymous text/metadata/links, complete authors for all 13 references, main-page boundaries, and resolved references passed. No overfull boxes remain. The official style's harmless empty-anchor warning remains.
- Manual scientific review confirmed: overview is not a ranking; verification is a target-forward proxy and ranges span contexts; M4 is not a paired between-workload causal experiment; state bars cannot derive prompt-GM headlines and cannot isolate replay; A1 is not exhaustive. No new unsupported causal claim was identified.

Detailed machine-readable records: `evidence/NARRATIVE_FIGURE_INTEGRATION_BASELINE.json`, `NARRATIVE_FIGURE_QA.json`, `NARRATIVE_V02_QA.json`, and `PDF_QA.json`. The historical scientific ledger is untouched; `NARRATIVE_REFACTOR_V02.md` supplies its current location crosswalk.

## Runtime removal and delivery boundary

The runtime section remains proposed design only, with implementation and results pending. Its removal produces **9 main pages + 1 reference page** without unresolved references. The opening observation, M4 contrast, two measured diagnoses and independent hardware conclusion remain coherent. Title/abstract and the final runtime decision remain editorially open; figure integration is complete.

Delivery is one Draft PR for review. Do not merge automatically, submit, upload to arXiv, or change private visibility. Only the two final output PDFs are anonymous review artifacts; internal provenance notes are not.
