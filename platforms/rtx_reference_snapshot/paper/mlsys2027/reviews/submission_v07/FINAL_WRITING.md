# Independent final writing review — v0.7

## Basis and recommendation

I read the complete integration brief, the delivered `manuscript/output/manuscript-v0.7.pdf` (10 body pages plus one reference page), and the separate five-page `appendix-v0.7.pdf`. The main PDF SHA-256 is `da3c5c9951774880f2cc562ee767417d761a8aefcd686ba8e49e2002d3fa0670`; the appendix is `afa4ab81d346c5764be43a24e7a58b43c117e2cbc65c872cf79d1421e3b7b15f`. I checked extracted PDF text, rendered page flow, Figure 3 at page scale, relevant TeX, generated direct-ID macros, the formal RTX/B570 analyses, scope/claim records, and the Guard/Always secondary result. I read the v0.5 mock decision only after establishing the new manuscript's argument. I read no other v0.7 reviews. This is an independent writing and claim-coherence assessment, not a fresh literature search, archive replay, or inference experiment.

**Recommendation: Weak Reject on overall contribution significance; no blocking writing defect. Confidence: high on narrative scope and consistency, moderate on the selective MLSys significance judgment.** The paper is scientifically coherent and ready for author review. Clear writing and defensible evidence do not themselves settle whether the contribution clears the conference bar.

## What the delivered paper communicates well

The abstract gives the new result early and economically: RTX 75/90 to 90/90, B570 60/90 to 78/90 against a 90/90 gate. It immediately limits the implication of serialization. It also retains the 358H stateful-interface result and closes with the negative incremental Guard result. This is a useful hierarchy: path qualification first, realized cost second, continuation control last. The contribution paragraph expressly describes empirical scope rather than presenting the accounting identity or threshold policy as an algorithmic advance.

Section 5.1 successfully distinguishes three evidence layers. Historical target-forward measurements establish physical opportunity; separately frozen direct-ID studies establish current qualification; the historical HumanEval/106 score-margin sign change supplies bounded mechanism support. The latter is not used to explain B570 or identify a universal kernel defect. This separation is substantive, not merely a caveat in the limitations.

Figure 3 supports that argument. Panel A uses path shapes without qualification encoding. Panel B spells out all four counts and statuses and shows the 90/90 boundary. Its caption explicitly denies a same-run cost-versus-correctness experiment and distinguishes the forward proxy from complete target work and end-to-end speedup. The appendix preserves the historical lookup and adds a separate direct-ID table. No fresh counts have been inserted into historical timing rows.

Historical RTX 0.404×/0.650× controls remain text-path evidence. Section 4, Section 5, limitations, appendix, and conclusion prevent retroactive strict-ID certification. Historical B570 45/90 and 60/90 likewise remain distinct from the fresh 60/90 and 78/90. RTX driver 616.92 versus historical 616.56 is explicit. The text names runtime/front-end, context, and reference differences; the appendix gives context 4096 versus 1024 and distinct capture/reference arrangements. These are parallel studies with common protocol elements, not causal GPU comparisons. The B570 zero-execution launcher failure is confined appropriately to provenance detail.

Guard is not promoted. The PDF's rounded Guard/Always latency 1.0271 [1.0130, 1.0436] agrees with the evidence's exact 1.0270760219826773 [1.0129560055428655, 1.0435592653980876]. The interval is above parity; 24 prompts favor Guard and 36 favor Always. Its secondary, post-study status is clear. Neither control activity nor hindsight-oracle distance is offered as evidence of utility.

## Remaining writing improvements

The chief editorial cost is repeated defensive scope language. Comparator distinctions, separate sessions, absent persistence benefit, and lack of controller novelty recur across captions, synthesis, runtime introduction, related work, and limitations. This protects validity but makes the scientific progression slower than necessary. Consolidating repeated caveats while preserving one prominent statement per claim would sharpen the acceptance case.

The main text could state the concrete reference-setting difference once rather than only naming the category of confound. RTX reference micro-batch one versus B570 reference micro-batch 128 is more informative than “reference settings differ.” It would make the reason for avoiding hardware interpretation immediately assessable. This is a clarity recommendation, not evidence that the present conclusions are invalid.

The title remains defensible and should remain unchanged in this integration. Its breadth means the introduction must continue to prioritize qualification boundaries rather than suggesting a uniform four-platform benchmark. No title change is required.

## A–E delta and significance

**A, historical comparator weakness: partially addressed.** New prospective direct-ID positive and negative controls materially strengthen qualification, while historical M4 and historical performance retain their original limitations.

**B, common replication: partially addressed.** Shared workload, models, k, repetitions, and gate give the two GPU studies a coherent common question. Distinct reference, context, and runtime arrangements still prevent a controlled hardware contrast.

**C, remedy: improved qualification evidence, unresolved performance remedy.** RTX serialization crosses the gate; B570 serialization does not. No fresh admissible timing demonstrates that this intervention produces a usable gain.

**D, Guard utility: now explicitly negative on the frozen paired comparison.** The missing paired inference from v0.5 is supplied, but it strengthens the limitation rather than the controller contribution.

**E, payoff: materially stronger, still borderline in significance.** The qualification result is now reproducible prospective systems evidence rather than only a historical path-control anecdote. It changes the evidentiary strength of the paper, but the strongest remaining objection is that “validate this execution path, then measure complete cost” remains a familiar operational rule supported by one model pair and a small workload. The minimum missing scientific increment is a demonstrated transferable qualification boundary or an admissible, consequential performance remedy. Better wording alone cannot supply it. Acceptance as careful characterization remains defensible; my weak rejection is about that unresolved increment, not an integrity or writing blocker.
