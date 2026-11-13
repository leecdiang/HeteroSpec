# Causal control over qualified verification frontiers

## Research question and current answer

Can a controller exploit a **measured difference between numerically legal execution frontiers**, after charging additional weight passes, synchronization, draft reconciliation, terminal materialization and the controller itself? This is a falsifiable systems question. A generic acceptance predictor plus a latency table is already covered by adaptive speculative decoding; it is not the contribution claimed here.

The present data cannot answer the performance question positively. PR221's first nontrivial CPU width comparison failed complete-vector/state qualification. Its separate q1 smoke supplies no width comparison. Even a future successful CUDA run of that probe would measure a capture-conditioned target operation, not an online resident stage. Therefore the real stage-cost catalog in this release is empty, and the production-facing decision path abstains.

The new work has two concrete purposes: close demonstrated cost-admission gaps, and provide an executable causal decision model with explicit places where the missing numerical and cost evidence must enter. Synthetic tests establish properties of that model only.

## Three distinct objects

1. **A macro operation.** At one frozen history, compare schedules `[8]`, `[4,4]`, and eight `[1]` calls with the same eight input rows and all requested vectors. All rows execute regardless of acceptance. This is PR221's scope.
2. **A stage.** At an actually reached observed frontier, execute another prefix, inspect its results, and possibly terminate. Its input cache, graph/cache conditioning, output obligations and lifecycle work differ from the macro's initial state.
3. **A request.** Multiple stages and proposal episodes, including prefill, terminal behavior, future draft catch-up and policy overhead. Neither a macro-cost difference nor this finite-episode objective is a request-level speedup.

In particular, `T([4,4]) - T([4])` is not an admitted estimate of the cost of continuing after an observed successful first stage. It combines measurements with different operation scopes, initial captures and conditioning. It does not price a decision boundary or a short-circuit cleanup path.

### A concrete frontier discrepancy

The first q4 call consumes `[seed,p1,p2,p3]`. Its four logits can establish that `p1,p2,p3,p4` match, while target KV ends at **p3**. If p4 triggers CAP/EOG and the declared reference retains p4, a q1 materialization is still required, even though the request is terminal. Draft KV reconciliation may also be required. Continuing instead starts the next input block at p4. A zero-cost STOP at that boundary would silently change the active-state contract.

The controller therefore does not infer STOP legality from a matching token or from a successful complete q8 macro. Every stop/convergence action requires its own postcondition and qualified cost. Missing stop or outcome costs make the corresponding decision unavailable.

## Causal information and updates

The initial domain is deterministic greedy decoding with an already generated, fixed draft block. The draft cost is already paid. Selecting a shorter verification prefix cannot refund it. Replacing this proposer with lazy short drafting or a parallel block proposer is a separate experiment and must be offered to the baseline.

At each decision the controller may read:

- The fixed candidate IDs already produced and their known EOS membership.
- The current verified frontier, known output-cap budget, observed terminal flag, and a runtime state key.
- Acceptance observations from previously completed verification actions.
- A frozen, same-deployment cost/legality catalog available before the decision.

It does not receive future acceptance length, future target decisions, final output length, the hindsight oracle route, root identity as a predictive feature, or missing-bit completions. The update API accepts a chronological observation only after the action ID has been issued. It learns from the true accepted prefix and, when observed, the first mismatch. Everything after the first mismatch or an observed terminal event is censored.

The initial predictor is deliberately simple: a Beta(1,1) conditional-acceptance estimate at each draft position, updated only with those observed trials. This is a transparent causal baseline, not a novel calibrated predictor. Repeated public sessions are not independent new task samples.

## Finite-episode decision model

Let v be the number of target decisions already revealed on the matching candidate prefix, with the current pending token and physical frontier described by the runtime. Let q be the width of the next qualified stage, and let o be a possible observable outcome: first mismatch, matching CAP/EOG, a bonus row, or another fully matching nonterminal frontier.

Let `P(o | F_t, q)` use only the predecision information above. Let `g(o)` count additional committed output tokens, `C(v,q,o)` be the qualified **complete incremental cost through the stated outcome frontier**, and `H(v)` be the controller cost at the decision point. In particular, C includes the required synchronization, trim, target/draft materialization and recovery for that outcome. Let b be a frozen value in nanoseconds per useful token, calibrated externally from past observations rather than from this episode's future path.

For the finite candidate episode:

```
V(v) = -H(v) + max {
    -C_stop(v),
    max over legal q: sum_o P(o | F_t, q) *
        [b*g(o) - C(v,q,o) + V(next(o))]
}
```

The continuation term is zero for an outcome that closes this candidate episode. A matching nonterminal frontier may make another causal decision. Unknown EOG probabilities must not be invented; costs can conservatively cover all documented terminal/nonterminal reconciliation outcomes, or the action is unavailable. A known cap may restrict legal actions before execution, but a future EOG position may not.

This is a finite-horizon, local value surrogate. It is not an optimal policy for the remaining request, an SLO guarantee or a long-run throughput theorem. The earlier one-step counterexample—locally attractive progress leading to cost 101 versus an alternative ending at cost 3—still applies to unmodeled state after this episode. b and the approximation's continuation value need independent validation.

### Explicit Markov-state assumption in the small implementation

The synthetic recursion merges successors by `at`, the revealed frontier. It **assumes** every path reaching that frontier has already converged to the same sufficient physical/graph/cache state for all future prices. `Price.postcondition` is descriptive test metadata; checking that it is nonempty does not authenticate a postcondition or prove this convergence. The initial deployment/state key is checked, but the code is not a complete physical-state DP and does not certify stage concatenation.

A constructed counterexample illustrates the missing obligation. Two paths reach the same logical frontier. Path A costs 1 and leaves a latent state whose next operation costs 100; path B costs 5 and leaves one whose next operation costs 1. A frontier-only table that supplies the cheaper suffix cost 1 to both chooses A at modeled cost 2, although its actual total is 101 and B costs 6. These are hypothetical units, not device measurements. A real adapter must either prove both successors share a cost-relevant state, or expand the key to distinguish their recipe, graph/cache conditioning and retained physical state. Equal token IDs or serialized active KV alone do not prove equal future latency.

The measured decision time is recorded even when the answer is fallback/abstention. Falling back after evaluating a policy does not make that evaluation free. The internal watchdog observes the decision body until final accounting starts; the external host harness times the whole Python call including that accounting. Feature construction, state identity acquisition, runtime synchronization and any native adapter still require separate end-to-end measurement. An overhead budget can disable further evaluations, but it cannot remove already incurred cost.

## Cost evidence boundary

`cost_admission_v2.py` repairs specific failures reproduced in the old diagnostic readers: changed JOB history, failed RUN status, changed model identity, deleted repetitions and an empty actual-module inventory could previously pass a raw replay helper. The new reader validates a complete, externally pinned run and its explicit assets before exposing costs. The expected RUN hash must come from an external trusted publication or manifest; computing it from the file currently under review is not authentication.

Current CPU runs produce no imported deployment costs. A future valid CUDA run can produce typed **capture-conditioned target-operation macro costs** bound to source, binary, actual libraries, model, history, candidate IDs, initial state, mode and observed graph work. They retain their actual timing/instrumentation scope. They do not authorize clean resident stage control, supply historical-R qualification or provide missing branch/STOP costs. This release does not merge costs across runs or extrapolate them across histories or deployment fingerprints.

## What would make approximately 5% plausible?

For candidate episode b of the simple fixed-block first4/remaining4 policy, write the actual qualified costs as `C8_b`, `Cfirst4_b`, `Cnext4_b` and reconciliation difference `DeltaR_b`. Let p4_b be the causally predicted probability of reaching the second stage without a stopping event, and H_b its incremental control overhead. The modeled saving for that episode is

```
Delta_b = C8_b - Cfirst4_b - p4_b*Cnext4_b - DeltaR_b - H_b
E[sum over aligned reached episodes b of Delta_b] > 0.05*T_baseline_request
```

The second line is the model-level request condition only when candidate and baseline episodes align and all additional request costs have been charged. A single episode need not save 5% of the entire request. If adaptive stopping changes episode boundaries, this sum is not an observed request comparison; the new sequential state trajectory must be measured. All costs must share deployment and measurement scope; `Cnext4_b` must be measured at its actual admitted frontier. The already generated draft block, common prefill and other request costs remain in `T_baseline_request`. They cannot be removed from the denominator or refunded to the candidate. An episode here is not one of the eight repeated measurement blocks in the older trace analysis; its 151-call count difference and 4.498 ms calculation use different aggregation levels.

This inequality is currently unmeasured. The public AR-drafter trace already shows ordinary q4→q4 reveal using more target q4 calls than the strong k3 baseline, while generating more proposals. A benefit against fixed q8 alone would therefore be insufficient. The potential residual is a useful architecture-specific frontier where rejected-suffix work falls substantially while extra weight passes and reconciliation stay cheap, and a causal predictor can identify it without future acceptance information. If such a frontier does not exist, the controller should not be pursued as an independent optimization.

## Minimal next experiment and failure conditions

First qualify one actual stage and all of its possible terminal/rejection convergence branches against the fixed numerical reference, including the p4 pending/materialization case. Measure its complete resident cost and the same strong baseline, with controller instrumentation priced separately and then included. Compare q8, qualified staged reveal, short lazy drafting and ordinary cost-aware adaptive verification with the same generic optimizations.

Only after that evidence exists should the controller be evaluated on new sequential requests, using development-only costs and predictors. A frozen controller must beat the best fair baseline after its own overhead. A controller × lowering comparison is needed to separate scheduling benefit from a better kernel. Generality requires more than one deployment and explicit negative cases; no broad shape or model sweep is authorized by this software release.

Stop the research claim if the new frontier fails numerical/state qualification, stage savings disappear after reconciliation/control costs, existing adaptive selection achieves the same result, performance exists only against a weaker long-draft baseline, or a timing/cost model fails on held-out states. The current result is a method component and a testable hypothesis, not a new complete speculative-decoding method or a demonstrated 5% improvement.

## Prior art boundary

The earlier reviewed sources already cover profile-driven adaptive lengths and useful-token/cost objectives (TurboSpec), confidence pruning with profiled verification costs (EVICT and native adaptive verification), and partial/preverification (PEARL and the public incremental-verification design). Root's new literature review also identifies PACER's trainable blockwise preverification. Bellman recursion, Bayesian count estimates, causal histories, prefix closure and a STOP action are standard ingredients.

The candidate contribution, if later supported, would be the actual numerical/state-compatible frontier transformation and its measurable residual advantage under architecture constraints—not renaming these standard ingredients. The evidence and primary-source links remain in the immutable prior literature reviews; the new report should cite the root's updated PACER review before claiming a distinction from it.
