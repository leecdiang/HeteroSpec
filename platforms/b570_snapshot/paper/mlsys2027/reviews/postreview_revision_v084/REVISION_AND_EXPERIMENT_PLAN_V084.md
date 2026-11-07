# v0.8.4 post-review revision and experiment boundary

Base: merged PR #39 (`f8290281156f6b3de8fbc8b44fd10a4afa7bcd89`). This is a manuscript, presentation, and existing-array audit revision. It adds no model run, hardware measurement, or new numerical inference.

## Implemented without new experiments

| Review item | Revision |
| --- | --- |
| CR-01, P1 | Every headline 72/72 is identified as 24 reserved prompts with three repeat-stable runs. The four reference-divergent prompts (12 runs) and same-set UB128/live 60/72 appear on the first page and in the replacement Figure 2. The 72/72 execution endpoint is retained. |
| CR-02, P1 | A separate anonymous ZIP contains the existing 72 reference, frozen-predictor, and live complete ID arrays with full array digests and a deterministic verifier. The paper states that the sanitized export cannot reproduce the original file digest or independently establish its pre-live timestamp. The recorded chronology and content digest keep distinct roles. |
| CR-03, P1 | Predictive target-partition sufficiency is scoped to the tested B570 stack and capped generated-ID endpoint. No unique numerical cause, history-controlled live-loop intervention, or cross-backend transfer is claimed. |
| CR-07, P1 | Table 2 separates historical text-path outcomes from 358H direct-ID rows, explicitly distinguishes the historical B570 60/90 from the fresh B570 fast direct-ID 60/90, and states that the fresh gates have no matched latency. Figure 3 and §5.1 reiterate this boundary. |
| CR-04, CR-09, CR-10 | The 128-ID/EOG endpoint and all-cap reserved outputs are explicit; 358H's 58.35% NPU region remains inseparable reconstruction/replay plus proposal; M4 Guard is presented beside fixed Always-Spec and its slower post-study paired secondary result. |
| CR-11, CR-12, CR-13, CR-14 | The prospective full-trajectory test is contrasted with batch-shape observations; the generic Figure 2 is replaced by the B570 discovery/freeze/reserved comparison; the M4 session caveat and Figure 3 shape key remain visible; Table 2 class labels are expanded. Appendix Table A4 is retained to preserve its evidence-class distinctions. |

## Verification

- Independent extraction of the 41-member anonymous source ZIP: SHA-256 manifest passes, both PDFs build with `latexmk -pdf`, 12 manuscript pages (10 body + 2 references) and 8 appendix pages.
- No overfull boxes or unresolved references/citations in the final logs; all pages rendered and visually inspected. PDF metadata names anonymous authors.
- Independent extraction of the sequence ZIP: `python3 verify.py` passes for 24 tasks, 72/72 predictor/live, 60/72 reference/live, four divergent tasks, and 12/12 first-divergence indices. No raw host paths, repository metadata, absolute timestamps, or prompt contents are included.
- The protected frozen numerical macro files remain untouched. The new PDF and ZIP files have distinct v0.8.4 names; earlier outputs remain intact.

## New experiments, only if a broader result is desired

These are separate prospective studies. None is needed to maintain the narrow v0.8.4 within-stack claim, and none should be described as already completed.

1. **Independent transfer (CR-05; highest significance value).** Select a genuinely different backend or model before outcomes. Fix tokenizer, reference path, exact generated-ID endpoint, greedy settings, discovery/reserved split, repetitions, and all-or-nothing sequence-equality gate. Use exposed discovery only to choose a predictor, then freeze the full predicted arrays and a timestamped, independently inspectable commitment before live reserved runs. Publish all reference/predicted/live arrays, full hashes, task-level counts, reference-divergent cases, and failures. Report results by distinct prompt and by repetition. A failure limits transfer; a success on reference-equal prompts alone gives little discrimination.
2. **Causal B570 partition discrimination (CR-06).** On the four known divergent prompts and an independent reserved set, compare UB1 versus UB128 target logits and IDs at identical committed prefixes with identical preceding target history. If technically feasible, intervene on only the live speculative target partition while holding proposal stream and rollback/history fixed. Prespecify which token-level transition and complete-sequence outputs count as restoration. Record all compared prefixes, logits/IDs, and state controls. Keep this new causal endpoint separate from the archived 72/72 prediction. H2 was not run in the archived study; testing it now requires a separate frozen protocol.
3. **Matched latency after fresh qualification (CR-08).** On the prospectively qualified RTX serialized direct-ID path, freeze hardware/runtime/driver, prompt set, target-only reference, timer boundary, order randomization, repetitions, and analysis before timing. Reconfirm the 90/90 ID gate on that same path, then measure paired post-prefill latency and bootstrap by prompt. State both the cost and any gain; do not attach historical RTX timing ratios to the new gate.
4. **Optional 358H persistent-state test.** Implement a state-capable draft path and qualify complete direct-ID equality first. Only a passing configuration should enter a timed, paired persistent-versus-reconstruction study. The existing 58.35% NPU region cannot be subtracted as replay-only savings.

Before anonymous submission, upload the manuscript PDF, appendix PDF, and **separate sequence ZIP** as three distinct artifacts. The source ZIP is for reproducible editing/building; the sequence ZIP is the reviewer-facing array audit.
