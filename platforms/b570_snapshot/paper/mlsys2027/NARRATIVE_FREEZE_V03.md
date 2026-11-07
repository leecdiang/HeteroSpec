HeteroSpec — Narrative Freeze v0.3
Target: MLSys 2027 Research Track
Status: initial-manuscript narrative anchor
Hardware evidence: CLOSED
Runtime/software intervention: PLANNED / NOT YET MEASURED

============================================================
1. PRIMARY QUESTION
============================================================

What prevents favorable local indicators from translating into gains
in integrated post-prefill speculative decode on the tested consumer
configurations?

The paper is a retrospective synthesis of independently frozen campaigns.
It is not a jointly preregistered four-platform portability benchmark.

============================================================
2. TOP-LEVEL OBSERVATION
============================================================

Favorable local indicators do not by themselves establish useful
integrated post-prefill decode performance.

The tested cases expose different realized outcomes:

- exact and profitable;
- exact but unprofitable;
- physically favorable but correctness-blocked;
- exact but limited by realized stateful integration.

These are observed regimes, not a hardware ranking or population-wide
failure-rate estimate.

============================================================
3. TWO MEASURED SYSTEM BOUNDARIES
============================================================

Boundary A — Execution-path qualification

A physically cheap target-verification path may not be usable under the
chosen strict token-equivalence contract.

Evidence:
- RTX batched CUDA path has favorable V2_micro but fails the frozen
  correctness gate.
- RTX serialized exact controls cost substantially more.
- B570 serialization improves agreement but remains globally
  inadmissible.

Supported lesson:
qualify the actual execution path before treating its physical cost as
an optimization opportunity.

Not claimed:
- CUDA is broken;
- Vulkan is broken;
- serialization guarantees exactness;
- numerical batch-shape divergence is newly discovered.

Boundary B — Stateful realization

Favorable isolated component performance may not survive the actual
state interface paid by the speculative loop.

Evidence:
- 358H NPU isolated drafting exceeds CPU at long context;
- both formal CPU and NPU paths are token-exact;
- NPU realized speculative execution is dominated by the combined
  replay+proposal region;
- CPU is instead dominated by complete target-side work.

Supported lesson:
measure realized stateful subsystem cost rather than substituting
isolated throughput.

Not claimed:
- intrinsic NPU compute weakness;
- replay-only timing;
- persistent state is already proven to solve the problem.

============================================================
4. M4 ROLE
============================================================

M4 is not evidence for either diagnosed mechanism.

It establishes the empirical outcome contrast:

- representative frozen 24Q study:
  exact, ~0.842x;

- separately preregistered HumanEval fixed-k2 study:
  exact, ~1.387x.

The studies were run in separate sessions and are not a controlled
between-workload causal experiment.

Safe interpretation:

the same tested Metal stack exhibits both profitable and unprofitable
observed regimes.

Do not claim:
- workload alone caused the difference;
- M4 is generally profitable;
- unified memory explains the positive result.

============================================================
5. ACCOUNTING ROLE
============================================================

S = C / (D_real + R_target + X)

is a measurement/accounting lens, not a novel theory.

Definitions must remain strict:

C:
all committed output tokens, including correction/bonus output;

D_real:
realized draft-subsystem cost, including state work actually charged to
that interface;

R_target:
complete realized target-side round cost;

X:
residual orchestration/synchronization/bookkeeping cost.

V_k_micro is a target-forward diagnostic proxy and is NOT automatically
R_target.

Isolated draft throughput is NOT D_real.

Accepted draft tokens per round are NOT automatically C.

============================================================
6. EMPIRICAL CONTRIBUTIONS
============================================================

Contribution 1:
A bounded retrospective characterization that retains positive,
negative, and correctness-blocked outcomes from independently frozen
consumer-system campaigns.

Contribution 2:
Measured execution-path evidence showing that correctness qualification
can change which physically favorable verification path is actually
usable.

Contribution 3:
Direct 358H evidence showing that isolated draft-device advantage can
fail to survive the measured stateful integration boundary.

Accounting, heterogeneous SD, state reuse, numerical nondeterminism, and
generic verification bottlenecks are not claimed as new ideas.

============================================================
7. SOFTWARE / RUNTIME ROLE
============================================================

The runtime work is a planned prospective contribution, not a current
measured result.

Current hardware evidence motivates at least:

- persistent or lower-cost draft-state handling;
- correctness-qualified path selection;
- realized-cost-aware profitability control.

Software evaluation must be a new frozen study.

It must not reinterpret or rescue closed hardware campaigns after the
fact.

If successful, the final paper may become:

Observation
    ->
Diagnosis
    ->
Runtime design
    ->
Measured intervention

If unsuccessful, the hardware characterization remains independently
valid.

============================================================
8. FINAL MAIN-FIGURE STORY
============================================================

Headline outcome table:
complete result inventory.

Figure 1:
M4 workload-study forest plot.
Question answered:
Can the same tested stack expose opposite realized profitability regimes?

Figure 2:
translation / mechanism schematic.
Question answered:
Where can local opportunity be lost between component measurements and
qualified realized execution?

Figure 3:
verification-path figure.
Question answered:
Can the physically cheapest verification path remain usable after
correctness qualification?

Figure 4:
358H isolated-vs-realized figure.
Question answered:
Can isolated draft-device advantage survive the measured stateful
integration?

Old graphical overview:
remove from main paper.

Verification mechanism table:
candidate for appendix after exact lookup information is preserved.

Regime inventory:
appendix table, not main infographic.

============================================================
9. NON-NEGOTIABLE SCIENTIFIC BOUNDARIES
============================================================

- Exact means generated token-ID equality under the frozen reference.
- HumanEval token equality is not pass@k.
- No absolute cross-platform energy ranking.
- No Phase-3 358H energy claim.
- B570 serialized remains globally inadmissible.
- RTX batched timing remains diagnostic when correctness-blocked.
- Replay and proposal are inseparable on 358H.
- M4 studies are separate sessions.
- Cross-platform synthesis is retrospective.
- Hardware/runtime/software variables co-vary across systems.
- Diagnosed mechanisms are configuration-scoped and non-exhaustive.