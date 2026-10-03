# HeteroSpec

Prospective execution-path prediction and bounded optimization choices in speculative decoding.

Start with [HANDOVER_CURRENT.md](paper/mlsys2027/HANDOVER_CURRENT.md) and [repository status](REPO_STATUS.md).

## Current manuscript candidate: v0.8.8

The author revision continues Draft PR #51 on its existing branch `paper/mlsys2027-rtx-integration-v0.8.7`; the branch name is historical. It is based on the delivered v0.8.7 HEAD `79327fd0c15e4d382b6264e9e780004b046fe5c1`, while the PR remains directly against main `87b811e21a164468232cfea3c2404a1ebc869477`. A candidate does not imply main has advanced.

v0.8.8 follows the completed fixed-artifact v0.8.7 review. It reorganizes the paper around prospective trajectory prediction, same-set specified-candidate discrimination, and the resulting qualification/cost choices; 358H and M4 supply bounded optimization constraints. A new global system readout states what each result adds beyond a basic gate. New V4 absolute latency descriptors use only the existing 171 QPC records and do not replace the frozen GM/CI.

B570 H1 remains 72/72 reserved complete predictions against reference/live 60/72. RTX V4 remains UB2/live 51/57, replay 57/57, with /15 both comparators failing, /18 reference-only failure and /25 UB2-only failure. Its fresh cost gate remains batched 51/57 BLOCKED (speedup/CI null), serialized 57/57 QUALIFIED but slower: 0.677351 [0.661653,0.691812], 0/19 faster. A/B share 19 exposure-conditioned prompts; the earlier 0.646 belongs to a different study.

All campaigns remain CLOSED. No new GPU/model execution, merge, release or submission. Original arrays, estimates/seeds, versioned artifacts/reviews/scripts, numerical macros, official style and scientific author-freeze tag are preserved. The historical Figure 3 is moved into Appendix F with identical tex/PDF/caption and textwidth inclusion. Its numbering changes with relocation, not its data or geometry. Old scores apply only to v0.8.7; main-track significance remains a judgment, not a QA result.

- [Main PDF](paper/mlsys2027/manuscript/output/manuscript-v0.8.8.pdf) and [appendix](paper/mlsys2027/manuscript/output/appendix-v0.8.8.pdf).
- [Source ZIP](paper/mlsys2027/manuscript/output/overleaf-system-revision-v0.8.8.zip) and [anonymous evidence](paper/mlsys2027/manuscript/output/anonymous-evidence-index-v0.8.8.zip).
- [Global readout](paper/mlsys2027/reviews/system_revision_v088/GLOBAL_SYSTEM_READOUT_V088.md), [review response](paper/mlsys2027/reviews/system_revision_v088/REVIEW_RESPONSE_V088.md), [manifest](paper/mlsys2027/evidence/FINAL_ARTIFACT_MANIFEST_V088.json) and [delivery identity](paper/mlsys2027/evidence/DELIVERY_V088.md).
- [Build instructions](paper/mlsys2027/manuscript/README.md); the hardware-only PDF remains an internal section-removal proof.

`scripts/` contains runners/verifiers, `benchmarks/` frozen campaigns, `artifacts/` indexed archives, `analysis/` and `reports/` historical results, `paper/mlsys2027/` manuscript/evidence/reviews, and `docs/` reproduction/data policy. See [reproduction](docs/reproduction.md) and [data policy](docs/data_policy.md).

<details>
<summary>Historical v0.8.7 living-pointer text, retained as history; not current instructions</summary>

# HeteroSpec

Execution-path qualification, prospective trajectory prediction and realized cost in speculative decoding on consumer systems.

**Start with [HANDOVER_CURRENT.md](paper/mlsys2027/HANDOVER_CURRENT.md).** [REPO_STATUS.md](REPO_STATUS.md) distinguishes the moving main branch from this delivery candidate. Older reports and versioned handovers retain their original campaign context.

## Current manuscript candidate

This branch delivers **v0.8.7**, integrating the completed RTX V4 evidence. Its base is main `87b811e21a164468232cfea3c2404a1ebc869477`, which contains v0.8.6, the terminal V3 history, completed V4 experiments and independent raw closeout. v0.8.7 is a candidate pending merge; reading this branch does not establish that main already contains it.

The central observation remains the original B570 draft-free target-only UB1 predictor, frozen before reserved live outcomes: **72/72 complete generated-ID trajectories on 24 prompts × three repetitions**, including reference-divergent runs. Reference/live is **60/72**, so predictive agreement does not qualify a lossless replacement.

RTX V4 adds a same-set candidate comparison: UB2/live **51/57**, H2/live and R_ONLY/live **57/57**. This rejects the specified UB2 candidate on 19 exposure-audited prompts; it does not prove history necessary or minimal. Fresh matched cost measurements have batched **51/57 BLOCKED** and serialized **57/57 QUALIFIED**, with target/serialized **0.677× [0.662, 0.692]**, 0/19 prompts faster. The old **0.646×** result remains a separate cohort.

B570's sampled fork remains a bounded intervention result with persistent UB128 continuation. M4 Guard loses to fixed speculation. 358H's zero-draft/residual bounds remain below parity at fixed measured progress and target work. Existing studies are closed.

## Read and reproduce v0.8.7

- [Main PDF](paper/mlsys2027/manuscript/output/manuscript-v0.8.7.pdf): 10 body + 2 reference pages.
- [Separate appendix](paper/mlsys2027/manuscript/output/appendix-v0.8.7.pdf): 14 pages.
- [Source ZIP](paper/mlsys2027/manuscript/output/overleaf-rtx-integration-v0.8.7.zip) and [anonymous evidence index](paper/mlsys2027/manuscript/output/anonymous-evidence-index-v0.8.7.zip).
- [Build instructions](paper/mlsys2027/manuscript/README.md), [exact manifest](paper/mlsys2027/evidence/FINAL_ARTIFACT_MANIFEST_V087.json) and [claim/campaign map](paper/mlsys2027/reviews/rtx_integration_v087/CLAIM_AND_CAMPAIGN_MAP_V087.md).
- [Independent review packet and reports](paper/mlsys2027/reviews/submission_v087/).

The hardware-only PDF is an internal section-removal proof, not a submission manuscript. Prior PDFs, ZIPs, arrays, numerical macros, Figure 3, vendor styles and scientific tag are retained unchanged. No new GPU/model inference occurred in this integration.

## Scope and repository layout

The fixed-artifact independent review is complete (one weak reject, five weak accepts; significance remains disputed). Read [the meta-review](paper/mlsys2027/reviews/submission_v087/META_REVIEW_V087.md), [existing-material revision priorities](paper/mlsys2027/reviews/submission_v087/REVISION_PRIORITY_V087.md) and [the decision not to execute B570 now](paper/mlsys2027/reviews/submission_v087/B570_DECISION_V087.md). The next decision is author assessment of the fixed artifacts and these requests; no manuscript changes were made during review. B570 dense scanning, additional backends, 358H persistence and M4 variants are deferred and not authorized by a limitation paragraph. Public release, arXiv and conference submission remain separate decisions.

`scripts/` contains runners/verifiers; `benchmarks/` frozen campaigns; `artifacts/` indexed archives; `analysis/` and `reports/` processed/historical reports; `paper/mlsys2027/` manuscript/evidence/reviews; `docs/` reproduction, history and data policy. Model weights, downloaded datasets, caches and most machine-local logs are absent by policy. See [reproduction](docs/reproduction.md) and [data policy](docs/data_policy.md).

</details>
