# HeteroSpec Current Handover

## 1. Current repository state

Current `main` is `1d3b556c93b477680788dfd1eb0737dfe9eee28c` (merged PR #35). Manuscript v0.8 is the merged baseline. PR #34 merged the B570 mechanism study, PR #33 merged manuscript v0.7, PRs #31–32 merged the direct-ID B570/RTX studies, and PR #30 merged the paired M4 secondary analysis.

## 2. Current paper thesis

Favorable local draft throughput or target-forward batching does not establish usable integrated speculative decoding. Four consumer-system campaigns retain positive, negative and correctness-blocked outcomes within their own measurement boundaries. Two separately frozen direct generated-ID studies qualify the tested serialized RTX path (75/90 batched to 90/90 serialized), but not B570 (60/90 fast to 78/90 serialized). A controlled B570 follow-up selects target execution-partition sufficiency on exposed discovery prompts, freezes the hypothesis, and predicts all 72 reserved serialized output sequences from target-only UB1. This shows a sufficient numerical path under the tested stack without proving a unique kernel or explaining RTX. On 358H, isolated NPU draft throughput fails to survive the stateful interface; a later runtime intervention stops at qualification. M4 has both an unprofitable representative campaign and a profitable separate HumanEval campaign under historical comparators. Its prospective Guard endpoint is exact and profitable against target-only, yet slower than fixed Always-Spec on the paired secondary comparison. The paper separates physical opportunity, admissibility and mechanism, realized stateful cost, and runtime outcome, without claiming a portable performance law.

## 3. Scientific invariants

- Where direct generated-ID equality is claimed, compare complete committed/generated IDs against the frozen target reference; exclude prompt IDs, include an earlier generated EOG, and never substitute semantic equivalence.
- Historical M4/RTX/B570 parsed/re-tokenized text comparators retain their original scope. Fresh direct-ID evidence does not retroactively certify historical timing or old equality labels.
- $V_k^{micro}$ is a target-forward proxy, not complete $R_{target}$; isolated tok/s is not realized $D_{real}$. $C$ counts all committed output including correction/bonus, not only accepted drafts.
- Do not rank energy across M4 package, B570 adapter board, RTX mixed domains, or unmeasured runtime boundaries.
- Timing means post-prefill decode unless explicitly stated otherwise; loading and initial prefill are outside the reported endpoint.
- Keep PRIMARY, SECONDARY, DIAGNOSTIC, MECHANISM_SUPPORTED, and controlled-inference claims distinct. A blocked gate stays blocked.

## 4. Experiment ledger

| Campaign | Status and main result | Comparator / class | Canonical paths |
|---|---|---|---|
| M4 representative | Closed; 0.842×, negative | Historical text-path / primary timing | `reports/m4/M4_CONFIRMATORY_VALIDATION.md`, `analysis/m4_confirmatory_summary.json` |
| M4 HumanEval | Closed; 1.387×, positive | Historical text-path / primary timing | `reports/m4/M4_HUMANEVAL_CODE_CONDITIONED.md`, `analysis/m4_humaneval_summary.json` |
| RTX historical | Closed; fast path blocked, serialized secondary timing | Parsed text; separate CUDA margin capture / diagnostic and secondary | `reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.md`, `artifacts/windows_humaneval_replication/` |
| B570 historical | Closed; fast/serialized text-path 45/90 and 60/90; diagnostic timing only | Parsed/re-tokenized text / diagnostic | `reports/b570/`, historical `benchmarks/b570_*` and `artifacts/b570_*` |
| 358H Phase 3 | Closed; CPU ~0.734×, NPU ~0.352×; replay+proposal inseparable | Direct generated IDs / primary stateful timing | `benchmarks/358h_threshold_validation/`, `paper/mlsys2027/evidence/RUNTIME_LEDGER_V04.md` |
| 358H runtime intervention | Qualification-closed; no R2 performance | Direct-ID qualification / diagnostic | `paper/mlsys2027/evidence/RUNTIME_358H_PIN_V04.json`, runtime closeout |
| M4 runtime Guard | Closed; Guard 1.3114× and Always-Spec 1.3469× vs target; Guard/Always latency 1.027076 [1.012956, 1.043559] | 180/180 direct IDs; primary Guard vs target, post-study paired secondary Guard vs Always | `paper/mlsys2027/evidence/M4_GUARD_ALWAYS_SECONDARY_QA_V06.json`, M4 runtime archive |
| RTX direct-ID v2 | Closed; 75/90 batched, 90/90 serialized, latter qualified | Direct generated IDs / prospective qualification | `benchmarks/rtx_direct_id_v2/`, `artifacts/rtx_direct_id_v2/` |
| B570 direct-ID v1 | Closed; 60/90 fast, 78/90 serialized, both blocked | Direct generated IDs / prospective qualification | `benchmarks/b570_direct_id_v1/`, `artifacts/b570_direct_id_v1/` |
| B570 mechanism v0.8 | Closed; H1 36/36 discovery, 72/72 reserved prediction; reserved 60/72 reference equality blocked | Complete direct IDs / discovery then frozen prospective prediction | `benchmarks/b570_mechanism_v08/`, `artifacts/b570_mechanism_v08/` |

The summary is a locator, not a replacement for each closeout's precise estimator, model/runtime identity or admissibility boundary.

## 5. Strongest findings

RTX 75/90→90/90 and B570 60/90→78/90 show that serialization changes qualification but is not its certificate. B570 H1 predicts 72/72 previously unexposed reserved serialized trajectories, including four divergent prompts, from target-only UB1. On 358H the draft-device advantage is lost at the measured state interface; no persistence benefit was measured. M4's separate positive and negative regimes cannot be assigned a single diagnosed cause. Guard's paired latency disadvantage against fixed speculation remains prominent despite its target-only speedup.

## 6. Claims allowed / forbidden

**Allowed:** Under the tested B570 configuration, the target execution partition alone suffices to reproduce the serialized output path without live drafting; the frozen predictor generalizes from exposed discovery tasks to the selected reserved tasks. Qualify a specific intended path under its output contract before judging its complete realized cost.

**Forbidden:** A unique Vulkan kernel, general Intel defect, universal UB1 correctness rule, RTX/B570 common mechanism, cross-platform energy ordering, historical direct-ID certification, 358H persistence payoff, M4 Guard incremental benefit, production correctness certificate, or functional HumanEval pass@k claim.

## 7. Current manuscript map

`manuscript/main.tex` includes Introduction, framework, methodology, outcomes, Section 5 qualification/mechanism/stateful realization, synthesis, Section 7 runtime endpoint, related work, limitations and conclusion. `manuscript/appendix.tex` contains estimator and energy boundaries, historical lookup and inventory, runtime reproducibility, direct-ID protocols and B570 mechanism chronology/tasks. Figures: M4 outcomes (Figure 1), opportunity-to-outcome schematic (Figure 2), two-panel historical opportunity/direct-ID qualification (Figure 3, unchanged), and 358H state decomposition (Figure 4). Main tables cover platforms, outcomes and runtime; the mechanism chain is in Section 5 prose to preserve publication legibility and the ten-page body. Check final PDF numbering and placement, not old planning maps.

## 8. Internal reviewer state

These are **internal model-review simulations**, not external conference reviews. v0.5 and v0.7 mock decisions were Weak Reject. v0.5 questioned the limited scientific payoff, historical comparator scope and Guard's incremental utility. v0.7 credited fresh direct-ID qualification but still found limited transferable explanatory/predictive reach, particularly the unexplained B570 residual. v0.8 tests whether a frozen H1 followed by 72/72 reserved prediction addresses that specific objection. It does not supply cross-platform transfer or improve Guard. Read `reviews/submission_v07/` and the new `submission_v08/` without conflating mock judgments with peer review.

## 9. Open scientific questions

How far does partition sufficiency transfer across model pairs, workloads, contexts, builds and devices? Which numerical operation mediates the B570 path difference? Would a qualified path with a different state interface make 358H profitable? Would any continuation policy outperform fixed speculation on a new M4 sample? These are future questions, not authorization to reopen closed experiments.

## 10. Immediate next actions

Freeze the v0.8 submission candidate against the author-freeze tag, then request external author review of the exact PDF, appendix, claim scope and source bundle. Resolve submission-format or wording issues in a separate reviewable PR before final submission; retain the closed scientific evidence.

## 11. Repository map

Manuscript and builds: `paper/mlsys2027/manuscript/`; claim ledger: `paper/mlsys2027/evidence/`; reviews: `paper/mlsys2027/reviews/`; current human handover: this file; deeper history: `MANUSCRIPT_STATUS.md`; B570 mechanism closeout and chronology: `benchmarks/b570_mechanism_v08/`; content-addressed evidence: `artifacts/b570_mechanism_v08/`. Other campaign records remain under their `benchmarks/`, `artifacts/`, `reports/`, and `analysis/` paths.

## 12. Working protocol for future agents

Fetch `main`, record its exact SHA, and inspect canonical evidence before changing claims. Never infer unmeasured results or reopen a closed campaign. Preregister genuinely prospective work; separate discovery from validation and preserve negative outcomes and original comparator classes. Build and inspect the actual PDF, retain numerical/chronological QA receipts, and open a Draft PR for author review without auto-merge. Update this handover after any merged PR materially changing scientific evidence, thesis, reviewer blocker or experiment status; skip trivial formatting-only changes.

## 13. Last updated

2026-09-29 UTC. `main` merge commit: `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. Manuscript: v0.8 merged baseline.
