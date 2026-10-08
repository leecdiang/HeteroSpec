# HeteroSpec — scientific baseline v0.12.0

Updated 2026-10-08. The author authorized review and merge of all open PRs #57–66; all ten were merged at reviewed heads. Research evidence anchor: `f9b9457fe528a343dd0b01614dcce017801913db`. Earlier pause notices and unexecuted-stage statements below are historical.

**Current manuscript:** [State and Cost Limits of Reference-Preserving Speculative Decoding](baseline_v012/output/manuscript-v0.12.0.pdf) (6 body + 1 references page); [supplement](baseline_v012/output/appendix-v0.12.0.pdf) (3 pages); [portable author source](baseline_v012/output/portable-source-v0.12.0.zip). [Scientific baseline and build](baseline_v012/README.md); [whole-baseline review and contribution overlap](reviews/baseline_v012/BASELINE_REVIEW.zh-CN.md).

Mainline: natural numerical state × current execution path → bounded target-path constraints → independent output and amortization gates. RTX24 yields **1.170× generation / 1.742× resident-request speed against the paid ordinary scalar reference**, and **1.169× / 1.035× against matched draft-free execution**. The matched path already provides **1.683× request speed without speculation**; the total is not all attributable to speculation. B570 finite endpoint repair has no ordinary-reference cost gain. Fixed-UB wider drafting stays qualified but slows down. Four platforms do not establish one universal mechanism.

The v0.12 review judges a stronger bounded empirical contribution than v0.11, with substantial nearest-work overlap and limited cross-model generality. It is not a high-confidence MLSys acceptance claim. Public-table arithmetic, bootstrap and qualification-hash checks pass; private raw-archive authentication is inherited rather than independently repeated here. CPU reanalysis is not new inference. No submission or new GPU experiment occurred. Portable source includes provenance identities and is not an anonymous submission artifact.

---

<details>
<summary>Historical documents and versioned artifacts (superseded for current status)</summary>

# HeteroSpec — v0.11.0 baseline Draft; further merges paused

Updated 2026-10-05 **on this review branch**. PR #53–56 were merged before the author's pause request, ending at main `e87291d26df32f2cb9571e005ab173b1c7a6830b`. All further merges are paused. This v0.11.0 delivery is a complete baseline covering evidence through #56, **not a frozen submission or a manuscript integration of #57–60**. The paper revision itself remains a Draft pending research review.

Artifacts: [main PDF](../../paper/mlsys2027/manuscript/output/manuscript-v0.11.0.pdf) (10 body +2 references), [appendix](../../paper/mlsys2027/manuscript/output/appendix-v0.11.0.pdf) (27 pages), [portable source](../../paper/mlsys2027/manuscript/output/overleaf-integrated-empirical-v0.11.0.zip), [anonymous evidence](../../paper/mlsys2027/manuscript/output/anonymous-integrated-evidence-v0.11.0.zip). From repository root, build with `python paper/mlsys2027/manuscript/scripts/build_v011.py`; this packages all document dependencies and checks two independent extracted builds. Run the separately extracted evidence pack with `python -B verify_v011.py`. Neither operation launches models or GPU jobs. Historical versioned outputs and frozen experimental files are preserved.

The baseline adds the native target-only bridge (ordinary U2 equals N1 on 19/19 exposed tasks; reference agreement is 17/19) and scoped offline selection feasibility (no measured selector advantage; MBPP U2 unknown). Interventions and historical cost studies retain separate contracts and denominators. [Evidence map](../../paper/mlsys2027/reviews/integration_v011/EVIDENCE_MAPPING.md), [complete baseline review](../../paper/mlsys2027/reviews/integration_v011/FINAL_REVIEW.md), [style/build QA](../../paper/mlsys2027/reviews/integration_v011/STYLE_QA.md), [artifact manifest](../../paper/mlsys2027/reviews/integration_v011/ARTIFACT_MANIFEST.json).

The [new research review](../../paper/mlsys2027/reviews/integration_v011/LATEST_RESEARCH_REVIEW.md) separately assesses open Drafts [#57](https://github.com/leecdiang/HeteroSpec/pull/57), [#58](https://github.com/leecdiang/HeteroSpec/pull/58), [#59](https://github.com/leecdiang/HeteroSpec/pull/59), [#60](https://github.com/leecdiang/HeteroSpec/pull/60). #59/#60 provide a native repair with matched speculative speedup on the exposed cohort; Stage B/C/D transfer remains unexecuted. The extra generation gain from relaxing draft constraints did not pass its predeclared gate. These later results are not included in the anonymous v0.11.0 manuscript. Audit unused-task eligibility before new outputs; do not silently treat the old 19 tasks as a holdout.

[Venue assessment](../../paper/mlsys2027/reviews/integration_v011/VENUE_ASSESSMENT.md) is conditional on the next research results. Do not infer acceptance probabilities from old internal ratings, or apply this baseline's novelty rating to future method revisions. No submission, further merge, upstream communication or new hardware execution was performed during this delivery.

---

<details>
<summary>Historical status before this baseline review (preserved, superseded above)</summary>

# Current handover — B570 prefill study verified; manuscript integration pending

Updated 2026-10-04. The separately authorized B570 prefill diagnostic study is **COMPLETE and CLOSED**. Its [delivery](https://github.com/leecdiang/HeteroSpec/blob/196ed563b36d0e16a3cdb667b6996a4afd98da1d/benchmarks/b570_prefill_diagnostic_v1/DELIVERY_REPORT.md) and [independent review](https://github.com/leecdiang/HeteroSpec/blob/main/paper/mlsys2027/reviews/b570_prefill_review_20261004/REVIEW_REPORT.md) supersede the PREPARE_ONLY study status preserved below.

All 360 planned formal units are valid, with zero failed formal attempts. T0/N0 and sealed T1/N1 each match 72/72 complete arrays and endpoints. Native/reference agreement changes from 60/72 to 72/72; all four original diagnostic tasks recover reference output and none of the 20 controls regresses. The 24 tasks were previously exposed; three repetitions establish stability. The independent review checks 120 G0 arrays, 30 sham pairs, frozen source identities and local prediction-seal order. The [read-only CPU audit](https://github.com/leecdiang/HeteroSpec/actions/runs/37178393741) validates all 30 remote parts and 4,073 manifest files.

The new evidence supports a bounded predictor-guided prefill intervention confirmed on native execution. It strengthens the practical diagnostic contribution. Generality, omitted external asset authentication and local-only chronology remain limitations; no performance, energy, functional-pass-rate or unique-kernel result is added. Historical v0.9.0 internal ratings of 3/6 are not updated scores for the new study or acceptance probabilities.

The manuscript delivery remains **v0.9.0**, fixed content `01682f3b992a11b36b309fbd6c9e9950f1dc5d89`: 10 body + 2 reference pages and a 17-page appendix. Its TeX/PDFs/ZIPs are unchanged by this evidence review. The B570 intervention has not yet been integrated into a new manuscript. Build and artifact instructions remain in the preserved delivery documentation below.

[Integration PR #52](https://github.com/leecdiang/HeteroSpec/pull/52) targets main and includes the previously reviewed #51 ancestor plus this study, review receipts and current-status reconciliation. Resolve the actual PR/main state on GitHub; this file does not predict its own containing merge SHA. Prior draft/unmerged wording below describes its historical delivery. The scientific author-freeze remains `mlsys2027-v0.8-author-freeze`, peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`.

Next: integrate the intervention and reference-recovery chain into the contribution, results and controls of a new manuscript, then independently review that exact delivery. The original B570/RTX/358H/M4 campaigns remain CLOSED. Public release and conference submission are separate decisions.

<details>
<summary>Preserved status before B570 prefill integration</summary>

# Current handover — v0.9.0 reassessment

Updated 2026-10-03. The [fresh reassessment](reviews/acceptance_reassessment_v090/ACCEPTANCE_REASSESSMENT_V090.md) supersedes the review status in the preserved history below. The manuscript remains v0.9.0.

Two new reviewers independently recommend **3/6 weak reject, confidence 4/5**. Both read all 12 main and 17 appendix text pages, inspect selected renders, and directly check retained arrays and costs. Their arithmetic agrees with the bounded claims; neither identifies a new material defect in the checked results. The remaining blocker is demonstrated systems significance: the simpler reproducer has not yet guided a discriminating intervention confirmed on native execution. These are internal simulated judgments, not acceptance probabilities. Historical v0.8.9 scores (3/6 and 4/6) are different reviewers' assessments of a different packet; there is no score evidence of improvement.

The [B570 diagnostic study plan](reviews/acceptance_reassessment_v090/DIAGNOSTIC_STUDY_PREPARE_ONLY.md) is **PREPARE_ONLY, not execution-ready or executed**. It proposes one target-prefill intervention on the four known divergent cases plus 20 regression controls, after new baseline, sham-transfer, state and instrumentation qualification. Five conditions with three repetitions would yield 360 planned complete arrays; these are not new observations. The [source check](reviews/acceptance_reassessment_v090/PREPARE_SOURCE_AUDIT.json) establishes caller-level facts only, not a prefill cause. Original B570/RTX/358H/M4 campaigns remain CLOSED.

Frozen delivery: [main PDF](manuscript/output/manuscript-v0.9.0.pdf), 10 body + 2 reference pages; [appendix](manuscript/output/appendix-v0.9.0.pdf), 17 pages; [document source](manuscript/output/overleaf-diagnostic-revision-v0.9.0.zip); [anonymous scientific package](manuscript/output/anonymous-evidence-index-v0.9.0.zip). All four are byte-identical to content commit `01682f3b992a11b36b309fbd6c9e9950f1dc5d89`. The [artifact manifest](evidence/FINAL_ARTIFACT_MANIFEST_V090.json) retains its original identity. No TeX build, historical verifier/bootstrap, model or GPU ran in this review round; earlier build and whole-page QA remain historical receipts for the same hashes.

New [systems review](reviews/acceptance_reassessment_v090/SYSTEMS_ACCEPTANCE_REVIEW.md), [evidence review](reviews/acceptance_reassessment_v090/EVIDENCE_ACCEPTANCE_REVIEW.md), and [coverage/consistency QA](reviews/acceptance_reassessment_v090/REVIEW_COVERAGE_QA.json) retain their individual judgments and limits. Only six living status files and new review/plan files change. Original scientific records, manuscript sources/PDFs/ZIPs, prior reviews, and scripts remain unchanged. Existing Draft PR #51 stays open and unmerged; no release or conference submission. Base/main stays `87b811e21a164468232cfea3c2404a1ebc869477`; author-freeze tag remains object `a3e33d405a53b8ee9fe4018d166b651001daa305`, peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`.

<details>
<summary>Preserved v0.9.0 diagnostic revision status and earlier history</summary>

# Current handover — v0.9.0

Updated 2026-10-03. This status supersedes the preserved history below. Read the [revision response](reviews/diagnostic_revision_v090/REVISION_RESPONSE_V090.md) for the implemented acceptance-reassessment requests and their limits.

v0.9.0 explains the tested B570/RTX reproduction tasks, adds complete-trajectory failure extents, and aligns the 358H optimization budget with the original prompt estimator. It quantifies M4 opportunity between two measured fixed modes and carries those conclusions through the whole paper. All analyses use retained records after outcomes were known. Original observations, primary GM/CI/seeds and all historical artifacts remain unchanged.

Current files: [main PDF](manuscript/output/manuscript-v0.9.0.pdf) (10 body + 2 reference pages), [separate appendix](manuscript/output/appendix-v0.9.0.pdf) (17 pages), [portable document source](manuscript/output/overleaf-diagnostic-revision-v0.9.0.zip), and [anonymous scientific package](manuscript/output/anonymous-evidence-index-v0.9.0.zip). The new scientific package retains every v0.8.8 member byte-identically and adds the new diagnostic calculator/data. The hardware-only PDF is an internal section-removal proof, not a submission artifact. [Manifest](evidence/FINAL_ARTIFACT_MANIFEST_V090.json) and [revision QA](evidence/REVISION_V090_QA.json) bind the files and checks.

Two clean source-ZIP builds agree on exact raw per-page text. Final 40-page visual coverage comprises 26 manually inspected final pages and 14 exact pixel matches to manually inspected pages from the current revision's first candidate. Fonts, citations, anonymity and page limits pass. The new diagnostic calculator passes twice in clean extractions. Historical verifier/bootstrap suites are not rerun; 319 protected files and all 30 historical scientific ZIP members retain their original bytes.

The [fixed v0.8.9 reassessment](reviews/acceptance_reassessment_v089/ACCEPTANCE_REASSESSMENT_V089.md) remains historical: systems 3/6 weak reject, evidence 4/6 weak accept. These are not v0.9.0 scores or acceptance probabilities. Concrete reproduction inputs and conditional budgets are now clearer; no actual bug fix or measured debugging saving is demonstrated. Main-track significance remains open to a fresh assessment. No further B570 experiment is needed for the current finite claims.

Existing [Draft PR #51](https://github.com/leecdiang/HeteroSpec/pull/51) keeps branch `paper/mlsys2027-rtx-integration-v0.8.7`. Revision parent is `c39461230f34554151dcfddafffb41ab938517dd`; main remains `87b811e21a164468232cfea3c2404a1ebc869477`. The author-freeze tag remains peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. **B570/RTX/358H/M4 remain CLOSED.** This revision authorizes no new model/hardware experiment, merge, release or conference submission.

<details>
<summary>Preserved v0.8.9 status and earlier history</summary>

# Handover Current — v0.8.9 review closeout

Updated 2026-10-03. This current status supersedes all historical wording below. [Final review](reviews/system_revision_v089/FINAL_REVIEW_V089.md) records the complete request mapping and remaining significance concern.

v0.8.9 completes the missed A6 prospective-path endpoint wording and the A9 Section Q entry. The scientific prose, observations, primary estimates and [v0.8.8 global system analysis](reviews/system_revision_v088/GLOBAL_SYSTEM_READOUT_V088.md) remain unchanged. Assessment: **Share with caveats**; finite claims are supported, while main-track significance remains an author judgment. This is an author closeout, not a fresh committee vote.

Current artifacts: [main PDF](manuscript/output/manuscript-v0.8.9.pdf) (10 body + 2 references), [separate appendix](manuscript/output/appendix-v0.8.9.pdf) (16 pages), [document source ZIP](manuscript/output/overleaf-system-revision-v0.8.9.zip), and unchanged [anonymous scientific evidence v0.8.8](manuscript/output/anonymous-evidence-index-v0.8.8.zip). The internal hardware-only proof is not a submission artifact. [Manifest](evidence/FINAL_ARTIFACT_MANIFEST_V089.json) and [delivery identity](evidence/DELIVERY_V089.md) bind the final files.

Two clean ZIP builds pass with exact raw per-page text equality. Three changed appendix pages were manually checked; the other 36 pages exactly match previously inspected pixels. Scientific CPU/data verification receipts are reused after hash verification, not described as new executions. [Closeout QA](evidence/REVIEW_CLOSEOUT_V089_QA.json) records the scope.

The [official 2027 format check](reviews/system_revision_v089/VENUE_PRECHECK_20261003.md) confirms 2025 style and the 10-page body limit. Style/bst bytes stay fixed. The CFP and homepage disagree by one hour on the deadline; the note preserves both times pending OpenReview confirmation.

Existing [Draft PR #51](https://github.com/leecdiang/HeteroSpec/pull/51) retains branch `paper/mlsys2027-rtx-integration-v0.8.7`. Parent is `4a4854575dcd1f652975bb008ceccbae0300d6c2`; main is `87b811e21a164468232cfea3c2404a1ebc869477`. The author-freeze tag remains peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. **B570/RTX/358H/M4 remain CLOSED.** No model execution, merge, release or conference submission is authorized by this closeout.

<details>
<summary>Preserved v0.8.8 status and earlier history</summary>

# Current handover — v0.8.8 author revision

Updated 2026-10-03. This first-read file supersedes historical “next/current” wording below.

## Repository identity

Existing Draft PR #51, direct base main `87b811e21a164468232cfea3c2404a1ebc869477`, parent v0.8.7 delivery `79327fd0c15e4d382b6264e9e780004b046fe5c1`. Branch `paper/mlsys2027-rtx-integration-v0.8.7` retains its historical name. New exact content/metadata-child identities are in [DELIVERY_V088.md](evidence/DELIVERY_V088.md); do not assert main was merged or an author machine checkout changed. Scientific tag remains peeled `1d3b556c93b477680788dfd1eb0737dfe9eee28c`.

v0.8.8 follows the completed fixed-artifact v0.8.7 review. It reorganizes the paper around prospective trajectory prediction, same-set specified-candidate discrimination, and the resulting qualification/cost choices; 358H and M4 supply bounded optimization constraints. A new global system readout states what each result adds beyond a basic gate. New V4 absolute latency descriptors use only the existing 171 QPC records and do not replace the frozen GM/CI.

B570 H1 remains 72/72 reserved complete predictions against reference/live 60/72. RTX V4 remains UB2/live 51/57, replay 57/57, with /15 both comparators failing, /18 reference-only failure and /25 UB2-only failure. Its fresh cost gate remains batched 51/57 BLOCKED (speedup/CI null), serialized 57/57 QUALIFIED but slower: 0.677351 [0.661653,0.691812], 0/19 faster. A/B share 19 exposure-conditioned prompts; the earlier 0.646 belongs to a different study.

All campaigns remain CLOSED. No new GPU/model execution, merge, release or submission. Original arrays, estimates/seeds, versioned artifacts/reviews/scripts, numerical macros, official style and scientific author-freeze tag are preserved. The historical Figure 3 is moved into Appendix F with identical tex/PDF/caption and textwidth inclusion. Its numbering changes with relocation, not its data or geometry. Old scores apply only to v0.8.7; main-track significance remains a judgment, not a QA result.

## Read and verify

Read [global system analysis](reviews/system_revision_v088/GLOBAL_SYSTEM_READOUT_V088.md), [complete review response](reviews/system_revision_v088/REVIEW_RESPONSE_V088.md), [analysis plan](reviews/system_revision_v088/ANALYSIS_PLAN_V088.md), [main](manuscript/output/manuscript-v0.8.8.pdf), [appendix](manuscript/output/appendix-v0.8.8.pdf), [source](manuscript/output/overleaf-system-revision-v0.8.8.zip), [anonymous evidence](manuscript/output/anonymous-evidence-index-v0.8.8.zip), [build instructions](manuscript/README.md) and [manifest](evidence/FINAL_ARTIFACT_MANIFEST_V088.json).

New checks: independent original-QPC/NumPy descriptors; two clean anonymous executions; two rehashed corrupt descriptor cases rejected; two fresh builds with exact raw page text; PDF completeness/fonts/anonymity/reference scans; all final pages inspected. Receipts state exact hashes and actual execution scope. Reused only: prior nine-capsule raw audit and historical suites. No GPU/model execution, no new six-report score, and no hidden retuning of candidates or endpoints.

## Authorized work and next decision

Existing-material repair and compilation are complete when final receipts pass. All prior campaigns remain CLOSED. Do not launch B570 dense scans or a single-block causal study without a new concrete objective and bounded protocol. Current finite claims do not require it. The old six grades are not v0.8.8 grades; main-track significance remains unresolved despite a clearer contribution and decision argument.

Author assessment/merge is next; no automatic merge, release, arXiv or conference submission. Avoid repeating full historical suites or six votes absent a new failure/material scientific change. Exact old sequence ZIP, 358H runtime raw traces, omitted assets and trusted absolute chronology remain unavailable. Fan/host amendment is retained and not a work/rerun blocker under author instruction.

<details>
<summary>Historical v0.8.7 living-pointer text, retained as history; not current instructions</summary>

# Current handover — v0.8.7 candidate; RTX V4 integrated

Updated 2026-10-02. This is the living control file for current state and scope. Historical manifests, handovers and stopping rules retain their original delivery context.

## 1. Repository state

Candidate [Draft PR #51](https://github.com/leecdiang/HeteroSpec/pull/51), branch: `paper/mlsys2027-rtx-integration-v0.8.7`, based directly on main `87b811e21a164468232cfea3c2404a1ebc869477`. v0.8.7 is pending merge. Baseline main contains v0.8.6 via #46, V3 terminal history via #48, V4 completed evidence via #49, and independent raw closeout via #50. The earlier #45 stacked merge was resolved by #46; the new candidate must target main.

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

</details>

</details>

</details>

</details>

</details>

</details>

</details>

