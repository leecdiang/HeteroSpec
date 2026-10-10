# M4 Guard / Always-Spec paired secondary report

Reviewer-requested **post-study paired secondary analysis**, not the registered
primary endpoint or a preregistration. Aggregate results were already known.
The committed plan fixes all choices; none changed after seeing this result.

Guard / Always-Spec geometric-mean latency ratio: **1.0270760219826773**.
95% paired prompt-bootstrap interval: **[1.0129560055428655, 1.0435592653980876]**.
Values above one mean Guard is slower. The interval lies entirely above parity: Guard had higher latency than Always-Spec on this frozen comparison.

Prompt medians: Guard faster **24**, Always-Spec faster
**36**, exact ties **0** (60 total).
These counts are descriptive; no subgroup or additional tests were performed.

The verified archive SHA-256 is
`af73b8f0edeae5027357338a627d899b08db425884a1373162932a72f4f119ab`; formal attempt
`unattended-20260924t125921z-formal`. All 540 records reconstruct the same 60 prompt
medians as the immutable primary analysis. Each condition has three formal
repetitions. Both speculative conditions remain 180/180 direct generated-ID
exact against their matched target-only references.

For each prompt, divide its Guard median by its Always-Spec median, then take
`exp(mean(log(r_i)))`. Bootstrap the paired prompts 10,000 times with a fresh
standalone Python `random.Random(20260924)` stream in frozen held-out order;
each draw uses `randrange(60)`. Linearly interpolate sorted estimates at
`(10000-1)*0.025` and `(10000-1)*0.975`. Repetitions are not bootstrap units.
Full prompt medians, ratios, and source hashes are in the adjacent JSON.

No new measurements, model execution, timing, tuning, policy search, or changes
to primary results occurred. Energy remains NOT_CLAIMED. The original
freeze-hash metadata defect and stopped pipeline markers remain intact.
This comparison covers one M4 model/runtime pair, fixed k=2, one held-out set,
and one post-prefill boundary. Its interval excludes session and recalibration
variation. It supplies no robustness, risk-reduction, near-optimality, or
general controller-superiority claim.
