# Current handover — v0.8.7 candidate; RTX V4 integrated

Updated 2026-10-02. This is the living control file for current state and scope. Historical manifests, handovers and stopping rules retain their original delivery context.

## 1. Repository state

Candidate branch: `paper/mlsys2027-rtx-integration-v0.8.7`, based directly on main `87b811e21a164468232cfea3c2404a1ebc869477`. v0.8.7 is pending merge. Baseline main contains v0.8.6 via #46, V3 terminal history via #48, V4 completed evidence via #49, and independent raw closeout via #50. The earlier #45 stacked merge was resolved by #46; the new candidate must target main.

The v086 delivery remains `494a5ca4fe62534b032b37d01652c3f88e0d16e1`; authoritative TeX source `da8d5739eb108de7f35d3a3cfbd954d42462f2e0`. Scientific author-freeze tag `mlsys2027-v0.8-author-freeze` still peels to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. See [DELIVERY_V087.md](evidence/DELIVERY_V087.md) for the candidate content identity and PR; do not confuse that fixed anchor with a moving branch tip. No author-machine checkout state is inferred.

## 2. Paper thesis and exact artifacts

Qualification → prospective trajectory prediction → supporting intervention/program reproduction → realized cost/runtime decisions. Original B570 draft-free target-only UB1 prediction remains central: 72/72 complete trajectories on 24×3 reserved runs, including all 12 runs on four reference-divergent prompts. Reference/live 60/72 remains BLOCKED. Predicting a trajectory does not make it lossless-compatible.

RTX V4 adds the same-set UB2/replay comparison and matched qualification–cost. These distinguish specified candidates, not all possible predictors or necessary/minimal state. Main is [10+2 pages](manuscript/output/manuscript-v0.8.7.pdf); the [appendix](manuscript/output/appendix-v0.8.7.pdf) is 14 pages. [Source ZIP](manuscript/output/overleaf-rtx-integration-v0.8.7.zip), [anonymous evidence index](manuscript/output/anonymous-evidence-index-v0.8.7.zip), [manifest](evidence/FINAL_ARTIFACT_MANIFEST_V087.json), [build instructions](manuscript/README.md) and [claim/campaign map](reviews/rtx_integration_v087/CLAIM_AND_CAMPAIGN_MAP_V087.md) identify the fixed delivery. Internal hardware-only proof is 9+2, not a submission manuscript.

## 3. Closed evidence ledger


| Study | Retained result | Interpretation boundary |
|---|---|---|
| B570 original H1 | 36/36 exposed discovery; reserved prediction/live 72/72 on 24×3; reference/live 60/72 | Draft-free tested-path predictive sufficiency; reference compatibility still blocked |
| B570 same-state fork | Scores change 72/72; raw top-1 and immediate decisions change 0/72; later trajectories change 18/72 on 6/24 prompts | UB128 persists after the sampled fork; delayed effects cannot be attributed to that block alone; separate cohort from original H1 |
| RTX earlier H1 | Target-only UB2/live discovery 24/36; H2 not executed in that arm; reserved 0 | Failed candidate and stopping outcome remain visible |
| RTX H2 V2 | H2/live, R_ONLY/live, H2/R_ONLY each 72/72; UB1 reference/live 60/72 | Independent program orchestration on shared numerical libraries; H2 builds tape with draft; V2 alone has no same-set UB2 competitor |
| RTX fresh serialized cost | New 90/90 direct-ID gate; 180 runs; target/serialized 0.646 [0.630, 0.660]; 0/30 prompts faster | Instrumented post-prefill CLI boundary; no same-study qualified batched timing or production estimate |
| RTX V3 | 72 valid pre-live conditions + one failed capture; A live 0; 54 valid B conditions + one failed capture | Terminal prefixes only; no full-cohort accuracy, speedup or CI; old failed status remains unchanged |
| RTX V4 trajectory A | 19×3: target-only UB2/live 51/57, H2/live and R_ONLY/live 57/57; UB1 reference/live 51/57; 2 reference-divergent prompts | Rejects only the predefined UB2 candidate on this cohort; replay agreement is finite empirical sufficiency, not history necessity or unique cause |
| RTX V4 matched cost B | 171 new runs: batched 51/57 BLOCKED; serialized 57/57 QUALIFIED; target/serialized 0.677351 [0.661653, 0.691812]; 0/19 faster | Same cohort/timer/schedule, instrumented post-prefill latency; blocked timing diagnostic only; not comparable as an optimization to the old 0.646 cohort |
| 358H | CPU/NPU Phase 3 each 90/90; fixed-progress/target-work zero-draft-and-residual bounds 0.82745 / 0.83519 | Conditional arithmetic total-time bounds; replay/proposal inseparable; runtime qualification stopped; no runtime gain or NPU-general claim |
| M4 runtime | Guard 1.3114×, Always-Spec 1.3469×; both 180/180; Guard/Always 1.0271; Always/oracle 1.000692 | Guard beats target-only but loses to fixed speculation; hindsight oracle compares two measured fixed modes; no incremental adaptive-policy win |

Use the [v0.8.7 claim/campaign map](reviews/rtx_integration_v087/CLAIM_AND_CAMPAIGN_MAP_V087.md) and original closeouts for cohorts, references, endpoints, ratio directions and raw evidence. Repetitions and correlated events are not independent prompts. v0.8.6 record-derived quantities are post-study; original primary estimates/CIs remain intact.

## 4. Non-claims and audit limits

No unique numerical cause, universal backend transfer, necessary/minimal history state, B570 lossless replacement, qualified batched RTX speedup, production throughput/energy, general 358H NPU weakness or M4 adaptive-policy win is claimed. HumanEval IDs are paired greedy equality, not functional pass@k. Repetitions/correlated events are not independent prompts.

V4 A/B share all 19 remaining exposure-audited tasks after 145 conservative exclusions. B observations are fresh but not a new task generalization set. UB1 and UB2 have equal aggregate 51/57 yet fail different prompts. Global native micro-batch changes draft as well as target; B is a whole-path comparison. V3 remains a failed terminal campaign with no full-study accuracy or speedup/CI. Never pool V3 prefixes, V2 or old cost into V4.

Current checks: two independent source-ZIP builds with exact raw per-page text equality, all 37 PDF pages visually inspected, old anonymous member/verifier bytes preserved, 285 A and 171 B arrays/timer intervals recomputed, ten negative cases rejected, two clean anonymous-package executions, and 71 Figure 3 checks. [Prior V4 raw closeout](evidence/RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002.md) already replayed nine capsules and reconstructed native arrays/QPC on CPU; it is not a new GPU or archive run in this integration. Other old suites are historical receipts, not new claims.

358H runtime traces and exact old v084 sequence ZIP remain unavailable. Offline evidence does not authenticate omitted assets, exposure completeness or trusted absolute chronology. The disclosed host-policy amendment and strict-host stopping record are preserved; author instructions say fan adjustment is not a work/rerun blocker.

## 5. Validity versus strengthening

All existing B570, RTX, 358H and M4 campaigns are CLOSED. The finite claims do not authorize further experiments simply because limitations remain. Delivery QA is separate from independent judgments of significance, novelty and venue fit. The fixed-artifact submission review is complete: R1 gives 3/6 (weak reject), R2–R6 each 4/6 (weak accept), all confidence 4/5. No reviewer identified a demonstrated central validity failure or logically required new model execution. The disagreement concerns main-track significance; votes are not acceptance probabilities. Read [the meta-review](reviews/submission_v087/META_REVIEW_V087.md) and [revision priorities](reviews/submission_v087/REVISION_PRIORITY_V087.md). Old scores do not carry forward.

## 6. Next authorized action

Assess the exact v087 artifacts and completed review, then decide existing-material manuscript revisions and merge. The current recommendation is not to execute B570 now; [the B570 decision](reviews/submission_v087/B570_DECISION_V087.md) records why and the bounded trigger for any later single-block/common-policy study. No review request has been silently applied to the frozen PDFs. The old RTX execution prompt is historical; RTX A+B has been completed and no GPU study remains authorized. Do not modify this frozen review packet while collecting votes. A later manuscript edit requires a new artifact identity and explicit record of what changed.

## 7. Scope and release guardrails

- B570 dense/all-block scan, more prompts/backends, 358H persistence and M4 controller variants remain deferred and NOT AUTHORIZED.
- Optional future B570 work requires a separately bounded single-block intervention followed by common continuation policy; it is not an automatic validity repair.
- No result-driven candidate/cohort expansion, outcome-selected repetitions, hidden failures or pooling unmatched studies. Negative results are valid endpoints.
- Old arrays, numerical macros, Figure 3, vendor styles, prior artifacts/reviews/manifests and scientific tag stay immutable. New TeX and v087 artifacts are versioned separately.
- arXiv, public release, author/licensing metadata and conference submission are separate decisions. No submission or public release is performed here.

After a materially changing merge, reconcile this file with actual remote main. Check PR base before merging; merged=true alone does not prove main contains a stacked PR.
