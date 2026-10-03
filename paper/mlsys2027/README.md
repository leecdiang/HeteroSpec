# MLSys 2027 manuscript — v0.9.0

Updated 2026-10-03. This status supersedes the preserved history below. Read the [revision response](reviews/diagnostic_revision_v090/REVISION_RESPONSE_V090.md) for the implemented acceptance-reassessment requests and their limits.

v0.9.0 explains the tested B570/RTX reproduction tasks, adds complete-trajectory failure extents, and aligns the 358H optimization budget with the original prompt estimator. It quantifies M4 opportunity between two measured fixed modes and carries those conclusions through the whole paper. All analyses use retained records after outcomes were known. Original observations, primary GM/CI/seeds and all historical artifacts remain unchanged.

Current files: [main PDF](manuscript/output/manuscript-v0.9.0.pdf) (10 body + 2 reference pages), [separate appendix](manuscript/output/appendix-v0.9.0.pdf) (17 pages), [portable document source](manuscript/output/overleaf-diagnostic-revision-v0.9.0.zip), and [anonymous scientific package](manuscript/output/anonymous-evidence-index-v0.9.0.zip). The new scientific package retains every v0.8.8 member byte-identically and adds the new diagnostic calculator/data. The hardware-only PDF is an internal section-removal proof, not a submission artifact. [Manifest](evidence/FINAL_ARTIFACT_MANIFEST_V090.json) and [revision QA](evidence/REVISION_V090_QA.json) bind the files and checks.

Two clean source-ZIP builds agree on exact raw per-page text. Final 40-page visual coverage comprises 26 manually inspected final pages and 14 exact pixel matches to manually inspected pages from the current revision's first candidate. Fonts, citations, anonymity and page limits pass. The new diagnostic calculator passes twice in clean extractions. Historical verifier/bootstrap suites are not rerun; 319 protected files and all 30 historical scientific ZIP members retain their original bytes.

The [fixed v0.8.9 reassessment](reviews/acceptance_reassessment_v089/ACCEPTANCE_REASSESSMENT_V089.md) remains historical: systems 3/6 weak reject, evidence 4/6 weak accept. These are not v0.9.0 scores or acceptance probabilities. Concrete reproduction inputs and conditional budgets are now clearer; no actual bug fix or measured debugging saving is demonstrated. Main-track significance remains open to a fresh assessment. No further B570 experiment is needed for the current finite claims.

Existing [Draft PR #51](https://github.com/leecdiang/HeteroSpec/pull/51) keeps branch `paper/mlsys2027-rtx-integration-v0.8.7`. Revision parent is `c39461230f34554151dcfddafffb41ab938517dd`; main remains `87b811e21a164468232cfea3c2404a1ebc869477`. The author-freeze tag remains peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. **B570/RTX/358H/M4 remain CLOSED.** This revision authorizes no new model/hardware experiment, merge, release or conference submission.

<details>
<summary>Preserved v0.8.9 status and earlier history</summary>

# Readme — v0.8.9 review closeout

Updated 2026-10-03. This current status supersedes all historical wording below. [Final review](reviews/system_revision_v089/FINAL_REVIEW_V089.md) records the complete request mapping and remaining significance concern.

v0.8.9 completes the missed A6 prospective-path endpoint wording and the A9 Section Q entry. The scientific prose, observations, primary estimates and [v0.8.8 global system analysis](reviews/system_revision_v088/GLOBAL_SYSTEM_READOUT_V088.md) remain unchanged. Assessment: **Share with caveats**; finite claims are supported, while main-track significance remains an author judgment. This is an author closeout, not a fresh committee vote.

Current artifacts: [main PDF](manuscript/output/manuscript-v0.8.9.pdf) (10 body + 2 references), [separate appendix](manuscript/output/appendix-v0.8.9.pdf) (16 pages), [document source ZIP](manuscript/output/overleaf-system-revision-v0.8.9.zip), and unchanged [anonymous scientific evidence v0.8.8](manuscript/output/anonymous-evidence-index-v0.8.8.zip). The internal hardware-only proof is not a submission artifact. [Manifest](evidence/FINAL_ARTIFACT_MANIFEST_V089.json) and [delivery identity](evidence/DELIVERY_V089.md) bind the final files.

Two clean ZIP builds pass with exact raw per-page text equality. Three changed appendix pages were manually checked; the other 36 pages exactly match previously inspected pixels. Scientific CPU/data verification receipts are reused after hash verification, not described as new executions. [Closeout QA](evidence/REVIEW_CLOSEOUT_V089_QA.json) records the scope.

The [official 2027 format check](reviews/system_revision_v089/VENUE_PRECHECK_20261003.md) confirms 2025 style and the 10-page body limit. Style/bst bytes stay fixed. The CFP and homepage disagree by one hour on the deadline; the note preserves both times pending OpenReview confirmation.

Existing [Draft PR #51](https://github.com/leecdiang/HeteroSpec/pull/51) retains branch `paper/mlsys2027-rtx-integration-v0.8.7`. Parent is `4a4854575dcd1f652975bb008ceccbae0300d6c2`; main is `87b811e21a164468232cfea3c2404a1ebc869477`. The author-freeze tag remains peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. **B570/RTX/358H/M4 remain CLOSED.** No model execution, merge, release or conference submission is authorized by this closeout.

<details>
<summary>Preserved v0.8.8 status and earlier history</summary>

# MLSys 2027 paper workspace — v0.8.8 candidate

Read [HANDOVER_CURRENT.md](HANDOVER_CURRENT.md) first. This revision responds to the completed v0.8.7 reviews in the existing Draft PR #51, directly against main. Parent delivery is `79327fd0c15e4d382b6264e9e780004b046fe5c1`; main remains `87b811e21a164468232cfea3c2404a1ebc869477` until a separately authorized merge.

v0.8.8 follows the completed fixed-artifact v0.8.7 review. It reorganizes the paper around prospective trajectory prediction, same-set specified-candidate discrimination, and the resulting qualification/cost choices; 358H and M4 supply bounded optimization constraints. A new global system readout states what each result adds beyond a basic gate. New V4 absolute latency descriptors use only the existing 171 QPC records and do not replace the frozen GM/CI.

B570 H1 remains 72/72 reserved complete predictions against reference/live 60/72. RTX V4 remains UB2/live 51/57, replay 57/57, with /15 both comparators failing, /18 reference-only failure and /25 UB2-only failure. Its fresh cost gate remains batched 51/57 BLOCKED (speedup/CI null), serialized 57/57 QUALIFIED but slower: 0.677351 [0.661653,0.691812], 0/19 faster. A/B share 19 exposure-conditioned prompts; the earlier 0.646 belongs to a different study.

All campaigns remain CLOSED. No new GPU/model execution, merge, release or submission. Original arrays, estimates/seeds, versioned artifacts/reviews/scripts, numerical macros, official style and scientific author-freeze tag are preserved. The historical Figure 3 is moved into Appendix F with identical tex/PDF/caption and textwidth inclusion. Its numbering changes with relocation, not its data or geometry. Old scores apply only to v0.8.7; main-track significance remains a judgment, not a QA result.

Read [main](manuscript/output/manuscript-v0.8.8.pdf), [appendix](manuscript/output/appendix-v0.8.8.pdf), [source](manuscript/output/overleaf-system-revision-v0.8.8.zip), [anonymous evidence](manuscript/output/anonymous-evidence-index-v0.8.8.zip), [build instructions](manuscript/README.md), [global readout](reviews/system_revision_v088/GLOBAL_SYSTEM_READOUT_V088.md), [response](reviews/system_revision_v088/REVIEW_RESPONSE_V088.md), [manifest](evidence/FINAL_ARTIFACT_MANIFEST_V088.json) and [delivery](evidence/DELIVERY_V088.md).

The fixed six reports remain [v0.8.7 history](reviews/submission_v087/). The [B570 decision](reviews/submission_v087/B570_DECISION_V087.md) still applies: no new experiment is required for current finite claims; a stronger single-block causal objective needs a separately bounded protocol. The internal hardware-only PDF cannot substitute for the submission paper.

<details>
<summary>Historical v0.8.7 living-pointer text, retained as history; not current instructions</summary>

# MLSys 2027 paper workspace — v0.8.7 candidate

**Read [HANDOVER_CURRENT.md](HANDOVER_CURRENT.md) first.** Update living status after materially changing merges; retain frozen handovers, stopping rules and reviews in their original delivery context.

This branch delivers v0.8.7 from main `87b811e21a164468232cfea3c2404a1ebc869477`, which already contains v0.8.6 and closed RTX V4 evidence. v0.8.7 is pending merge. Its PR base must be main, not an earlier paper branch.

Read [main PDF](manuscript/output/manuscript-v0.8.7.pdf), [appendix](manuscript/output/appendix-v0.8.7.pdf), [source ZIP](manuscript/output/overleaf-rtx-integration-v0.8.7.zip), [anonymous evidence index](manuscript/output/anonymous-evidence-index-v0.8.7.zip), [build instructions](manuscript/README.md) and [manifest](evidence/FINAL_ARTIFACT_MANIFEST_V087.json). Main is 10+2 pages and appendix 14. The hardware-only proof is internal, not a submission paper.

The original B570 draft-free prospective 72/72 remains central; reference/live 60/72 is blocked. RTX V4 distinguishes predefined target-only UB2 from replay on the same 19-prompt cohort and pairs qualification with measured instrumented cost. Neither replay agreement nor UB2 failure proves history necessary. Existing fork, RTX V2/old-cost, 358H and M4 evidence remains separately scoped.

Use [the current claim/campaign map](reviews/rtx_integration_v087/CLAIM_AND_CAMPAIGN_MAP_V087.md), [delivery record](evidence/DELIVERY_V087.md) and [independent review](reviews/submission_v087/). The [V4 raw closeout](evidence/RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002.md) records the prior completed CPU-only nine-capsule/native-log audit. No new model inference occurs in this revision.

[MANUSCRIPT_STATUS.md](MANUSCRIPT_STATUS.md), older claim maps and versioned handovers retain history. Their Draft/unmerged wording describes their own snapshots. Original numerical macros, arrays, Figure 3, styles, prior PDFs/ZIPs and author-freeze tag remain immutable.

The review is complete: [meta-review](reviews/submission_v087/META_REVIEW_V087.md), [revision priorities](reviews/submission_v087/REVISION_PRIORITY_V087.md), [B570 decision](reviews/submission_v087/B570_DECISION_V087.md). One weak reject and five weak accepts reflect a significance disagreement, not a demonstrated validity failure or required new execution. Next is author assessment of these fixed artifacts and existing-material requests. Existing studies are CLOSED. No dense B570 scan, new backend, 358H persistence or M4 variant is authorized. A future B570 study requires a separately frozen single-block/common-continuation design. Public release, arXiv and submission remain separate decisions.

</details>

</details>

</details>
