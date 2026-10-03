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
