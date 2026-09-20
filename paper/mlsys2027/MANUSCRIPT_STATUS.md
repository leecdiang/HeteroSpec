# Manuscript v0.2 — narrative refactor / hardware-complete / runtime-reserved

Completed: 2026-09-20. Branch: `paper/mlsys2027-narrative-v0.2`.

Baseline main: `1a11361f8526ec361e20dd6878d6e67352fb7bbd`. This includes manuscript v0.1 and independently audited publication-figure candidates. `evidence/NARRATIVE_V02_BASELINE.json` records the baseline and protected hashes before editing. Historical completion details remain in `MANUSCRIPT_V01_STATUS.md` and the unchanged v0.1 PDFs. Use `git rev-parse HEAD` for the delivery revision.

## Narrative and deliverables

Working title, still provisional: **Speculative Decoding Across Consumer Systems: Gains, Failures, and Runtime Costs**.

The paper now begins with variation in integrated gains across the tested consumer workloads and stacks, asks why favorable local indicators fail to translate reliably, then diagnoses correctness-path and state-interface failures. These are bounded measured mechanisms, not an exhaustive theory. M4's observed workload-conditioned contrast stands independently of those mechanisms.

- `manuscript/output/manuscript-v0.2.pdf`: **9 main-text pages + 1 reference page**.
- `manuscript/output/appendix-v0.2.pdf`: **2 separate appendix pages**.
- `manuscript/README.md`: reproducible build and review boundaries.
- `NARRATIVE_REFACTOR_V02.md`: changes, title alternatives, figure coordination, updated claim-placement map and manual causal-wording review.

The official submission style and all its hashes remain unchanged. No margin, type-size, spacing, or geometry adjustment was made. Both review PDFs are anonymous. Title, abstract, and final paper conclusion remain provisional; the hardware conclusion is complete.

## Section and page allocation

Ranges include floats and are not additive. The runtime section retains approximately 1.5 pages of text across pp. 6–8 within the reserved 1.5–2-page planning budget. Hardware figures occupy substantial space on p. 7. The complete main body remains below the ten-page ceiling.

| Section | Current compiled location |
|---|---|
| 1. Introduction | pp. 1–2 |
| 2. Experimental question and measurement discipline | p. 2 |
| 3. Experimental methodology and platforms | p. 3 |
| 4. Gains do not translate uniformly | p. 4, final line on p. 5 |
| 5. Why favorable local indicators fail | pp. 5–6; state figure on p. 7 |
| 6. Hardware-study synthesis | p. 6; regime figure on p. 7 |
| 7. Runtime co-design from measured failure modes | pp. 6–8 |
| 8. Related work | p. 9 |
| 9. Limitations | p. 9 |
| 10. Conclusion | p. 9 |
| References, excluded from main-page budget | p. 10 |
| Appendix, separate artifact | 2 pages |

## Figure and table status

Four existing vector manuscript figures are included: M4 observed contrast (Figure 1), correctness-path diagnosis (Figure 2), 358H isolated versus realized cost (Figure 3), and descriptive regime synthesis (Figure 4). The old accounting schematic remains an unchanged, unused source; definitions and equations remain in Section 2. Independent candidate figures under `paper/mlsys2027/figures/` have not been edited or substituted. Final visual selection belongs to the separate figure Work; this pass coordinates roles and adjusts two captions only.

Three main tables cover platforms, headline outcomes, and verification mechanisms, respectively. Two appendix tables cover frozen statistical policies and sensor boundaries. All table values and captions, numeric macros, and plot coordinate files are byte-identical to the baseline. No energy ranking was added.

## Evidence and wording checks

- **228/228 existing numerical checks rerun and passed** using the unchanged validator. The numerical report is byte-identical to the baseline.
- The frozen evidence ledger, machine-readable exact values, source provenance, datasets, estimators, correctness/evidence classes, preregistration status and closeout claims are unchanged.
- Additional narrative checks pass for **71 protected file entries**, every one of the **57 prior prose numeric macros**, and the change scope. This count includes a few files covered by both hash and asset checks; it is not a count of unique experimental datasets.
- The ledger's historical v0.1 location map is preserved with the authoritative records. Its v0.2 location crosswalk is in `NARRATIVE_REFACTOR_V02.md`.
- All 13 bibliography entries and complete author lists are unchanged. No new source or citation gap was introduced by the refactor.
- Manual causal-wording review retained M4 session uncertainty, bounded CUDA divergence, B570 diagnostic status, complete target-side costs, inseparable replay-plus-proposal, and the absence of a measured runtime intervention. “Integrated” remains post-prefill decode execution, not whole-request user latency. No universal or exhaustive explanation is claimed.

No unresolved factual or causal wording defect was identified. Remaining editorial decisions are the final title/abstract, figure selection in the separate figure Work, and the runtime decision. Detailed dispositions of the two benign forbidden-word search matches are recorded in the narrative note.

## Runtime reservation and hardware-only coherence

Section 7 visibly states **proposed design only; implementation and measured results pending**. Its requirements follow diagnosed failures: draft-state persistence and reconciliation, correctness-qualified verification, and an optional profitability guard whose overhead must be measured. No implementation, speed, energy, correctness, or ablation result was added.

`make hardware-only` removes Section 7 and produces **8 main pages + 1 reference page** with no undefined references. The observation-to-diagnosis argument, independent hardware synthesis, related work, limitations and conclusion remain coherent. This local verification PDF is not a separate delivery artifact.

## Final PDF review

Both delivered PDFs compile successfully and match the checked build bytes. Automated checks confirm anonymous metadata/text/links, embedded Type 1 fonts, complete reference authors, page count, and absence of overfull boxes or undefined references/citations. A line-wrap false positive in the old RTX identity check was fixed to accept whitespace before “Laptop”; the full hardware identity is still required. The official style's harmless empty-anchor warning remains.

After the final prose edits, all ten main-PDF pages and both appendix pages were rendered at 1,400 pixels on the long edge and visually inspected. Text, equations, tables, figure labels, captions, references and section transitions are legible and unclipped. The hardware-only PDF was rendered at 1,100 pixels; the hardware-synthesis/related-work transition, figures, limitations and conclusion were inspected. Its final main page has spare space, appropriate for an internal removal check. Final artifact hashes are in `evidence/PDF_QA.json`.

This work opens one Draft PR. It does not rerun experiments, merge, submit, upload to arXiv, or change repository visibility. Internal provenance files are not anonymous review artifacts.
