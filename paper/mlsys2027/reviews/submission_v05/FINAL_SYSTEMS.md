# Final independent systems review — revised v0.5

Scope: independently read `main.tex`, every manuscript section, `appendix.tex`, comparator-scope addendum, and numerical macro tables. No other reviewer report was read. This is an assessment of the stated evidence and contribution, not a raw-trace audit or external literature verification.

## Main surviving objection

**The paper is now substantially more defensible than it is compelling as an MLSys systems contribution.** It establishes useful, bounded implementation case studies, but does not demonstrate a new capability, validated portable decision procedure, or successful bottleneck-directed intervention. Numerical path dependence, complete-cost accounting, state reuse, and adaptive speculation are acknowledged prior art. What remains new is their measured conjunction in these consumer configurations. A reviewer can reasonably find that empirical increment insufficient even while accepting the claims.

The failed 358H intervention and the M4 guard do not close this gap: the former has no performance result, and the latter tests a different stack without establishing incremental utility. More caveats cannot resolve this objection; stronger evidence or a characterization-paper contribution standard is needed.

## Risks resolved or materially reduced

- **Novel algorithm framing:** Introduction, accounting section, and related work explicitly disclaim novelty for the threshold rule, cost identity, and heterogeneous execution. The contribution is clearly empirical.
- **Guard versus fixed speculation:** Abstract, runtime section, limitations, and conclusion disclose Always-Spec's higher point estimate (1.3469× versus 1.3114×). Exactness and profitability against target-only are supported by the stated direct-ID evaluation (180/180 per condition); control superiority and risk reduction are not claimed.
- **Historical comparator scope:** The revised text clearly distinguishes parsed/re-tokenized CLI-text agreement from generated-ID equality. M4/RTX historical successes are no longer promoted to the intended strict contract; B570 remains blocked. The new M4 direct-ID results explicitly do not repair historical evidence retrospectively.
- **Mechanism boundaries:** Forward-only proxies are separated from complete target work; replay and proposal remain jointly timed. M4 session/workload confounding, heterogeneous-stack differences, and absent persistence benefit are explicit.
- **Runtime connection:** Sections 6–7 state that these are separate qualification and continuation decisions, not an intervention/ablation chain. That removes an unsupported causal narrative.

## Remaining scientific risks

1. **Simple guard has no demonstrated purpose beyond feasibility.** A frozen cumulative-cost rule using one calibration reference is a reasonable engineering baseline, but its successful execution is a low novelty bar. Always-Spec is already exact and profitable. The speedup point estimates imply Guard's geometric-mean latency is approximately 2.7% higher than Always-Spec on the same prompts; this is descriptive, not a significance claim. Fallback in 30.6% of runs does not establish useful decisions. No paired direct Guard/Always interval or decision-benefit breakdown is presented.
2. **The central runtime bridge is conceptual, not validated.** The 358H diagnosis motivates an intervention that fails eligibility; M4 validates continuation mechanics without demonstrating a remedy for the diagnosed heterogeneous costs. That is honestly stated, but leaves Section 7 resembling a supplementary feasibility study rather than the culmination of the systems result.
3. **Strict-contract characterization is uneven.** Historical text-path agreement cannot establish that the supposedly usable serialized path satisfies the paper's intended generated-ID contract. The CUDA captured token divergence supports a narrow exclusion result, but the alternative's strict-contract qualification remains unproven. Keeping the historical comparator is legitimate; readers must understand that the paper has two qualification strengths, not one common feasible-set measurement.
4. **General insight versus avoidable implementation cost:** The NPU replay-plus-proposal result shows the tested interface is expensive; without persistent-state performance or an isolating experiment it does not establish how much replay causes, how much is avoidable, or whether the lesson predicts outcomes elsewhere. Four co-varying stacks and one model family limit generalization. Disclosure handles validity but cannot create broader significance.

## Necessary fixes / acceptance-changing work

- **For the current evidence:** Keep the characterization framing and the explicit no-control-benefit statements. Add the paired Guard-versus-Always latency ratio and prompt-bootstrap interval using the frozen prompt medians as a clearly labeled secondary analysis. This makes the policy's incremental result directly inspectable; do not infer it from overlapping baseline-relative intervals. If no additional analysis is authorized, retain the present bounded language and acknowledge the absent direct contrast.
- Tighten residual wording such as the RTX “token-equivalence gate” to “historical text-path comparator” where it could be read as direct-ID qualification. Preserve stronger language for the separately captured token divergence and direct-ID studies.
- **To materially change an acceptance judgment:** Supply either a controlled, exactness-qualified intervention on a diagnosed bottleneck with measured benefit, or replicated characterization demonstrating a nontrivial predictive lesson across additional independent configurations. A useful guard result would require a predeclared benefit such as paired latency/tail improvement over Always-Spec, demonstrated prospectively. This is new experimental work, not a prose fix, and should not be implied by the current study.
- Do not add elaborate controller comparisons merely to manufacture algorithm novelty. If the paper remains empirical characterization, the priority is depth and reproducibility of its mechanisms and a clear account of what existing literature did not already establish.

## Mock assessment

**Weak reject, moderate confidence.** Strengths are disciplined evidence scoping, concrete failed-path diagnostics, preservation of negative outcomes, and a transparent prospective exact-output experiment. The major weakness is significance: after appropriately removing overclaims, the results remain configuration-specific observations plus a guard that adds no established benefit over fixed speculation. I would be more positive at a venue explicitly welcoming careful reproducibility/negative systems studies, or with acceptance-changing mechanism evidence. No remaining issue identified here requires accusing the authors of unsupported general claims; the main disagreement is whether the bounded contribution clears the MLSys bar.
