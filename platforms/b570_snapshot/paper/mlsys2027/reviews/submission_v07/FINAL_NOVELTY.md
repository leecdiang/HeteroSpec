# Independent novelty review — frozen submission v0.7

**Recommendation: Weak Reject. Confidence: moderate-high (4/5) on the bounded assessment; moderate on the conference outcome.** Scientific validity is substantially stronger than in v0.5. Contribution significance remains the acceptance blocker.

## Review basis

I read the actual delivered `manuscript/output/manuscript-v0.7.pdf`: SHA-256 `da3c5c9951774880f2cc562ee767417d761a8aefcd686ba8e49e2002d3fa0670`, independently recomputed. It contains 11 pages: body pages 1–10 and references page 11. I also read the five-page `appendix-v0.7.pdf`, SHA-256 `afa4ab81d346c5764be43a24e7a58b43c117e2cbc65c872cf79d1421e3b7b15f`, and visually inspected the delivered Figure 3 page and appendix direct-ID table/protocol page. Relevant sources were the attachment brief, both formal direct-ID reports and analysis JSONs, recorded independent validation outputs, qualification-scope and claim-audit records, M4 paired secondary QA, and v0.5 novelty review/mock decision. I read no other v0.7 reviewer report. This is a fresh scientific assessment, not an independent raw-archive replay or literature search. No experiment, manuscript edit, or evidence mutation was performed.

## Contribution and significance

The strongest new contribution is a prospectively specified, directly observable qualification boundary. With a common HumanEval30/model/k/repetition/gate family, serialization takes the tested RTX path from 75/90 to 90/90 direct-ID matches, while the tested B570 path improves from 60/90 to 78/90 and remains blocked. Every condition is repetition-stable. Thus reproducible output is distinct from agreement with the designated reference, and serialization is insufficient as a portable certificate. The retained failures and strict all-pairs gate make this appreciably more convincing than an anecdotal successful control.

This result has a concrete operational consequence: accepting a serialized execution setting on one runtime does not license accepting that setting on another. The paper now provides a reproducible qualification-boundary core, supported by parallel studies, within its broader heterogeneous characterization. That is a better characterization than describing the whole work solely as four unrelated cases.

However, the measured boundary does not yet explain or predict which additional configurations will qualify. The historical CUDA argmax capture establishes a concrete divergence in its own configuration; it does not identify the new B570 mechanism. Different reference, context, and front-end settings are especially consequential for an endpoint defined by reference equality. The RTX/B570 difference cannot isolate an architectural cause. The paper appropriately acknowledges this, but acknowledging the limit does not supply the missing transferable result.

Related Work now explicitly recognizes established heterogeneous placement, numerical variation, deterministic inference, complete-cost accounting, adaptive disabling, and BanditSpec's online selection. Neither the identity nor Guard constitutes a new algorithmic contribution. I find no obvious novelty misrepresentation in the supplied material; I did not independently refresh the literature. The acceptance case must rest on the importance of these measured consumer-runtime boundaries.

## Required v0.5-to-v0.7 deltas

**A — Historical comparator weakness: partially addressed.** Direct generated-ID observations now establish RTX serialized qualification and B570's failures without text reconstruction. They strengthen the central strict-contract claim prospectively. They do not certify historical M4 results or historical RTX 0.404×/0.650× timing. Fresh RTX uses driver 616.92 rather than historical 616.56. Historical B570 45/90 and 60/90 remain their original text-path comparisons, distinct from new 60/90 and 78/90. Figure 3's separate panels preserve this distinction; it is not a same-run cost/correctness experiment.

**B — Common replication: partially addressed.** Two independently frozen studies now share 30 task IDs, Qwen3-8B/0.6B Q8_0, greedy k=2, three repetitions, and the 90/90 gate. This improves coherence and reproducibility. RTX context 4096 and reference micro-batch one differ from B570 context 1024 and its completion reference; front ends and capture methods also differ. These are parallel qualification replications, not fully controlled hardware replications. The broader four-stack synthesis remains heterogeneous.

**C — Successful remedy: locally improved, generally unresolved.** RTX serialization successfully restores tested qualification. That is a meaningful qualification intervention. It is neither a demonstrated profitable repair nor a general correctness remedy: B570 stays blocked and no fresh formal performance endpoint accompanies these studies. The 358H intervention still supplies no R2 performance result. Its replay-plus-proposal timing remains inseparable and establishes no persistence benefit.

**D — Guard utility: now explicitly negative on the frozen paired comparison.** Guard/Always-Spec latency is exactly **1.0270760219826773**, with CI **[1.0129560055428655, 1.0435592653980876]**; Guard is faster on **24** prompts and Always-Spec on **36**, with zero ties. This is post-study paired secondary analysis, not a preregistered primary result, and excludes session/recalibration uncertainty. It supports higher Guard latency in this comparison. Guard's approximately 1.3114× versus target-only cannot establish incremental utility over approximately 1.3469× Always-Spec.

**E — Scientific payoff: materially stronger but still below my acceptance threshold.** New direct-ID evidence changes the evidentiary strength of the qualification finding. It does not turn an established requirement to validate runtime outputs and complete cost into a validated predictive principle or effective optimization.

## Principal remaining objection and minimum missing contribution

The v0.5 principal Weak Reject reason was modest scientific payoff, rather than invalidity. That reason remains, although its comparator-related support is weakened by genuine new evidence. An anecdotal historical observation has become a consequential bounded replicated finding; I do not yet judge its reach sufficient for selective MLSys acceptance.

The minimum missing contribution is one validated transferable consequence: for example, a mechanism-derived rule predicting admission failures on an untouched configuration, or a qualification-preserving bottleneck remedy demonstrating useful performance at the same measured endpoint. A new controller or universal hardware theory is unnecessary. More repetition of the same finite gate or editorial repositioning alone would not close this gap. These are future scientific recommendations only; this frozen integration should remain unchanged and launch no experiment.
