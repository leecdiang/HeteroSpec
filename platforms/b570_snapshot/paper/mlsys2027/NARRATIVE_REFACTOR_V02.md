# Narrative refactor v0.2

Baseline main: `1a11361f8526ec361e20dd6878d6e67352fb7bbd`, recorded before authoring on 2026-09-20. This includes merged manuscript PR #16 and independent figure-candidate PR #15. Work branch: `paper/mlsys2027-narrative-v0.2`.

## Author-directed hierarchy

The opening observation is variation in integrated speculative-decoding outcomes across the tested consumer workloads and stacks. The question is when favorable local indicators survive integrated execution. Correctness qualification and realized state-interface cost appear later as two measured failure mechanisms, not an exhaustive theory or a common explanation imposed on every platform.

The empirical headline is bounded: favorable local indicators do not reliably translate into gains **across the tested configurations**. It is not a measured population-wide failure probability, a benchmark of software portability, or an estimate with hardware/workload/runtime independently controlled. The timing boundary remains decode execution after initial prefill; “integrated” does not mean whole-request latency including loading and initial prefill.

The user's narrative direction supersedes the old handoff's top-level framing only. All scientific claims and qualifications in that handoff remain intact. The handoff itself has not been edited.

## Material changes

- Abstract and introduction now lead with the local-promise/integrated-outcome puzzle, including both M4 regimes and compact RTX/358H previews. The four contributions are characterization, verification-path diagnosis, stateful-integration diagnosis, and auditable measurement discipline.
- Section 2 asks the experimental question, then defines the contract, evidence classes, and accounting lens. The identity remains unchanged and is explicitly not novel. It is no longer the opening thesis or first figure.
- Section 3 retains frozen methodology, statistical estimators, provenance and energy boundaries. Evidence classes moved to Section 2 without reclassification.
- Section 4 presents the M4 contrast and cross-stack outcomes before diagnosing causes. Every prior speed/CI/exactness statement is retained, using the existing numeric macros and unchanged tables.
- Section 5 joins RTX/B570 verification-path controls and the complete 358H stateful diagnosis. The M4 contrast is explicitly not forced into either mechanism.
- Section 6 is a standalone hardware synthesis, with overlapping descriptive regimes rather than a universal taxonomy.
- Section 7 remains proposed design/results pending. Motivation now follows diagnosed failures; state persistence is a hypothesis, qualified verification is a requirement, and any optional profitability guard must account for its own overhead.
- Sections 8–10 align related-work positioning, limitations, and conclusion with the new hierarchy. No reference, scientific result, or novelty claim was added.

## Title considered after refactoring

The working title remains provisional: **Speculative Decoding Across Consumer Systems: Gains, Failures, and Runtime Costs**.

Other considered directions were **Speculative Decoding Across Consumer AI Systems** (too little indication of the observed puzzle) and **When Speculative-Decoding Gains Survive Consumer Runtime Stacks** (useful question, but can suggest a general predictive criterion the study does not establish). The chosen title describes observations and diagnosis without implying a completed intervention. The project name is omitted from the anonymous review PDF. No final submission title has been frozen.

## Final figure integration after the narrative checkpoint

The prose-only pass was checkpointed at `249c31c986da180bfae2e3f5881c300ae220edfa` before merging current main `575f7d3c2991bdf00915fa213a644cb9deeb0673`. The author's subsequent figure-integration instruction supersedes the checkpoint's temporary figure selection. Four selected publication PDFs now appear in the main paper, with the evidence inventory in the separate appendix. Asset filenames are unchanged; appearance order determines manuscript numbering.

| Final number | Selected asset | Narrative role |
|---|---|---|
| 1 | `figure1.pdf` | Opening empirical puzzle |
| 2 | `figure3.pdf` | M4 contrast from two separate frozen studies |
| 3 | `figure2.pdf` | Correctness-path diagnosis |
| 4 | `figure4.pdf` | Isolated-versus-realized stateful diagnosis |
| A1 | `figure5.pdf` | Appendix evidence inventory, non-exhaustive and non-ranking |

The entire selected figure tree remains byte-identical to integration main. The old accounting schematic remains an unused historical source; equations and definitions remain in Section 2. Captions preserve the supplied qualifications and use semantic references. Exact source commits, placement and native-size checks, caption changes and layout decisions are recorded in `NARRATIVE_FIGURE_INTEGRATION.md`.

Table order now follows the argument: platforms (Table 1), headline outcomes (Table 2), mechanism (Table 3). Table cells and captions are unchanged. The appendix's two tables are unchanged.

## Current placement map for the frozen ledger

The authoritative ledger and its original v0.1 placement map are preserved byte-for-byte. This table supersedes **only the old location references**, never the claim records, exact values, classes, estimators, source commits, or caveats.

| Frozen claim IDs | v0.2 placement |
|---|---|
| M4-24, M4-HE | Abstract; introduction; Section 4.1; Figures 1–2; Table 2; appendix energy |
| M4-MICRO, RTX-MICRO, B570-FAST, B570-SERIAL | Section 5.1; Figure 3; Table 3 |
| RTX-DIVERGENCE | Section 5.1 numerical capture |
| RTX-cpu_k2, RTX-rtx_k2 | Section 4.2; Table 2; qualification in Section 5.1 |
| 358H-CPU, 358H-NPU | Abstract/introduction; Sections 4.2 and 5.2; Figures 1 and 4; Table 2; Figure A1; appendix accounting |
| 358H-ISOLATED | Section 5.2; Figure 4 |
| *-PROTOCOL | Sections 2–3; Table 1; appendix |
| M4-SECONDARY, M4-HE, B570-SERIAL | Section 4 energy qualifications; appendix energy |

## Manual wording review

- M4 is described as workload-conditioned **observed** regimes. Session differences remain explicit; workload-only causality and unified-memory causality are not claimed.
- RTX refers to **RTX 5070 Ti Laptop**. Its fast CUDA path is blocked on the frozen scope; serialized controls remain secondary. The diagnosis is not a backend defect or universal numerical law.
- B570 fast and serialized paths remain diagnostic. Serialization improves agreement but does not guarantee exactness; formal failure and the stop rule remain the platform result.
- 358H retains both exact negative outcomes, direct committed work, CPU target-side dominance, NPU inseparable replay-plus-proposal dominance, tiny residual, no Phase-3 energy claim, and STRONGLY_SUPPORTED source qualification. Isolated NPU statements concern median throughput, not statistical superiority at every context or intrinsic compute weakness.
- The identity remains an accounting lens. Target-forward proxies are not complete target cost; accepted drafts are not complete committed output. Arithmetic decomposition remains distinct from prompt-GM speedup.
- “First-token cost” in the state figure is a timing boundary, not a novelty claim. “Proves correctness” occurs only in an explicit denial of universal proof for the proposed registry. No new firstness claim is made.
- No measured runtime intervention, universal predictor, exhaustive causal explanation, hardware ranking, common energy ranking, or whole-request latency result is claimed.

Remaining editorial decisions are the final title/abstract and the runtime decision. Figure selection and integration are complete. No unresolved factual or causal wording defect was identified in this pass. These editorial choices do not prevent the hardware paper from standing alone.

## Validation records

- `evidence/NARRATIVE_V02_BASELINE.json`: main HEAD and hashes recorded before editing.
- `evidence/NUMERICAL_QA.json`: original 228 comparisons rerun; identical results and byte-identical report.
- `evidence/NARRATIVE_V02_QA.json`: immutable scientific files, selected publication-figure tree, table/coordinate values, complete prior numeric-macro coverage, and change-scope check.
- `evidence/NARRATIVE_FIGURE_INTEGRATION_BASELINE.json`: merged main, figure source, narrative checkpoint and selected-tree hashes.
- `evidence/NARRATIVE_FIGURE_QA.json`: five independent figure checks and actual PDF insertion widths/locations.
- `evidence/PDF_QA.json`: current compiled artifacts, anonymity, fonts, references, page counts and runtime-removed build.
- `MANUSCRIPT_STATUS.md`: final page allocation and visual inspection record. Historical v0.1 status is retained separately.
