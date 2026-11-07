# Initial preparation validation

Date2026-10-18; Python3.12.14; standard library only. CPU preparation, not RTX
execution and not external independent review.

`python3 -B -m unittest -v test_cpu`: **15 tests passed** in2.619s.
All observations are explicitly fabricated fixtures. Checks cover deterministic
plan counts/identity; within-mode Williams position/carryover balance; mode-order
balance per cycle; off-only fallback and optional gates; known complete-matrix
ratios; unverified ON exclusion; false qualification refusal; missing realization/
arm coverage; wrong/duplicate identities and views; nonfinite/boolean/nonpositive
samples; wrong call counts; mixed source/runtime/input/reference identities;
single-session limits; same-QB label bias; failed-attempt incomplete receipts.

Actual command-line checks:

```sh
python3 -B plan.py --graph dual --out runs/plan.json
python3 -B analyze.py --plan runs/plan.json --receipts runs/synthetic.jsonl --draws 100 --out runs/synthetic-analysis.json
```

The analyzer consumed896 fabricated timed-host receipts (768core+128optional),
and reported896 expected timed hosts. CLI fixtures use known ON/OFF=.8 and known
QB/QH and producer conversion ratios. This validates serialization and pairing,
not measured speedups. The production descriptive bootstrap default is4000draws.
Full plans, CLI fixtures and outputs stay in ignored runs/, not scientific tables.

Default plan hash:
`22525ea80cbb82ef6a9bd0021c36a07c9860db08bd7e1dd85630b211f8a4d78e`.
The CLI plan equals make_plan(). PLAN_OVERVIEW.json is generated from that object.
Core956hosts/34124calls; optional176hosts/5968calls; total1132planned tasks.
Off-only core500hosts/17084calls. Capability/profile ceilings are additional and
must be reported separately without double-counting a reused qualification host.

The pinned PR121 collector was inspected to confirm the explicit graph-disabled
setting. Its compact HOSTS.csv was independently recomputed during the preceding
review; the absolute means quoted in PROTOCOL.md are rounded from those rows.
This session did not restore/authenticate the Windows raw archive. The parent
result's numerical/evidence claims retain their stated local-only scope.

Not validated here: Windows compilation, native input/reference binding, actual
graph activation, profiler support, changed-input capture safety, telemetry repair,
integrated Q transaction, device bytes or GPU timing. The native executor must
implement and qualify these before formal collection. Compact hash fields and
passing CPU tests cannot substitute for real evidence. No GPU/model/profiler ran
in this preparation; no hardware benefit or natural-request result is claimed.
