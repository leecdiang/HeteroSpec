# Current handover — v0.8.6 manuscript; RTX A+B V4 evidence closed on main

Status reconciled 2026-10-02 after the RTX experiment merges and independent CPU-only raw replay. Read this file first for current decisions. Versioned handovers, stopping rules, manifests and experiment closeouts retain their original delivery context; they are not live branch status.

## 1. Repository state and version identities

`main` now contains the complete v0.8.6 delivery through [PR #46](https://github.com/leecdiang/HeteroSpec/pull/46). The integration made no content changes to the #45 delivery tree.

| Role | Exact identity / meaning |
|---|---|
| Last manuscript integration into main | `361cb43a67f7fd9bfae95de4cdf7e816c46bbe90`; PR #46, immutable integration anchor |
| Prior main / v0.8.5 merge | `30673fd8153b30681e959ea36a10b23ef89a990e`; PR #44 |
| Stacked #45 merge | `30635a680a93a2bd145361861b6c563f2f485fca`; originally merged into the v0.8.5 branch, now also an ancestor of main |
| v0.8.6 delivery/content tree | `494a5ca4fe62534b032b37d01652c3f88e0d16e1`; exact delivered source and artifacts |
| v0.8.6 authoritative TeX source/content | `da8d5739eb108de7f35d3a3cfbd954d42462f2e0` |
| RTX V3 terminal-history merge | `7f365f4fa87aedcebc2ae4cae5d8071b8223132d`; PR #48; incomplete scientific schedule, not successful A/B evidence |
| RTX V4 completed-study merge | `4500d140d78f77d0e314044acab1ae8e68dec42f`; PR #49; 19 prompts, 285 A and 171 fresh B conditions |
| Immutable scientific author-freeze | `mlsys2027-v0.8-author-freeze` peels to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`; not advanced to v0.8.6 |

The integration anchor is not a claim that the moving main HEAD always equals that SHA. This documentation maintenance and later commits may follow it. Resolve the actual remote HEAD with GitHub or `git fetch origin` / `git rev-parse origin/main`; verify that it contains the anchor and inspect subsequent changes. A document cannot truthfully embed its own future containing commit hash.

Authoritative development baseline is main. PR #48 preserves the failed V3 study; PR #49 contains the completed V4 study. Both now target and are merged into main. Manuscript TeX and delivered artifacts remain v0.8.6; the RTX V4 results have not yet been integrated into a new manuscript version. Do not assume the author's machine-local checkout has moved. Its current HEAD/dirty state must be read on that host before work.

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
| RTX H2 V2 | H2/live, R_ONLY/live, H2/R_ONLY each 72/72; UB1 reference/live 60/72 | Independent program orchestration on shared numerical libraries; H2 builds tape with draft; V2 alone has no same-set UB2 competitor |
| RTX fresh serialized cost | New 90/90 direct-ID gate; 180 runs; target/serialized 0.646 [0.630, 0.660]; 0/30 prompts faster | Instrumented post-prefill CLI boundary; no same-study qualified batched timing or production estimate |
| RTX V3 | 72 valid pre-live conditions + one failed capture; A live 0; 54 valid B conditions + one failed capture | Terminal prefixes only; no full-cohort accuracy, speedup or CI; old failed status remains unchanged |
| RTX V4 trajectory A | 19×3: target-only UB2/live 51/57, H2/live and R_ONLY/live 57/57; UB1 reference/live 51/57; 2 reference-divergent prompts | Rejects only the predefined UB2 candidate on this cohort; replay agreement is finite empirical sufficiency, not history necessity or unique cause |
| RTX V4 matched cost B | 171 new runs: batched 51/57 BLOCKED; serialized 57/57 QUALIFIED; target/serialized 0.677351 [0.661653, 0.691812]; 0/19 faster | Same cohort/timer/schedule, instrumented post-prefill latency; blocked timing diagnostic only; not comparable as an optimization to the old 0.646 cohort |
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

## 6. RTX A+B closeout and next manuscript work

RTX A+B execution is complete and **CLOSED**. The old [execution prompt](../../docs/experiments/RTX_A_B_V3_EXECUTION_PROMPT.md) is historical preparation guidance, not an instruction to rerun experiments. Original V3 stopping records are unchanged; its EOS/cap capture failure led to a separately authorized V4 protocol and a new 19-prompt cohort containing all remaining exposure-audited tasks. The V3 seven exposed tasks are excluded. Never pool failed prefixes, the V2 cohort, or repetitions into V4's 19 independent prompts.

All nine sealed V4 author/anonymous/pre-live capsules were fetched at exact study HEAD `8f30449d51bca1fe4907c392c5c65d5cc0fbcd3f`, rebuilt from their parts, and replayed with the original CPU-only offline verifier in [the independent audit run](https://github.com/leecdiang/HeteroSpec/actions/runs/37015269566). A separate parser reconstructed all 57 A native arrays and 171 B arrays/QPC intervals, and recomputed gates, medians and the frozen 10,000-draw paired-prompt bootstrap. Read [the closeout](evidence/RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002.md) and [machine-readable receipt](evidence/RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002.json) for exact evidence identities and limits. No GPU/model forward or scientific rerun occurred.

Completion retains the disclosed host-policy amendment and original strict-host stop. The author explicitly instructed that fan adjustment is not to block the work or cause reruns. Frozen numeric source, gate, denominator and failed records remain unchanged. Offline evidence does not authenticate omitted external weights/runtime/driver bytes or establish independently trusted absolute timestamps.

The next scientific-document action is a new manuscript integration revision: add the same-set UB2/replay discriminator and matched correctness–cost table, retain V3 failure/exposure history in the appendix, build and independently review the resulting exact artifacts. Do not overwrite v0.8.6 artifacts or claim this evidence merge already generated v0.8.7.

UB2 failure plus replay success does not prove proposal/history necessity. Native `--ubatch-size` also affects draft; B is a whole-path configuration comparison. Do not call the blocked batched path faster, manufacture a speedup/CI for it, compare 0.677 with 0.646 as an improvement, or expand candidates/prompts until a positive result appears. There is no remaining authorized GPU study in this closeout.

## 7. Scope guardrails and separate release decisions

- B570 dense/all-verification-block scan, more B570 prompts, more backends, 358H persistence and M4 controller variants are **NOT AUTHORIZED** in the current next step.
- A possible future B570 study would require a separately bounded single-block intervention followed by a common continuation policy, with its own protocol. It is deferred, not approved for execution.
- No result-driven dataset/parameter expansion, outcome-selected repetition, hidden failures or reopening old studies. Negative results are valid endpoints.
- Repository integration/status repair does not modify scientific arrays, TeX, macros, Figure 3, official styles, delivered PDFs/ZIPs, old manifests/reviews, or the author-freeze tag.
- arXiv, public release, licensing/authorship metadata and conference submission are separate decisions. No public release/submission is claimed or authorized by this handover.

Keep this compact current file and root REPO_STATUS synchronized after a materially changing merged PR. Put history in MANUSCRIPT_STATUS, versioned handovers and original closeouts. Before a stacked PR merge, check its actual base; `merged=true` alone does not prove main contains it.

