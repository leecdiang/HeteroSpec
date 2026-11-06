# TPDS phase one: reviewed execution framework v2

**Read `REVIEW_V2.md` first.** It implements the author's pre-timing review of
PR192/193. `RTX.md`, `B570.md`, `EXECUTION.md` and `HOST_ADAPTER.md` retain the
original design/integration details; the v2 amendment overrides their fixed
four-arm R2 default, incomplete-input staging, and cost normalization rules.
No native GPU work has been executed in this authoring update.

## Existing runs are immutable

Check original-host freeze/ledger/working-tree state. No GitHub result is not
proof that a host has not started. An already frozen/running panel stays on its
original commit, arms and timing definitions. Do not hot-patch or add controls
mid-panel. Retain its outcome and register corrected work as a new version with
new output paths. Ordinary build/ABI/path/observer integration can proceed
without repeatedly asking the author. Independent branches need not wait for
one another.

## What changes before a new freeze

1. **R2 baseline coverage.** Review W_L4, W_P, L_L4 and L_P under the same R.
   Include every legal distinct target-only implementation; omit a mixed arm
   only with actual source/trace/cost-path equivalence or native inapplicability
   evidence. The strongest observed legal development combination is covered.
   Freeze the review before R2 outputs; test timings never select controls.
2. **Build closure.** Full isolated source-tree hashes, all frontend headers and
   generated inputs, compiler dependency reports, exact compile/link options,
   toolchain/link inputs and actually loaded modules are frozen after native
   qualification and before formal timing. Staging is not a native build.
3. **Append cost.** B570 needs actual C4096 allocation/output/observer qualification.
   Structural comparisons read native `append_ms`, never total service/prefill.
   Clean observer counters are observed, not filled with zero from a flag.
4. **Missing costs.** Unmeasured nested draft phases are null; verified measured
   zero, NOT_EXECUTED and partial coverage remain different. Partial sums are
   `observed_sum_s`, not complete totals.

## Entry points

- `HOST_PROMPT_V2.md`: concise native-agent handoff.
- `REVIEW_V2.md`: full amendment, record schemas and version rules.
- `baselines.py`: complete R2 strategy disposition and frozen-panel adoption.
- `build_freeze.py`: explicit compiler-input/module closure freeze and recheck.
- `stage_native.py`: two qualified-recipe source cores and common frontend,
  independent four-way factor/job maps and all six possible R2 arms.
- `stage_b570_probe.py`: actual capacity, original output-mask and append clocks.
- `design.py`: structural/natural schedules and baseline-bound persistent bursts.
- `analyze.py`: complete-panel contrasts, factor interaction and every fixed M.
- `receipts.py`: append normalization, saved phase coverage and source packaging.

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -O -m unittest discover -s tests -p 'test_*.py'
python3 design.py rtx-struct --out new-version/R1-STRUCT.json
python3 design.py b570-struct --out new-version/B1-STRUCT.json
python3 design.py burst --inputs frozen-inputs.json --primers EXPOSED_A EXPOSED_B \
  --baseline-review R2-baseline-review-v2.json --out new-version/R2-WORKERS.json
python3 build_freeze.py freeze build-inputs-v2.json build-freeze-v2.json
python3 receipts.py saved-costs saved-results.json new-version/COSTS.json --expected-sessions 6
```

R2 retains 16 roots and four sessions. Depending on documented equivalence/
inapplicability, 4–6 arms produce 256–384 test requests and 32–48 primers.
No session is added. Primary D4 comparisons cover every included target-only M
with multiplicity adjustment; matched-residency sensitivity is separate.
The original total limits (RTX 3072 requests/4M rows; B570 1024/2.5M) remain.
All failures, reference work, qualification and warmups count toward them.

The R1 structural and B1 sparse matrices are unchanged. A redundant natural R1
panel can close while R2/build work proceeds. A C4096 resource failure does not
erase C1024 work. Do not change original R, old results, arXiv or safety floors;
do not rent compute, merge, add models or expand algorithmic scope here.

`VALIDATION.json` reports helper/fixture tests only. Complete original-host
build, qualification, native observer binding and actual performance remain
executing-agent work. No template evidence ID is an approval or a measured fact.
