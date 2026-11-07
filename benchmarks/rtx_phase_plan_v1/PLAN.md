# RTX: reference-derived resident phase plans

Status: prospective implementation/experiment. No new GPU results. Parent PR186
`e8f1ea5aaa35789216801dd971b17e7d5e9f090f`; historical D failure remains closed.

## Research decision

Fixed numerical R is the obligation. A failed candidate binary, its per-request
state copies, its invocation segmentation, and its context allocation policy are
not immutable. A changed candidate must be qualified against R, not silently
redefine R. The objective is an executable, structure-derived resident phase
plan, not a new audit hierarchy or another percentage-significance attempt.

Hypothesis: reference-sensitive prefix/arithmetical constraints can be compiled
into phase-specific execution groups while keeping one active target KV owner
across prefill, ordinary decode and verification. Supported requests then need no
online reference replay or host KV export/import for phase switching. Parallel
independent reductions remain usable. This is a research hypothesis; zero copies
on RTX, which already uses resident contexts in PR151, is NOT a newly achieved
speedup. B570's legacy migration motivates portability, not an RTX result.

Potential contribution is automated composition of a *pre-existing numerical
reference* with state-stationary phase transitions and competitive lowerings.
Individual fixed reductions, four-column loops, same-context execution, batching,
and checking state are not claimed novel. Compare Taming (2609.11356), Vosti
(2609.38981), and LLM-42 (2601.17768); no performance comparison is meaningful
without matching the numerical/feature contracts. Do not rename known ideas as
new algorithms.

## Positive artifact to build

Implement a small native API: extract live supported structural requirements ->
produce immutable phase plan -> execute on the existing target context -> return
only originally requested output rows. Requirements must be obtained from actual
cache occupancy/head/padding, graph shape/strides, supported scalar arithmetic
and backend placement/dispatch. No prompt IDs, answer data, model-name switches,
or hardcoded head767/cap704. Model assets remain inputs, not strategy keys.

Use `native/phase_plan.hpp` and `native/execute_groups.hpp` as tested, backend-
neutral helpers. The dense formula is only a model for a bound dense cache
profile. Native extraction supersedes it; holes, wrapping/sliding windows and
unqualified backends must be rejected before mutation. Matching metadata does
not establish numerical equality. Reuse existing native qualification machinery
rather than authoring a generalized theorem prover or certificate framework.

Two equal-opportunity lowerings:
- SIMPLE: boundary-aware whole-graph groups / re-alignment with backend_loop4.
  This is the strong control, not the invalid PR151 unsplit caller.
- LOCAL: local reference-prefix attention with the qualified packed projection
  path. Both must receive any common numerical or lifecycle repair.

Do not put a caller cap4 on the entire LOCAL prefill: its outer projection needs
wide known-query groups. Attention grouping and projection grouping are separate
plans. SIMPLE may use maximal legal groups and re-alignment, not artificially
small calls. Keep the fastest lawful simple organization found on development
and freeze it before test exposure. No learned AUTO/online trial execution.

## Sources and deployment identities

Oracle: preserve PR151's original models, numerical libraries, producer/caller
and output flags, C1024, resident/reset history, k3, cap128 and reference reserve1
where those define R. Keep original R as an independent process/binary. Runtime
upgrade on the candidate side is permitted only with a direct original-R bridge.
Candidate prefill/verify calls may differ as the tested method, not as an
unreported change to the oracle.

Integration alternatives, selected during development:
1. Port the minimal proven prefix rule and compatible projection choices to the
   original D source family, preserving its scalar numerical path.
2. Use the later PR171/PR186 candidate family only after it matches original R on
   scalar producer and state controls. If it differs, do not rename its scalar
   execution R; use option1 or report the obstruction.

Keep context maximum capacity/output reservation separated from actual query
width. Do not enlarge reference output flags to obtain easier observation.
Copy requested candidate vectors before the next split overwrites their memory;
`OutputRows` owns these bytes. Never use last native logits after trim as the
frontier by assumption. Keep source positions, masks, row ownership, pending
unmaterialized terminal token, and sampler state explicit.

No state export/import, reference replay, new target context, or hash of full KV
is allowed in clean supported phase transitions. If needed for correctness,
report the path as a migration/fallback path and charge it rather than hiding it.
Offline qualification may inspect full state; it is not a timed performance arm.
Do not move online safety checks out of the timer without actually removing them
from the candidate implementation and qualifying that implementation.

## Stage 1 — mechanism and useful implementation, not a panel rerun

Use the retained APPS/train/65 failure for development only. Reproduce original
D1 and original R once; fixed historical artifacts may supply the old failure.
Then verify the generic plan produces 1+3 for observed head767 and the actual
extent vector, without specifying this cut in executable logic.

Development coordinates: registered actual extent transitions near 256/512/768,
q1/2/3/4/5/8/16/32 within capacity, both crossing and noncrossing, plus unequal
terminal tails. Exercise k3 rejection after acceptance, all-accept/bonus, cap and
native EOG, and a reused context after a prior request. Controlled protocol
branches are diagnostics, never natural acceptance-rate observations. Start with
saved operands and exposed inputs. Do not manufacture padded natural prompts.

Qualify both SIMPLE and LOCAL, including ordinary M, against independent free R
and actual-prefix forced references. Compare full requested target vectors,
active KV and frontier at the predeclared committed boundaries, correct output
length and terminal state; state exactly which boundaries are observed. Use the
existing PR186 adapters/replay bank and extend only missing native bindings.
Check the observer bridge separately; dump time must not be in clean service.

Count the actual online phase work (exports/imports, context construction,
replay, requested output copies, graph build/reuse, physical widths). Mere source
expectations are not measured launch counts. GPU traces are separate from clean
timing; capture/fusion settings must be equally available to both methods.

## Stage 2 — cross-structure transfer before additional statistics

After Qwen implementation development, freeze its shared rule source. Apply it
to the existing RTX Smol target/draft family with that family's own preselected
original numerical R; do not compare cross-model bytes. At least one actual head
mapping or dimension must differ, confirmed from model metadata. Use existing
assets only. No name-conditioned patch. If new structural support is required,
retain the failed transfer, revise the common rule, freeze again and call this
an implementation extension, not zero-change transfer. Do not keep picking new
models until one passes. Optional Llama controls cannot replace a failed Smol
transfer or be pooled into the same sample.

This is the generality question: does one extractor/planner/native API prescribe
legal execution for multiple structures and phases, not merely whether their
endpoint text matches?

## Stage 3 — fixed-arm costs, then new natural confirmation if informative

Six arms = {SIMPLE, LOCAL} x {M, D1, D4}; target-only gets the same lawful target
optimizations and matched model residency. Same k3 and post-prefill singleton
draft sync/proposal policy. D4 is an ordinary strong alternative, not novelty.
SIMPLE may beat LOCAL; that is a valid method choice. Keep all controls.

Before test exposure use four exposed development roots/family and one fixed
all-six-arm timing pass. Record disjoint synchronized phase intervals, complete
resident service, process/model setup and initial plan compilation separately.
If the actual implementation has no cross-phase capability difference and no
plausible saving over the strongest same-contract simple arm, do NOT add test
sessions to rescue a mean. Deliver the implementation, exact limitation and
measured development costs. Amdahl-style ceilings are screening arithmetic, not
measured speedups. No universal 3%/5% acceptance threshold.

Prospective confirmation default for a viable candidate: eight new independent
natural roots per family, two existing families, six arms, six Williams sessions:
576 measurements +576 immediate same-arm warmups. Use the existing outcome-free
selection/exposure ledger; exclude every prior test and development root,
including PR174/175/177/186/187 exposure. Select source roots before token-based
admission and keep both admission and selection denominators. Confirm each
family independently; do not pool graphics cards or model families.

Primary total complete-service ratios: LOCAL-D4/SIMPLE-D4 and
LOCAL-D4/min(SIMPLE-M,LOCAL-M). For the second comparison report BOTH individual
M contrasts with family adjustment, rather than claiming an uncorrected posthoc
minimum. Also retain the full fifteen paired contrasts and equal-root log
sensitivity. Independent statistical units are roots; six repetitions remain
clustered. Freeze all estimands and multiplicity handling before blind output.
Report absolute time, adverse roots, phase work and setup amortization. Preserve
PR186's original primary/secondary distinction; do not add its samples here.

Budget default: <=4096 total model trajectories, <=12M decoded rows, <=1536
operator probes, including failed/teacher/qualification/warm work. Use inherited
request ownership, signed memory/disk reserves and cleanup. These are ceilings,
not targets. A justified amendment before test exposure is allowed and must be
recorded; never alter an exposed panel or discard inconvenient outcomes. No
waiting for B570 or an arbitrary common freeze barrier.

## What the executor may change

Autonomously repair paths, compiler/ABI issues, source anchors, serializer bindings,
planning instrumentation and normal implementation errors. Pin the resulting
actual code and rerun affected finite qualification. Do not stop at helper tests
or require a new human approval for ordinary engineering. A numerical failure
is not permission to swap R, drop the strong control, or cherry-pick test inputs.
If a blind numerical failure occurs, preserve and close that version; bounded
mechanism diagnosis is allowed, a new version gets a new pre-output freeze and
separately labeled panel. Finish useful independent work even if one branch is
blocked. No rental, merge, manuscript edit, MMA, universal transaction layer or
another AUTO sweep in this task.

## Decision deliverable

Deliver one small reusable native interface and its actual supported phases,
source-derived predictions vs observed execution, the old-R equivalence scope,
all strong-baseline outcomes, complete costs and a short novelty assessment.
A positive result must be a new capability or useful same-contract efficiency,
not a larger audit corpus. If SIMPLE suffices, adopt it and narrow the claim.
