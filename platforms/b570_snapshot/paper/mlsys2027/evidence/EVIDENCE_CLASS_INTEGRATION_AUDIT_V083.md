# Evidence-Class Integration — Phase 3

## Canonical vocabulary

- Historical (H): **historical text-path agreement**. Parsed CLI output, with campaign-specific normalization or re-tokenization, is the recorded comparator. It is not direct generated-ID evidence.
- Fresh qualification (Q): **direct-ID sequence equality** against each frozen reference, with **QUALIFIED** or **BLOCKED** gate status.
- Mechanism prediction (P): **predictor-to-live complete-ID agreement**. The B570 72/72 result validates a frozen prediction. Its separate reference-to-live qualification result is 60/72, **BLOCKED**.

## Main manuscript changes

- Added a compact H/Q/P key in Framework and tightened the methodology, outcomes, diagnoses, runtime, and conclusion language around the distinct endpoints.
- Table 2 now has separate Endpoint and Pairs columns: five historical M4/RTX/B570 rows say Text-path; both 358H rows say Direct-ID. Historical timing remains scoped to its recorded comparator.
- The M4 runtime table names direct-ID sequence equality. Prospective M4 Guard is explicitly separated from historical M4 text-path results.
- The fresh RTX/B570 90/90 gate remains an output qualification only; no matching fresh latency endpoint is claimed.

## Appendix changes

- A3 uses historical text-path status throughout. A4 uses a generated row overlay with six historical Text-path rows and two 358H Direct-ID rows. The protected style table remains byte-for-byte unchanged, and the overlay generator checks numeric row tokens and order.
- A5 labels the direct-ID endpoint, pair counts, and gate per row. B570 reserved prediction prose and ledger maintain predictor/live 72/72 versus reference/live 60/72 BLOCKED.
- The original 24-prompt ledger values, content digest, and chronology remain unchanged. Phase 1 and Phase 2 validators pass.

## Figure 3 changes

Panel A visibly says “Historical target-forward proxy” and “Different runs / contexts.” Panel B says “Fresh direct-ID qualification” and “No matching fresh latency endpoint.” The caption states that the panels are not a matched cost–qualification experiment and that fresh qualification does not authorize historical timing. Only labels changed; numerical content, all 11 historical cells, all four fresh qualification conditions, marker coordinates, axes, and panel membership are unchanged. Independent Figure 3 validation passes 71 checks, including actual vector markers, labels, native dimensions, and font embedding.

## Numerical invariants

**PASS.** Historical speedup/value macros and source data are unchanged. Frozen fresh RTX values are 75/90 and 90/90; B570 values are 60/90 and 78/90. B570 reserved values remain 72/72 predictor/live, 60/72 reference/live, 24/24 prompt classifications, 12/12 divergent first indices, and four divergent prompts. The 358H timing macros and M4 Guard/Always values are unchanged. The A4 overlay generator independently confirms identical row numeric tokens. The Figure 3 validator confirms original plotted values and coordinates.

## Validator

**PASS.** `scripts/validate_evidence_classes_v083.py` checks active table row labels, class distinctions, B570 72/72 and 60/72 semantics, 358H and prospective M4 direct-ID labels, Figure 3 source/rendered labels, known frozen counts, PDF ambiguity patterns, and main page count. Phase 1 ledger, Phase 2 appendix, Figure 3, and full figure integration checks also pass.

## Build and visual QA

**PASS.** Clean-directory main and appendix builds succeeded. Main: 10 body pages plus 2 reference pages. Appendix: 8 pages. No overfull boxes or unresolved references/citations were reported. All pages were rendered and visually inspected; Table 2, Figure 3, Section 4/5, A3/A4/A5, and the B570 ledger are readable without clipping. A4 column widths were adjusted for its endpoint labels; no margin, font, or template-spacing change was made.

## CR-05 status

**ADDRESSED.** A reviewer can identify the historical text path, fresh direct-ID gate, and frozen B570 predictor/live endpoint directly from active rows and Figure 3, with the comparator boundary stated in text and captions.

## CR-16 status

**IMPROVED.** The Figure 3 panels now state their different evidence classes and explicitly rule out a matched cost–qualification reading. Numerical and visual encodings are unchanged.

## Deferred reviewer issues

CR-03 cross-backend transfer; CR-04 sufficiency versus unique cause; CR-09 first-page significance; CR-10 Related Work novelty; CR-11 M4 Guard positioning; CR-12 358H boundary; CR-14 timeline visualization; CR-15 Figure 2 density; CR-18 Figure 4 labels; Table 1 hardware scope. Phase 4 was not started.

## Scientific integrity

No new inference, no new performance data, no new experiment, no historical evidence upgrade, and no closed evidence modification. Protected `benchmarks/`, `artifacts/`, `reports/`, and `analysis/` trees have no Phase 3 diff.
