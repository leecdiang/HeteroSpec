# RTX boundary confirmation v1

Status: **CPU_PLAN_AND_ANALYSIS_READY; RTX_IMPLEMENTATION_AND_EXECUTION_PENDING**.

This lane follows PR120 at `c6eb66368bc876332afe82f9df5ea51fe0b4b5ec`. It asks
whether mapping cost differences survive same-implementation controls and balanced
acquisition, and whether changes in one declared geometry factor predict a change
in relative cost. It does not assume a QH win or a hardware opportunity.

PR120 restored immutable resident inputs and established a useful numerical panel.
Its q1 labels use the same arithmetic graph, yet block-level QB/QH_C ratios ranged
approximately 0.923–1.223; synthetic development q1 gave about 0.770. The aggregate
near-one q1 ratio cannot by itself establish fine measurement resolution. These
observations motivate a new experiment; they do not retroactively invalidate PR120.

## What is implemented here

- `study.py`: standard-library-only plan generator, fixed geometry contrasts,
  prospective holdout, counts, independent-QB controls and balanced orders.
- `analyze.py`: compact-receipt validator, paired block analysis, same-unit A/A
  diagnostic, swapped-QB sensitivity, geometry and factor contrasts, missingness.
- `test_cpu.py`: risk-focused CPU tests using clearly synthetic observations.
- `audit_parent.py` and [PARENT_REVIEW.json](PARENT_REVIEW.json): recomputation of
  the PR120 compact-table findings motivating this study, with their source scope.
- [PLAN_OVERVIEW.json](PLAN_OVERVIEW.json): generated compact overview of the default
  plan. The complete deterministic task list is generated locally by study.py.

The planner does not import CUDA or execute tasks. The analyzer does not verify
device bytes or authenticate raw archives; it consumes receipts produced by an
independent numerical/evidence check. The native collector, input resolver and
Windows integration remain RTX work. No GPU execution or hardware result is
claimed by this PR's initial delivery.

## Read and dispatch

1. [PROTOCOL.md](PROTOCOL.md): research design, implementation scope, budgets and decisions.
2. [DATA_AND_RECEIPTS.md](DATA_AND_RECEIPTS.md): logical input recipe, native timing
   requirements and exact compact analysis schema.
3. [RTX_PROMPT.md](RTX_PROMPT.md): complete Chinese task for the author to forward.
4. [VALIDATION.md](VALIDATION.md): what was actually checked locally.

```sh
python3 -B -m unittest -v test_cpu
python3 -B study.py --out runs/plan30.json
python3 -B analyze.py --plan runs/plan30.json --observations runs/observations.jsonl --out runs/analysis.json
```

Run from this directory, using the actual available Python. `runs/` is ignored.
The last command requires **actual** verified receipts; there is no runnable RTX
entrypoint in this initial delivery. The executor must record its real commands.
The generated plan has unresolved runtime/data fields and cannot launch old tasks.

## Scope and budget

Core: 24 q2/q4 geometries, two q1 controls, two value realizations each. Formal
confirmation uses PQ, QB_A, QH_C, QB_B, where both QB labels execute exactly QB.
Eight blocks comprise two balanced four-block cycles in separately started sessions.
Optional holdout: six q3 geometries, two value realizations each, kept unopened until
a prediction rule and its comparison metrics are frozen.

The default 30-call design has 2480 core host tasks / 81976 graph calls including
independent serial references, qualification and A/A pilot. Optional holdout adds
528 host tasks / 17112 calls. These are planned ceilings at the task level, not
observations or all-OS process counts. One GPU worker, eight-hour first-dispatch
budget, final hour reserved for delivery; do not promise the full matrix fits.

Develop and repair interfaces autonomously within scope. Freeze scientific conditions
before formal data. Preserve failures and partial cycles. If noise remains large,
report the resolvable effect scale and unresolved cells; do not restart a supervision
project or silently relax correctness. Partial evidence is useful, but incomplete
cycles cannot be described as a balanced eight-block confirmation.

All PR120 runs remain stopped. New UUID, new entrypoint, new source freeze. Reuse
its persistent-input implementation and exact numerical stack with provenance;
never bypass an old guard or manufacture an old approval. B570 and its ongoing
work are separate. No natural decoder, actor/W1, RTL, FPGA, merge, release or paper
claim update is part of this dispatch. Follow CONTRIBUTING.md for raw retention.
