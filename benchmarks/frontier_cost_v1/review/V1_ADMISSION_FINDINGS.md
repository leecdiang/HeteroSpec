# Independent review: diagnostic replay is not controller cost admission

**FAIL for promotion into a controller; PASS as retained, explicitly bounded diagnostic evidence.** The original `verify_run.py` can replay the selected saved records without establishing that the complete, successful experiment described by the caller actually occurred. A controller must use the new admission boundary and must still reject these CPU records as production stage costs.

This review ran only Python and filesystem operations. It made **zero model executions, zero CUDA driver calls, zero new measurements and zero new qualification observations**. Five deliberately modified copies of a genuine q1 CPU run are negative fixtures, not experiments. Every copy is marked `REDTEAM_ONLY.txt`. The original files were hashed before and after and remained identical.

## Executed reproduction

`reproduce_v1_admission_gaps.py` accepts an explicit read-only path to the earlier `matched_cost` directory, which must contain its original `cpu_protocol_final` evidence. Run it in a fresh output directory:

```sh
python -B reproduce_v1_admission_gaps.py --baseline /path/to/matched_cost --out /fresh/redteam-output
```

The actual independent execution is recorded in `v1_repro_01/REPRODUCTION.json`. The original RUN SHA256 was `135e1901e8c2715492f512c54dc949d21b363b9dddf9a7d01f7c9a4a16a4324f`. Reviewed reader hashes were:

- `verify_run.py`: `7749726db762f007a7aebce359ee958ee942aa46ca06cca938c153f3f7f2be0f`
- `summarize_cost.py`: `9f9c6a5e43755274a03c0a40d1f7d3468016ecf1a13a547912697c5e1fe1bd2e`

| Fixture | Minimal change | Original replay result | Required admission result |
|---|---|---|---|
| Unmodified q1 copy | None | PASS; 40 blob comparisons | Internally complete diagnostic; no production cost |
| Same-length history drift | Change one JOB history token; leave the recorded JOB digest unchanged | PASS; 40 comparisons | Reject JOB binding |
| Failed run status | Change RUN to timeout, return code 124 and reaped child code −9; leave RESULT/raw intact | PASS; 40 comparisons | Reject execution status |
| Model identity drift | Change only RUN model SHA256 to zeros | PASS; 40 comparisons | Reject model asset binding or external RUN pin |
| Missing repetition panel | Keep only the already recorded repeat-0 rows and recompute their RESULT counters; declared repeats remain 2 | PASS; 20 comparisons | Reject complete-panel/work binding |
| Empty actual module inventory | Remove both RESULT actual-module inventories; RUN still declares four numerical libraries | PASS; 40 comparisons | Reject missing observed modules |

For the last two structural fixtures, the script explicitly updates the copied RESULT digest in the copied RUN. This makes the test about the missing coverage/module check rather than a trivial stale RESULT digest. It does **not** claim that changing a digest creates trusted evidence. All modified RUNs would also be rejected by a correct external pin to the original RUN.

Every summary, including every modified case, still reports `NO_Q8_PAIRS_Q1_PROTOCOL_SMOKE_ONLY` and emits **zero cost pairs**. The demonstration therefore does not assert that a fabricated q8 observation was accepted or that the old summarizer claimed a measured speedup. It demonstrates that the legacy PASS cannot safely acquire the broader authority of controller admission.

## Specific failure mechanism

The old verifier checks the recorded RESULT hash and compares the referenced raw captures. It reconstructs work from the records that remain present. It does not bind JOB/input/history to the RUN, require successful RUN exit, validate the actual model asset, or compare the observed record set with the full declared case × width × schedule × mode × repetition panel. Its actual-module test rejects a conflicting recorded module but accepts an empty set. These are concrete omissions for the proposed stronger use.

The old summary further omits source/model/deployment/history/state fingerprints from its exported cost-pair interface. Even a genuine future diagnostic pair must not be joined to another run, state or backend by `case/mode/repeat` labels alone. This is a static interface finding; this review did not fabricate a successful GPU run or cross-run performance table.

## Minimum corrected boundary

The new reader should require a RUN SHA fixed by an external trusted publication or manifest, validate the successful parent and native process, bind explicit source/model/binary/library assets and actual loaded modules, bind JOB/inputs/plan/RESULT, and verify the exact planned record coverage and raw state/vector comparisons. A negative-fixture test should reach the relevant field check; an early “CPU is not eligible” rejection alone does not verify that these gaps were repaired.

The corrected output must preserve the actual measurement scope. The old target-operation timer includes batch/schedule work, original planning, synchronization and complete logits materialization. Prefix replay, state export, comparisons, file writes and next continuation lie outside that timer, but their cache effects condition the subsequent operation. The warmed/reset label is not proof of resident graph reuse; the observed CPU smoke still built one graph and reused zero for each measured operation.

Thus, even a future complete CUDA run can at most authorize a same-deployment, same-history, same-initial-state **capture-conditioned macro-operation diagnostic**. It cannot authorize clean serving costs, historical-R equivalence or stage costs after observing a partial result. `T([4,4])` cannot be split into invented conditional stage prices, and a missing terminal repair cannot be assigned zero cost. This release should expose no real stage-cost catalog and should abstain at the real controller interface.

## Preserved evidence and remaining limitation

The earlier native eager/deferred CPU comparison and the separate full-vector/state CPU width failure retain their independent raw audits. Tightening an artifact interface does not erase those observations. The wide CPU comparison remains a failure at its specific model/backend/history/shape, with zero timing records; the q1 smoke remains an implementation check, with no wide-cost pair.

The final published wrapper was validated by host-only checks and was not the wrapper snapshot that executed the original CPU smoke. Neither wrapper has a production GPU result in this evidence. All claims of approximately 5% service improvement, a new complete decoding method, generalized numerical compatibility and clean stage cost remain **OPEN**.
