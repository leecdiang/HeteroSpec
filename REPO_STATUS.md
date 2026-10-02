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
