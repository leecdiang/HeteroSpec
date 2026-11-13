# M — isolate cut scope, then test the verification-width threshold

## Decision and hypothesis

PR195's structural 2x2 and target-only comparisons are retained. PR196 compares
W_L4-D4 with L_P-D4 and therefore combines two factors. This study adds the direct
same-projection D4 comparisons, without editing that running experiment.
The question is whether local attention cuts retain a benefit with identical
projection arithmetic, and whether independent-group packing can serve a real
q8 verification rather than only prefill. Neither outcome is required positive.

## M0: bind the actual Linux runtime

Use the qualified PR196 successor, not merely its design SHA. Recover the same
Qwen3-8B/0.6B Q8_0, F16 KV, C1024, greedy, no-FA, resident/reset contract. Preserve
that target reference. Record reference/resource/source and all compiler inputs.
Dev source can be repaired; live PR196 files and frozen measurements cannot.

## M1: four real D4 paths under fixed k3

| Arm | Attention cut | Projection | Draft prefill UB | k |
|---|---|---|---:|---:|
|W_L4_D4|whole/rechunk|loop4|4|3|
|W_P_D4|whole/rechunk|packed|4|3|
|L_L4_D4|local|loop4|4|3|
|L_P_D4|local|packed|4|3|

Implement the two mixed combinations in the common frontend, not timing aliases.
Give every path identical legal lifecycle, precision, placement and graph-reuse
repairs. Actual requested rows/physical graph widths and dispatch establish what
ran. Use fixed existing counterexamples and short/long/tail/EOG cases for native
qualification; full vectors, active KV/frontier, pending and transaction checks
precede clean timing. If the paths coalesce on aligned work, record that fact.

After freeze, use the16 fixed PR195 roots as explicitly exposed attribution/transfer
inputs, four sessions and four arms:256 complete tests +32 primers. Use one worker
per arm/session, two separate exposed primers,16 distinct requests. Primary
contrasts and multiplicity family (including the interaction) are in study.json.
Report full resident service and actual burst/startup, not only verify. The root
interaction is (L_P/W_P)/(L_L4/W_L4); it is not a claim of global performance optimality.
No speculation-vs-M claim is made from these four D-only arms. Prior M data cannot
be silently reused as a new same-panel control.

## M2: a bounded native k7/q8 capability study

This is a new candidate epoch, not a k sweep. D4 stays draft prefill UB4. Test k3
and k7 only: k3 commonly requests q4, whereas k7 can request q8 and trigger packing.
Do not globally divide verification into q4 pieces and then claim q8 parallelism.

Required source work: parameterize ArmSpec k, real transient allocation, requested
row buffers, all acceptance/correction/bonus indexes, trim frontier and cap/EOG
paths. `verification_spec.hpp` validates relationships only; it does not implement
these changes. Keep scalar R at its declared UB1/output reservation. Qualify
k3-reserve8 as a bridge before comparing k3 and k7 at common candidate reserve8;
retain original k3-reserve4 results as a separate configuration. Observe actual
rows and requested mask rather than assuming k+1 always executes. Preserve the
registered generation/early-stop policy, including any work executed near cap.

Use owned actual operands and same known proposal tape to isolate target costs,
then live drafting to measure changed acceptance and wasted work. Report these
as different studies: a free replay is not end-to-end drafting. q4 is a negative
control where wide packing is inactive; unexplained q4 timing differences are
not attributed to packing.

Four exposed roots, eight {cut,projection}x{k3,k7} arms and two sessions give64
pilot tests +32 primers, after finite qualification. These are descriptive. Compare
same-k/same-projection before interpreting a cross-k total. Larger acceptance or
fewer calls alone do not establish profitability.

Do not automatically open a large panel. If a new implementation has a concrete
complete-cost opportunity, freeze a distinct confirmation with **all four real
M controls and all eight D controls**,12 new roots/four sessions (576 tests +96
primers), including all candidate failures and original controls. Predeclare the
new cohort, family of contrasts and resource amendment; no favorable subset or
extra rounds. This optional panel is not included in the default plan generator.

## Deliverable and latitude

Complete M1 even if q8 integration remains unsupported; continue q8 engineering
when a local compiler/API/ownership issue can be repaired. Diagnose arithmetic
counterexamples and implement general structural rules, never token-ID exceptions.
Preserve native traces, failed versions, complete costs and source diffs. Initial
envelope2048 requests/8M rows includes references/pilots/failures; track cumulative
charges. No extra model/k sweep, masked MMA, automatic paper edit or PR merge.
