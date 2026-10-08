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

# Manuscript status — v0.9.0 and new B570 evidence

Updated 2026-10-04. The separately authorized B570 prefill diagnostic study is **COMPLETE and CLOSED**. Its [delivery](https://github.com/leecdiang/HeteroSpec/blob/196ed563b36d0e16a3cdb667b6996a4afd98da1d/benchmarks/b570_prefill_diagnostic_v1/DELIVERY_REPORT.md) and [independent review](https://github.com/leecdiang/HeteroSpec/blob/main/paper/mlsys2027/reviews/b570_prefill_review_20261004/REVIEW_REPORT.md) supersede the PREPARE_ONLY study status preserved below.

All 360 planned formal units are valid, with zero failed formal attempts. T0/N0 and sealed T1/N1 each match 72/72 complete arrays and endpoints. Native/reference agreement changes from 60/72 to 72/72; all four original diagnostic tasks recover reference output and none of the 20 controls regresses. The 24 tasks were previously exposed; three repetitions establish stability. The independent review checks 120 G0 arrays, 30 sham pairs, frozen source identities and local prediction-seal order. The [read-only CPU audit](https://github.com/leecdiang/HeteroSpec/actions/runs/37178393741) validates all 30 remote parts and 4,073 manifest files.

The new evidence supports a bounded predictor-guided prefill intervention confirmed on native execution. It strengthens the practical diagnostic contribution. Generality, omitted external asset authentication and local-only chronology remain limitations; no performance, energy, functional-pass-rate or unique-kernel result is added. Historical v0.9.0 internal ratings of 3/6 are not updated scores for the new study or acceptance probabilities.

The manuscript delivery remains **v0.9.0**, fixed content `01682f3b992a11b36b309fbd6c9e9950f1dc5d89`: 10 body + 2 reference pages and a 17-page appendix. Its TeX/PDFs/ZIPs are unchanged by this evidence review. The B570 intervention has not yet been integrated into a new manuscript. Build and artifact instructions remain in the preserved delivery documentation below.

[Integration PR #52](https://github.com/leecdiang/HeteroSpec/pull/52) targets main and includes the previously reviewed #51 ancestor plus this study, review receipts and current-status reconciliation. Resolve the actual PR/main state on GitHub; this file does not predict its own containing merge SHA. Prior draft/unmerged wording below describes its historical delivery. The scientific author-freeze remains `mlsys2027-v0.8-author-freeze`, peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`.

Next: integrate the intervention and reference-recovery chain into the contribution, results and controls of a new manuscript, then independently review that exact delivery. The original B570/RTX/358H/M4 campaigns remain CLOSED. Public release and conference submission are separate decisions.

<details>
<summary>Preserved status before B570 prefill integration</summary>

# Manuscript status — v0.9.0 reassessment

Updated 2026-10-03. The [fresh reassessment](reviews/acceptance_reassessment_v090/ACCEPTANCE_REASSESSMENT_V090.md) supersedes the review status in the preserved history below. The manuscript remains v0.9.0.

Two new reviewers independently recommend **3/6 weak reject, confidence 4/5**. Both read all 12 main and 17 appendix text pages, inspect selected renders, and directly check retained arrays and costs. Their arithmetic agrees with the bounded claims; neither identifies a new material defect in the checked results. The remaining blocker is demonstrated systems significance: the simpler reproducer has not yet guided a discriminating intervention confirmed on native execution. These are internal simulated judgments, not acceptance probabilities. Historical v0.8.9 scores (3/6 and 4/6) are different reviewers' assessments of a different packet; there is no score evidence of improvement.

The [B570 diagnostic study plan](reviews/acceptance_reassessment_v090/DIAGNOSTIC_STUDY_PREPARE_ONLY.md) is **PREPARE_ONLY, not execution-ready or executed**. It proposes one target-prefill intervention on the four known divergent cases plus 20 regression controls, after new baseline, sham-transfer, state and instrumentation qualification. Five conditions with three repetitions would yield 360 planned complete arrays; these are not new observations. The [source check](reviews/acceptance_reassessment_v090/PREPARE_SOURCE_AUDIT.json) establishes caller-level facts only, not a prefill cause. Original B570/RTX/358H/M4 campaigns remain CLOSED.

Frozen delivery: [main PDF](manuscript/output/manuscript-v0.9.0.pdf), 10 body + 2 reference pages; [appendix](manuscript/output/appendix-v0.9.0.pdf), 17 pages; [document source](manuscript/output/overleaf-diagnostic-revision-v0.9.0.zip); [anonymous scientific package](manuscript/output/anonymous-evidence-index-v0.9.0.zip). All four are byte-identical to content commit `01682f3b992a11b36b309fbd6c9e9950f1dc5d89`. The [artifact manifest](evidence/FINAL_ARTIFACT_MANIFEST_V090.json) retains its original identity. No TeX build, historical verifier/bootstrap, model or GPU ran in this review round; earlier build and whole-page QA remain historical receipts for the same hashes.

New [systems review](reviews/acceptance_reassessment_v090/SYSTEMS_ACCEPTANCE_REVIEW.md), [evidence review](reviews/acceptance_reassessment_v090/EVIDENCE_ACCEPTANCE_REVIEW.md), and [coverage/consistency QA](reviews/acceptance_reassessment_v090/REVIEW_COVERAGE_QA.json) retain their individual judgments and limits. Only six living status files and new review/plan files change. Original scientific records, manuscript sources/PDFs/ZIPs, prior reviews, and scripts remain unchanged. Existing Draft PR #51 stays open and unmerged; no release or conference submission. Base/main stays `87b811e21a164468232cfea3c2404a1ebc869477`; author-freeze tag remains object `a3e33d405a53b8ee9fe4018d166b651001daa305`, peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`.

<details>
<summary>Preserved v0.9.0 diagnostic revision status and earlier history</summary>

# Manuscript status — v0.9.0

Updated 2026-10-03. This status supersedes the preserved history below. Read the [revision response](reviews/diagnostic_revision_v090/REVISION_RESPONSE_V090.md) for the implemented acceptance-reassessment requests and their limits.

v0.9.0 explains the tested B570/RTX reproduction tasks, adds complete-trajectory failure extents, and aligns the 358H optimization budget with the original prompt estimator. It quantifies M4 opportunity between two measured fixed modes and carries those conclusions through the whole paper. All analyses use retained records after outcomes were known. Original observations, primary GM/CI/seeds and all historical artifacts remain unchanged.

Current files: [main PDF](manuscript/output/manuscript-v0.9.0.pdf) (10 body + 2 reference pages), [separate appendix](manuscript/output/appendix-v0.9.0.pdf) (17 pages), [portable document source](manuscript/output/overleaf-diagnostic-revision-v0.9.0.zip), and [anonymous scientific package](manuscript/output/anonymous-evidence-index-v0.9.0.zip). The new scientific package retains every v0.8.8 member byte-identically and adds the new diagnostic calculator/data. The hardware-only PDF is an internal section-removal proof, not a submission artifact. [Manifest](evidence/FINAL_ARTIFACT_MANIFEST_V090.json) and [revision QA](evidence/REVISION_V090_QA.json) bind the files and checks.

Two clean source-ZIP builds agree on exact raw per-page text. Final 40-page visual coverage comprises 26 manually inspected final pages and 14 exact pixel matches to manually inspected pages from the current revision's first candidate. Fonts, citations, anonymity and page limits pass. The new diagnostic calculator passes twice in clean extractions. Historical verifier/bootstrap suites are not rerun; 319 protected files and all 30 historical scientific ZIP members retain their original bytes.

The [fixed v0.8.9 reassessment](reviews/acceptance_reassessment_v089/ACCEPTANCE_REASSESSMENT_V089.md) remains historical: systems 3/6 weak reject, evidence 4/6 weak accept. These are not v0.9.0 scores or acceptance probabilities. Concrete reproduction inputs and conditional budgets are now clearer; no actual bug fix or measured debugging saving is demonstrated. Main-track significance remains open to a fresh assessment. No further B570 experiment is needed for the current finite claims.

Existing [Draft PR #51](https://github.com/leecdiang/HeteroSpec/pull/51) keeps branch `paper/mlsys2027-rtx-integration-v0.8.7`. Revision parent is `c39461230f34554151dcfddafffb41ab938517dd`; main remains `87b811e21a164468232cfea3c2404a1ebc869477`. The author-freeze tag remains peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. **B570/RTX/358H/M4 remain CLOSED.** This revision authorizes no new model/hardware experiment, merge, release or conference submission.

<details>
<summary>Preserved v0.8.9 status and earlier history</summary>

# Manuscript Status — v0.8.9 review closeout

Updated 2026-10-03. This current status supersedes all historical wording below. [Final review](reviews/system_revision_v089/FINAL_REVIEW_V089.md) records the complete request mapping and remaining significance concern.

v0.8.9 completes the missed A6 prospective-path endpoint wording and the A9 Section Q entry. The scientific prose, observations, primary estimates and [v0.8.8 global system analysis](reviews/system_revision_v088/GLOBAL_SYSTEM_READOUT_V088.md) remain unchanged. Assessment: **Share with caveats**; finite claims are supported, while main-track significance remains an author judgment. This is an author closeout, not a fresh committee vote.

Current artifacts: [main PDF](manuscript/output/manuscript-v0.8.9.pdf) (10 body + 2 references), [separate appendix](manuscript/output/appendix-v0.8.9.pdf) (16 pages), [document source ZIP](manuscript/output/overleaf-system-revision-v0.8.9.zip), and unchanged [anonymous scientific evidence v0.8.8](manuscript/output/anonymous-evidence-index-v0.8.8.zip). The internal hardware-only proof is not a submission artifact. [Manifest](evidence/FINAL_ARTIFACT_MANIFEST_V089.json) and [delivery identity](evidence/DELIVERY_V089.md) bind the final files.

Two clean ZIP builds pass with exact raw per-page text equality. Three changed appendix pages were manually checked; the other 36 pages exactly match previously inspected pixels. Scientific CPU/data verification receipts are reused after hash verification, not described as new executions. [Closeout QA](evidence/REVIEW_CLOSEOUT_V089_QA.json) records the scope.

The [official 2027 format check](reviews/system_revision_v089/VENUE_PRECHECK_20261003.md) confirms 2025 style and the 10-page body limit. Style/bst bytes stay fixed. The CFP and homepage disagree by one hour on the deadline; the note preserves both times pending OpenReview confirmation.

Existing [Draft PR #51](https://github.com/leecdiang/HeteroSpec/pull/51) retains branch `paper/mlsys2027-rtx-integration-v0.8.7`. Parent is `4a4854575dcd1f652975bb008ceccbae0300d6c2`; main is `87b811e21a164468232cfea3c2404a1ebc869477`. The author-freeze tag remains peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. **B570/RTX/358H/M4 remain CLOSED.** No model execution, merge, release or conference submission is authorized by this closeout.

<details>
<summary>Preserved v0.8.8 status and earlier history</summary>

# Manuscript status — v0.8.8 and preserved history

Current candidate: **v0.8.8**, an author revision of existing Draft PR #51. Parent v0.8.7 HEAD `79327fd0c15e4d382b6264e9e780004b046fe5c1`; main remains `87b811e21a164468232cfea3c2404a1ebc869477`. Read [current handover](HANDOVER_CURRENT.md), [delivery](evidence/DELIVERY_V088.md) and [response](reviews/system_revision_v088/REVIEW_RESPONSE_V088.md).

v0.8.8 follows the completed fixed-artifact v0.8.7 review. It reorganizes the paper around prospective trajectory prediction, same-set specified-candidate discrimination, and the resulting qualification/cost choices; 358H and M4 supply bounded optimization constraints. A new global system readout states what each result adds beyond a basic gate. New V4 absolute latency descriptors use only the existing 171 QPC records and do not replace the frozen GM/CI.

B570 H1 remains 72/72 reserved complete predictions against reference/live 60/72. RTX V4 remains UB2/live 51/57, replay 57/57, with /15 both comparators failing, /18 reference-only failure and /25 UB2-only failure. Its fresh cost gate remains batched 51/57 BLOCKED (speedup/CI null), serialized 57/57 QUALIFIED but slower: 0.677351 [0.661653,0.691812], 0/19 faster. A/B share 19 exposure-conditioned prompts; the earlier 0.646 belongs to a different study.

All campaigns remain CLOSED. No new GPU/model execution, merge, release or submission. Original arrays, estimates/seeds, versioned artifacts/reviews/scripts, numerical macros, official style and scientific author-freeze tag are preserved. The historical Figure 3 is moved into Appendix F with identical tex/PDF/caption and textwidth inclusion. Its numbering changes with relocation, not its data or geometry. Old scores apply only to v0.8.7; main-track significance remains a judgment, not a QA result.

The global evidence/decision readout and system outlook are implemented, not just proposed. All v0.8.7 review requests are mapped to changes or a retained significance caveat. New artifact identity/QA replaces the current pointer while frozen prior review artifacts remain intact. Final pages/hashes are in [manifest](evidence/FINAL_ARTIFACT_MANIFEST_V088.json); build/CPU checks and actual page inspection are separate receipts.

<details>
<summary>Historical v0.8.7 living-pointer text, retained as history; not current instructions</summary>

# Manuscript status — v0.8.7 candidate and historical record

Current candidate: **v0.8.7**, branch `paper/mlsys2027-rtx-integration-v0.8.7`, directly based on main `87b811e21a164468232cfea3c2404a1ebc869477`. Pending merge; main at the baseline contains v0.8.6 and the closed RTX V4 evidence. Read [HANDOVER_CURRENT.md](HANDOVER_CURRENT.md), [delivery record](evidence/DELIVERY_V087.md) and [fixed-artifact review](reviews/submission_v087/) for current decisions.

v087 integrates same-set RTX UB2/replay discrimination and fresh matched qualification–cost, preserving original B570 prospective72/72 as the center. Main10+2 pages; appendix14; internal proof9+2. Two independent clean builds and37-page visual inspection are complete. No new model/GPU execution;scientific tag,arrays,macros,Figure3,style and old artifacts unchanged. Existing campaigns remain CLOSED;B570 dense scan is deferred/not authorized. Review significance judgments are separate from validity and build checks.

Completed fixed-artifact review: one 3/6 weak reject and five 4/6 weak accepts, all confidence 4/5; no demonstrated central validity error or logically necessary new execution. [Meta-review](reviews/submission_v087/META_REVIEW_V087.md) retains the significance disagreement. [Existing-material requests](reviews/submission_v087/REVISION_PRIORITY_V087.md) remain unapplied to the frozen PDFs. [B570 recommendation](reviews/submission_v087/B570_DECISION_V087.md): do not execute now; bounded single-block/common-policy design remains an optional future study.

<details>
<summary>Repository-state pointer before v0.8.7 integration, preserved 2026-10-02</summary>

# Manuscript status — current pointer and historical record

Current manuscript: **v0.8.6 on main** through PR #46, integration anchor `361cb43a67f7fd9bfae95de4cdf7e816c46bbe90`. Later documentation commits may follow this anchor. Read [HANDOVER_CURRENT.md](HANDOVER_CURRENT.md) for live status and [manuscript/README.md](manuscript/README.md) for current build entries.

PR #44 entered main first; #45 merged into its old v0.8.5 branch; #46 brings the identical v0.8.6 delivery into main. The scientific author-freeze tag is unchanged. RTX A+B protocol preparation is next; no new A/B reserved/model measurement is performed by this maintenance. B570/358H/M4 expansions are deferred.


</details>

All text below is preserved history. A historical heading containing current, next, Draft or unmerged retains its date/version meaning and does not override the canonical handover.

<details>
<summary>Historical manuscript status before repository reconciliation on 2026-10-01</summary>

# Current manuscript status — v0.8.6

Current convergence draft is on `paper/mlsys2027-convergence-v0.8.6`, stacked
on the unmerged v085 branch at `dccbbb53e1f91d3239e2075336100795dd6daa1e`.
Main remains `98e8470f2559f78335de8d3473997d21b4bb55b8`; v086 is not merged.
Current outputs, exact content commit, QA and handover are in
`evidence/FINAL_ARTIFACT_MANIFEST_V086.json`, `evidence/DELIVERY_V086.md`,
`HANDOVER_CURRENT.md` and `reviews/convergence_v086/`.

Main10+2 pages, appendix12, internal proof9+2. No inference or hardware
measurements were made; new analyses are explicitly post-study existing-record
calculations. Original experiment/macro/style/Figure3/older-output bytes and
scientific tag are preserved. Historical versioned records remain history.

<details>
<summary>Historical pre-v086 status; not current instructions</summary>

# Current handover — v0.8.5

The active draft integrates already merged B570 intervention, RTX independent
proposal/replay and freshly qualified matched cost evidence. Base and starting
worktree HEAD: `98e8470f2559f78335de8d3473997d21b4bb55b8`.
Branch: `paper/mlsys2027-evidence-integration-v0.8.5`.

Use `manuscript/README.md` for the tested current build/QA entries and
`reviews/integration_v085/AUTHOR_HANDOVER_V085.md` for review delivery.
Content and delivery commit roles plus artifact hashes are recorded in
`evidence/FINAL_ARTIFACT_MANIFEST_V085.json` and `evidence/DELIVERY_V085.md`.

Current pagination: main 10 body + 2 references, separate appendix 10,
internal hardware-only proof 8 body + 2 references. The build uses current
sources in new directories and independently recompiles the final source ZIP.
Manual page review and automated checks have separate receipts.

New-study boundaries: B570 72/72 changed scores, 0/72 immediate ID decisions,
18/72 differing continuations on 6/24 prompts; persistent alternate UB128.
RTX failed H1 24/36, zero reserved; V2 H2/live 72/72 on 24×3 but reference/live
60/72 blocked, shared numerical runtime. New RTX cost qualifies 90/90 direct
IDs and is slower: target/serialized 0.646 [0.630, 0.660]. Original H1, old
historical timing/Figure 3 and qualification-only counts remain distinct.
M4 Guard's adverse fixed-policy comparison and 358H stopped runtime/no-energy
and inseparable replay-plus-proposal boundaries remain visible.

This is an integration draft awaiting a separate author-initiated review.
No new inference/measurement/search, simulated decision, merge, tag, release,
OpenReview submission, email or invitation was performed. Scientific
untested scope is not a build blocker and does not authorize new experiments.

---

The following entries are historical status snapshots. They do not override the current v0.8.5 build or the author’s integration authorization.

# v0.8.2 — final clean-room textual fixes (Draft PR)

Starting merged main: `2f4a38c316d6d4683822e6a24a74bddad9d3117f` (observed for this revision, not a permanent current-main pointer). Four original PDF-only clean-room review files are included under `reviews/final_clean_room_v081/`. Their final gate is **READY AFTER MINOR TEXTUAL REVISION**; **new experiment required: NO**.

The manuscript changes only the abstract's complete generated-token-ID reserved endpoint wording and one Introduction sentence separating prospective direct-ID qualification from historical timing. Title, contribution structure, section headings, results, figures, numerical macros and closed evidence remain unchanged. Current v0.8.2 PDFs and source ZIP are built separately from retained v0.8.1 outputs; results are in `evidence/FINAL_SUBMISSION_QA_V082.json` and exact wording in `evidence/FINAL_CLEANROOM_FIXES_V082.md`.

Human authors review and approve the new Draft PR before merge. After merge, run QA against that exact merged commit, then create an annotated submission-candidate tag pointing to the post-merge commit. Complete OpenReview author/conflict checks and upload. No merge or candidate tag occurs in this revision task.

---

# v0.8.1 — final title and author-review preparation (Draft PR #37)

Current title: **Execution-Path Qualification and Realized Costs in Speculative Decoding on Consumer Systems**. Running title: **Execution-Path Qualification in Speculative Decoding**. The only headline change in this finalization is the authorized title; sections, claim wording, closed evidence, numerical values and figures remain unchanged. `reviews/AUTHOR_REVIEW_NOTE_V081.md` and `SUBMISSION_UPLOAD_CHECKLIST.md` guide human review and upload. Updated PDFs/source ZIP retain v0.8.1 filenames; older versions and historical records below remain intact.

Keep PR #37 Draft and unmerged until human author approval. After approval and merge, perform final QA on the merged commit, then create the annotated submission-candidate tag; no candidate tag is created in this task. Final build results are recorded in `evidence/FINALIZATION_QA_V081.json`. Query repository main at session start; the immutable scientific baseline is the author-freeze tag.

---

# v0.8 — B570 mechanism prediction integration (Draft PR)

Starting `main`: `00da1d00bd24328826b04db10b481c56fbba4f3e` (merged PR #34). Branch: `paper/mlsys2027-mechanism-integration-v0.8`. The final delivery HEAD is the Draft PR head, recorded in the PR and final delivery report; a SHA cannot be embedded in its own commit. No main edit or automatic merge was performed.

The closed B570 study selected H1 target-execution-partition sufficiency after 36/36 exposed discovery agreement. Hypothesis freeze commit `313069ce5ac10d4d31849f515c912cad29ac7360` (2026-09-29 10:35:25 UTC) precedes reserved inference. All 72 reserved predictions were committed at `c99aaf2082ffff46741bef6f69dd96b4654d4c08` (11:04:57 UTC) before live serialized outcomes; prediction-file SHA-256 `0201ccd1f67492510d34be567aa83f1c38d3bd1f162a970c05d3cea9d3957826`. The reserved result is 72/72 complete predictor-to-live sequences, 24/24 prompt classes, 12/12 divergent-pair first-divergence indices and four/four divergent prompts. Predicted and actual reference equality is 60/72, BLOCKED. The mechanism is sufficient for the tested B570 trajectory, not a unique kernel or an RTX explanation. No new inference, performance, energy or parameter experiment was run during this integration.

The main PDF has **10 body pages plus one reference page**; the separate appendix has **six pages**; hardware-only is **10 pages total**. Figure 3 remains the v0.7 two-panel PDF byte-identical to base; no new figure or main table was added. Section 5.2 and appendix J contain the mechanism chronology. Exact build PDFs and Overleaf bundle are under `manuscript/output/` with `v0.8` suffixes; v0.7 outputs are retained. Clean source ZIP recompilation matches page count and extracted text. Every final main/appendix page was rendered and visually inspected; the appendix seven-page draft's orphaned final paragraph was repaired.

`evidence/MECHANISM_INTEGRATION_QA_V08.json` records **114 freshly run local offline checks** (mechanism projections, all 72 pair records, manuscript claim boundaries, PDF/anonymity/fonts/TeX and prior receipt presence). Existing v0.7 receipts report 228 historical numerical, 136 runtime, 638 M4 paired-secondary, 2,459 direct-ID integration and 67 Figure 3 checks; these were **inspected, not rerun** in this connector-supplied partial workspace. The 87 MB B570 archive verifier likewise was not freshly rerun here; committed independent/portable PASS receipts (5,681 and 5,696 checks) and extracted validation were inspected. This limit is explicit in the new QA receipt. Scientific claims and closed evidence files were not modified.

Internal model-review simulations in `reviews/submission_v08/` assess the actual v0.8 PDF. The mock decision is **Borderline, lean Weak Accept (moderate 3/5 confidence)**, from v0.7 Weak Reject. The frozen 72/72 prediction materially answers the missing within-stack explanatory/predictive result, while the strongest remaining objection is transfer and practical reach beyond one B570 model/build/workload configuration. These are not external conference reviews. `HANDOVER_CURRENT.md` is the first-read current handover; it should be refreshed after this PR merges.

---

# v0.7 — prospective direct-ID qualification integration

**HARDWARE + RUNTIME CHARACTERIZATION WITH PROSPECTIVE DIRECT-ID
QUALIFICATION REPLICATIONS; DRAFT FOR AUTHOR REVIEW.** This is not a final
submission or an accepted paper.

- Starting main: `bab0e44c74f7fa59d2ea42faf4dcf4c51a78e674`.
- Integration branch: `paper/mlsys2027-direct-id-integration-v0.7`.
- Branch HEAD at artifact freeze: `1ea5c6e09d01c3219631f183fc1934db84955a66`.
  The final delivery commit adds review/status/visual disposition and helper
  portability repairs; its exact HEAD is the Draft PR head and final delivery
  response. A document cannot embed its own containing commit SHA.
- Main was independently rechecked on GitHub and remains the required base.

## New evidence and preserved boundaries

RTX batched: **75/90 exact pairs, 25/30 wholly exact prompts, BLOCKED**.
RTX serialized: **90/90, 30/30, QUALIFIED**. B570 fast: **60/90, 20/30,
BLOCKED**. B570 serialized: **78/90, 26/30, BLOCKED**. Each study completes
270 executions and 180 comparisons. No passing subset qualifies.

The studies share HumanEval30 IDs, model pair, greedy k=2, three repetitions,
and a 90/90 rule. Runtime, reference, frontend and context differences preclude
causal hardware ranking. Serialization changes tested qualification, but is
not a portable correctness certificate. New qualification is separate from
historical physical/timing evidence and the historical CUDA mechanism capture.
No historical timing is retroactively certified; old B570 counts and all
protected evidence, archives, old outputs and approved v0.5 figures are intact.
Section 7 and its runtime table are unchanged from the starting main.

Independent offline replay verifies archive SHA-256 and included records:

- RTX: `fc3676adae93c4f21bf6e29d9787d95d1e60d08c2d7223de30fc58c46c3e0822`.
- B570: `58daa4159de12042c73194bbd99abc5e5e23c171578ea873675f07901582db20`.

The portable replay verifies recorded identities of omitted weights/binaries;
it does not freshly rehash those absent assets. RTX v1 transport and B570's
zero-inference launcher failure remain disclosed; no campaigns were reopened.

The M4 paired secondary result remains Guard/Always-Spec latency
**1.0270760219826773**, CI **[1.0129560055428655, 1.0435592653980876]**,
24 Guard-faster and 36 Always-faster prompts. Guard is slower on this frozen
comparison, despite remaining profitable against target-only.

## Builds and QA

- Main: **10 body pages + 1 reference page**. Appendix: **5 pages**.
  Hardware/reference build: **9 body pages + 1 reference page**.
- Full, appendix and hardware builds pass. The source ZIP clean-compiles main
  and appendix with matching page counts and all page text; original official
  style bytes are unchanged. The build used Tectonic with official Times
  encoding, without font substitution, font-size or margin changes.
- Historical numerical: **228 PASS**. Narrative: **260 protected files,
  57 historical macros PASS**. Runtime: **136 checks, 29 sourced macros PASS**,
  retaining all 117 old gates plus 19 paired-secondary gates.
- M4 primary archive: **62 payload hashes PASS**; independent paired-secondary
  replay: **638 checks PASS**; unchanged rejection/replay tests: **7 PASS**.
  Submission projection: **41 checks PASS**.
- Direct-ID integration: **2459 checks PASS**, including protected base blobs;
  Figure 3: **67 independent checks PASS** including actual vector coordinates.
  Both direct-ID archives replay independently; all 180 comparisons per study
  are reproduced from native events/sidecars.
- All 15 references retain full author lists. Anonymous PDFs, embedded fonts,
  resolved citations/references, zero overfull boxes and no substitutions: PASS.
- Every delivered page was rendered at 150 dpi and inspected: **26/26 PASS**.
  Figure 3 actual vector PDF was inspected in color/grayscale at 96 and 200 dpi.

Figure 3 is the versioned **6.75 × 2.12 inch** two-panel vector PDF/SVG.
A retains all eleven historical target-forward micro cells with path shapes
and no qualification encoding. B has exactly four direct-ID rows and a visible
90/90 gate; open/filled markers and written labels survive grayscale.
It stays with the qualification synthesis on main page 7. Counts and caption
are readable, with no clipping or annotation overlap. Closely spaced historical
markers rely on Table A3 for exact lookup, as disclosed in the visual review.
All other approved figure assets remain byte-identical.

## Fresh submission assessment

Seven independent model-review simulations inspect the actual frozen v0.7 PDFs
without reading one another's reports. Meta-review, mock decision and A–E delta
are under `reviews/submission_v07/`. These are not external human peer reviews.
The new evidence strengthens validity and the replicated qualification core;
conference-level significance remains a substantive author-review question.
The fresh mock decision is **Weak Reject, moderate confidence (3/5)**. Rigor and
champion support bounded weak acceptance; the central remaining objection is
limited transferable explanatory/predictive reach, not a demonstrated invalid
endpoint. See the explicit v0.5-to-v0.7 A–E delta and unexecuted recommendations.
The exact added/changed file manifest and output hashes accompany delivery.
No recommended future experiment is authorized or executed by this integration.

---

# v0.6 paired M4 Guard versus Always-Spec secondary analysis

Current integration base: `9b996dd702e5807b3cacc9db9c69aa7eb80035a4` (main after PR #29).
The original scientific starting point below is retained as provenance.
The conflict in Table 3 was resolved by retaining the approved compact three
primary rows and adding the clearly separated paired secondary block. Approved
Fig. 1/3/4 assets and the original mechanism diagram are byte-identical to latest
main. All frozen primary and secondary results, plan and formulas are unchanged.
Full QA and rendered-page review were refreshed on this combined version.

Current review: `reviews/M4_GUARD_ALWAYS_SECONDARY_RESPONSE_V06.md`. Current
PDFs: `manuscript/output/manuscript-v0.6.pdf` and `manuscript/output/appendix-v0.6.pdf`.
This reviewer-requested post-study contrast uses only frozen raw observations:
Guard/Always-Spec = 1.0270760219826773, 95% prompt-bootstrap interval
[1.0129560055428655, 1.0435592653980876]. The interval lies above parity;
Guard had higher latency on this comparison. Prompt medians favor Guard on
24 prompts and Always-Spec on 36, with no ties. No new measurement or policy
change occurred. All v0.5 review qualifications remain in force.

## v0.6 validation and visual review

- Main paper: **10 body pages + 1 reference page**; separate appendix: **4 pages**.
- Hardware-only removal/reference check: **9 body pages + 1 reference page**.
- **228** historical numerical checks; **260** protected narrative/source/assets;
  **57** historical macros; **117** prior runtime checks preserved in order plus
  **19** new checks (**136** total), with **23** primary and **6** secondary macros.
- Full primary archive replay: all **62** payload hashes, frozen policy, direct-ID
  qualification/formal pairs, primary intervals and fallback reproduced.
- Independent secondary path: **638** checks, all 60 prompt medians and ratios,
  exact headline and finite-bootstrap endpoints, and descriptive counts.
- **7** hardware-free replay/rejection tests; **41** submission scope/projection
  checks. All **41** pre-existing runtime-tree files and all **40**
  pre-existing paper evidence files are byte-identical to the latest integration main.
  All prior main PDFs/ZIP and approved manuscript figure files are also preserved.
- Main, appendix, and hardware-only builds passed. Official style unchanged;
  fonts embedded, PDFs anonymous, no unresolved citations/references or overfull
  boxes. The **37-file** source ZIP also compiled in a clean directory.
- Fresh visual review covered every main/appendix page and detailed full-page
  inspection of main pages 9–10 and appendix page 4: Table 3's separated contrast
  and direction, literal interpretation, limitations, formula and provenance
  note are readable and fit without clipping or overlap. No new figure.

Receipts: `evidence/M4_GUARD_ALWAYS_SECONDARY_QA_V06.json`,
`evidence/M4_GUARD_ALWAYS_SECONDARY_TEST_QA_V06.json`,
`evidence/M4_GUARD_ALWAYS_SECONDARY_VISUAL_QA_V06.json`, and the versioned
`NUMERICAL`, `RUNTIME`, `NARRATIVE`, `NARRATIVE_FIGURE`, `NARRATIVE_PDF`, and
`SUBMISSION` v0.6 receipts. Previous receipts and PDFs match latest main, including PR #29
review updates. The artifact comparison sharpens the existing negative/control
conclusion; no result-dependent analysis choice or new measurement occurred.

# v0.5 coordinated submission review

Current review: `SUBMISSION_REVIEW_V05.md`. Current PDFs: `manuscript/output/*-v0.5.pdf`. Independent reports and disposition: `reviews/submission_v05/`. Historical comparator claims are narrowed by `evidence/SUBMISSION_COMPARATOR_SCOPE_V05.md`; closed values and evidence classes remain unchanged. Runtime integration is complete; no new timing or policy search was performed.

The previous status below is retained as history.

---

# Manuscript v0.4 — measured runtime integration

Current status: **MEASURED HARDWARE + BOUNDED PROSPECTIVE RUNTIME STUDY; DRAFT FOR AUTHOR REVIEW** — 2026-09-25.

Base main: `bbf0c555cc50242f85c086eac342c9deb5c2e945`. Branch: `paper/mlsys2027-runtime-integration-v0.4`. The exact delivery HEAD is the Draft PR head; `RUNTIME_INTEGRATION_V04.md` records scope and QA.

Section 7 now connects qualification to realized-cost control: the tested 358H intervention is qualification-blocked with no R2 performance result, and the separately frozen M4 guard is exact and profitable against target-only. The Guard does not beat fixed speculation's aggregate point estimate. Runtime energy is not claimed. The metadata-recording defect and independent M4 provenance recovery remain disclosed. Hardware campaigns and figures remain unchanged.

Current artifacts are `manuscript/output/manuscript-v0.4.pdf` (10 body pages + 1 reference page), `manuscript/output/appendix-v0.4.pdf` (4 pages), and the current v0.4 collaboration ZIP. The old v0.3 ZIP/PDFs below are historical. Four main figures retain native sizes on pages 4–7; new Table 3 reports M4 runtime ratios, CIs and descriptive oracle regret. Title retained.

Canonical build/check passes: 228 original numerical checks, 260 protected-file checks, all 57 prior prose numeric macros, 117 runtime checks and 23 sourced runtime macros, five original figure replays, active asset/placement checks, embedded fonts, anonymous PDFs, full-author references, zero overfull boxes and unresolved citations/references. Hardware-only removal remains an internal reference test (9 body + 1 reference page), not the primary paper or a standalone hardware manuscript.

Humanizer was used after claims/citations were frozen. Eight style edits preserved numerical literals, TeX commands and citations; each scientific assertion was manually checked. A later layout-only page break separates hardware appendix tables from runtime notes. All final main and appendix pages were rendered and inspected, including the runtime table in 96-dpi grayscale. The final body page has a normal unused right column; the conclusion is complete in the left column. No geometry or font changes were used.

Remaining reviewer risks: modest controller novelty; one model/runtime and finite held-out workload; M4 session/thermal uncertainty; 358H compact diagnostic provenance without local raw-trace replay. Full v0.2 raw qualification outputs are not present locally; their disposition is supplied by the task closeout, with pinned transition/protocol/diagnostic corroboration. These limits are not resolved by the integration.

No new hardware/runtime timing was performed. No closed experiment result was modified. The PR is Draft and must not be automatically merged.

---

# Initial manuscript v0.3 — collaboration freeze

**INITIAL DRAFT FROZEN FOR OVERLEAF COLLABORATION** — 2026-09-22.

This v0.3 status is historical. The v0.2 record below is also historical and is superseded where it describes active figures, page counts, validator invocation, or unresolved integration decisions.

- Starting main: `9014e4b8a89031cfa26fc2c03180181bee124d86`. Fetched, checked out main, confirmed this exact HEAD and a clean working tree before creating the requested integration branch.
- Branch: `paper/mlsys2027-initial-draft-v0.3`.
- Integration branch HEAD at the artifact-freeze checkpoint: `8ea0be7ae0e18e733e12405b136f58460473dfba`. The follow-up documentation commit records this already-built artifact revision. Resolve the delivery HEAD with `git rev-parse paper/mlsys2027-initial-draft-v0.3`; the Draft PR head identifies the final documentation revision.
- Delivery target: Draft PR against `main`; no automatic merge.
- Hardware evidence: closed and unchanged. Cross-platform synthesis: retrospective; campaign primary outcomes were frozen independently. Later controls retain their bounded evidence classes.
- Runtime/software: full Section 7 retained, proposed and unmeasured, including requirements, persistent-state interface, qualified path selection, and evaluation questions. Future evaluation must be a new frozen study. No implementation or result is claimed.

## Current artifacts and displays

| Artifact | Pagination |
|---|---|
| `manuscript/output/manuscript-v0.3.pdf` | 10 body pages + 1 reference page |
| `manuscript/output/appendix-v0.3.pdf` | 3 separate pages |
| `manuscript/build/hardware-only/hardware-only.pdf` | 8 body pages + 1 reference page; verification build only |
| `manuscript/output/overleaf-initial-draft-v0.3.zip` | 35 required source/dependency files; clean local compilation verified |

| Main figure | Semantic label | Asset relative to `figures/` | Page / width |
|---|---|---|---|
| 1: M4 independent observed contrast | `fig:m4` | `style_v04/pdf/m4.pdf` | 4 / 3.25 in |
| 2: measured translation boundaries | `fig:translation` | `mechanism_v05/mechanism.pdf` | 5 / 6.75 in |
| 3: verification-path qualification | `fig:verification` | `style_v04/pdf/verification.pdf` | 6 / 6.75 in |
| 4: isolated versus realized 358H cost | `fig:state` | `style_v04/pdf/state.pdf` | 7 / 6.75 in |

All assets are unchanged from the specified main, including Candidate B after PR #24. Only the manuscript mechanism caption adopts “does not survive the tested stateful integration.” The source `mechanism_v05/caption.tex` is untouched.

Main tables remain platform scope (Table 1, p. 3) and headline outcomes (Table 2, p. 5). The old overview is inactive; the old verification table is removed from the main flow and reproduced in appendix A3, retaining its five rounded ranges and qualification labels plus all 11 underlying context cells. Historical sources remain in place.

| Appendix display | Contents | Page |
|---|---|---|
| A1 | Frozen statistical policies | 2 |
| A2 | Sensor boundaries and allowed energy interpretations | 2 |
| A3 | Verification context lookup and original rounded ranges | 3 |
| A4 | Eight-case regime inventory, including unchanged 358H P/M labels | 3 |

The inventory uses the unchanged v0.4 booktabs source instead of the old graphical inventory. No active `fig:overview`, `fig:regimes`, or main-paper `tab:mechanism` reference remains.

## Verification and visual review

The ordinary `make check` passes: **228/228 numerical checks**, all five independent historical figure replays, the three active quantitative style receipts, the final schematic hash, four actual native-width placements, all 11 lookup cells, and eight inventory cases. Narrative checks preserve 260 protected-file entries (including overlapping checks), all 57 prior prose numerical macros, the complete figure tree, and the scientific ledger. Raw/processed records, scientific closeouts, original numerical validator, official template and bibliography are unchanged.

Both delivery PDFs pass anonymity checks on text, metadata and links; all fonts, including nested figure resources, are embedded. All 13 references retain full author lists. There are no overfull boxes or undefined references/citations. The official style's harmless empty-anchor warning remains. QA records and hashes are under `evidence/`.

Every page of the final full manuscript (11) and appendix (3) was rendered and visually inspected at 1,500 pixels on the long edge, preserving publication geometry. Figure placement checks confirm the actual 3.25/6.75-inch sizes. The verification page was also inspected in grayscale at 96 dpi: open/filled status marks, shapes and labels remain distinguishable. Hardware-only pp. 7–9 were additionally inspected for the synthesis, related work, limitations, conclusion and references.

All figures and captions are readable and unclipped. Consecutive wide floats occupy pp. 5–7 within the relevant results/diagnosis sequence, without an unintended blank page or drift into an unrelated later section. M4 is a normal top-of-page float on the page where its results begin. The final body page leaves the right column unused before the separate reference page; appendix p. 3 uses normal vertically centered table-float spacing. These are retained initial-draft whitespace, not a reason to shrink artwork, alter the official template, or compress runtime.

## Overleaf handoff and freeze scope

**Ready to become the shared Overleaf initial draft: yes.** Upload the source ZIP as a new project, use pdfLaTeX / TeX Live 2025, and select `main.tex`; select `appendix.tex` for the separate supplement. The bundle has been compiled in an independent directory. Its page counts and every page's extracted text match the reviewed PDFs, and its selected figures, inventory body, and style files retain their original bytes. No Overleaf project, upload, invitation, or submission was performed.

**Coherent without future software results: yes.** The observed outcomes, two configuration-scoped diagnoses, and standalone hardware synthesis do not depend on the proposed intervention. The full runtime reservation remains in the collaboration version. The hardware-only build is a coherence check, not a scope reduction.

The freeze covers the hardware story, scientific boundaries, figure language and manuscript structure. It is not a final submission, a final title/abstract, or a completed runtime contribution. `NARRATIVE_INTEGRATION_V03.md` records the integration decisions and validation boundaries.

---

# Manuscript v0.2 — narrative and selected publication figures

Integration completed: 2026-09-21. For the subsequent internal review and conservative revision, see the follow-up at the end of this record. Integration branch: `paper/mlsys2027-narrative-v0.2`.

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

## Independent internal review and conservative revision — 2026-09-21

The next pass reviewed PR #18 at exact HEAD `afda6a192f3e9359eb5f5d7d24d3313bf59ef2f3` using three independent experimental-rigor, systems-contribution and presentation reviewers. Their complete initial reviews, meta-review and revision disposition are in `reviews/INTERNAL_REVIEW_V02.md`; the review was committed before any manuscript edit. The follow-up branch is `codex/mlsys2027-review-v02` and its Draft PR targets the narrative branch, not main.

Unanimously supported prose corrections make the retrospective synthesis explicit, distinguish independently frozen primary outcomes and later bounded controls, align prominent latency wording with post-prefill decode, name separate M4 sessions in the abstract, soften isolated state-cost causality, and present accounting as a method. All numerical results, estimators, evidence classes, correctness statuses, tables, bibliography, scientific records and the selected figure tree remain unchanged. The overview's manuscript caption wrapper changes one timing phrase; the publication artwork is untouched.

The resulting main PDF remains 10 body pages plus 1 reference page, the unchanged appendix remains 3 pages, and removing runtime leaves 9 body pages plus references. The original 228 numerical checks, five figure checks, protected-source checks, numeric-macro coverage and anonymous PDF checks pass. The historical narrative path allowlist required one explicit in-memory exception for the new review file; no validator was edited, and unmodified `make check` still needs that path exception. The review report records the reproducible invocation and final hashes.

The prior integration pass's absence of identified wording defects is a historical assessment, superseded by this review's concrete corrections and remaining concerns. The paper still requires author decisions on incremental novelty, runtime submission scope, mechanism-table duplication, caveat consolidation and the final title. Conservative copyediting does not make it submission-ready.

All 11 revised main-PDF pages were visually inspected after the final build, split between the coordinating editor (pp. 1–6) and Reviewer C (pp. 7–11). The state figure, synthesis/runtime transition, conclusion and references remain correctly placed. Reviewer C additionally inspected the changed hardware-only ending; the byte-identical appendix retains its complete prior inspection.

</details>

</details>


</details>

</details>

</details>

</details>

</details>

</details>

</details>

