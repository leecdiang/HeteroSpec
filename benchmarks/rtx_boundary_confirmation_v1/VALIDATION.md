# Initial CPU validation

Validated on 2026-10-18 with Python 3.9.6, standard library only. This document
records preparation checks, not RTX execution or an external independent review.

## Executed checks

`python3 -B -m unittest -v test_cpu`: **19 tests passed**. The observations in these
tests are explicitly fabricated fixtures. Checks cover:

- Deterministic plan identity, exact host/call counts, one-factor edges, distinct
  holdout seeds and prediction-freeze gates, 64-call host bounds, H0 fallback
  qualification, and arm-position/directed-neighbor balance in every cycle.
- Known paired ratios, same-QB label bias, alternate-QB sensitivity, q1 equality,
  missing arms/realizations, one actual session and block-level replication.
- Duplicate/unknown tasks, wrong layout/method/plan/cost view, changed runtime or
  input identities, and boolean/nonfinite/nonpositive/wrong-count timing arrays.
- Factor differences and the complete 52-input / 1664-timed-host synthetic panel,
  including separate q1 controls and all 24 q2/q4 geometries across eight blocks.

The command-line planner was executed with:

```sh
python3 -B study.py --out runs/plan_final.json
```

Default plan SHA256:
`fbfd827eac7db0f49261ece8e0eef3ab50c2a1e5311ba9069b6187d45a63f82c`.
The generated file equals `study.make_plan()`; PLAN_OVERVIEW.json was generated
from that object. It contains 3008 planned tasks: 2480 core hosts / 81976 graph
calls, plus 528 optional hosts / 17112 calls. These are task counts, not measured
execution or all-process accounting. H0 qualification or 50 measurements creates
a different plan identity.

The analyzer CLI was exercised on 64 fabricated receipts for one two-realization
geometry, using 100 bootstrap draws to check serialization and the CLI path:

```sh
python3 -B analyze.py --plan runs/plan_final.json --observations runs/observations_synthetic.jsonl --draws 100 --out runs/analysis_synthetic.json
```

It retained the unstarted scope and correctly withheld a complete-panel estimate.
The production default is 4000 draws. Generated full plans and synthetic CLI data
stay in the ignored runs directory; no synthetic observation is published as a
scientific result.

## Parent evidence recalculation

`audit_parent.py` was executed against TIMING_HOST.csv and R1_CONTRASTS.csv from
PR120 at `c6eb66368bc876332afe82f9df5ea51fe0b4b5ec`:

```sh
python3 -B audit_parent.py --host-csv local_artifacts/TIMING_HOST.csv --r1-csv local_artifacts/R1_CONTRASTS.csv --out PARENT_REVIEW.json
```

It reproduced 90 eligible q>1 resident-graph pairs over blocks 0,1,2,3,5:
QB/QH_C=0.8856270167699429 and PQ/QB=1.8146204762656193. It also exposed the
per-block and synthetic-development q1 variation recorded in PARENT_REVIEW.json.

The source hashes in that JSON describe the locally materialized UTF-8 CSVs after
CRLF-to-LF normalization through the content transport. They are not asserted to
be raw Git-blob hashes. This is recalculation of committed compact tables; the
PR120 local RTX archive was not accessed, restored or independently authenticated
in this preparation session. Previous eligibility and historical results are
unchanged.

## Scope still pending

No CUDA, GPU, profiler, native host, model request or natural decoder ran here.
The logical recipe still needs a tested RTX tensor generator and actual hashes;
the buffered observer, native adapter, cleanup and qualification require platform
implementation. Compact-receipt validation cannot prove actual device bytes,
clock calibration, numerical qualification or archive authenticity. These remain
explicit executor responsibilities under PROTOCOL.md and DATA_AND_RECEIPTS.md.

CPU tests and planned counts do not establish a hardware benefit. The scientific
state remains NOT_RUN for this lane and the inherited hardware decision remains
SOFTWARE_FIRST/HOLD.
