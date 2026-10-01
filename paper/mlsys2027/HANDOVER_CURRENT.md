# Current handover — v0.8.6 on main; RTX A+B protocol preparation next

Status reconciled 2026-10-01. Read this file first for current decisions. Versioned handovers, stopping rules, manifests and experiment closeouts retain their original delivery context; they are not live branch status.

## 1. Repository state and version identities

`main` now contains the complete v0.8.6 delivery through [PR #46](https://github.com/leecdiang/HeteroSpec/pull/46). The integration made no content changes to the #45 delivery tree.

| Role | Exact identity / meaning |
|---|---|
| Last manuscript integration into main | `361cb43a67f7fd9bfae95de4cdf7e816c46bbe90`; PR #46, immutable integration anchor |
| Prior main / v0.8.5 merge | `30673fd8153b30681e959ea36a10b23ef89a990e`; PR #44 |
| Stacked #45 merge | `30635a680a93a2bd145361861b6c563f2f485fca`; originally merged into the v0.8.5 branch, now also an ancestor of main |
| v0.8.6 delivery/content tree | `494a5ca4fe62534b032b37d01652c3f88e0d16e1`; exact delivered source and artifacts |
| v0.8.6 authoritative TeX source/content | `da8d5739eb108de7f35d3a3cfbd954d42462f2e0` |
| Immutable scientific author-freeze | `mlsys2027-v0.8-author-freeze` peels to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`; not advanced to v0.8.6 |

The integration anchor is not a claim that the moving main HEAD always equals that SHA. This documentation maintenance and later commits may follow it. Resolve the actual remote HEAD with GitHub or `git fetch origin` / `git rev-parse origin/main`; verify that it contains the anchor and inspect subsequent changes. A document cannot truthfully embed its own future containing commit hash.

Authoritative development baseline is main. The new RTX branch is to be created separately as `experiment/rtx-trajectory-and-matched-cost-v3`; no RTX V3 experiment implementation or execution is delivered by this maintenance. Do not assume the author's machine-local checkout has moved. Its current HEAD/dirty state must be read on that host before work.

## 2. Current paper thesis and exact artifacts

The paper connects execution-path qualification, prospective trajectory prediction, supporting intervention/program reproduction, and realized cost/runtime decisions. Its central result is the original B570 draft-free target-only UB1 predictor: frozen before reserved live outcomes, it predicts 72/72 complete capped trajectories on 24 prompts × three repetitions, including all 12 runs of four reference-divergent prompts. UB128 reference/live is only 60/72, so predicting that path does not qualify it as a lossless replacement.

The conclusion is finite predictive sufficiency on the tested path. It does not identify a unique numerical cause. The three contributions and original claim boundaries remain unchanged by repository reconciliation.

Current artifacts are [main PDF](manuscript/output/manuscript-v0.8.6.pdf), [separate appendix](manuscript/output/appendix-v0.8.6.pdf), [source ZIP](manuscript/output/overleaf-convergence-v0.8.6.zip) and [anonymous evidence index](manuscript/output/anonymous-evidence-index-v0.8.6.zip). Main: 10 body + 2 references pages; appendix: 12 pages. The 9+2-page hardware-only proof is an internal section-removal check, not a submission manuscript.

Full artifact SHA-256/lengths and the original delivery QA scope remain in [FINAL_ARTIFACT_MANIFEST_V086.json](evidence/FINAL_ARTIFACT_MANIFEST_V086.json). Build instructions are in [manuscript/README.md](manuscript/README.md). Integration QA is distinct from an independent submission-level review. No completed new v0.8.6 acceptance verdict is asserted by this maintenance.

## 3. Current evidence ledger

| Study | Retained result | Interpretation boundary |
|---|---|---|
| B570 original H1 | 36/36 exposed discovery; reserved prediction/live 72/72 on 24×3; reference/live 60/72 | Draft-free tested-path predictive sufficiency; reference compatibility still blocked |
| B570 same-state fork | Scores change 72/72; raw top-1 and immediate decisions change 0/72; later trajectories change 18/72 on 6/24 prompts | UB128 persists after the sampled fork; delayed effects cannot be attributed to that block alone; separate cohort from original H1 |
| RTX earlier H1 | Target-only UB2/live discovery 24/36; H2 not executed in that arm; reserved 0 | Failed candidate and stopping outcome remain visible |
| RTX H2 V2 | H2/live, R_ONLY/live, H2/R_ONLY each 72/72; UB1 reference/live 60/72 | Independent program orchestration on shared numerical libraries; H2 builds tape with draft; no same-set UB2 competitor |
| RTX fresh serialized cost | New 90/90 direct-ID gate; 180 runs; target/serialized 0.646 [0.630, 0.660]; 0/30 prompts faster | Instrumented post-prefill CLI boundary; no same-study qualified batched timing or production estimate |
| 358H | CPU/NPU Phase 3 each 90/90; fixed-progress/target-work zero-draft-and-residual bounds 0.82745 / 0.83519 | Conditional arithmetic total-time bounds; replay/proposal inseparable; runtime qualification stopped; no runtime gain or NPU-general claim |
| M4 runtime | Guard 1.3114×, Always-Spec 1.3469×; both 180/180; Guard/Always 1.0271; Always/oracle 1.000692 | Guard beats target-only but loses to fixed speculation; hindsight oracle compares two measured fixed modes; no incremental adaptive-policy win |

Use the [v0.8.6 claim/campaign map](reviews/convergence_v086/CLAIM_AND_CAMPAIGN_MAP_V086.md) and original closeouts for cohorts, references, endpoints, ratio directions and raw evidence. Repetitions and correlated events are not independent prompts. v0.8.6 record-derived quantities are post-study; original primary estimates/CIs remain intact.

## 4. Non-claims and evidence-access limits

- No unique numerical cause, universal backend transfer or necessary/minimal proposal-history state is established.
- B570 prediction does not make its blocked path lossless-compatible. RTX replay is not draft-free prediction generation.
- No RTX production-speed or energy claim; empty clock-hook cost does not bound all instrumentation/logging.
- No general NPU weakness; the 358H bound fixes measured progress, target work and baseline. Removing draft/residual alone cannot reach parity under those assumptions.
- No M4 adaptive-controller advantage over the measured fixed strategy, and no universal workload generalization.
- Exact IDs are not HumanEval functional pass@k. Sensor boundaries are not a common calibrated energy domain.
- 358H runtime raw traces and the exact old v0.8.4 sequence ZIP remain unavailable. Original B570 arrays and processed component inputs remain preserved. Offline hashes do not authenticate omitted assets or original absolute chronology.

## 5. Closed studies versus remaining decisions

Existing B570, RTX, 358H and M4 campaigns are **CLOSED**. Their negative results, failed gates and boundaries are final records, not requests to improve a result.

Under the current explicitly limited claims, no additional experiment is recorded as a prerequisite to rescue validity. The v0.8.6 [stopping rule](reviews/convergence_v086/STOPPING_RULE_V086.md) remains the historical revision-completion decision, not an acceptance guarantee. Importance, generality and venue fit remain independent review questions. New optional studies below do not reopen old campaigns.

## 6. Authorized next RTX direction and execution state

The author has selected one RTX activity with two separately reported studies:

| Priority | Question | Current execution state |
|---|---|---|
| A — trajectory sufficiency comparison | On one new reserved cohort, compare UB1 reference, target-only UB2, H2 P/R, R_ONLY and native batched live | Protocol/engineering preparation next; no V3 reserved predictions or live executions performed here |
| B — matched qualification–cost | In one frozen timer build/cohort/schedule, jointly measure target reference, batched and serialized IDs and time | Protocol/engineering preparation next; no new matched three-condition runs performed here |

Use [the complete RTX A+B prompt](../../docs/experiments/RTX_A_B_V3_EXECUTION_PROMPT.md). First run is **PREPARE_ONLY**: exposed engineering runs, exposure audit, implementation, two concrete protocols and F0 remote freeze/Draft PR. Reserved model forwards remain zero. **EXECUTE_FROZEN** follows author review of the exact protocol/source SHA; this handover is not that authorization.

Normal plan: new 24 prompts × three; A 360 complete condition runs, B 216 separate runs, total 576, engineering separately counted. B need not wait for A success. It does wait for a safe exposure barrier: A predictions remotely sealed before any reserved A live/B formal call; ordinarily A closes before B. If A stops before F2, terminally close it before B and never resume prospective A on those exposed tasks.

Reaudit repository and accessible local archives. The old V2 inventory's 50 eligible minus 24 selected leaves 26 only under that old inventory, not a guarantee of 24 fresh tasks today. No new discovery set is drawn from that pool. The prompt predeclares an audit-complete, pool-insufficient A-blocked/B-only 30-task preparation branch; the exact mode/workload still needs protocol review before formal execution.

Freeze candidates, conditions, inputs, counts, full arrays/tapes, timetable, gate, timer, estimator and failure branches before outcomes. A uses two predefined candidates without an H1-success selection gate; no H3 search. Zero reference divergence is NONDISCRIMINATING. UB2 failure plus replay success excludes the tested UB2 candidate; it does not establish proposal/history necessity. Native `--ubatch-size` also affects draft; B compares whole path configurations, not target-verification-only causality.

B gate precedes timing interpretation. Failed paths retain diagnostic times but no lossless speedup/CI; negative scientific outcomes complete the frozen schedule. Operational/provenance failures retain their actual prefix without selective replacement. Do not fill B with the old 0.646 result.

## 7. Scope guardrails and separate release decisions

- B570 dense/all-verification-block scan, more B570 prompts, more backends, 358H persistence and M4 controller variants are **NOT AUTHORIZED** in the current next step.
- A possible future B570 study would require a separately bounded single-block intervention followed by a common continuation policy, with its own protocol. It is deferred, not approved for execution.
- No result-driven dataset/parameter expansion, outcome-selected repetition, hidden failures or reopening old studies. Negative results are valid endpoints.
- Repository integration/status repair does not modify scientific arrays, TeX, macros, Figure 3, official styles, delivered PDFs/ZIPs, old manifests/reviews, or the author-freeze tag.
- arXiv, public release, licensing/authorship metadata and conference submission are separate decisions. No public release/submission is claimed or authorized by this handover.

Keep this compact current file and root REPO_STATUS synchronized after a materially changing merged PR. Put history in MANUSCRIPT_STATUS, versioned handovers and original closeouts. Before a stacked PR merge, check its actual base; `merged=true` alone does not prove main contains it.
