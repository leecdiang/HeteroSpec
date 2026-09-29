# Scientific claim audit v0.7

This audit applies to the integrated abstract, Introduction, outcomes,
diagnosis, synthesis, Related Work, limitations, conclusion, Figure 3 and
separate appendix. Canonical data remain the two formal analysis JSONs.

| Major sentence / claim | Classification | Evidence and limit |
|---|---|---|
| Serialization restored direct-ID qualification on the tested RTX path. | DIRECTLY MEASURED | 75/90 to 90/90; 25/30 to 30/30 wholly exact prompts; tested frozen CUDA path only |
| Serialization improved agreement but remained blocked on B570. | DIRECTLY MEASURED | 60/90 to 78/90; 20/30 to 26/30 prompts; 90/90 gate unchanged |
| Each study completed 270 executions and 180 comparisons. | DIRECTLY MEASURED | Formal coverage independently replayed offline |
| All conditions are repeat-stable on all 30 prompts. | DIRECTLY MEASURED | Within-condition stability; does not imply equality to reference |
| Five RTX mismatch prompts repeat at the same first divergence. | DIRECTLY MEASURED | HumanEval/64:114, /106:65, /119:17, /128:41, /129:21, each 3/3 |
| Serialization is not itself a correctness certificate. | CROSS-STUDY SYNTHESIS | Restores qualification on one tested runtime, insufficient on another; not a universal backend theory |
| Cheap verification does not guarantee an admissible path. | CROSS-STUDY SYNTHESIS | Historical physical opportunity plus separately frozen qualification; no same-run joint cost/correctness claim |
| Validate the actual execution path before exploiting its cost. | CROSS-STUDY SYNTHESIS | Operational consequence of the two different responses to serialization |
| Qualification and complete realized cost answer separate decisions. | CROSS-STUDY SYNTHESIS | New qualification plus retained 358H decomposition and prospective M4 negative Guard comparison |
| Historical RTX margin changes from +0.080948 to -0.126457. | MECHANISM-SUPPORTED | Separate same-commit instrumented historical capture; no specific kernel identification |
| Runtime/front-end, reference and context differences prevent a causal hardware comparison. | LIMITATION | RTX context 4096 vs B570 1024; distinct reference settings and capture/front-ends |
| Historical timing remains comparator-scoped. | LIMITATION | New studies measure qualification, not formal performance; driver/campaign mismatch |
| Only one model pair, HumanEval30, k=2, three repetitions are covered. | LIMITATION | No population/backend-wide estimate or functional correctness endpoint |
| Fresh RTX driver differs from historical; B570 launcher recovery preserves semantics. | LIMITATION | 616.92 vs 616.56; zero-run failed launch precedes unchanged direct execution |
| CUDA and Vulkan share the same numerical root cause. | INFERENCE NOT CLAIMED | No common numerical diagnostic isolates this |
| Historical RTX 0.650x is now strict-ID qualified. | INFERENCE NOT CLAIMED | Separate campaign and environment; forbidden retroactive certification |
| Serialization guarantees correctness or supplies a performance remedy. | INFERENCE NOT CLAIMED | B570 counterexample under its frozen contract; no new formal timing |
| GPU architectures were causally compared or rates generalize to a population. | INFERENCE NOT CLAIMED | Protocol-family commonality does not equal controlled hardware comparison |
| Guard adds incremental value. | INFERENCE NOT CLAIMED | Guard/Always latency 1.0270760219826773, CI [1.0129560055428655, 1.0435592653980876]; Guard slower |

The title is retained. The accounting identity, batch-shape divergence,
heterogeneous placement and adaptive control are not promoted as novel.
Historical comparator tables, original approved figures, archives,
bibliography and official style are preserved byte-for-byte at the base.
New counts are generated macros and a separate appendix table, never spliced
into historical timing rows. See the scope record for archive hashes and
observational transport/deployment history. No new experiment was executed.
