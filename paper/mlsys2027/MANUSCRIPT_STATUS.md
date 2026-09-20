# Manuscript v0.1 — hardware-complete / runtime-reserved

Completed: 2026-09-20. Branch: `paper/mlsys2027-manuscript-v0.1`.

Baseline: `62d1c134b096882c37ce58c1d0ac140236acd9c3` (current main when construction began). Baseline date, recent merged PRs, and authoritative input hashes are in `evidence/BASELINE.json`. The scientific control document `PAPER_FRAMEWORK_HANDOFF.md` and frozen experiment evidence are unchanged. Use `git rev-parse HEAD` for the complete delivery revision; the PR contains the logical construction commits.

## Deliverables and format

- Main: `manuscript/output/manuscript-v0.1.pdf`, **9 main-text pages + 1 reference page**.
- Separate appendix: `manuscript/output/appendix-v0.1.pdf`, **2 pages**.
- Source and build instructions: `manuscript/README.md`.
- Official submission package: unchanged MLSys package linked by the 2027 Research Track CFP, preserved with its ZIP, source URL and SHA-256 manifest in `manuscript/vendor/`.
- Anonymous review format, two columns, complete bibliography author lists. No margin, type-size, spacing, column-geometry, or style-internal changes.
- Title and abstract are explicitly provisional. Section 5.5 is the stable hardware-study conclusion; Section 9 remains provisional pending the software decision.

## Section allocation

The planning budget totals ten pages; the compiled body currently occupies nine. Page ranges include intervening floats and are not additive. The runtime text occupies approximately 1.5 pages of column area across pages 6–8; hardware Figures 4–5 occupy substantial space on page 7. No measurements are implied by the reserved space.

| Section | Ten-page planning allocation | Current compiled location |
|---|---:|---|
| 1. Introduction, including title/abstract overhead | 0.85 | p. 1 |
| 2. Correctness contract and realized-cost accounting | 1.05 | p. 2 |
| 3. Experimental methodology and evidence classes | 1.25 | pp. 2–3 |
| 4. Correctness changes the usable execution path | 1.10 | pp. 3–4 |
| 5. Hardware results and stable synthesis | 2.40 | pp. 5–6; associated Figures 4–5 on p. 7 |
| 6. Runtime co-design, proposed/results pending | 1.75 | pp. 6–8 |
| 7. Related work | 0.70 | pp. 8–9 |
| 8. Limitations | 0.65 | p. 9 |
| 9. Provisional final conclusion | 0.25 | p. 9 |
| References, outside main-page budget | excluded | p. 10 |
| Appendix, separate artifact | excluded | 2 pages |

## Figures and tables

All five figures are native vector sources. Figure order follows first use, so admissibility precedes the M4 contrast.

| Figure | Scientific question | Source |
|---|---|---|
| 1 | What must be counted after the correctness gate? | `figures/01_framework.tex` |
| 2 | How does correctness change usable verification paths? | `figures/03_verification.tex` |
| 3 | Is the positive M4 result representative? | `figures/02_m4.tex` |
| 4 | Why does isolated NPU throughput not survive integration on 358H? | `figures/04_358h.tex` |
| 5 | Which regimes survive the evidence distinctions? | `figures/05_regimes.tex` |

Main tables: Table 1 platform/model/runtime/backend/evidence scope (contract in caption); Table 2 verification/admissibility mechanisms; Table 3 speedup/CI/exactness/faster-prompt/evidence-class headlines. Appendix Table 1 records frozen estimators and bootstrap conventions; Appendix Table 2 separates sensor boundaries and allowed energy claims. There is no global energy ranking. Internal evidence pointers accompany the generated tables and claim ledger.

## Evidence and citation status

`evidence/MANUSCRIPT_EVIDENCE_LEDGER.md` contains 17 grouped claim records, including exact quantitative values and settings, estimators, correctness status, evidence class, report/analysis/script/archive pointers, source commits, hashes, and caveats. `published_values.json` drives numeric macros and figure coordinates. Headline numbers have evidence entries.

`evidence/NUMERICAL_QA.json`: **228 comparisons passed**, including independent reconstruction of headline estimators, campaign-specific bootstrap conventions, token equality, energy boundaries, direct 358H round accounting, source hashes and official-style hashes. Frozen B570 insertion order and differing bootstrap endpoint conventions are preserved. Arithmetic accounting ratios are explicitly distinguished from prompt-geometric-mean headline speedups.

`evidence/LITERATURE_AUDIT.md`: **13 references**, inspected primary publications/preprints or official publication pages, complete author lists (including all 58 HumanEval authors). Two historical titles were updated to the inspected current versions with their identity changes documented. No unresolved citation-identity or cited-mechanism gap was found. This targeted positioning is not an exhaustive literature review or a claim of firstness.

No unresolved numerical contradiction or unsupported scientific wording was found in the final pass. Remaining editorial decisions are the provisional title/abstract, final contribution list and conclusion after the software decision, and author review of positioning. The known evidence qualifications remain explicit: M4 workload dependence and unexecuted corrected ceiling; secondary RTX serialized controls and bounded numerical divergence; diagnostic B570 fallback; 358H STRONGLY_SUPPORTED source reconstruction and inseparable replay-plus-proposal cost; distinct energy boundaries and weaker Windows raw per-run provenance.

## Runtime section and independent hardware story

Section 6 visibly states **proposed design only; implementation and measured results pending**. It contains measured requirements, a minimal request-scoped persistent-state/checkpoint/reconcile interface proposal, correctness-qualified path selection, an optional realized-cost profitability guard, and prospective evaluation questions. Adaptive width and device selection are deferred. There are no fabricated implementation claims, latency/speedup/energy values, correctness results, or ablations.

The hardware story is independently coherent. `make hardware-only` removes Section 6 and produces an **8-main-page + 1-reference-page** verification PDF, with no undefined references. The introduction, all four platform results, stable synthesis, related-work positioning, limitations and conclusion remain present. This alternate build is a local coherence check, not an additional submission deliverable.

## Final quality control

`evidence/PDF_QA.json` records final deliverable hashes, PDF metadata, font inventory, page count, section starts, bibliography checks, and the alternate-build result. Both delivered PDFs use embedded Type 1 fonts. There are no overfull boxes, undefined citations/references, usernames, identifying repository links, local paths, institutional identities, or acknowledgments in the review PDFs. The anonymous institution/contact placeholders and review notice are supplied by the unchanged official style; no submission has occurred.

Final PDFs were rendered after all manuscript edits. All ten main-PDF pages and both appendix pages were visually inspected at 110 dpi on 2026-09-20: text, mathematical notation, plot marks and axes, table cells, captions, references and page boundaries are legible and unclipped. The alternate hardware-only build was also rendered; its synthesis/related-work transition, conclusion and references were inspected. The final page of its body has spare space, which is acceptable for this internal removal check.

Manual forbidden-word review found two benign matches: “proves correctness” occurs only in an explicit denial of universal proof in the proposed registry paragraph; “first-token cost” is a measurement boundary in Figure 4. No forbidden firstness, universal CUDA failure, weak-NPU explanation, or unified-memory causal claim remains.

Repository visibility remains private. This work opens one draft PR only; it does not merge, publish, upload to arXiv, or submit to MLSys. Internal evidence files retain private provenance and are not anonymous review artifacts.
