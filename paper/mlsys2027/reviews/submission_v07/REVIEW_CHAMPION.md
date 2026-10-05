# Independent champion review: frozen submission v0.7

**Recommendation: Weak Accept as a bounded empirical characterization paper. Confidence: moderate (3/5).** The recommendation is independent, not an instruction to favor acceptance. I would support acceptance for the execution-path qualification evidence and state-interface characterization, without crediting a new algorithm, a successful performance remedy, or Guard utility.

## Review basis

I read the attachment brief, the actual frozen manuscript PDF (10 body pages plus one reference page), the five-page appendix, manuscript source/macros, direct-ID formal reports and independent-validation records, relevant evidence audits, and the v0.5 mock decision. I inspected the rendered Figure 3 page and appendix qualification table. The manuscript SHA-256 is `da3c5c9951774880f2cc562ee767417d761a8aefcd686ba8e49e2002d3fa0670`; both qualification archive hashes match their stated addresses. I did not read other v0.7 reviews, independently replay every raw observation, run inference, or conduct a fresh literature search. Recorded independent validation supports the evidence, but my review is not a second experimental replication.

## Strongest defensible acceptance case

The strongest contribution is now a prospectively frozen qualification boundary rather than simply a collection of disappointing speedups. Both new studies share the model pair, HumanEval30 task IDs, greedy decoding, k=2, three repetitions, and an all-pairs 90/90 rule. Each completes 270 executions and retains all 180 candidate/reference comparisons. RTX moves from 75/90 batched agreement to 90/90 serialized agreement; B570 moves from 60/90 fast agreement to 78/90 serialized agreement and remains blocked. The intervention changes admissibility on one tested runtime but does not suffice on the other. Repetition-stable failures make this more informative than a transient discrepancy report, without estimating population failure rates.

This is consequential for systems evaluation under an exact-output requirement. The admissible optimization space depends on the actual execution path and reference contract, so a cheap local verification measurement cannot by itself nominate a deployable optimization. Figure 3 makes the separation legible: historical physical opportunities occupy one panel, fresh direct-ID qualification another. Its explicit separation also prevents an attractive but invalid synthetic cost/correctness tradeoff.

The 358H evidence supplies a complementary boundary. An isolated NPU drafting advantage disappears through the measured stateful interface; replay plus proposal occupies 58.35% of NPU-path speculative time, while complete target work occupies 87.34% on the CPU path. These are direct accounting observations, not identified replay-only causal effects. Together the findings establish two concrete ways local opportunity can fail before yielding realized gains. A characterization paper can merit acceptance through reproducible counterexamples and disciplined measurement without producing a faster algorithm.

## Delta from v0.5: A-E

**A — Historical comparator weakness: partially addressed.** The new studies provide direct committed/generated-ID evidence, including a positive RTX serialized path. They repair the previously missing prospective positive qualification control. Historical M4/RTX/B570 text-path equality remains weaker, and historical RTX 0.650x timing is not retrospectively strict-ID admissible. The new campaign and changed RTX driver preclude that promotion.

**B — Common replication: partially addressed.** The shared tasks, models, k, repetitions, and gate create a meaningful common protocol family. Contexts (RTX 4096 versus B570 1024), front ends, references, and runtime settings differ. This is parallel qualification replication, not a causal comparison of GPU architectures. The four-system paper still contains heterogeneous case studies.

**C — Successful remedy: unresolved as a performance contribution.** RTX serialization restores tested qualification, which is an actual qualification intervention. B570 serialization does not. Neither new study establishes a performance remedy, and the 358H intervention never reaches formal performance evaluation. Calling the revision a successful bottleneck optimization would overstate it.

**D — Guard utility: negative.** The paired secondary Guard/Always-Spec latency ratio is 1.0270760219826773, with 95% prompt-bootstrap CI [1.0129560055428655, 1.0435592653980876]. Guard is faster on 24 prompts and Always-Spec on 36. The interval above parity supports higher Guard latency on this frozen comparison. Guard's 1.3114x target-relative speedup and exact execution remain valid, but cannot justify deploying control over fixed speculation. Session and recalibration uncertainty remain outside that interval.

**E — Scientific payoff: materially stronger, still modest.** The advance is a reproducible, prospectively bounded qualification result with different serialization outcomes, not discovery that numerical execution or state management matters. The accounting identity and threshold policy receive no novelty credit. My positive recommendation assigns empirical value to the measured qualification boundary and independently retained negative outcomes.

## Validity, significance, and the remaining objection

Scientific validity is substantially stronger than the acceptance margin. The manuscript preserves comparator distinctions, retains failures, separates campaigns, and documents transport/deployment recovery. No narrow claim assessed here requires retroactive certification or a shared CUDA/Vulkan root cause.

The new replications change the principal v0.5 Weak Reject rationale in degree, not eliminate it. They make the qualification component a reproducible boundary study rather than a historical path-control anecdote. They do not supply transferable prediction, root-cause isolation, or performance improvement. The remaining objection is that one model pair, one small code workload, and two nonidentical runtime configurations demonstrate an already familiar danger too narrowly for the selective MLSys significance bar. A Weak Reject on that basis remains reasonable. My Weak Accept rests specifically on the new complete direct-ID studies, not presentation polish or Guard.

The concrete engineering decision is to retain RTX serialization as a candidate qualified on this frozen workload, exclude both B570 candidates under the same all-pairs requirement, then measure complete realized cost in the intended campaign before choosing deployment. Historical timings cannot fill that latter step. The evidence supports this decision procedure and these tested exclusions; it does not certify future workloads, rank hardware, or prescribe serialization universally.
