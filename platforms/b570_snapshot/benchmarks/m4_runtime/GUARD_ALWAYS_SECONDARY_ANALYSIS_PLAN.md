# M4 Guard versus Always-Spec: secondary analysis plan

Status: reviewer-requested **post-study paired secondary analysis**. The
observations were prospectively collected and frozen; this contrast was not the
registered primary endpoint. Aggregate results are already known. This plan's
commit is a procedural timestamp, not preregistration, and implies no blinding.

## Source and reconstruction

Use the complete frozen M4 evidence archive with SHA-256
`af73b8f0edeae5027357338a627d899b08db425884a1373162932a72f4f119ab`.
Verify archive bytes and all payload hashes, require exactly one eligible formal
dataset, and reconstruct all 540 formal observations (60 held-out prompts,
three repetitions, three conditions). Pair prompts in the archived
`HELDOUT_SPLIT.json` order. Check uniqueness and completeness of prompt,
repetition, and condition keys, and direct generated-ID equality to target-only.
Reconstruct the three condition medians for every prompt and require exact
numerical agreement with archived and repository `FORMAL_ANALYSIS.json`.
Do not change or repair any primary evidence or the historical freeze-hash defect.

## Fixed quantity and uncertainty

For each prompt i,

    r_i = median(Guard latency over its three formal repetitions)
          / median(Always-Spec latency over its three formal repetitions).

The headline estimator is the geometric mean of these 60 positive ratios:
`exp(mean(log(r_i)))`. Values below one mean Guard has lower latency; one is
parity; values above one mean Guard has higher latency (Always-Spec lower).
This is a latency ratio, not a speedup.

Resample the 60 paired prompts with replacement 10,000 times. Each replicate
has 60 draws; repetitions are not bootstrap units. Use seed **20260924**, with
one fresh standalone Python standard-library `random.Random(20260924)` stream
initialized immediately before this contrast. Do not continue the primary
analyzer's stream after its three intervals. For each draw use `randrange(60)`
in archived held-out order and compute the same geometric mean.

Use the frozen formal analyzer's percentile convention, confirmed by source
inspection: sort the bootstrap estimates; for q=0.025 and q=0.975 set
`index = (10000 - 1) * q`, then linearly interpolate between floor(index) and
ceil(index). Report both exact finite-bootstrap endpoints and full-precision
headline values in JSON; four decimal places may be used in the paper.

## Allowed outputs and interpretation

In addition to the headline ratio and its 95% prompt-bootstrap interval, report
only counts of prompts where the Guard median is lower, where the Always-Spec
median is lower, and exact median ties. Include all 60 prompt medians and paired
ratios for reproducibility. An independent implementation must reconstruct
these medians, headline estimate, finite-bootstrap endpoints, and counts from
the archive without importing the new analyzer's calculation.

An interval wholly above one means Guard had higher latency on this frozen
comparison; wholly below one means Guard had lower latency; an interval
including one does not establish a latency difference under this interval.
State the finding literally. Limit it to this M4 model/runtime pair, fixed k=2,
held-out prompt set, and post-prefill timing boundary. The uncertainty does not
cover session or recalibration variation.

No new measurements, inference, timing, policy search, tuning, subgroup tests,
family-specific claims, alternative seeds or estimators, threshold sweeps,
selected tail metrics, or sensitivity search are authorized. Preserve primary
speedups, oracle result, fallback fraction, direct-ID correctness, energy
NOT_CLAIMED, policy, splits, source, archive bytes, and stop markers. Do not
claim robustness, risk reduction, near-optimality, controller superiority, or
universal dominance. No analysis choice will change after seeing the result.
