# Internal research-track review of HeteroSpec v0.2

Review date: 2026-09-21. Target: [Draft PR #18](https://github.com/leecdiang/HeteroSpec/pull/18), branch `paper/mlsys2027-narrative-v0.2`, **exact starting HEAD `afda6a192f3e9359eb5f5d7d24d3313bf59ef2f3`**. The working revision branch starts at that commit. No older manuscript was reviewed.

These are three independent simulated internal reviews, not actual MLSys committee reviews or an acceptance prediction. Each reviewer formed and saved its findings independently before evaluating a shared conservative-edit plan. This report preserves their disagreements and distinguishes evidence defects, wording issues, author decisions and possible new research.

The review uses the [MLSys 2027 call's novelty, quality, interest and impact criteria](https://mlsys.org/Conferences/2027/CallForResearchPapers), checked on the review date. The call does not supply a numerical scale here; none is invented. The exact-HEAD main PDF has 10 main pages plus one reference page (SHA-256 `4d7f674a234b2dd889e254486d053c48dcdd6f6b3c6e3187480e4a12a2f4d632`); the separate appendix has three pages (`7ac248fa0c59f2788a6bed1004d8303ed50553c2b792181dfe312be78d3b0e3e`). Page references below refer to those starting artifacts, not any subsequently revised PDF.

## Skills inspected before review

The requested skills were available under the installed `openai-templates/0.1.1` package. Their `SKILL.md`, `artifact-template.json` and retained `assets/reference.docx` contents were inspected. In accordance with the author's request, they were used as review lenses only; the requested Markdown report replaces their normal DOCX production workflow, and their reference files were not modified.

| Skill | Applied lens | Limits |
|---|---|---|
| Experiment Analysis | Hypothesis/design correspondence, primary versus exploratory outcomes, measurement definitions, uncertainty, deviations and limitations | Template statistical slots do not justify new tests, p-values or reanalysis. |
| System Design | Actual interfaces and contracts, state lifecycle, tradeoffs, feasibility, evaluation readiness and unverified guarantees | A design template supplies no implementation or measured contribution. |
| Design Report | Findings-to-implications hierarchy, conditions, recommendations, redundancy and page efficiency | Presentation structure is not scientific authority. |

Local skill sources: `/Users/lee/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-experiment-analysis/SKILL.md`, `artifact-template-system-design/SKILL.md`, and `artifact-template-design-report/SKILL.md` in the same skills directory. The PDF skill was used for visual review; all 11 main-PDF pages and all three appendix pages were inspected. The review is internal and contains identifying repository/provenance details; it is not an anonymous submission artifact.

## Reviewer A — Experimental rigor

**Reviewed version:** Draft PR #18, branch `paper/mlsys2027-narrative-v0.2`, exact starting commit `afda6a192f3e9359eb5f5d7d24d3313bf59ef2f3`; manuscript v0.2 (10 main-text pages and one reference page), v0.2 appendix, active source, evidence ledger, scientific handoff, and selected campaign closeouts. No older manuscript was reviewed. This is a simulated independent internal review, not an official venue review. I read the available Experiment Analysis, System Design, and Design Report instructions and retained references. They supplied hypothesis/method/outcome, measurement-contract, and evidence-to-recommendation lenses; they did not establish scientific validity.

### Summary

The paper retrospectively assembles four consumer hardware/runtime campaigns around a useful question: why do apparently favorable component measurements fail to deliver profitable speculative decode execution? It retains a positive M4 HumanEval campaign alongside an exact negative M4 representative campaign, correctness-blocked RTX/B570 paths and bounded follow-up controls, and exact negative CPU/NPU results on 358H. The strongest evidence is the qualification-induced change in usable verification paths and the direct measurement of the 358H replay-plus-proposal region. The paper does not establish architecture effects, workload-only causality, population-wide reliability of local predictors, or benefits from a persistent-state intervention.

**Readiness:** major revision before submission, principally for scope and confirmatory-versus-retrospective presentation rather than a demonstrated numerical error. The existing case conclusions can stand without new hardware experiments. Stronger causal or deployment claims would require a separately designed study.

**MLSys criteria:** novelty is limited but potentially meaningful at the boundary between correctness qualification and realized integration cost; quality is comparatively strong in retained failures, estimator discipline, and measurement semantics, but campaign chronology is underexplained; interest is good for practitioners evaluating consumer inference stacks; impact remains conditional because the paper measures a narrow model family, selected stacks, and no implemented remedy.

### Strengths

- The negative and blocked campaigns remain visible. Table 2 reports evidence class, exact pairs, and faster prompts beside speedup; a precise confidence interval is not used to convert a mismatching B570 path into an admissible optimization.
- Sections 2.3–2.4 and 5.2 correctly distinguish complete committed progress from accepted draft tokens, target-forward proxies from full target-round cost, and arithmetic component totals from the primary prompt-level geometric mean. This avoids several plausible but invalid cross-experiment calculations.
- Section 3.2 and Appendix B preserve campaign-specific estimators and the prompt as the resampling unit. Three repeated runs are not represented as three independent prompts. The paper explicitly limits confidence intervals to within-campaign prompt uncertainty.
- The M4 comparison already has substantial safeguards: separate preregistration, both outcomes retained, no pooled or paired between-workload estimate, and explicit session confounding in Section 4.1 and Figure 2. This is not currently presented as a clean causal workload ablation.
- Correctness claims are carefully scoped. The CUDA numerical capture does not purport to identify a kernel root cause; B570 serialization is not conflated with exactness; HumanEval token equality is not functional correctness. The 358H source and energy limitations are retained.

### Major concerns

1. **The manuscript does not state the retrospective synthesis as directly as it states campaign freezing.** Sections 1–3 repeatedly call outcomes or campaigns “frozen,” while the introduction now presents one coherent question that can be mistaken for a jointly prespecified cross-platform study. The source handoff documents sequential campaigns, later controls, and subsequent scientific synthesis. This is a reporting gap, not evidence that the frozen outcomes were altered. Add one explicit statement near the study design: “The cross-platform synthesis is retrospective: campaign-level primary outcomes were frozen independently, and later mechanism controls retain their stated secondary or diagnostic scope.” Avoid implying every mechanism observation was prospectively registered.

2. **The headline question sounds like an evaluation of predictor reliability that the study does not perform.** The title’s “across consumer systems” is defensible as a description of four cases, and Section 9 explicitly disclaims a population failure rate. However, “how reliably” and “do not reliably predict” in the abstract, introduction, and synthesis can imply a prespecified predictor, sampled population, or general reliability estimate. No such accuracy/calibration analysis is reported. The supported inference is that the measured local indicators are insufficient to establish profitable integrated execution in these cases. Prefer “can fail to translate” or “do not by themselves establish gains in the tested configurations.” A narrower title referring to “four consumer stacks” is an author positioning option, not required to repair the numerical evidence.

3. **The timing boundary should accompany the highest-level claims.** Section 3.1 accurately distinguishes native decode counters and the 358H complete post-prefill loop from whole-request latency. Yet “integrated gains” in the abstract opener and synthesis, “end-to-end controls” in Section 5.1, and “realized request decomposition” in Section 5.2 require readers to remember this definition. Use “integrated post-prefill decode” at these first or summary mentions. Do not claim the heterogeneous timing instruments have become identical; retain the native-counter versus enclosing-loop distinction.

4. **The 358H interpretation should remain an observed boundary diagnosis rather than an isolated causal attribution.** The measured call combines replay and proposal, and no persistence intervention or replay-only timer exists. Section 5.2 and Figure 4 correctly disclose this. “The state interface erases” in the abstract and synthesis is less careful than “the isolated advantage does not survive the tested stateful integration.” A dominant measured aggregate identifies where time is spent; it does not quantify the gain that removing replay would deliver. Replace the stronger causal shorthand where it appears; keep the direct component evidence and its qualifications.

5. **The unmeasured runtime section cannot remedy the research contribution gap.** Section 7 is honest about its status and includes sensible prospective requirements. Nonetheless, roughly 1.5 pages of interface and evaluation plans add no experimental support to the current Research Track claim. For submission, either treat a much shorter version as discussion/future work, or complete a separately scoped intervention study before claiming a systems implementation contribution. Removing or relocating the full section is an author scope decision, not a conservative review edit. Its presence in this internal draft is acceptable only while its proposed status remains unmistakable.

### Minor concerns

- “Representative 24Q” should consistently mean the frozen six-group Spec-Bench sample, not consumer usage in general. The equal group allocation is already stated, which limits the risk; no change to its estimator or historical label is warranted.
- “Secondary” groups registered variants with bounded follow-up controls (Section 2.2). Keep the provenance distinction visible where a control matters; “secondary” must not silently imply preregistration. A short chronology would be more useful than repeating generic caveats.
- The existing M4 session qualification is adequate for the observed-regime claim. The source closeout additionally records repetition drift; that makes an interleaved same-session replication necessary for a future workload-causal claim, not a reason to discard either closed result or recompute its interval.
- The equations are correct as an accounting identity, but their early placement and inclusion of “accounting discipline” as a contribution can suggest methodological novelty beyond what Section 8 disclaims. Present them as measurement definitions rather than a separate innovation.
- Figure 1 overlaps with Table 2, but the table supplies complete numerical outcomes, correctness counts, and evidence classes that the overview cannot replace. The overlap is not an experimental defect. Table 3 duplicates Figure 3 more closely; it is a plausible space-saving removal if all its qualification information remains in the figure and prose.
- Retain the essential scope conditions at first use, in self-contained captions, and in limitations. Repetition in the synthesis and conclusion can be trimmed without weakening inference.

### Questions for authors

1. Can you give an anonymous chronology distinguishing campaign freezes, the separately registered M4 HumanEval study, later mechanism controls, and the retrospective synthesis? A chronology clarifies design intent without changing any frozen outcome.
2. Which reproducibility artifacts can be released anonymously for the Windows derived pair tables and captures, and which raw records are irrecoverably unavailable? Current prose discloses the weaker provenance but offers little guidance for independent reproduction.
3. Is the intended contribution an explanatory multi-case characterization, or a general test of local predictor reliability? The current evidence supports the former.
4. Will the submission contain a measured runtime intervention? If not, what editorial rationale justifies a full design section in the main text rather than a short discussion?

### Concrete requested changes

**Low-risk prose/table edits supported by this review:** explicitly label retrospective synthesis and independently frozen campaign outcomes; qualify headline integrated/end-to-end claims as post-prefill decode; replace general reliability language with bounded insufficiency/counterexample language; describe the 358H contrast without implying isolated replay causality or a measured persistence benefit; identify accounting as a measurement aid; retain all evidence classes, mismatches, estimators, numerical values, and frozen deviations. Removing the mechanism table is acceptable only as a presentation edit with its informational content preserved elsewhere.

**Research or submission-scope decisions, not automatic edits:** choose the final narrow title; decide whether to shorten/relocate runtime; establish an anonymous reproducibility release; run a matched-session M4 comparison only if claiming workload causality; implement and prospectively evaluate persistent state only if claiming its benefit. None is permission to reopen or relabel the closed campaigns.

**Pressure-point verdicts:** (1) title needs scope discipline, not necessarily rejection; (2) M4 is already responsibly qualified, and no causal contrast should be added; (3) boundary wording needs tightening; (4) retrospective status needs an explicit statement; (5) accounting is useful but overprominent as a contribution; (6) overview/headline overlap is functional; (7) verification/table overlap is a reasonable cut candidate; (8) unmeasured runtime adds no measured Research Track contribution; (9) consolidate caveats while retaining self-contained figure qualifications; (10) the related-work disclaimers are sound, but the positive incremental contribution must be sharper than “we also characterize SD.”

## Reviewer B — MLSys systems contribution

**Review target:** Draft PR #18, branch `paper/mlsys2027-narrative-v0.2`, exact commit `afda6a192f3e9359eb5f5d7d24d3313bf59ef2f3`. Page references refer to that commit's 10-page main text and separately paginated appendix. This review was written independently before reading the other reviews.

**Review lens and scope:** I inspected the available System Design skill and its retained reference, using its architecture, contract, tradeoff, and evaluation-readiness questions as a review lens, not scientific authority. I read the manuscript source, selected-figure captions, tables, bibliography, literature audit, and extracted current PDF text. I checked selected cited primary sources online; this is targeted novelty assessment, not an exhaustive literature review or independent experiment replication. The [MLSys 2027 Research Track call](https://mlsys.org/Conferences/2027/CallForResearchPapers) names novelty, quality, interest, and impact; it does not require every contribution to be a new algorithm or a positive speedup.

### Summary

The paper assembles four consumer hardware/runtime case studies of speculative decoding with a strict greedy-token contract and post-prefill decode timing. M4 has an exact positive HumanEval outcome and an exact negative representative-workload outcome in different sessions. RTX and B570 illustrate the interaction of correctness qualification and usable target paths. The 358H case shows an isolated NPU draft advantage disappearing in a stateful adapter whose replay-plus-proposal region dominates. The proposed runtime interface remains unimplemented.

My most favorable reading is a measurement paper about two implementation boundaries: the numerical execution path admitted by a chosen correctness contract, and the state interface at which a component advantage is actually consumed. Those are useful systems observations. The present high-level claim that favorable local indicators do not ensure whole-loop gains, however, is familiar and underspecified as a research contribution. The manuscript needs a sharper account of what its consumer-stack evidence adds beyond prior characterization and correctness-cost work.

**Criterion assessment:** Novelty is currently limited but plausible at the level of these specific measured boundary interactions; quality is strengthened by scope discipline and honest negative results; interest is credible for local-inference/runtime practitioners; demonstrated impact remains bounded because neither a reusable intervention nor a broad controlled comparison is evaluated. **Current readiness recommendation:** I would not support acceptance of the draft in its present form. I would reconsider a focused empirical submission with a clearer delta from prior work; a measured new runtime is one possible path, not a mandatory condition for a characterization paper. Copyediting alone cannot settle this contribution question.

### Strengths

1. **An actionable distinction between physical opportunity and usable execution.** Section 5.1, pp. 5–7, measures cheap batched target forwarding alongside a failed contract and more expensive exact RTX controls. The B570 counterexample prevents serialization from becoming a false correctness guarantee. This is stronger than reporting slowdowns alone.
2. **The 358H measurement boundary is concrete.** Section 5.2 and Figure 4, pp. 7–8, distinguish isolated throughput, realized replay-plus-proposal time, complete target-side work, and residual overhead. The CPU and NPU paths identify different dominant regions. That helps an implementer decide which boundary to investigate without incorrectly blaming accelerator compute capability.
3. **Negative results are retained without promoting diagnostics.** Table 2 keeps primary, secondary, and diagnostic results distinct, and the M4 positive result does not erase the negative study. This materially improves the credibility of the systems evidence.
4. **Related work acknowledges the right neighboring ideas.** Section 8, pp. 9–10, explicitly disclaims novelty in heterogeneous placement, numerical variation, state reuse, and the accounting identity. The runtime section also names unverified backend capabilities and reconciliation costs rather than assuming that persistence is free.

### Major concerns

1. **The novelty boundary is mostly a list of disclaimers, not a positive incremental claim.** The final introduction paragraph, p. 2, gives accounting discipline contribution-level status; Section 8 then correctly says the identity is established. [Performance or Illusion?](https://proceedings.mlsys.org/paper_files/paper/2026/hash/554e056fe2b6d9fd27ffcd3367ae1267-Abstract-Conference.html) already studies SD performance across workloads and batch sizes and reports verification dominance and gaps from theoretical bounds. [Correctness Forensics](https://arxiv.org/html/2510.22876v4) already connects output-equivalence checks to implementation costs and separates numerical effects from ragged-batch faults. The relevant distinction here is the measured consequence of numerical path qualification for single-request consumer execution, plus the isolated-versus-realized adapter boundary—not discovery that correctness or overhead matters. State that distinction positively and identify which claims are supported by which experiments. Do not assert that the cited works lack these observations without a deeper comparison.
2. **The breadth of the framing exceeds the design's comparative power.** “Across consumer systems” is literally true as a case inventory, but the title and “how reliably” question can suggest a sampled cross-platform reliability assessment. Four co-varying stacks cannot estimate failure prevalence or isolate hardware properties. Sections 3 and 9 acknowledge this, but the main framing still asks a broader question than it answers. The M4 contrast is an observation across separately run studies, not a controlled workload ablation or an explanation for why code succeeds. A four-configuration case-study framing would preserve the useful evidence and make the contribution more defensible. Explicitly identify the cross-platform synthesis as retrospective while campaign primary outcomes were independently frozen.
3. **The unmeasured runtime section does not currently supply a Research Track systems contribution.** Section 7 occupies much of pp. 8–9. Its request-state object, checkpoint/reconcile operations, path registry, and evaluation plan are reasonable engineering requirements, but no implementation, feasibility result, memory tradeoff, intervention effect, or ablation is available. [LLM-42](https://arxiv.org/html/2601.17768v2) already evaluates a scheduling-based verify/rollback mechanism with a fixed-shape verifier; [Strong Drafts Need Compact Memories](https://arxiv.org/html/2608.30252v1) already develops incrementally maintained draft-side state, though with different objectives and mechanisms. Neither prior result establishes that this OpenVINO adapter can support the proposed interface. The current manuscript responsibly says so, but the long proposal still makes an otherwise complete empirical paper look unfinished. Before submission, choose between a short implications/future-work treatment and a separately evaluated intervention. This is an author-level structural decision, not a conservative prose edit.
4. **Systems impact needs a clearer beneficiary and decision.** The results justify “qualify the actual execution path, then measure the whole post-prefill loop”; they do not establish a general path-selection policy or portable API. Explain what a practitioner can decide from each closed result: e.g., a cheap but blocked path is ineligible under this contract; reducing tiny residual orchestration cannot address the dominant measured loss; optimizing NPU state handling is a hypothesis, while CPU drafting remains target dominated. This uses existing evidence. Claims that persistent state solves the loss, or that one placement is generally preferable, would need new controlled measurements.

### Minor concerns

- **Timing language remains loose at high-visibility points.** The abstract opens with “integrated gains”; Figure 1 says “end-to-end gains”; Section 5.1 calls the serialized paths “complete end-to-end controls.” Methods defines the boundary, but these phrases can be read as whole-request latency. Prefer “integrated post-prefill decode” where the full speculative loop is intended, and reserve whole-request wording for measurements that include prefill/startup.
- **Accounting still occupies more conceptual space than its novelty merits.** Section 2, pp. 2–3, is useful methodology. Its output contract and evidence classes should remain visible. The cost identity, normalized version, break-even inequality, and aggregation cautions could be tighter without changing any equation or estimator. Do not delete the distinction between accepted draft tokens and all committed output.
- **The two apparent display redundancies differ.** Figure 1 supplies the local-indicator/outcome contrast; Table 2 supplies complete CIs, sample counts, and evidence classes. They are complementary despite repeated headline values. Table 3 and Figure 3 repeat nearly the same verification ranges and qualification categories and are better candidates for reducing table prose or relocating a duplicate table. Preserve accessible exact values and provenance somewhere; figure assets need not change.
- **Repeated caveats obscure the positive systems message.** “Not exhaustive,” “not a hardware ranking,” “not measured,” and related qualifiers recur in the abstract, introduction, results, synthesis, runtime, related work, limitations, and conclusion. Keep qualifications where a display or claim could be misread independently, but consolidate generic scope statements. Precision need not require a disclaimer after every observation.
- **Heterogeneous placement is already established.** [Mirror-SD](https://arxiv.org/html/2510.13161v2) explicitly proposes GPU/NPU mapping and overlapping execution. This manuscript correctly does not claim firstness. The distinction is its measured qualified consumer adapter, not the existence of a GPU/NPU combination. The manuscript's cited [runtime-controlled study](https://www.mdpi.com/2079-9292/15/14/3179) is relevant to accounting novelty according to its literature audit; a fresh publisher retrieval failed during this review, so I do not independently extend that source's claims beyond the audit.

### Questions for authors

1. What is the single strongest observation a reader could not obtain simply from existing characterization, numerical reproducibility, and KV-state literature? Which within-stack measurements establish it?
2. Is the intended final contribution an empirical case-study paper or a new runtime? The current “hardware-complete / runtime-reserved” status leaves that decision open.
3. Which cross-platform questions and mechanisms were selected retrospectively, and where are the separately frozen campaign questions and follow-up evidence classes stated for the reader?
4. What concrete deployment need motivates exact greedy-token equivalence here? The strict contract is legitimate, but how much of the intended impact applies specifically to that contract?
5. Does the qualified OpenVINO backend expose usable state restoration/truncation, or is that capability still an open feasibility question? Please do not imply an answer without evidence.

### Concrete requested changes

**Conservative edits supported by the existing record:** Add one explicit retrospective-synthesis statement near the study design; qualify integrated/end-to-end results as post-prefill decode; make the contribution paragraph center the two measured implementation-boundary findings and present accounting as their measurement method; retain the M4 session caveat next to its contrast; clarify that the pending runtime is future work and contributes no measured result; tighten repeated generic disclaimers without deleting local correctness/CI/timing qualifications. If retaining the current title, make the four-case scope unmistakable in its subtitle or opening sentence.

**Author decisions before a submission-ready draft:** Sharpen the novelty argument against the closest characterization and correctness-cost studies; decide whether to shorten/relocate the runtime proposal or supply a new prospective evaluation; decide whether Table 3 earns its space next to Figure 3. Do not replace frozen estimators or “upgrade” diagnostic evidence to make the contribution appear stronger. Additional platforms, matched-session workload controls, or a state-persistent intervention could increase impact, but they are new research rather than edits authorized by this review.

## Reviewer C — clarity and presentation

### Review basis and criterion assessment

Independent review of PR #18 at `afda6a192f3e9359eb5f5d7d24d3313bf59ef2f3`, before revision. The main PDF has 10 text pages and one reference page; the supplement has three pages. Both PDF hashes match the recorded `PDF_QA.json`; all 14 pages were visually inspected, together with the active TeX. I read the available Design Report skill and its retained reference as an information-hierarchy lens: findings should lead to bounded implications and recommendations. Its report template is not a scientific authority or a requirement to change the paper format. I also followed the PDF skill's read-only visual review workflow.

- **Novelty:** The presentation is candid about established characterization, accounting, heterogeneous execution, numerical reproducibility, and state reuse. It still needs a more affirmative statement of what this collection of bounded cases adds beyond those strands. I do not award novelty for the unimplemented runtime proposal.
- **Quality:** The measured-result presentation is generally careful and visually clean. Evidence-class labels, uncertainty, and timing boundaries are unusually explicit. Retrospective synthesis chronology and headline terminology need clarification; repeated disclaimers obscure the hierarchy of findings.
- **Interest:** The contrast between favorable component measurements and blocked or negative realized paths is interesting to practitioners. The M4 positive result usefully prevents a uniformly negative story.
- **Impact:** Practical impact is plausible as a warning against extrapolating isolated measurements. Broader portability, prediction, and runtime-intervention impact are not demonstrated.
- **Readiness:** The hardware characterization is coherent enough to review, but the current combined manuscript reads as an internal draft with a substantial future-work reservation. It is not submission-ready as presented. This is a qualitative internal assessment, not an official numeric review score.

### Summary

The paper presents separately frozen speculative-decoding campaigns on four consumer hardware/runtime stacks. It contrasts local target-forward or draft-throughput opportunities with qualified decode outcomes, then develops two bounded diagnoses: correctness changes which verification path is usable, and the measured state interface erases an isolated NPU drafting advantage. A separately preregistered M4 code workload has positive speedup while the representative workload is negative. A proposed runtime interface is explicitly unmeasured. The strongest presentation is the results-to-diagnosis sequence and the direct 358H cost figure; the weakest is the split identity between a completed characterization paper and an unfinished runtime-design paper.

### Strengths

1. **The visual hierarchy generally works.** Figure 1 (p. 2) gives the local-versus-realized puzzle; Figure 2 (p. 4) makes both M4 outcomes visible; Figure 3 (p. 6) combines cost and qualification; Figure 4 (p. 7) connects isolated and realized measurements. All are readable at the inspected publication size, without clipping or overlap. The appendix inventory is appropriately separate from the main argument.
2. **The M4 interpretation is already carefully bounded.** Methods (pp. 3–4), §4.1 (pp. 4–5), and the Figure 2 caption explicitly distinguish separate workload studies from a controlled between-workload comparison and mention session differences. This pressure point warrants headline alignment, not an accusation that the body claims a workload-only effect.
3. **Figure 1 and Table 2 are not simply duplicates.** Figure 1 selectively pairs local opportunity with realized outcome; Table 2 (p. 5) supplies the complete seven-path outcome inventory, confidence intervals, exact pairs, faster prompts, and evidence class. Both have defensible roles if their accompanying prose does not repeatedly restate every row.
4. **Qualifications protect interpretation where they matter.** Figure 3's context ranges are distinguished from CIs, and Figure 4 distinguishes arithmetic component means from prompt-level geometric-mean speedups. These are necessary reading aids, not removable defensive language.
5. **Related work avoids inflated novelty claims.** Section 8 acknowledges established work in all five relevant areas, and §7 clearly labels its claims as proposals.

### Major concerns

1. **The runtime reservation weakens the finished-paper identity (pp. 8–9, §7).** Roughly a page and a half details a proposed interface and a prospective evaluation, while the opening status line and conclusion call the title and paper conclusion provisional. The issue is not hidden overclaiming: the text is explicit that nothing is implemented or measured. The issue is that scarce Research Track space is used for a project plan rather than evidence, and the reader is asked to evaluate two different contribution states. Before submission, the authors must choose a completed characterization paper with concise implications/future work, or a separately evaluated runtime contribution. That scope choice is larger than conservative copyediting.
2. **Retrospective synthesis is not explicitly named (pp. 1–4, §§1–3).** “Frozen campaigns” and the evidence-class descriptions do not by themselves tell a reader whether the cross-platform question and case grouping preceded every campaign. State clearly that this cross-platform synthesis is retrospective, that campaign-level primary outcomes were frozen independently, and that subsequent mechanism controls retain their bounded classes. This short clarification would improve credibility and remove ambiguity without weakening any measured result.
3. **Headline scope remains broader than the precise body (p. 1, title/abstract; pp. 8 and 10, synthesis/conclusion).** “Across consumer systems” is defensible as a description of the four cases, but the opening “how reliably” and repeated “do not reliably translate” can sound like an estimated general failure rate. The limitations correctly reject that inference. Frame the principal question and conclusion directly around the observed configurations. “Integrated” and several “end-to-end” references can also imply whole-request latency; Methods correctly says initial prefill and loading are excluded. Use “integrated post-prefill decode” at headline uses and when returning to a latency claim. A concise abstract clause about differing M4 sessions would align its strongest contrast with the body.
4. **The contribution hierarchy is still diluted (pp. 2–3 and 9–10).** Section 2 spends substantial early space on the accounting identities, and the introduction lists accounting discipline alongside empirical contributions even though the paper correctly disclaims a novel cost identity. The definitions are useful, particularly for Figure 4, but their role should be visibly methodological. The novelty boundary in Related Work is predominantly a sequence of things not claimed. Add a short positive statement that locates the specific observations and measured consequences relative to the cited work, without claiming that characterization, state reuse, or numerical divergence is new.
5. **One figure/table pair and several caveat passages consume space without equivalent information gain.** Table 3 (p. 5) repeats the same five paths, proxy ranges, and qualification outcomes shown more precisely in Figure 3 (p. 6). It offers little distinct content. This is a much stronger redundancy candidate than Figure 1 versus Table 2. Separately, the same “not exhaustive,” “not a hardware ranking,” “no measured intervention,” and M4 noncausality qualifications recur in the introduction, results, synthesis, runtime, limitations, and conclusion. Retain qualifications at the claims and figures they govern, but remove adjacent restatements. Do not shorten the indispensable distinction between proxy and complete cost or between arithmetic and geometric summaries.

### Minor concerns

- “Representative” is a study label for a frozen 24-prompt, six-group sample, not evidence of representativeness for all consumer workloads. Keep the sampling definition nearby and avoid letting the unqualified label carry a broader claim.
- Table 2's abbreviated “Second.” and “Diag.” are decipherable but less clear than full labels; expand if the existing table width permits, without changing classifications.
- Section 5's title “Why Favorable Local Indicators Fail” is stronger than its carefully scoped opening. “Two Measured Failures of Local Indicators” or an equivalent bounded heading would better match the content.
- Figure 1's caption is long and partly repeats its internal annotations. Because the asset and its scientific qualifications are fixed, any later shortening should be limited to redundant wrapper prose and must preserve shared-M4-micro-study and context qualifications.
- Appendix Figure A1 occupies a dedicated third page with generous white space. It is readable, appropriately scoped as an inventory, and not an urgent layout defect. Do not shrink the artwork merely to save that page.
- Section 6 already supplies a hardware conclusion; §10 repeats much of it and then returns to internal planning. The eventual submission version should have a single decisive conclusion consistent with the chosen scope.

### Questions for authors

1. Is the intended submission a completed consumer-stack characterization or a systems intervention paper? What concrete contribution will remain if no runtime measurements are added?
2. Which aspects of the synthesis question and case selection were decided after the individual campaign outcomes were available?
3. What is the single most important systems insight that a reader should retain beyond “measure the complete qualified path”? Can it be stated affirmatively and tied to the RTX/B570 and 358H evidence?
4. Does Table 3 serve an audience or information need that Figure 3 does not? If not, why keep both in the main text?
5. Would a title explicitly signaling four case studies better match the intended generalization, or do the authors intend “across” only descriptively?

### Concrete requested changes

**Conservative changes supported by the inspected evidence:**

1. Add one explicit retrospective-synthesis statement distinguishing independently frozen campaign primary outcomes from later bounded controls.
2. Make abstract/introduction/synthesis/conclusion latency references explicitly post-prefill decode, and avoid language suggesting an estimated population-wide reliability rate.
3. Add a short M4 session-difference qualifier in the abstract; preserve both effect sizes, CIs, exactness counts, and the existing body qualifications.
4. State the empirical contribution affirmatively while retaining the established-prior-art boundaries; identify accounting as a measurement tool and runtime as an unmeasured proposal.
5. Remove only adjacent redundant caveat wording and expand ambiguous table abbreviations where layout permits. Preserve all scientific qualifiers required to interpret a figure or numerical claim independently.

**Structural choices for the authors, not automatic edits:**

- Remove or substantially reduce §7 for a hardware-only submission, or replace it with independently measured results under a new protocol. Do not imply that prose refinement supplies the missing contribution.
- Remove or relocate the redundant mechanism Table 3 after confirming all of its information remains accessible through Figure 3 and text.
- Consider shortening §2 and consolidating §§6/10 after resolving the runtime scope; retain the definitions needed for the numerical accounting.
- Decide whether to narrow the title to explicitly signal four case studies. A title edit should follow the authors' chosen submission identity, not substitute for it.

## Meta-review

The reviewers converge on a viable **bounded empirical case-study paper**, not yet an acceptance-ready Research Track submission. The strongest evidence concerns the usable verification path after correctness qualification and the gap between isolated draft throughput and the measured stateful integration boundary. No reviewer identified a demonstrated numerical error in this review; this is not a fresh audit of every raw experiment. The principal remaining risks are incremental novelty, the breadth of the question relative to the case-study design, and the amount of main-paper space assigned to an unmeasured proposal. A new runtime intervention is not inherently required for an empirical paper, but its proposal cannot count as an evaluated contribution.

### Must-fix before the next draft

1. **State the study chronology explicitly.** Identify the cross-platform synthesis as retrospective and campaign-level primary outcomes as independently frozen. Preserve the distinction among registered variants, later secondary controls, mechanism-supported findings and diagnostics. “Frozen” must not imply a jointly preregistered four-platform hypothesis.
2. **Align headline scope with the design.** Replace predictor-reliability rhetoric with observed-case claims. Four co-varying stacks establish counterexamples and bounded mechanisms, not a failure rate, predictor-calibration result or hardware-only effect. The current title is not literally false; whether to narrow it is an author positioning decision.
3. **Make the timing boundary visible at first and summary use.** Prefer “integrated post-prefill decode” to ambiguous “integrated” or “end-to-end” latency wording. Retain the distinction between native runtime decode counters and the complete 358H enclosing loop; terminology does not harmonize the measurement instruments.
4. **Keep state-cost conclusions observational.** Say that the isolated NPU advantage does not survive the tested stateful integration. Preserve direct replay-plus-proposal dominance without implying a replay-only timer or a quantified benefit from persistence.
5. **Give the measured contribution a positive statement.** Center the path-qualification and realized-state-boundary observations; describe accounting as the measurement method. This wording correction is possible now, but an author-level argument for sufficient incremental novelty over the closest studies remains necessary.

For a submission-ready next draft, the authors must also choose the runtime scope: shorten/relocate the unmeasured proposal as implications, or establish a separately evaluated intervention. The current internal draft may retain its unmistakable pending status; conservative copyediting does not resolve that submission decision.

### Should-fix

- Make the paper's concrete practitioner decisions easier to identify: exclude blocked paths under the selected contract; measure realized state cost; prioritize dominant timed regions rather than tiny residual orchestration. Do not promise a general policy or successful persistence implementation.
- Consider removing or relocating Table 3, whose verification ranges and qualification categories overlap heavily with Figure 3. Preserve any unique information and provenance. This is a structural presentation choice, not a numerical correction.
- Consolidate generic repeated caveats while preserving qualifications at first use, in self-contained captions, and in limitations. Avoid deleting session, correctness, timing or estimator conditions merely to shorten the draft.
- Decide how to present an anonymous reproducibility package, especially the weaker Windows raw-record provenance. Do not imply the current internal repository is an anonymous artifact.

### Optional

- Narrow the provisional title to four consumer runtime stacks if the authors want the scope visible before the abstract.
- Compress the two equivalent accounting forms after checking that the full-versus-proxy and arithmetic-versus-geometric distinctions remain accessible. The equations themselves are not invalid.
- Add a compact, source-backed anonymous chronology if the one-sentence retrospective statement proves insufficient. Do not invent dates or preregistration coverage.
- Conduct same-session M4 controls or a prospective state-persistence study only if pursuing stronger causal or intervention claims. Neither is authorized or necessary to preserve the present bounded outcomes.

### Disposition of the ten pressure points

| Pressure point | Review finding | Conservative treatment versus author decision |
|---|---|---|
| 1. “Across consumer systems” | Literal case coverage is defensible; reliability/population framing is too broad. | Narrow opening and summary claims; retain provisional title pending author choice. |
| 2. M4 as workload ablation | Methods, results and Figure 2 already reject workload-only causality. | Keep both studies, add a short abstract session cue; no reanalysis or new causal comparison. |
| 3. Integrated versus whole-request | Defined correctly in methods, ambiguous at some headline/summary mentions. | Use post-prefill decode wording locally; preserve different timing instruments. |
| 4. Retrospective synthesis | Present implicitly through evidence classes and history, insufficiently explicit in the design narrative. | Add an explicit retrospective/independent-freeze statement. |
| 5. Accounting prominence | Necessary definitions, but not an independent novelty claim. | Demote it in the contribution paragraph; leave equations and estimators unchanged. |
| 6. Figure 1 versus Table 2 | Complementary: empirical puzzle versus complete CI/count/class inventory. | Retain both; no automatic deletion. |
| 7. Figure 3 versus Table 3 | Substantial duplication. | Record as a should-fix layout decision; retain during conservative pass. |
| 8. Pending runtime section | Honest but contributes no measured evidence and makes submission scope look unfinished. | Preserve pending status; structural removal/relocation or new study remains open. |
| 9. Repeated caveats | Some repetition is necessary for independently read figures; generic repetitions reduce clarity. | Do not weaken specific qualifications; broader consolidation remains editorial work. |
| 10. Prior-work boundary | Correct disclaimers, insufficient positive statement of incremental insight. | Sharpen measured-boundary contribution wording without firstness claims; deeper novelty case remains open. |

### Conservative revision plan

Only prose clarifications common to the experimental, systems and presentation lenses will be applied: retrospective design status, bounded case scope, explicit post-prefill timing, noncausal M4/session wording, observational state-cost phrasing, and accounting as method. Numerical results, estimators, evidence classes, correctness statuses, raw data, scientific closeouts and the entire `paper/mlsys2027/figures/` tree remain untouched. No table deletion, runtime relocation, new experiment, title finalization or new bibliography claim is included.

The initial reviews above describe the exact starting HEAD, not the later edited PDF. Implementation and validation will be recorded below after this review is written, so the concerns and their eventual disposition remain distinguishable.

### Cross-lens concurrence before revision

After saving their independent reviews, A, B and C each explicitly approved the seven-item conservative plan: bounded four-case framing; explicit retrospective synthesis; post-prefill timing; an abstract M4 session cue; observational state-interface wording; accounting as method with a positive measured-boundary contribution statement; and an M4 heading naming separate studies. B and C preferred the empirical opening question “How do favorable local indicators compare with gains in integrated post-prefill decode?” A required preservation of the existing distinction between native decode counters and the 358H enclosing loop. The implementation follows these constraints. None of the approvals resolves the larger novelty or submission-scope decisions.


## Implemented conservative revision and remaining decisions

The complete initial review was written and committed first at `b9a700c` on `codex/mlsys2027-review-v02`, branched directly from the requested starting HEAD. Only then were the unanimously supported prose edits applied. The original title, all tables, all equations, full pending runtime section and bibliography are retained.

| Review request | Applied change | Remaining issue |
|---|---|---|
| Retrospective synthesis | Abstract identifies retrospective case studies; §3.1 explicitly distinguishes independent campaign freezes from the later synthesis and bounded controls. | A longer anonymous chronology is optional; no registration status was changed. |
| Scope and reliability | Abstract, introduction, synthesis, related work and conclusion use bounded observed-case claims instead of a predictor-reliability claim. | Final title and sufficiency of the contribution remain author decisions. |
| Timing boundary | High-level and returning latency mentions use post-prefill decode; Figure 1's manuscript wrapper caption is aligned. | The immutable artwork retains its existing wording and its explicit post-prefill footnote. Native counters versus enclosing-loop instrumentation remains explicit. |
| M4 contrast | Abstract names separate sessions; §4.1 heading names two separate studies. | No causal workload effect is inferred or estimated. |
| State-cost interpretation | High-level “interface erases” shorthand becomes the observed failure of an isolated advantage to survive the tested integration. | Persistence feasibility and benefit remain unmeasured. |
| Contribution hierarchy | Introduction presents accounting as measurement method; Related Work positively identifies the measured verification-path and state-interface boundaries. | The editors do not claim that wording alone resolves novelty or impact. |
| Structural presentation | No tables, figures or runtime subsections removed. | Table 3 duplication, generic caveat repetition, runtime scope and final title remain open. |

No file under `paper/mlsys2027/figures/` was touched. The sole figure-related source change is one timing phrase in `manuscript/figures/00_overview.tex`, which is a manuscript caption wrapper outside that protected tree. No quantitative asset was regenerated.

### Validation of the revised artifact

- Main and hardware-only builds succeed with the unmodified official style. Main remains **10 pages plus 1 reference page**; appendix remains **3 pages** and is byte-identical to the starting artifact. Hardware-only remains **9 pages plus 1 reference page**, with coherent argument and no unresolved references.
- Original evidence validator: **228/228 numerical checks pass**, with the same numerical report and all frozen scientific sources unchanged.
- Narrative invariants: **89 protected file entries and all 57 prior prose numeric macros pass**. The new review report is the sole added exception to the historical narrative scope allowlist, as explained below.
- Five independent figure checks pass; selected assets, insertion sizes, figure numbers and page placements are unchanged. Tables, bibliography, source scripts, raw data and scientific closeouts are byte-identical to the starting HEAD.
- Every numerical literal sequence and scientific numeric-macro sequence in changed TeX files matches the starting version. No estimator, CI, evidence class or correctness status was edited.
- Anonymous PDF text/metadata/links, recursive font embedding and complete authors for all 13 references pass. No overfull boxes or unresolved references/citations remain. The official template's pre-existing harmless empty-anchor warning remains.
- Final visual review: revised main pages 1–6 were inspected by the coordinating editor and pages 7–11 independently by Reviewer C. All pages are legible without clipping or overlap; Figure 4 remains with its diagnosis on page 7. Reviewer C also inspected hardware-only pages 8–10 and confirmed the removal flow; its last body page has normal spare space before references. The appendix is byte-identical to the already inspected starting PDF.
- Revised main PDF SHA-256: `fb4e38a1740547a067ef138b8998b1769d30f05a78872010ab71f9b72632b42e`. Unchanged appendix: `7ac248fa0c59f2788a6bed1004d8303ed50553c2b792181dfe312be78d3b0e3e`. Hardware-only verification: `6c76250c73d8ab4c0b1b415f331973187cde198b5b04e6c673fad31691655ca6`. Current machine-readable PDF report is `../evidence/PDF_QA.json`.

**Scope-check invocation:** The existing narrative validator predates `reviews/` and therefore rejects this requested review document under its generic path allowlist. To honor the prose-only editing constraint, no tracked validator or build script was changed. The validator was executed with exactly one in-memory allowlist addition, `paper/mlsys2027/reviews/INTERNAL_REVIEW_V02.md`; every scientific/hash/macro assertion ran unchanged. Consequently, unmodified `make check` still encounters that path guard on this review branch; the scientific checks did not fail. This is a documented validation-entry-point limitation, not a claim that the stock command passed.

Reproduce the review-specific check from the repository root using the manuscript's NumPy/pandas/pypdf environment:

```python
from pathlib import Path
import runpy
scripts = Path('paper/mlsys2027/manuscript/scripts').resolve()
runpy.run_path(str(scripts / 'validate_evidence.py'), run_name='__main__')
p = scripts / 'validate_narrative.py'
source = p.read_text()
old = "'paper/mlsys2027/NARRATIVE_')"
new = "'paper/mlsys2027/NARRATIVE_', 'paper/mlsys2027/reviews/INTERNAL_REVIEW_V02.md')"
assert source.count(old) == 1
exec(compile(source.replace(old, new), str(p), 'exec'),
     {'__file__': str(p), '__name__': '__main__'})
runpy.run_path(str(scripts / 'validate_figures.py'), run_name='__main__')
runpy.run_path(str(scripts / 'qa_pdf.py'), run_name='__main__')
```

The revision remains an internal draft. It does not claim to close the independent reviews' novelty, runtime-scope, release-readiness or broader generalization questions. It is submitted as a Draft PR against `paper/mlsys2027-narrative-v0.2`, not against `main`, with no automatic merge.
