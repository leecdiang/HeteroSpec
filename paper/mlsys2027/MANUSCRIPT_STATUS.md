# Manuscript v0.2 — narrative and selected publication figures

Completed: 2026-09-21. Branch: `paper/mlsys2027-narrative-v0.2`.

The narrative pass started from main `1a11361f8526ec361e20dd6878d6e67352fb7bbd` and was checkpointed at `249c31c986da180bfae2e3f5881c300ae220edfa`. Current main `575f7d3c2991bdf00915fa213a644cb9deeb0673`, including publication-figure source `6cf4924a796ce12ef9c52cb4ef0527cff0937702`, was then merged at `37d2f32dfe6fc180d1c0856f049ec2f10ca22ac8`. No narrative work was discarded. The two `NARRATIVE_*BASELINE.json` evidence records preserve those phases and their protected hashes. Use `git rev-parse HEAD` for the delivery revision.

## Narrative and deliverables

Working title, still provisional: **Speculative Decoding Across Consumer Systems: Gains, Failures, and Runtime Costs**.

The paper begins with variation in integrated gains across the tested consumer workloads and stacks, asks why favorable local indicators fail to translate reliably, then diagnoses correctness-path and state-interface failures. These are bounded measured mechanisms, not an exhaustive theory. M4's observed workload-conditioned contrast stands independently of those mechanisms.

- `manuscript/output/manuscript-v0.2.pdf`: **10 main-text pages + 1 reference page**.
- `manuscript/output/appendix-v0.2.pdf`: **3 separate appendix pages**.
- `manuscript/README.md`: reproducible build and review boundaries.
- `NARRATIVE_REFACTOR_V02.md`: material narrative changes, title alternatives, claim-placement crosswalk and causal-wording review.
- `NARRATIVE_FIGURE_INTEGRATION.md`: final asset selection, captions, placement, validation and layout decisions.

The official submission style and all its hashes remain unchanged. No margin, type-size, spacing, or geometry adjustment was made. Both review PDFs are anonymous. Title, abstract, and final paper conclusion remain provisional; the hardware conclusion is complete. Historical v0.1 completion details and PDFs remain unchanged.

## Section and page allocation

Ranges include floats and are not additive. The runtime section retains approximately 1.5 pages of text across pp. 8–9 within the reserved 1.5–2-page planning budget. The main body reaches the ten-page ceiling.

| Section | Current compiled location |
|---|---|
| 1. Introduction | pp. 1–2 |
| 2. Experimental question and measurement discipline | pp. 2–3 |
| 3. Experimental methodology and platforms | pp. 3–4 |
| 4. Gains do not translate uniformly | pp. 4–5 |
| 5. Why favorable local indicators fail | pp. 5–7 |
| 6. Hardware-study synthesis | p. 8 |
| 7. Runtime co-design from measured failure modes | pp. 8–9 |
| 8. Related work | pp. 9–10 |
| 9. Limitations | p. 10 |
| 10. Conclusion | p. 10 |
| References, excluded from main-page budget | p. 11 |
| Appendix, separate artifact | 3 pages |

## Figure and table status

| Final number | Selected asset | Role and placement | Width |
|---|---|---|---|
| Figure 1 | `figure1.pdf` | Empirical overview, main p. 2 | 6.75 in |
| Figure 2 | `figure3.pdf` | M4 observed contrast, main p. 4 | 3.25 in |
| Figure 3 | `figure2.pdf` | Correctness-path diagnosis, main p. 6 | 6.75 in |
| Figure 4 | `figure4.pdf` | Isolated versus realized stateful cost, main p. 7 | 6.75 in |
| Figure A1 | `figure5.pdf` | Evidence inventory, appendix p. 3 only | 6.75 in |

All five selected vector PDFs under `paper/mlsys2027/figures/pdf/` are byte-identical to integration main. No figure was regenerated. Native widths are preserved (the wide figures differ by only normal TeX unit rounding). All active references use semantic labels and resolve to the final order. No stale accounting-diagram reference remains. Its unchanged historical source is unused; equations and definitions remain in Section 2.

Normal LaTeX floats are used. The state figure is queued at the preceding paragraph boundary so it stays on the state-diagnosis page rather than drifting into the runtime section. Appendix A1 occupies a dedicated, vertically centered float page with spare space above and below. These layout choices preserve validated figure and caption readability without shrinking text or changing the template.

Three main tables cover platforms, headline outcomes, and verification mechanisms. Two appendix tables cover frozen statistical policies and sensor boundaries. All table values and captions, numeric macros, and historical plot-coordinate files are byte-identical to the narrative baseline. No energy ranking was added.

## Evidence and wording checks

- **228/228 existing numerical checks rerun after integration and passed**, using the unchanged validator. The numerical report is byte-identical to the baseline.
- All five figure-specific independent numerical checks pass, including frozen bootstrap conventions and source rows. `NARRATIVE_FIGURE_QA.json` records their scope and limitations; no experiment or raw token-array replay was performed.
- The frozen evidence ledger, machine-readable exact values, source provenance, datasets, estimators, correctness/evidence classes, preregistration status and closeout claims are unchanged.
- Additional narrative checks pass for **89 protected file entries**, every one of the **57 prior prose numeric macros**, and the change scope. Some files are counted by multiple checks; this is not a count of unique datasets.
- The selected figure tree remains unchanged relative to integration main. Its source lock includes one historical narrative document, `WRITING_STATUS.md`; that entry is checked against the locked main revision, while scientific source files are checked against actual working-tree bytes.
- The ledger's historical v0.1 location map is preserved. Its current crosswalk is in `NARRATIVE_REFACTOR_V02.md`.
- All 13 bibliography entries and complete author lists are unchanged. No new source or citation gap was introduced.
- Manual wording review retained shared-path M4 micro evidence, session uncertainty, bounded CUDA divergence, B570 diagnostic status, the distinction between context ranges and CIs, complete target-side costs, inseparable replay-plus-proposal, and the absence of a measured runtime intervention. “Integrated” remains post-prefill decode execution, not whole-request user latency. No universal or exhaustive explanation is claimed.

No unresolved factual or causal wording defect was identified. Remaining editorial decisions are the final title/abstract and the runtime decision; figure selection and integration are complete.

## Runtime reservation and hardware-only coherence

Section 7 visibly states **proposed design only; implementation and measured results pending**. Its requirements follow diagnosed failures: draft-state persistence and reconciliation, correctness-qualified verification, and an optional profitability guard whose overhead must be measured. No implementation, speed, energy, correctness, or ablation result was added.

`make hardware-only` removes Section 7 and produces **9 main pages + 1 reference page**, with no undefined references. The observation-to-diagnosis argument, independent hardware synthesis, related work, limitations and conclusion remain coherent. This local verification PDF is not a separate delivery artifact.

## Final PDF review

Both delivered PDFs compile successfully and match the checked build bytes. Automated checks confirm anonymous metadata/text/links, embedded Type 1 and Type 0 fonts (including nested figure resources), complete reference authors, page counts, and no overfull boxes or undefined references/citations. The RTX identity check accepts line wrapping before “Laptop” while requiring the full hardware identity. The official style's harmless empty-anchor warning remains.

All **11 main-PDF pages and 3 appendix pages** were rendered at 1,400 pixels on the long edge and visually inspected after final integration. Text, equations, tables, figure labels, captions, references and section transitions are legible and unclipped. All ten hardware-only pages were rendered at 1,100 pixels; pages 7–10 covering the state figure, hardware synthesis, related work, limitations, conclusion and references were inspected (earlier content matches the main PDF). Final artifact hashes are in `evidence/PDF_QA.json`.

This work opens one Draft PR. It does not rerun experiments, merge the PR, submit, upload to arXiv, or change repository visibility. Internal provenance files are not anonymous review artifacts.
