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
