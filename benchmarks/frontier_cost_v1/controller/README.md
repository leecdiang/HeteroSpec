# Causal frontier-control research component

This directory contains a repaired cost reader, a small causal policy model, and evidence that limits the current claim. **No new model, native inference or GPU request was executed. There are no admitted resident stage costs and no production action is enabled.** The CPU q2 failure does not prove that every stage or the original CUDA deployment fails; the blocker here is the absence of same-deployment stage/convergence cost qualification.

Read `DESIGN.md` for the mathematical objective, architecture question, same-frontier state assumption, 5% condition, competing baselines and stopping criteria. `RESEARCH_CONCLUSION.md` gives the short research judgment.

The compact published receipts are [VALIDATION.json](VALIDATION.json) for the final software checks and [TRACE_DIAGNOSTIC.json](TRACE_DIAGNOSTIC.json) for the fixed exposed-trace forecast diagnostic. Per-call timings and per-event forecasts remain outside Git.

## What is executable

| File | Function and boundary |
|---|---|
| `cost_admission_v2.py` | Validates a complete externally pinned raw run and explicit local assets. It repairs five demonstrated acceptance gaps in the old diagnostic reader. CPU smoke produces no deployment costs; future valid CUDA macros remain capture-conditioned target-operation diagnostics. |
| `causal_policy.py` | Chronological announce/observe API, censored conditional-acceptance estimates, finite-episode backward recursion, explicit required terminal materialization, and an abstaining runtime interface. Nontrivial recommendations accept only explicitly synthetic model prices in this release. |
| `test_causal_policy.py` | Fifteen contract tests, including future information, missing costs, no legal action, terminal p4/p7 materialization, physical versus logical frontier, sunk drafting and policy overhead. |
| `run_checks.py` | Runs those tests and measures complete Python call overhead on constructed data. It does not measure GPU or service latency. |
| `trace_diagnostic.py` | Causal prequential forecasts on existing logged k7 actions, preserving censoring and logging policy. It does not replay counterfactual actions or calculate a speedup. |

The runtime method never interprets a successful macro timing as a stage cost. It returns `ABSTAIN` with no q1, rewind or STOP instruction. The existing runtime owner retains control at its existing legal frontier. The policy's evaluation overhead remains paid even on abstention.

The synthetic recursion optimizes a local token-value-minus-cost surrogate in floating arithmetic. It assumes all paths at a frontier share a sufficient cost-relevant Markov state. The current metadata does not prove that assumption; see the 101-versus-6 path-conditioning counterexample in `DESIGN.md`. It is not a fully authenticated state-aware scheduler or a whole-request optimum.

## Exact-run validation

`validate_exact_run` checks RUN success/return code, externally pinned RUN bytes, JOB/input/RESULT binding, source/binary/model/frontend/library assets, actual loaded modules, the complete ordered qualification and measurement panels, full vectors/state comparisons, physical widths, required outputs, the independent full ledger and blob accounting. The integrity test runs before CPU cost rejection, so CPU data can exercise the specific structural checks without obtaining production eligibility.

Assets are passed as a JSON mapping from role to explicit local file. Receipt paths are not opened automatically. Required roles are `runner`, `probe_source`, `model`, `source_manifest`, `binary`, each `frontend/<header>` and each `library/<actual-basename>`. Each supplied file must match the role's recorded size and SHA. An old executed runner must map to its retained exact snapshot, rather than to a newer file with the same filename. This check hashes files; it does not load or execute a model/library.

```bash
python -B controller/cost_admission_v2.py \
  --run-dir "$HETEROSPEC_RECORDED_RUN" \
  --inputs "$HETEROSPEC_RECORDED_INPUTS" \
  --assets "$HETEROSPEC_EXPLICIT_ASSET_MAP" \
  --expected-run-sha256 "$HETEROSPEC_EXTERNALLY_TRUSTED_RUN_SHA256" \
  --output "$HETEROSPEC_FRESH_ADMISSION_RESULT"
```

The expected RUN SHA must come from a trusted, externally bound publication or manifest. Computing a hash from the same suspect file and supplying it is not authentication. Red-team tests deliberately re-pin modified files solely to test the inner structural checks; those pins confer no production trust.

The original immutable q1 smoke RUN pin is `135e1901e8c2715492f512c54dc949d21b363b9dddf9a7d01f7c9a4a16a4324f`, recorded in PR221's `matched_cost/SOURCE_SNAPSHOTS.json`. It passes exact-run validation and is then rejected as a deployment cost, with zero macro and zero stage entries. Five mutated copies that the old helper accepted are rejected for the actual changed JOB, failed RUN, changed model, missing repetition or empty actual-module inventory. A second reviewer also checked a same-count duplicated-repetition attack.

The new reader does not rewrite or replace the old PR221 helpers. Those helpers remain raw-diagnostic tools, not a cost authorization boundary. No cost merge across runs is implemented. Source and deployment fingerprints, history/candidate/state identity, timing mode and graph work are preserved in any future diagnostic macro output. Its `online_stage_cost_eligible` remains false.

## Causal interface and STOP obligations

`Snapshot.from_mapping` rejects unknown fields, including future acceptance or final output length. The domain is greedy decoding. `PastAcceptance.announce` records an action before `observe` may update it; a repeated or wrong action ID is rejected. Only the matched prefix plus the first rejection is learned. Outcomes after the first rejection or observed terminal are censored.

The first q4 operation consumes seed,p1,p2,p3 and can reveal p4. If p4 is accepted and terminal under a reference that retains it, p4 still needs target materialization. Deferred draft tail recovery is charged when needed, even at termination. Conversely, if a wider call has already materialized p4, the terminal action may require a priced trim rather than another q1. The snapshot therefore distinguishes `verified_rows` from `target_materialized_rows`. All of these are model obligations until a native stage/convergence qualifier supplies actual evidence.

The full draft block is already produced in this decision domain. `sunk_draft_nanoseconds` is recorded but never refunded or scaled by the selected prefix. A future short/lazy drafting comparator must receive the same generic optimizations. Probability zero in a learned estimate does not waive the correctness/cost requirement for an observable branch.

## Reproduce the model checks and logged forecast diagnostic

```bash
python -B -m unittest discover -s controller -p test_causal_policy.py -v
python -B controller/run_checks.py --output "$HETEROSPEC_FRESH_CONTROLLER_CHECKS"
python -B controller/trace_diagnostic.py \
  --records "$HETEROSPEC_PUBLIC_LIVE_RECORDS" \
  --output "$HETEROSPEC_FRESH_FORECAST_DIAGNOSTIC"
```

Only standard-library Python is needed. Output paths must be fresh. Public trace bytes are hard-pinned to SHA `53d76c43d4b2fa378855b90f76d9bcb60e509d4086fddd630e3c0f51f6197487`; the 74 MB source is not copied into this directory.

### Observed implementation overhead

On this CPU workspace, 200 complete calls of the maximum 36-action synthetic recursion had median **0.257 ms** and p95 **0.448 ms**. Runtime abstention calls had median **0.711 microseconds**. The first sample and all outliers were retained. These include final Python accounting but exclude feature/state construction, receipt admission, GPU synchronization and a runtime adapter. They are an implementation cost observation on this host, not a GPU price, calibrated deployment H, or a service speedup. The initial narrower internal-span check is retained separately and superseded by the complete-call measurement for this claim.

### Observed predictor diagnostic

The fixed exposed session0 LOCAL-k7 panel contains 16 logged requests and 287 cycles. Chronological updates used 1,301 valid prefix trials. First-four-match labels were 153 true, 128 false and six terminal-censored cases. A per-position Beta survival predictor had Brier score **0.25757**; a simpler past-only direct first-four frequency predictor had **0.25185**. Lower is better, so the more structured predictor did not beat this simple comparator on the exposed panel.

This forecast target is first-four matching, **not** survival past CAP/EOG into a second stage. The code preserves actual logger actions, does not simulate a different policy trajectory, and imports no cost. These are development diagnostics, not held-out evidence or a 5% result.

Both use Beta(1,1) initialization, but four conditional means initially multiply to 1/16 while the direct event predictor starts at 1/2. The observed ordering is conditional on those declared initializations and the fixed exposed file order; no significance test or general predictor-family ranking is claimed.

## Publication and evidence

`PR_ALLOWLIST.json` lists the small public source/doc/summary files. `EVIDENCE_ALLOWLIST.json` lists only new local evidence, including private explicit-asset paths, per-call overhead samples, per-event forecasts and the retained earlier timing-span snapshot. No old raw run or source archive is copied. The original research and PR221 continuation directories remain read-only.

The next scientific gate is one actual, same-deployment resident stage with complete rejection/terminal convergence qualification and costs. The current software does not automatically launch that experiment or request GPU access.
