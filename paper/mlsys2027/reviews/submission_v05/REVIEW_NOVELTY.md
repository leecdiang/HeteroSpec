# Independent Reviewer D — Novelty and Related Work

Review basis: source manuscript supplied at `b326ff7f20d9bac5afff6f53a6e9d9d8a7aaa7ae`; complete main TeX, sections, appendix and bibliography read. Review conducted independently on 2026-09-25 UTC / 2026-09-26 Asia/Shanghai. No other reviewer report was read. No manuscript or experiment file was edited. Targeted primary-source literature search is recorded in `LITERATURE_SEARCH.md`.

## Assessment

The defensible contribution is an empirical systems account of **how an exact-output contract and the realized state interface change which speculative execution opportunities survive**, followed by a prospective, deliberately simple control test on one surviving path. It is not a new controller family, profitability identity, determinism technique, or heterogeneous placement method. The current manuscript recognizes these boundaries unusually explicitly. Its principal novelty risk is therefore insufficient significance of the bounded empirical contribution, rather than an obvious false priority claim.

The current final introduction paragraph says the contribution is a “bounded empirical connection.” That is accurate but too abstract: it makes the reader reconstruct which measured consequence is new. State the connection concretely: cheap target batching can be excluded by the exact-output contract; isolated draft throughput can be erased at a stateful interface; a surviving qualified path can then support a frozen prospective cost-based fallback test. This is a measured sequence of constraints, not a universal execution framework.

## What is established rather than novel

| Candidate claim | Prior-art status | Appropriate claim here |
|---|---|---|
| Speculative decoding preserves target behavior under algorithmic assumptions | Established; Leviathan et al. and other foundational work | The implementation's direct token-ID qualification under the specified greedy reference |
| Draft/target heterogeneous placement | Established; Dovetail, DuoDecoding, Mirror-SD | Measured consequences of these particular CPU/GPU/NPU interfaces |
| Acceptance is insufficient to predict speedup | Established; Illusion, SpecLLM, TurboSpec | Concrete separation of target-forward proxy, complete round work, and qualified integrated decode in these cases |
| Cost per committed token / break-even identities | Established; SpecLLM and goodput-based control | Consistent measured accounting, without replacing campaign-specific estimators |
| Online speculation selection or disabling | Established; TurboSpec; adaptive per-round selection also in BanditSpec | One-way realized-cost fallback with frozen calibration and prospectively untouched prompt IDs on M4 |
| Numerical variation with batch shape | Established; numerical nondeterminism and LLM-42 literature | Stack-scoped loss of a cheap admissible path, including controls and retained failures |
| Correctness checking and qualification | Normal systems practice; verified deterministic inference has stronger prior techniques | Measured performance consequences of qualification, rather than invention of the obligation to check correctness |
| Persistent KV/state reuse | Established | Measured replay-plus-proposal cost; no claimed persistence speed benefit |
| Oracle comparison | Established and widespread; BanditSpec is a close language precedent | Descriptive hindsight latency ratio, without regret theorem or deployable-oracle interpretation |
| A threshold guard | Not an algorithmic novelty contribution by itself | A minimal instrument testing whether the selected runtime decision is executable, exact and profitable against target-only |

## Major novelty risks

1. **TurboSpec is more overlapping than the current one-sentence description makes visible.** It is already cited, but it explicitly supports disabling speculation when unhelpful. Describing it only as adjusting speculation risks an unnecessary objection that HeteroSpec hides prior admission control. Add “including disabling speculation” to the description, then state the narrow difference: this experiment evaluates a frozen one-way policy using cumulative already-realized charged cost on an empirically qualified single-request consumer path. This does not show that the different policy is better.
2. **A controller paper interpretation would be weak.** The larger Always-Spec aggregate point estimate matters. The M4 experiment establishes a qualified implementation and bounded profitable operation, but does not validate the decision rule as an improvement over simply leaving speculation on. Do not call it an effective safeguard, robustness improvement, or risk reduction without measured support. A fallback fraction proves activity, not value. The current main text mostly observes this boundary; “bounded profitable control” in the abstract still risks sounding like control supplied the profit.
3. **The measurement gap itself is already well known.** Illusion and SpecLLM are directly relevant and correctly acknowledged. “Local promise does not imply realized gain” is the organizing question, not a sufficient novelty claim. The novelty must live in the auditable consequences of qualification and the measured state interface across the retained cases.
4. **A prospective split does not transform a simple known policy into an algorithmic contribution.** It strengthens credibility of this evaluation. Nor does it mean the M4 platform outcome was previously unknown: distinguish untouched prompt outcomes from earlier knowledge that M4 supports profitable speculation.
5. **Correctness as a hard path constraint is meaningful but narrow.** A reviewer may prefer a weaker quality contract or a deterministic-inference repair. The response is to state what this contract excludes and why timings on excluded paths cannot answer this study's question. It is not to imply that other papers' correctness assumptions or quality contracts are illegitimate.

## Missing or weak related work

### Required targeted addition: BanditSpec

BanditSpec is a direct precedent for training-free online per-round speculative configuration selection and oracle/regret framing. A one-sentence addition is enough; it need not become a baseline because this manuscript makes no claim to beat adaptive controllers. Prefer the ICML 2025 proceedings citation, verified at https://proceedings.mlr.press/v267/hou25h.html. The updated arXiv v2 is dated 2025-11-20.

Suggested sentence, as a proposal: “BanditSpec selects speculative configurations online with bandit algorithms and analyzes stopping-time regret; our oracle ratio is a descriptive held-out latency comparison, not such a guarantee.” This avoids conflating two different meanings of regret. If space is tight, simply cite BanditSpec alongside TurboSpec and state that adaptive policy selection is established.

### Useful but conditional addition: MemSpec

A fresh primary arXiv abstract (2026-08-11) describes an edge-device runtime addressing draft-switching and residency overhead. It materially reinforces the boundary that actual state and memory availability already motivate adaptive speculative runtimes. Its full text could not be fetched in this review. Add only a narrow abstract-supported sentence if the coordinator retrieves enough source to judge it; otherwise retain it as a documented freshness lead, not a strong differentiating claim. No claim that HeteroSpec outperforms, fixes, or is more rigorous than MemSpec is supported.

### Existing citations worth retaining

Keep Illusion, SpecLLM, TurboSpec and LLM-42 prominent: they are stronger novelty checks than a long survey of draft-model methods. Existing Dovetail/DuoDecoding/Mirror-SD and state-reuse citations adequately prevent broad placement/persistence claims. LLM-42 v2 bibliographic authors in the repository match the current source; an older search snippet includes a different author list, so do not “correct” the pinned v2 using that snippet.

### Do not add indiscriminately

SPECTRA (2026-09-21, accepted ICCAD 2026) is fresh hardware-aware SD but describes a reconfigurable architecture, not this admission policy or exactness-boundary study. AdaptiveSD, ModeSwitch-LLM, and SparseSpec-L are search leads with broader/different objectives. Adding them would broaden the related-work survey without changing the narrow contribution. No new implementation or experiment against any of these is justified by this review.

## Best defensible positioning

Recommended single-contribution answer:

> We provide an auditable empirical account of which speculative-decoding opportunities survive an exact-output contract and the actual stateful execution interface, and test realized-cost fallback prospectively on one qualified path.

This is stronger than “we study consumer systems” because it identifies a decision-relevant distinction and measured consequences. It is weaker than a new general methodology or admission framework, appropriately: correctness gates and cost measurement are established, and the four campaigns are not a controlled cross-platform experiment.

Use “qualification before control” as the paper's organizing sequence, not a priority claim and not a claim of online certification. The 358H intervention and M4 policy are complementary tests of different decisions. Neither experimentally causes the other.

## Concrete revision priorities

1. P1: Replace the final introduction's abstract “connection” with the measured contribution in one explicit sentence. Keep the prior-art admission.
2. P1: Make the runtime section's role a prospective test of a qualified path and a simple decision process; explicitly avoid implying that fallback caused the aggregate benefit.
3. P1: Expand TurboSpec's description to acknowledge disabling speculation and add BanditSpec's directly relevant precedent.
4. P2: Keep oracle regret secondary to Target/Guard and Target/Always-Spec; call it a hindsight latency ratio in explanatory prose. Do not add “near oracle.”
5. P2: Reduce platform metric dumping in the abstract so the contribution and its boundary become legible on first reading. Retain the awkward fixed-speculation comparison.

No P0 factual novelty misrepresentation was identified in the reviewed source. The paper already rejects claims of new heterogeneous placement, numerical phenomena, cost theory, persistence benefit, and adaptive speculation.

## Independent abstract proposal (not an edit)

Favorable acceptance and component timings do not establish that a speculative decoding path is both exact and profitable. We examine this gap in four retrospective consumer-system studies, separating execution-path qualification from complete post-prefill cost. On the tested RTX and B570 stacks, cheap verification paths fail the greedy token-equivalence contract; serialization restores exactness only for the tested RTX control. On 358H, a faster isolated NPU draft does not retain its advantage through the measured stateful interface. Separate M4 studies retain both exact profitable and unprofitable outcomes without attributing their contrast to workload alone. We then test qualification and cost control in separately frozen runtime studies. A 358H intervention stops at correctness qualification, while an M4 one-way guard using already-realized cost achieves 1.3114× held-out speedup over target-only (95% CI [1.2487, 1.3787]) with 180/180 direct-token-exact comparisons. Fixed speculation has the higher aggregate point estimate. Together, these studies show how qualification and realized interface cost constrain usable speculation in the tested stacks; the guard tests this bounded decision process rather than a new speculative algorithm.

## Residual acceptance risk

Even after these edits, a fair reviewer may judge the manuscript a careful collection of implementation-specific results plus an uncompetitive simple controller. This cannot be eliminated editorially. The best defense is the precision and utility of the measured exclusions and accounting boundaries, plus reproducible prospective execution. Do not manufacture generality or convert the controller into the paper's claimed algorithmic novelty to escape this objection.
