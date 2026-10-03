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
