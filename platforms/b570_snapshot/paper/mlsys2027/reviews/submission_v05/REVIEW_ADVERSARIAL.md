# Independent Reviewer E — Adversarial systems review

Reviewed source: supplied PR #27 snapshot `b326ff7f20d9bac5afff6f53a6e9d9d8a7aaa7ae`. Reviewer E read the complete active manuscript and appendix, runtime integration report/ledger, M4 preregistration and closeout, and pinned 358H diagnostic report. No other reviewer report was read. No manuscript, evidence, policy, or measurement was changed. Locations below refer to this source snapshot.

## Recommendation and strongest surviving rejection case

**Weak reject to reject on contribution sufficiency, not on a demonstrated invalid numerical result.** The paper carefully documents when implementations of a known algorithm fail an intentionally strict output contract and when complete execution cost invalidates favorable component timings. Its only prospective controller retains a speedup already present in fixed speculation, with a lower aggregate point estimate. The other intended runtime intervention never reaches performance evaluation. Consequently the paper has not demonstrated that its runtime decision mechanism improves an objective over the available fixed speculative alternative. A careful characterization paper can be publishable, but the manuscript must earn that bar through the importance and portability of its measured systems insight. A list of correct caveats does not itself do that.

The strongest rejection argument is: **known numerical sensitivity and known state-management costs are documented in four confounded consumer stacks; a simple controller is added, but no incremental controller benefit is established; the larger intervention remains correctness-blocked.** This argument survives excellent prose, exact provenance recovery, and valid confidence intervals. It cannot be eliminated without additional evidence, which is outside this revision's scope. It can be made fairer by presenting the work explicitly as a measured execution-boundary contribution and the M4 guard as a bounded operational test, rather than letting “runtime co-design” imply a performance advance attributable to control.

## Attack matrix

### 1. Four heterogeneous consumer systems do not constitute a controlled cross-platform experiment

- **Real weakness:** Yes, if the intended contribution is architectural comparison, a general hardware rule, or explanatory coverage of all outcomes.
- **Already addressed:** Substantially. `03_methodology.tex`, first subsection, explicitly says retrospective, independently frozen, and not jointly preregistered. `09_limitations.tex:3` lists hardware/software/quantization confounding. Table 1 also discloses it.
- **Wording fix:** Preserve “case studies” and “tested configurations.” The introduction's “Profitability is not a simple hardware capability” (`01_introduction.tex:5`) is acceptable only as a statement about observed sessions; do not imply identification of workload causality.
- **Structural fix:** Frame Section 6 around what the controls establish, not a taxonomy extrapolated from four devices. An explicit single contribution sentence would help readers distinguish this from a portability benchmark.
- **Unfixable without new evidence:** Population-level generalization, architectural ranking, and controlled attribution among platform factors. Accept these limits; do not add experiments.

### 2. The Guard is trivial

- **Real weakness:** Yes as an algorithmic or controller novelty claim. Comparing cumulative time/token to a calibrated constant and permanently switching is not a substantial new policy idea.
- **Already addressed:** `01_introduction.tex:9`, Section 2 cost identity discussion, and related work disclaim a new speculative algorithm/profitability theory. Section 7 accurately describes the policy.
- **Wording fix:** “Bounded profitable control” in the abstract and “connect ... to measured control decisions” in the introduction are too easy to read as established usefulness of the controller. Say what was actually tested: charged within-request fallback can run prospectively with exact output and aggregate speedup over target-only, without an established advantage over fixed speculation.
- **Structural fix:** Put the scientific purpose of the simple policy before its mechanics. Keep mechanics sufficient for audit, but do not make complexity—or detailed candidate naming—carry the contribution.
- **Unfixable without new evidence:** A measured improvement due to control, comparison with stronger controllers, or algorithmic novelty. Do not complicate or retune the Guard to answer this review.

### 3. Always-Spec is faster, so why is the Guard needed?

- **Real weakness:** This is the strongest empirical objection to the software contribution. Guard 1.3114× versus Always-Spec 1.3469× establishes profitability versus Target, not benefit from admission. A 30.6% fallback rate establishes activity, not useful activity or risk reduction.
- **Already addressed:** Section 7 (`07_runtime_codesign.tex:25–27`), limitations, conclusion, and abstract all disclose the higher fixed-speculation point estimate. This is scientifically honest.
- **Wording fix:** Add an explicit sentence that fallback frequency and oracle regret do not establish better request-level choices or a safeguard benefit. Do not substitute hypothetical unseen deployment shifts for measured evidence. Do not infer significance from the displayed separate CIs.
- **Structural fix:** The table should keep both policies equally visible. Oracle regret should remain secondary. Proximity to an offline minimum is not itself evidence of effective adaptation: the fixed policy may already be close to that minimum. The current table does not establish an incremental decision-quality advantage for Guard.
- **Unfixable without new evidence:** A demonstrated latency, tail-risk, or regret advantage from control. No new analysis should be searched for to rescue the policy. Preserve the awkward result.

### 4. The M4 result does not generalize

- **Real weakness:** Yes. One model pair, one backend, fixed k=2, one 128-token cap, 60 balanced held-out prompts, and one campaign do not establish policy portability or operational robustness.
- **Already addressed:** Sections 7 and 9 explicitly bound the result and exclude stable small-stratum conclusions. Prompt resampling is correctly distinguished from session uncertainty.
- **Wording fix:** “Prospective” should clearly mean new held-out observations under a frozen policy, not design uninformed by historical M4 outcomes. The introduction openly knows which historical workloads were favorable. Excluding IDs prevents direct task reuse; it cannot remove prior knowledge of the model, task families, cap, or stack. That is legitimate development knowledge but should be named.
- **Structural fix:** Keep historical M4 outcomes as motivation, then explicitly reset the statistical population/estimator before the prospective result. The current estimator distinction is good and must survive editing.
- **Unfixable without new evidence:** Cross-session, cross-model, cross-hardware, longer-output, serving, energy, and distribution-shift claims.

### 5. 358H R2 never ran

- **Real weakness:** Yes for a claim that the proposed runtime intervention solves the measured state-cost problem. No intervention performance effect exists.
- **Already addressed:** `07_runtime_codesign.tex:10` is explicit. Appendix runtime notes (`appendix.tex:85`) are also explicit. The pinned diagnostic confirms `r2_authorized=false` and no R2 observations.
- **Wording fix:** Avoid treating the pair of runtime studies as two successful optimization demonstrations. “Tests those decisions” (`06_synthesis.tex:7`) is defensible if one decision is explicitly a qualification stop.
- **Structural fix:** Give the stopped intervention proportionate space. It supports the qualification boundary, not a solved persistence bottleneck. The M4 experiment should be described as a separate available-path test, without causal historical dependence on the failed 358H intervention.
- **Unfixable without new evidence:** A persistent-state speedup or useful optimized 358H runtime. Record absence; do not infer it.

### 6. The 358H negative result is an implementation failure, not hardware insight

- **Real weakness:** Yes against broad NPU/hardware claims. CPU reconcile correctness was not established and the frozen NPU IR was not compatible with the state-capable path. Those limitations could reflect this integration rather than an unavoidable architectural constraint.
- **Already addressed:** Section 7 says these are implementation boundaries, not inability to retain state. Section 5 separates interface failure from NPU compute capability.
- **Wording fix:** Keep `UB2_INTRINSICALLY_BLOCKED_IN_TESTED_STACK` out of universal claims: its scope qualifier is essential. “Intrinsic” is particularly dangerous without the frozen-stack qualifier. Current manuscript wording is appropriately narrower than the status label.
- **Structural fix:** Separate two facts clearly: the measured Phase-3 replay interface is expensive; the later candidate path fails qualification. The second does not prove the first unavoidable, nor isolate the benefit persistence would have produced.
- **Unfixable without new evidence:** The responsible floating-point/backend operation, a general UB2 correctness theorem, and a device-level inability to retain state.

### 7. Correctness qualification is obvious

- **Real weakness:** Yes as a novelty claim. Testing exact output before announcing an exact optimization is expected engineering discipline.
- **Already addressed:** The output contract is presented as a measurement discipline, with prior numerical/deterministic work cited. B570's small-probe/full-workload discrepancy supplies a concrete consequence beyond saying “test correctness.”
- **Wording fix:** Emphasize the measured loss of a cheap execution path and the cost of the remaining qualified control, rather than treating qualification itself as invented. Qualification is empirical and workload-bounded, not a certificate for all future prompts.
- **Structural fix:** The path-cost figures and controls should anchor this contribution. The abstract's long platform inventory presently hides this more memorable point.
- **Unfixable without new evidence:** General correctness certification or identification of a new numerical phenomenon. Neither is needed for the bounded measurement contribution.

### 8. Replay overhead is a stack artifact

- **Real weakness:** Yes against a hardware-general or NPU-general interpretation. The exact interface chosen reconstructs the full committed prefix; another state interface can differ.
- **Already addressed:** `05_diagnoses.tex:30–38`, `09_limitations.tex:9`, and related work explicitly scope the finding. The paper correctly measures replay plus proposal together and does not invent a replay-only number.
- **Wording fix:** Preserve “replay plus proposal” and “tested stateful integration.” A phrasing such as “replay dominates” would exceed the separable timing evidence.
- **Structural fix:** Use this as a counterexample to transferring isolated throughput into integrated prediction, not as proof that heterogeneous execution generally loses.
- **Unfixable without new evidence:** Causal replay-only share, persistence benefit, and comparison with alternative interface implementations.

### 9. The paper combines unrelated negative results

- **Real weakness:** Partly. M4's separate-session contrast is explicitly unexplained by the two mechanisms, yet it leads the abstract and consumes substantial early result space. RTX/B570 qualification and 358H state cost share an accounting lesson, but they do not form a common causal explanation of every case.
- **Already addressed:** The manuscript repeatedly says the diagnoses do not explain M4 and are nonexhaustive. These repeated caveats prevent overclaim but also emphasize fragmentation.
- **Wording fix:** Replace generic “bounded empirical connection” (`01_introduction.tex:9`) with one affirmative, testable contribution: measuring how exact-output eligibility and complete runtime cost jointly bound which locally promising speculative paths are usable in the tested stacks. Present M4 as evidence that admissibility alone is insufficient for profitability, not as an unexplained mechanism puzzle the paper promises to solve.
- **Structural fix:** Align abstract, introduction, Section 6, Section 7 opening, and conclusion around that boundary. Shorten repeated platform outcomes and repeated noncausality disclaimers while retaining one precise statement at each inference boundary.
- **Unfixable without new evidence:** A single causal mechanism explaining all four stacks. Do not manufacture one.

### 10. The freeze-hash defect undermines the prospective runtime result

- **Real weakness:** A real provenance exception, but not sufficient evidence that the timings or policy were altered. Automatic markers point at the wrong file, so the advertised automatic freeze check did not directly attest to the intended calibration artifact.
- **Already addressed:** Appendix (`appendix.tex:83`) describes loop-variable shadowing, clean formal-start commit reconciliation, retained markers, and STOPPED state. The M4 closeout gives actual and erroneous hashes and a complete portable archive. This is materially stronger than an undocumented manual override.
- **Wording fix:** Call this “independently audited recovery,” not uninterrupted prospective pipeline success. The recovery validates consistency with the committed freeze; it does not make the original marker correct. Use “metadata-recording defect” with the concrete explanation, not as a dismissive label.
- **Structural fix:** A short pointer from the main prospective-evaluation paragraph to the provenance exception would avoid surprise at the end. Full details belong in the appendix. No need to flood the main text with hashes.
- **Unfixable without new evidence:** Perfect original machine attestation cannot be restored retroactively. The existing reconciliation can support the bounded claim; reviewers may still discount confidence in experimental automation.

### 11. Characterization does not supply enough new systems technique

- **Real weakness:** Yes, and it survives all fixes above. Cost accounting, heterogeneous placement, state reuse, numerical path dependence, and threshold control all have prior art explicitly acknowledged by the paper.
- **Already addressed:** Related work is candid, but the introduction retreats to “this bounded empirical connection,” which is too vague to carry a submission-level novelty argument.
- **Wording fix:** State the measured advance affirmatively and narrowly. Do not claim the familiar ingredients are new. Explain why losing the fast path under the output contract and losing the isolated NPU advantage at the state interface are useful counterexamples to common feasibility proxies.
- **Structural fix:** Make the paper primarily an evidence-backed systems measurement argument with an operational extension. The guard demonstrates that the accounting boundary can be implemented under prospective freezing; it does not rescue the paper as a superior new controller.
- **Unfixable without new evidence:** Substantial new optimization technique or proof of controller utility relative to fixed speculation. The authors must accept the residual venue-fit risk.

## Priority actions within the closed-evidence revision

1. **P1: Clarify the single contribution.** Replace “bounded empirical connection” with an explicit measured execution-boundary statement. Align abstract, introduction, synthesis, runtime opening, and conclusion. This is the highest-value change.
2. **P1: State what Guard does not demonstrate at the result.** Existing fixed-policy disclosure is necessary but incomplete as an answer to “why control?” Make clear that fallback activity and small oracle regret do not establish improved decisions, quantitative protection, or superiority over fixed speculation.
3. **P1: Bound prospective independence.** Historical outcomes informed the research design; IDs and formal outcomes were held out. Preserve the stronger concrete chronology and avoid suggesting complete insulation from prior M4 knowledge.
4. **P2: Reduce the stitched-paper effect.** Present the runtime studies as two checks of the qualification/cost sequence. Shorten repeated M4 and 358H inventories; retain the difference between exact negative Phase 3 and correctness-blocked runtime qualification.
5. **P2: Surface the audited metadata exception at the claim boundary.** A brief appendix pointer near policy freezing suffices. Keep concrete recovery detail and the retained STOPPED state.

## Suggestions this reviewer would reject

- Add a more complex controller, new k, new timing, new workload, or a selective rerun to improve the aggregate comparison.
- Promote a small favorable stratum or per-request anecdote to an admission-benefit claim.
- Hide Always-Spec, omit the negative representative M4 campaign, or recast the failed 358H intervention as a performance result.
- Use strict correctness as an architectural verdict or generic proof that CUDA/Vulkan/NPU speculation is unsuitable.
- Treat the metadata exception as data corruption without evidence, or erase it because the final numbers reproduce.
- Demand a causal replay-only decomposition from timing that measures replay plus proposal together.

## Acceptance-bar judgment

The evidence discipline is a strength, but the strongest fair objection is still that the scientific lessons are known in general and demonstrated here in implementation-specific cases, while the runtime extension does not establish incremental benefit. Acceptance would depend on a reviewer valuing the particular controls, preserved negative evidence, and explicit execution boundaries as a consequential measurement contribution. Rejection would most likely be for insufficient novelty or systems impact, not for failing to disclose that Guard loses the aggregate point-estimate comparison. Revision can sharpen the contribution and remove misleading implications; it cannot guarantee acceptance or create a missing technique result.
