# HeteroSpec — v0.11.0 baseline Draft; further merges paused

Updated 2026-10-05 **on this review branch**. PR #53–56 were merged before the author's pause request, ending at main `e87291d26df32f2cb9571e005ab173b1c7a6830b`. All further merges are paused. This v0.11.0 delivery is a complete baseline covering evidence through #56, **not a frozen submission or a manuscript integration of #57–60**. The paper revision itself remains a Draft pending research review.

Artifacts: [main PDF](paper/mlsys2027/manuscript/output/manuscript-v0.11.0.pdf) (10 body +2 references), [appendix](paper/mlsys2027/manuscript/output/appendix-v0.11.0.pdf) (27 pages), [portable source](paper/mlsys2027/manuscript/output/overleaf-integrated-empirical-v0.11.0.zip), [anonymous evidence](paper/mlsys2027/manuscript/output/anonymous-integrated-evidence-v0.11.0.zip). From repository root, build with `python paper/mlsys2027/manuscript/scripts/build_v011.py`; this packages all document dependencies and checks two independent extracted builds. Run the separately extracted evidence pack with `python -B verify_v011.py`. Neither operation launches models or GPU jobs. Historical versioned outputs and frozen experimental files are preserved.

The baseline adds the native target-only bridge (ordinary U2 equals N1 on 19/19 exposed tasks; reference agreement is 17/19) and scoped offline selection feasibility (no measured selector advantage; MBPP U2 unknown). Interventions and historical cost studies retain separate contracts and denominators. [Evidence map](paper/mlsys2027/reviews/integration_v011/EVIDENCE_MAPPING.md), [complete baseline review](paper/mlsys2027/reviews/integration_v011/FINAL_REVIEW.md), [style/build QA](paper/mlsys2027/reviews/integration_v011/STYLE_QA.md), [artifact manifest](paper/mlsys2027/reviews/integration_v011/ARTIFACT_MANIFEST.json).

The [new research review](paper/mlsys2027/reviews/integration_v011/LATEST_RESEARCH_REVIEW.md) separately assesses open Drafts [#57](https://github.com/leecdiang/HeteroSpec/pull/57), [#58](https://github.com/leecdiang/HeteroSpec/pull/58), [#59](https://github.com/leecdiang/HeteroSpec/pull/59), [#60](https://github.com/leecdiang/HeteroSpec/pull/60). #59/#60 provide a native repair with matched speculative speedup on the exposed cohort; Stage B/C/D transfer remains unexecuted. The extra generation gain from relaxing draft constraints did not pass its predeclared gate. These later results are not included in the anonymous v0.11.0 manuscript. Audit unused-task eligibility before new outputs; do not silently treat the old 19 tasks as a holdout.

[Venue assessment](paper/mlsys2027/reviews/integration_v011/VENUE_ASSESSMENT.md) is conditional on the next research results. Do not infer acceptance probabilities from old internal ratings, or apply this baseline's novelty rating to future method revisions. No submission, further merge, upstream communication or new hardware execution was performed during this delivery.

---

<details>
<summary>Historical status before this baseline review (preserved, superseded above)</summary>

# Repository status — B570 prefill study verified

Updated 2026-10-04. The separately authorized B570 prefill diagnostic study is **COMPLETE and CLOSED**. Its [delivery](https://github.com/leecdiang/HeteroSpec/blob/196ed563b36d0e16a3cdb667b6996a4afd98da1d/benchmarks/b570_prefill_diagnostic_v1/DELIVERY_REPORT.md) and [independent review](https://github.com/leecdiang/HeteroSpec/blob/main/paper/mlsys2027/reviews/b570_prefill_review_20261004/REVIEW_REPORT.md) supersede the PREPARE_ONLY study status preserved below.

All 360 planned formal units are valid, with zero failed formal attempts. T0/N0 and sealed T1/N1 each match 72/72 complete arrays and endpoints. Native/reference agreement changes from 60/72 to 72/72; all four original diagnostic tasks recover reference output and none of the 20 controls regresses. The 24 tasks were previously exposed; three repetitions establish stability. The independent review checks 120 G0 arrays, 30 sham pairs, frozen source identities and local prediction-seal order. The [read-only CPU audit](https://github.com/leecdiang/HeteroSpec/actions/runs/37178393741) validates all 30 remote parts and 4,073 manifest files.

The new evidence supports a bounded predictor-guided prefill intervention confirmed on native execution. It strengthens the practical diagnostic contribution. Generality, omitted external asset authentication and local-only chronology remain limitations; no performance, energy, functional-pass-rate or unique-kernel result is added. Historical v0.9.0 internal ratings of 3/6 are not updated scores for the new study or acceptance probabilities.

The manuscript delivery remains **v0.9.0**, fixed content `01682f3b992a11b36b309fbd6c9e9950f1dc5d89`: 10 body + 2 reference pages and a 17-page appendix. Its TeX/PDFs/ZIPs are unchanged by this evidence review. The B570 intervention has not yet been integrated into a new manuscript. Build and artifact instructions remain in the preserved delivery documentation below.

[Integration PR #52](https://github.com/leecdiang/HeteroSpec/pull/52) targets main and includes the previously reviewed #51 ancestor plus this study, review receipts and current-status reconciliation. Resolve the actual PR/main state on GitHub; this file does not predict its own containing merge SHA. Prior draft/unmerged wording below describes its historical delivery. The scientific author-freeze remains `mlsys2027-v0.8-author-freeze`, peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`.

Next: integrate the intervention and reference-recovery chain into the contribution, results and controls of a new manuscript, then independently review that exact delivery. The original B570/RTX/358H/M4 campaigns remain CLOSED. Public release and conference submission are separate decisions.

<details>
<summary>Preserved status before B570 prefill integration</summary>

# Repository status — v0.9.0 reassessment

Updated 2026-10-03. The [fresh reassessment](paper/mlsys2027/reviews/acceptance_reassessment_v090/ACCEPTANCE_REASSESSMENT_V090.md) supersedes the review status in the preserved history below. The manuscript remains v0.9.0.

Two new reviewers independently recommend **3/6 weak reject, confidence 4/5**. Both read all 12 main and 17 appendix text pages, inspect selected renders, and directly check retained arrays and costs. Their arithmetic agrees with the bounded claims; neither identifies a new material defect in the checked results. The remaining blocker is demonstrated systems significance: the simpler reproducer has not yet guided a discriminating intervention confirmed on native execution. These are internal simulated judgments, not acceptance probabilities. Historical v0.8.9 scores (3/6 and 4/6) are different reviewers' assessments of a different packet; there is no score evidence of improvement.

The [B570 diagnostic study plan](paper/mlsys2027/reviews/acceptance_reassessment_v090/DIAGNOSTIC_STUDY_PREPARE_ONLY.md) is **PREPARE_ONLY, not execution-ready or executed**. It proposes one target-prefill intervention on the four known divergent cases plus 20 regression controls, after new baseline, sham-transfer, state and instrumentation qualification. Five conditions with three repetitions would yield 360 planned complete arrays; these are not new observations. The [source check](paper/mlsys2027/reviews/acceptance_reassessment_v090/PREPARE_SOURCE_AUDIT.json) establishes caller-level facts only, not a prefill cause. Original B570/RTX/358H/M4 campaigns remain CLOSED.

Frozen delivery: [main PDF](paper/mlsys2027/manuscript/output/manuscript-v0.9.0.pdf), 10 body + 2 reference pages; [appendix](paper/mlsys2027/manuscript/output/appendix-v0.9.0.pdf), 17 pages; [document source](paper/mlsys2027/manuscript/output/overleaf-diagnostic-revision-v0.9.0.zip); [anonymous scientific package](paper/mlsys2027/manuscript/output/anonymous-evidence-index-v0.9.0.zip). All four are byte-identical to content commit `01682f3b992a11b36b309fbd6c9e9950f1dc5d89`. The [artifact manifest](paper/mlsys2027/evidence/FINAL_ARTIFACT_MANIFEST_V090.json) retains its original identity. No TeX build, historical verifier/bootstrap, model or GPU ran in this review round; earlier build and whole-page QA remain historical receipts for the same hashes.

New [systems review](paper/mlsys2027/reviews/acceptance_reassessment_v090/SYSTEMS_ACCEPTANCE_REVIEW.md), [evidence review](paper/mlsys2027/reviews/acceptance_reassessment_v090/EVIDENCE_ACCEPTANCE_REVIEW.md), and [coverage/consistency QA](paper/mlsys2027/reviews/acceptance_reassessment_v090/REVIEW_COVERAGE_QA.json) retain their individual judgments and limits. Only six living status files and new review/plan files change. Original scientific records, manuscript sources/PDFs/ZIPs, prior reviews, and scripts remain unchanged. Existing Draft PR #51 stays open and unmerged; no release or conference submission. Base/main stays `87b811e21a164468232cfea3c2404a1ebc869477`; author-freeze tag remains object `a3e33d405a53b8ee9fe4018d166b651001daa305`, peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`.

<details>
<summary>Preserved v0.9.0 diagnostic revision status and earlier history</summary>

# Repository status — v0.9.0

Updated 2026-10-03. This status supersedes the preserved history below. Read the [revision response](paper/mlsys2027/reviews/diagnostic_revision_v090/REVISION_RESPONSE_V090.md) for the implemented acceptance-reassessment requests and their limits.

v0.9.0 explains the tested B570/RTX reproduction tasks, adds complete-trajectory failure extents, and aligns the 358H optimization budget with the original prompt estimator. It quantifies M4 opportunity between two measured fixed modes and carries those conclusions through the whole paper. All analyses use retained records after outcomes were known. Original observations, primary GM/CI/seeds and all historical artifacts remain unchanged.

Current files: [main PDF](paper/mlsys2027/manuscript/output/manuscript-v0.9.0.pdf) (10 body + 2 reference pages), [separate appendix](paper/mlsys2027/manuscript/output/appendix-v0.9.0.pdf) (17 pages), [portable document source](paper/mlsys2027/manuscript/output/overleaf-diagnostic-revision-v0.9.0.zip), and [anonymous scientific package](paper/mlsys2027/manuscript/output/anonymous-evidence-index-v0.9.0.zip). The new scientific package retains every v0.8.8 member byte-identically and adds the new diagnostic calculator/data. The hardware-only PDF is an internal section-removal proof, not a submission artifact. [Manifest](paper/mlsys2027/evidence/FINAL_ARTIFACT_MANIFEST_V090.json) and [revision QA](paper/mlsys2027/evidence/REVISION_V090_QA.json) bind the files and checks.

Two clean source-ZIP builds agree on exact raw per-page text. Final 40-page visual coverage comprises 26 manually inspected final pages and 14 exact pixel matches to manually inspected pages from the current revision's first candidate. Fonts, citations, anonymity and page limits pass. The new diagnostic calculator passes twice in clean extractions. Historical verifier/bootstrap suites are not rerun; 319 protected files and all 30 historical scientific ZIP members retain their original bytes.

The [fixed v0.8.9 reassessment](paper/mlsys2027/reviews/acceptance_reassessment_v089/ACCEPTANCE_REASSESSMENT_V089.md) remains historical: systems 3/6 weak reject, evidence 4/6 weak accept. These are not v0.9.0 scores or acceptance probabilities. Concrete reproduction inputs and conditional budgets are now clearer; no actual bug fix or measured debugging saving is demonstrated. Main-track significance remains open to a fresh assessment. No further B570 experiment is needed for the current finite claims.

Existing [Draft PR #51](https://github.com/leecdiang/HeteroSpec/pull/51) keeps branch `paper/mlsys2027-rtx-integration-v0.8.7`. Revision parent is `c39461230f34554151dcfddafffb41ab938517dd`; main remains `87b811e21a164468232cfea3c2404a1ebc869477`. The author-freeze tag remains peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. **B570/RTX/358H/M4 remain CLOSED.** This revision authorizes no new model/hardware experiment, merge, release or conference submission.

<details>
<summary>Preserved v0.8.9 status and earlier history</summary>

# Repo Status — v0.8.9 review closeout

Updated 2026-10-03. This current status supersedes all historical wording below. [Final review](paper/mlsys2027/reviews/system_revision_v089/FINAL_REVIEW_V089.md) records the complete request mapping and remaining significance concern.

v0.8.9 completes the missed A6 prospective-path endpoint wording and the A9 Section Q entry. The scientific prose, observations, primary estimates and [v0.8.8 global system analysis](paper/mlsys2027/reviews/system_revision_v088/GLOBAL_SYSTEM_READOUT_V088.md) remain unchanged. Assessment: **Share with caveats**; finite claims are supported, while main-track significance remains an author judgment. This is an author closeout, not a fresh committee vote.

Current artifacts: [main PDF](paper/mlsys2027/manuscript/output/manuscript-v0.8.9.pdf) (10 body + 2 references), [separate appendix](paper/mlsys2027/manuscript/output/appendix-v0.8.9.pdf) (16 pages), [document source ZIP](paper/mlsys2027/manuscript/output/overleaf-system-revision-v0.8.9.zip), and unchanged [anonymous scientific evidence v0.8.8](paper/mlsys2027/manuscript/output/anonymous-evidence-index-v0.8.8.zip). The internal hardware-only proof is not a submission artifact. [Manifest](paper/mlsys2027/evidence/FINAL_ARTIFACT_MANIFEST_V089.json) and [delivery identity](paper/mlsys2027/evidence/DELIVERY_V089.md) bind the final files.

Two clean ZIP builds pass with exact raw per-page text equality. Three changed appendix pages were manually checked; the other 36 pages exactly match previously inspected pixels. Scientific CPU/data verification receipts are reused after hash verification, not described as new executions. [Closeout QA](paper/mlsys2027/evidence/REVIEW_CLOSEOUT_V089_QA.json) records the scope.

The [official 2027 format check](paper/mlsys2027/reviews/system_revision_v089/VENUE_PRECHECK_20261003.md) confirms 2025 style and the 10-page body limit. Style/bst bytes stay fixed. The CFP and homepage disagree by one hour on the deadline; the note preserves both times pending OpenReview confirmation.

Existing [Draft PR #51](https://github.com/leecdiang/HeteroSpec/pull/51) retains branch `paper/mlsys2027-rtx-integration-v0.8.7`. Parent is `4a4854575dcd1f652975bb008ceccbae0300d6c2`; main is `87b811e21a164468232cfea3c2404a1ebc869477`. The author-freeze tag remains peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. **B570/RTX/358H/M4 remain CLOSED.** No model execution, merge, release or conference submission is authorized by this closeout.

<details>
<summary>Preserved v0.8.8 status and earlier history</summary>

# Repository status — v0.8.8 author revision

Updated 2026-10-03. [Current handover](paper/mlsys2027/HANDOVER_CURRENT.md) controls active work.

- Existing Draft PR #51 is revised to v0.8.8, on `paper/mlsys2027-rtx-integration-v0.8.7` (historical branch name).
- Parent delivery: v0.8.7 `79327fd0c15e4d382b6264e9e780004b046fe5c1`. Direct PR base: main `87b811e21a164468232cfea3c2404a1ebc869477`. No merge or author-host checkout state is inferred.
- Scientific tag `mlsys2027-v0.8-author-freeze` remains peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`.
- Exact revision commit, artifacts and final remote verification are in [DELIVERY_V088.md](paper/mlsys2027/evidence/DELIVERY_V088.md) and [manifest](paper/mlsys2027/evidence/FINAL_ARTIFACT_MANIFEST_V088.json).

v0.8.8 follows the completed fixed-artifact v0.8.7 review. It reorganizes the paper around prospective trajectory prediction, same-set specified-candidate discrimination, and the resulting qualification/cost choices; 358H and M4 supply bounded optimization constraints. A new global system readout states what each result adds beyond a basic gate. New V4 absolute latency descriptors use only the existing 171 QPC records and do not replace the frozen GM/CI.

B570 H1 remains 72/72 reserved complete predictions against reference/live 60/72. RTX V4 remains UB2/live 51/57, replay 57/57, with /15 both comparators failing, /18 reference-only failure and /25 UB2-only failure. Its fresh cost gate remains batched 51/57 BLOCKED (speedup/CI null), serialized 57/57 QUALIFIED but slower: 0.677351 [0.661653,0.691812], 0/19 faster. A/B share 19 exposure-conditioned prompts; the earlier 0.646 belongs to a different study.

All campaigns remain CLOSED. No new GPU/model execution, merge, release or submission. Original arrays, estimates/seeds, versioned artifacts/reviews/scripts, numerical macros, official style and scientific author-freeze tag are preserved. The historical Figure 3 is moved into Appendix F with identical tex/PDF/caption and textwidth inclusion. Its numbering changes with relocation, not its data or geometry. Old scores apply only to v0.8.7; main-track significance remains a judgment, not a QA result.

## Verification scope

The final receipts bind two independent fresh source-ZIP builds, exact unnormalized per-page text comparison, PDF trailer/font/anonymity/reference checks, page inspection and the author response. The anonymous verifier executes twice in clean directories; two rehashed corrupt descriptor cases must fail. A separate NumPy implementation checks all 171 original QPC durations and all condition descriptors. Original compact studies and verifier bytes remain unchanged. These are CPU/build checks, not new hardware experiments or new review votes.

The prior nine-capsule V4 native-log audit is reused as a prior completed receipt; the full historical suites are not newly rerun. Unavailable old sequence ZIP/358H runtime traces, omitted runtime assets and original absolute chronology remain verification limits. The disclosed fan/host amendment remains recorded; it is not a rerun blocker under author instructions.

B570 dense scans, additional backends, 358H persistence and M4 variants remain deferred. The existing-material revision is complete when its final receipts pass; author assessment/merge and eventual release/submission are separate decisions.

<details>
<summary>Historical v0.8.7 living-pointer text, retained as history; not current instructions</summary>

# Repository status — v0.8.7 delivery candidate

Updated 2026-10-02. [Current handover](paper/mlsys2027/HANDOVER_CURRENT.md) is the first-read control file.

## Repository identities

- Candidate branch: `paper/mlsys2027-rtx-integration-v0.8.7`, based directly on main `87b811e21a164468232cfea3c2404a1ebc869477`. v0.8.7 is pending merge; this document does not assert that main has advanced.
- Baseline main contains v0.8.6 through #46, failed V3 history through #48, completed V4 evidence through #49 and independent raw closeout through #50. The old stacked #45 topology has already been resolved.
- Original v0.8.6 delivery remains `494a5ca4fe62534b032b37d01652c3f88e0d16e1`, with TeX source `da8d5739eb108de7f35d3a3cfbd954d42462f2e0`.
- Scientific author-freeze tag remains `mlsys2027-v0.8-author-freeze`, peeled `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. New delivery hashes are in the v0.8.7 manifest and delivery record. No author-host checkout state is inferred.

## Integration and verification

v0.8.7 adds same-set RTX V4 trajectory and matched qualification–cost tables, preserves original B570 centrality and all earlier failed/negative outcomes, and records V3 failure/exposure history in Appendix Q. Main is 10+2 pages, appendix 14; the internal section-removal proof is 9+2.

The source ZIP was independently extracted and built twice; all raw page-extracted text matches without normalization. All 37 PDF pages were visually inspected. Fonts, anonymity, references and logs pass; overfull boxes and unresolved citations/references are zero. The compact anonymous index preserves old arrays/inputs/verifier bytes and recomputes 285 A arrays, 171 B arrays/timer intervals and the frozen paired-prompt bootstrap. Ten invalid-evidence cases were rejected, with two independent clean anonymous-package executions. Figure 3's 71 checks were rerun.

These are integration checks, not fresh GPU experiments or acceptance evidence. The nine-capsule V4 native-log audit was completed before this integration; its unchanged [receipt](paper/mlsys2027/evidence/RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002.md) is reused with explicit scope. Other historical numeric/runtime/secondary receipts are not claimed as newly executed here.

## Results and decisions

V4 uses all 19 remaining exposure-audited tasks after excluding 145. A: UB2/live 51/57 (fails /15, /25), UB1 reference/live 51/57 (fails /15, /18), H2/live and R_ONLY/live 57/57. B: batched 51/57 BLOCKED, speedup/CI null; serialized 57/57 QUALIFIED, target/serialized 0.677351 [0.661653, 0.691812], 0/19 faster. Repetitions are not independent prompts; A/B share a cohort. Old 0.646 cost is separate. Native global micro-batch configuration also affects draft; B is a whole-path comparison, not a target-only causal intervention.

All campaigns are CLOSED. Under current finite claims, integration does not create a validity requirement for another B570 study. Importance and venue fit remain review judgments. The [fixed-artifact independent review](paper/mlsys2027/reviews/submission_v087/META_REVIEW_V087.md) is complete: one 3/6 weak reject, five 4/6 weak accepts, all confidence 4/5. No demonstrated central validity error or logically required new model execution was identified. Main-track significance remains disputed; do not infer acceptance probability from votes. Prioritize [existing-material revisions](paper/mlsys2027/reviews/submission_v087/REVISION_PRIORITY_V087.md); [do not execute B570 now](paper/mlsys2027/reviews/submission_v087/B570_DECISION_V087.md). Frozen artifacts were not edited during review.

B570 dense/all-block scanning, more backends, 358H persistence and M4 variants remain deferred/not authorized. Future B570, if separately approved, must use bounded single-block intervention followed by common continuation policy. No candidate/cohort expansion driven by results.

Remaining access limits include unavailable 358H runtime traces and the exact old v0.8.4 sequence ZIP. Offline hashes do not authenticate omitted assets or trusted absolute chronology. The disclosed host-policy amendment remains recorded; fan adjustment is not a rerun blocker under author instructions. Release and submission require separate decisions.

</details>

</details>

</details>

</details>

</details>

</details>
