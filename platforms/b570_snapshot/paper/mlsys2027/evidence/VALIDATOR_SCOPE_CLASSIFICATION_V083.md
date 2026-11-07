# Phase-4 Validator Scope Classification — v0.8.3

Original validator: `paper/mlsys2027/scripts/validate_claim_calibration_v083.py` at Phase-4 output `d3ae7067fc5ff285d87238f8c48a7104ebfb349d`. Its baseline is Phase-4 input `3b6d7eee8888f96c71835b0b15eb1c7cb074a038`. The original validator is unchanged. The table classifies every assertion in its `main()`; repeated label loops are expanded below.

| Check | Class | Rationale |
|---|---|---|
| Formal title string | Current-state scientific invariant | The intended title continues to identify the qualified study; “unchanged” in the old message refers to the Phase-4 title decision, not a byte comparison. |
| Abstract: `72/72` | Current-state scientific invariant | The frozen predictor/live result remains central. |
| Abstract: `complete generated-token-ID sequences` | Current-state scientific invariant | Specifies the actual equality endpoint. |
| Abstract: `24 reserved prompts` | Current-state scientific invariant | Bounds the held-out result. |
| Abstract: `tested B570 stack` | Current-state scientific invariant | Prevents cross-stack generalization. |
| Abstract: `frozen before reserved live outcomes` | Current-state scientific invariant | Preserves prospective chronology. |
| Abstract: `reference-divergent trajectories` | Current-state scientific invariant | Explains why prediction is informative despite blocked reference qualification. |
| Abstract: `target-partition sufficiency` | Current-state scientific invariant | States the supported mechanism level. |
| Abstract distinguishes sufficient path from unique numerical cause; rejects root-cause/universal-rule language | Current-state scientific invariant | Prediction does not isolate a unique numerical operation or universal rule. |
| Exactly three numbered headline contributions | Current-state scientific invariant | Keeps the promised contribution count. |
| Contribution content/order: direct-ID qualification, frozen B570 prediction, realized 358H cost | Current-state scientific invariant | Keeps the central evidence sequence. |
| Introduction order: frozen direct-ID studies, case-study scope, contributions | Current-state scientific invariant | Preserves first-page interpretation. |
| Separately frozen case studies, no matched hardware ranking | Current-state scientific invariant | Prevents unsupported cross-hardware comparison. |
| Section 5 controlled B570 target-partition sufficiency heading; no “mechanism isolation” | Current-state scientific invariant | Prevents an unqualified causal claim. |
| Abstract B570 headline uses predictive/sufficiency language | Current-state scientific invariant | Maintains bounded claim. |
| Introduction B570 headline uses predictive/sufficiency language | Current-state scientific invariant | Maintains bounded claim. |
| Section 5 B570 headline uses predictive/sufficiency language | Current-state scientific invariant | Maintains bounded claim. |
| Synthesis B570 headline uses predictive/sufficiency language | Current-state scientific invariant | Maintains bounded claim. |
| Conclusion B570 headline uses predictive/sufficiency language | Current-state scientific invariant | Maintains bounded claim. |
| Section 5 tested configuration and synthesis/conclusion tested stack | Current-state scientific invariant | Keeps platform scope explicit. |
| Conclusion: 72/72 predictor/live complete IDs and no unique numerical cause | Current-state scientific invariant | Keeps result and causal limit together. |
| Limitations: one B570 platform/model pair/runtime/build, greedy k=2, HumanEval, 24 reserved prompts | Current-state scientific invariant | Keeps study scope visible. |
| Related Work byte-identical to Phase-4 input | Checkpoint-local scope check | Related Work editing was forbidden during Phase 4 and explicitly authorized in Phase 5. |
| Bibliography byte-identical to Phase-4 input | Checkpoint-local scope check | Proves Phase 4 did not add/change citations; later authorization must be judged separately. |
| `tables/values.tex` byte-identical to Phase-4 input | Checkpoint-local scope check | Proves Phase 4 did not edit frozen numeric source. |
| `tables/runtime_values.tex` byte-identical to Phase-4 input | Checkpoint-local scope check | Same Phase-4 edit perimeter. |
| `tables/direct_id_values.tex` byte-identical to Phase-4 input | Checkpoint-local scope check | Same Phase-4 edit perimeter. |
| `figures/03_verification.tex` byte-identical to Phase-4 input | Checkpoint-local scope check | Proves Phase 4 did not alter Figure 3 source. |
| Figure 3 `presentation_v07/plot.py` byte-identical to Phase-4 input | Checkpoint-local scope check | Proves Phase 4 did not alter plot generation. |
| Figure 3 PDF byte-identical to Phase-4 input | Checkpoint-local scope check | Proves Phase 4 did not alter the plotted artifact. |
| Figure 3 SVG byte-identical to Phase-4 input | Checkpoint-local scope check | Same Phase-4 edit perimeter. |
| Phase-4 preview exists and has 12 pages | Checkpoint-local artifact check | Verifies the Phase-4 build at its checkpoint; it is not a live manuscript invariant. |
| Phase-4 preview renders frozen RTX/B570 counts; Section 5 says four prompts | Mixed: checkpoint-local preview, current-state scientific counts | The archived preview belongs to Phase 4. The counts and informative-prompt statement remain scientific invariants and are covered by current Phase-1/3 checks. |

Current-state validation runs the surviving scientific claims in `validate_current_scientific_invariants_v083.py` plus the independent Phase-1, Phase-2, Phase-3, Phase-5, and Figure 3 validators. Historical Phase-4 scope is authenticated through `PHASE4_CHECKPOINT_VALIDATION_V083.json`; the original validator is never applied to the later authorized Related Work text.
