# Reviewer G — Independent Writing and Narrative Review

Source reviewed: `b326ff7f20d9bac5afff6f53a6e9d9d8a7aaa7ae`.

Scope: continuous reading of the complete abstract, Sections 1–10, and separate appendix; runtime values/table checked to preserve the meaning of proposed prose. No other reviewer report was read. No manuscript or evidence was edited. This is an editorial review, not a numerical audit or literature review. No specialist Humanizer skill was invoked.

## Overall assessment

The manuscript already has a defensible narrative: local opportunity is filtered first by empirical correctness and then by complete execution cost; the runtime studies test these two decisions separately. It does not fundamentally require a new section order. Its main weakness is that this intelligible argument is repeatedly restated with caveats while the contribution itself remains the vague phrase “this bounded empirical connection.” The paper sounds more like a meticulously defended audit than a paper that trusts readers to follow its measured result.

The two-project feeling is present principally at the Section 6/7 seam, not throughout the paper. Section 6 summarizes all hardware results and introduces qualification/control; Section 7 immediately summarizes qualification/control and the status of both studies again. Section 7’s successive 358H implementation history, M4 algorithm, and full evaluation protocol then make the seam feel like a second project report. A tighter synthesis and a clear contribution sentence would resolve much of this without deleting scientific boundaries.

The strongest defensible central statement is approximately: **The study measures how workload-qualified correctness and complete realized execution cost constrain speculative runtime choices, and prospectively tests cost-based continuation on an available exact path.** This identifies what the paper delivers. It should not be presented as invention of correctness checking, cost accounting, or a threshold policy, nor as proof that the policy is better than fixed speculation.

## Highest-value narrative revisions

| Priority | Location | Issue | Recommended revision |
|---|---|---|---|
| P1 | `01_introduction.tex`, final paragraph, especially last two sentences | “Our contribution is this bounded empirical connection” names a relationship but does not say what a reader learns or can verify. “The studies connect…” is similarly abstract. | State the contribution positively and concretely: measured constraints on the available speculative paths, followed by a frozen test of continued speculation using realized cost. Keep the prior-art disclaimer to one sentence, with fuller distinctions in related work. |
| P1 | `main.tex`, abstract | The abstract opens with a long interrogative, spends most of its space on historical platform figures, and only then introduces runtime control. It reads as a hardware abstract with runtime appended. | Open with the problem in declarative form; organize by qualification and realized cost; retain the historical M4 contrast as bounded evidence; give the prospective result sufficient prominence. Remove historical exactness denominators and most secondary speed figures from the abstract, keeping them in the body. |
| P1 | `06_synthesis.tex` and first paragraph of `07_runtime_codesign.tex` | Two adjacent summaries interrupt observation → diagnosis → response. Both say the studies do not reopen earlier results, and both restate qualification before control. | Compress Section 6 into two paragraphs: what the measured diagnoses change about usable paths; what runtime question follows. Let Section 7 open directly with its two separately frozen tests rather than re-explaining the hardware argument. Preserve “separately frozen”; do not imply a unified prospective four-platform design. |
| P1 | `07_runtime_codesign.tex`, final two paragraphs; `10_conclusion.tex` final sentence | “Establishes profitable prospective execution” is supported, but “usefulness” and a general admission/safeguard framing risk implying a demonstrated benefit of control. Always-Spec is faster in aggregate and no measured safeguard benefit is provided. | State the exact role: a measured implementation/test of realized-cost continuation that remains faster than Target. Explicitly retain the lack of demonstrated improvement over Always-Spec. Do not justify Guard by invented deployment uncertainty, risk reduction, or per-request win rates. |
| P2 | `09_limitations.tex`, all paragraphs | Five paragraphs recapitulate many caveats already stated locally, including some twice within the same section. Material issues compete with minor archival history. | Group into study scope, inference/timing boundaries, and reproducibility/runtime limitations. Keep the M4 provenance defect, 60 prompts, fixed k, no energy/concurrency, and 358H no-performance scope. Move repeated MLX/B570/context history to the appendix where already documented. |

## Repetition and page efficiency

1. **M4 contrast:** the abstract, introduction paragraph 2, Section 4.1, Section 6, Section 7.2 opening, limitations, conclusion, and appendix each restate that separate sessions prevent workload causality. Keep a compact scope phrase in the abstract and the full explanation in Sections 3/4. Elsewhere use “the separate M4 studies” or a cross-reference, without another full denial of causality.
2. **Two diagnoses are not exhaustive and do not explain M4:** this appears in introduction paragraph 3, Section 2 ending, Section 5 opening, Section 5.1, Section 6, and limitations. The Section 5 opening is the most useful home. Keep a concise limitations statement; remove duplicates that do not qualify a new inference.
3. **Frozen/internal status:** “closed,” “formal,” “frozen,” “qualified,” and “separately” often cluster. Their distinctions matter, but the opening narrative need not repeat all of them. Define evidence classes once and attach them when the permitted inference changes. Avoid turning every paragraph into a campaign-status record.
4. **358H stateful advantage:** Section 5.2 first and third paragraphs repeat the same isolated-NPU-versus-realized-state-interface conclusion. The third paragraph should interpret the decomposition figure and its scope, not repeat the first paragraph’s result.
5. **358H qualification:** Section 7.1 ends with two statements that no performance evaluation occurred, after already saying the registry retained no intervention pair. One direct sentence can retain the complete boundary: no qualified intervention remained, so no formal R2 performance comparison occurred and follow-up timings are diagnostic only.
6. **Prior-art disclaimers:** introduction and related work repeatedly say what the paper does not invent. Retain explicit novelty boundaries, but allow the introduction to state the positive contribution before related work elaborates the exclusions.

These edits should recover space for essential clarification without reducing font sizes, altering geometry, or adding a diagram.

## Clarity and terminology

- **Admission versus continuation:** Guard starts every request on Always-Spec and may fall back after completed rounds. Calling it “admission” without qualification can suggest that it decides whether to start speculation. Prefer “continued speculation,” “within-request cost control,” or explicitly define admission as continued use of a qualified path. This is a meaning issue, not merely a synonym choice.
- **“Integrated post-prefill speculative decode”:** accurate but cumbersome when repeated verbatim in abstract, introduction, framework, synthesis, and conclusion. Define the boundary in the first body use and methodology. Thereafter “the complete speculative loop” works where no alternative timing boundary is being discussed. Do not replace it indiscriminately with “end-to-end.”
- **“Profitability is not a simple hardware capability property”:** understandable after rereading, but needlessly abstract. Prefer “The same tested M4 system supports both profitable and unprofitable exact runs,” followed by the separate-study caveat once.
- **“Runtime decisions”:** name the actual decisions when first used—whether the path meets the output contract, then whether to continue speculation. This makes the Section 6→7 logic legible without relying on general systems terminology.
- **Guard calibration paragraph:** keep the cumulative ratio, target reference, one-way fallback, selected first decision, and held-out freeze in the main paper. The detailed median-of-latency/median-of-token definition and tie-breaking recipe can move to the appendix if space is needed. Preserve an explicit pointer and do not silently redefine the reference as a median of per-observation ratios.
- **358H Section 7.1, first paragraph:** CPU state reconciliation, unavailable NPU representation, interprocess design, and timer inclusion compete in one paragraph. State the attempted intervention first; group the two draft-side qualification boundaries together; retain timer inclusion as a short implementation sentence or appendix detail. Do not delete the explanation that failed qualification is stack/representation scoped.
- **“Formal,” “Phase 2,” “Phase 3,” “R2,” “STRONGLY_SUPPORTED”:** readers encounter workflow vocabulary that is useful internally but not inherently scientific. Keep necessary identifiers for auditability, with their ordinary-language meaning on first use. For example, “the integrated hardware experiment (Phase 3).” Raw status tokens need not recur throughout the main text.
- **CIs and exactness:** editorial compression must retain what exactness is compared against and that prompt intervals are conditional on sessions. Do not turn direct-token agreement into functional correctness, universal determinism, or a quality statement.
- **Pronouns:** no major unresolved pronoun reference was found. The greater clarity problem is abstract noun chains (“bounded empirical connection,” “realized stateful integration,” “execution-path qualification”), not pronoun ambiguity.

## Independent abstract proposal

This is an editorial proposal for comparison with independent reviewers’ proposals, not an instruction to replace the abstract verbatim. Existing value macros should supply its numbers.

> Favorable acceptance, draft throughput, and target batching do not necessarily produce faster speculative decoding. We examine this gap in four retrospective consumer-system studies under a strict greedy-token equivalence contract, then test runtime decisions in separately frozen studies. Two measured boundaries explain important failures: correctness qualification excludes cheap verification paths on the tested RTX and B570 stacks, while an isolated NPU drafting advantage does not survive the tested 358H stateful interface. Separate M4 studies yield both exact gains and exact slowdowns, without isolating workload from session effects. These observations motivate qualifying execution paths before controlling their realized cost. A 358H intervention stops at qualification, with no formal runtime performance result. On an available exact M4 path, a one-way cost guard achieves 1.3114× held-out post-prefill speedup over target-only (95% prompt-bootstrap CI [1.2487, 1.3787]). Fixed speculation has the higher aggregate point estimate, 1.3469×. The contribution is measured evidence linking path qualification and complete execution cost to prospective runtime control, not a new speculation algorithm or demonstrated improvement over fixed speculation.

Tradeoff: the final sentence remains somewhat meta-academic. It is defensible, but if the revised introduction already defines the positive contribution plainly, the abstract could end with the bounded runtime observation instead of another novelty disclaimer. Do not add oracle regret to this abstract; it would introduce a new denominator and compete with the essential result.

## Independent concise conclusion proposal

> Speculative runtime choices depend on more than favorable component measurements. In the tested stacks, correctness qualification can remove a cheap verification path, and a draft-device advantage can disappear at the state interface. The runtime studies expose the two resulting decisions: 358H has no qualified intervention to time, while M4 permits a prospective test of continued speculation using realized cost. That guard preserves exact outputs and remains profitable against target-only, but does not establish an improvement over fixed speculation. The practical lesson is to assess complete execution cost on the paths that actually satisfy the intended output contract; local opportunity alone does not establish realized gain.

This deliberately avoids another platform-by-platform numerical summary. It does not claim general policy benefit, universality of a qualification failure, or a new threshold algorithm.

## Recommendations deliberately not made

- Do not rewrite the paper around Guard as the primary algorithmic innovation.
- Do not hide Always-Spec’s higher estimate or remove the oracle row merely to simplify the story.
- Do not merge historical M4 studies with the prospective population or estimator.
- Do not delete material provenance or session qualifications under a Humanizer pass.
- Do not add a new figure simply to make the runtime section look larger.
- Do not claim that the negative 358H runtime result experimentally caused the M4 policy design unless the chronology supports that statement.
- Do not convert all cautionary wording to affirmative causal language. The goal is fewer, better-placed qualifications, not stronger claims.

## Residual objection after editorial repair

Writing can clarify the paper’s contribution but cannot increase its empirical breadth or establish that Guard improves on Always-Spec. A reviewer who requires a novel controller or controlled cross-platform causal study may still reject it. The manuscript should make that disagreement about the actual bounded contribution, rather than let vagueness or repetition make it appear to claim an unmeasured one.
