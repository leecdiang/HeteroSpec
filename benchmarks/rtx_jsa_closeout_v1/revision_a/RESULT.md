# RTX PR140 amended closeout — final result

**CLOSED: mixed finite-panel disposition.** SmolLM2 supports an incremental QB layout gain; Qwen is noise-limited; Llama supplies a deployed-reference counterexample and has no qualified cost panel. Every NATIVE_FAST family is numerically ineligible for timing. No further native experiment is part of this study.

Study UUID: `e5c03228-9eb9-4198-8f14-a7d279d08afa`. Execution freeze: `87570e6ac4c3f5060b5086969dfc5214e7b17da2`; primary implementation froze at `df4fd24ba77a904ceb7646c480f298b1a24c7783` before held-out selection. Final CPU readback rechecked all **7,729 file pins** and the authenticated remote registration. [Post-execution receipt](results/POST_EXECUTION_FREEZE.json).

## Primary cost result

Each qualified family contributes all 12 inputs × four sessions × R/PQ_A/PQ_B/QB, with one separately charged same-input warmup and one measurement per fresh worker. Ratios use geometric means of paired block ratios, with equal input/session weights. The dual control is the arithmetic mean of PQ_A and PQ_B within each block.

| Family | E1 disposition | QB / dual PQ | Layout time reduction | Max input-aggregate A/A imbalance | Required reduction | Final disposition |
|---|---|---:|---:|---:|---:|---|
| Qwen | All 12 inputs qualified | 0.967781 | 3.2219% | 4.7781% | >4.7781% | QUALIFIED_NOISE_LIMITED |
| SmolLM2 | All 12 inputs qualified | 0.930056 | 6.9944% | 1.5014% | >2% | SUPPORTED_FINITE_PANEL_GAIN |
| Llama | Failed first long input | — | — | — | — | Reference counterexample; all timing NOT_RUN |

| Family | Session 0 | Session 1 | Session 2 | Session 3 | QB / R | Dual PQ / R |
|---|---:|---:|---:|---:|---:|---:|
| Qwen | 0.975669 | 0.960604 | 0.967773 | 0.967138 | 0.560577 | 0.579239 |
| SmolLM2 | 0.928001 | 0.929086 | 0.931868 | 0.931273 | 1.007007 | 1.082739 |

Both families favor QB over dual PQ in each session aggregate. Qwen's reduction does not clear its registered A/A threshold. SmolLM2 clears its engineering screen, while its complete QB request remains **0.7007% slower than R**; its layout improvement does not establish an overall speedup over serial reference execution. Qwen's overall QB/R reduction is 43.9423%, separate from its unresolved incremental layout benefit. No confidence interval, bootstrap, outlier deletion, session extension or successful-subset estimate is used.

| Family | Short QB / dual PQ | Medium | Long |
|---|---:|---:|---:|
| Qwen | 0.952969 | 0.970605 | 0.979964 |
| SmolLM2 | 0.943906 | 0.928355 | 0.918087 |

All [36 input rows](results/INPUT_RESULTS.csv), [144 core block rows](results/BLOCK_RESULTS.csv), [768 warmup/measurement rows](results/TIMING_RECORDS.csv), session reversals, unstarted rows and exact [estimates](results/ESTIMATES.json) are retained. QB is not faster in 8/48 Qwen blocks and 0/48 SmolLM2 blocks; these blocks remain in the aggregates. Llama's eight passing earlier cells are not a replacement cost panel. Actual surviving-family order was Qwen→SmolLM2, SmolLM2→Qwen, Qwen→SmolLM2, Qwen→SmolLM2 after frozen conditional skipping. Four core arm positions remain balanced across the four sessions for every input.

## Reference and comparator counterexamples

| Stage | Family / arm | Input | First different output index (zero based) | Disposition |
|---|---|---|---:|---|
| Old-input calibration | SmolLM2 / FAST | GSM8K/test/111 | 8 | FAST ineligible; no held-out FAST or FAST timing |
| Old-input calibration | Llama / FAST | GSM8K/test/111 | 22 | FAST ineligible; no held-out FAST or FAST timing |
| Held-out E1 | Qwen / FAST | GSM8K/test/70; 75 prompt tokens | 68 | Heavy/count stable; FAST transfer failed; all FAST timing NOT_RUN |
| Held-out E1 | Llama / PQ and QB | CodeContests/valid/108; 737 prompt tokens | 81 | Both disagree with R; remaining three inputs and all Llama timing NOT_RUN |

Llama R/PQ/QB heavy/count pairs are internally stable on the counterexample, and all outputs reach cap128. PQ and QB agree in endpoint, complete decision-vector bytes and canonical causal trace, while both differ from deployed R. This identifies reference transfer failure; no numerical root cause or QB-specific fault is asserted. Full endpoints, EOG flags, terminal semantics and worker locations are in [COUNTEREXAMPLES.json](results/COUNTEREXAMPLES.json). All FAST timing is unqualified, so this study supplies no qualified cost comparison against that stronger route.

## Inputs and observed geometry

The approved amendment adds 117 original CodeContests validation descriptions at snapshot `802411c3010cb00d1b05bad57ca77365a3c699d6`; attribution and CC BY 4.0 non-code licensing are retained. The complete exposure audit excluded **579 tasks** and resolved all audited archive/text containers before selection. [Input manifest](INPUT_MANIFEST.json), [exposure audit](FINAL_EXPOSURE_AUDIT.json), [container coverage](COMPLETE_CONTAINER_COVERAGE.json).

The sealed panel has **36 family/input cells /21 distinct tasks**; E1 attempted **33 cells /20 distinct tasks**. There are 32 reference-passing cells, one reference-failing cell and three NOT_RUN cells. Exactly four inputs per family were selected in each unchanged 64–192 /256–448 /640–832 formatted-token stratum. Short inputs are GSM8K math; medium and long inputs are CodeContests code. **Domain and length are confounded**; stratum ratios do not isolate a length effect. Cross-family reuse is explicit. There is no inference about training-set novelty, task accuracy or 8K/32K contexts.

| Family | Sealed prompt range | Observed QB cells | Continuation q values observed | Continuation visible-key range | Natural early-EOG cells |
|---|---:|---:|---|---:|---:|
| Qwen | 71–811 | 12 | 1,2,3,4 | 72–938 | 1 |
| SmolLM2 | 75–797 | 12 | 1,2,3,4 | 76–924 | 3 |
| Llama | 77–737 | 9 | 1,2,4 | 78–864 | 2 |

These are observed heavy-capture ranges, not claims that every cell exercised every width. Llama q=3 is unobserved. All natural early-EOG cells remain. [E1_GEOMETRY_COVERAGE.json](results/E1_GEOMETRY_COVERAGE.json) records each planned input/arm, output length/stop, first/middle/last target layer, actual q, caller rows, physical extents, visible-key ranges, Q/K shapes/strides, masks and native event counts. The independent audit reconstructs mask visibility from full F16/F32 bytes, verifies logit ownership and captures all requested rows, including rejected verification rows. [E1 completeness gate](results/E1_CAPTURE_COMPLETENESS.json), [raw audits](results/RAW_AUDITS.json), [independent E1 reconstruction](results/INDEPENDENT_E1.json).

## Observation and clock contract

PR104's original three-family k3 resident HTTP recipe remains: Q8_0 weights, F16 KV, context1024, target UB4/draft UB1, original phase mask3 for PQ/QB, serial R UB1, non-flash primary execution, seed123 greedy, EOG/cap128, no prompt-cache reuse and no concurrent model workers. Input formatting/templates and numerical-library bytes are pinned. Loaded executable/DLL receipts are verified for every worker. The timer covers native nonstreaming request encoding/submission through full response parsing and endpoint validation; load, warmup, file hashing and disk writes remain separate. Timed counts mode has no heavy vector/mask writes, added observer synchronization or ETW profiling.

Calibration's 24 workers contain incorrect append-offset metadata. Their complete vector/mask streams are intact and independently reconstructible; all original metadata failures remain in [RAW_AUDITS.json](results/RAW_AUDITS.json). A prospective heavy-only V2 correction added two seek-to-end calls before held-out selection. E1 then required strict declared offsets and full requested-row ownership; there is no E1 offset recovery. No calibration model request was retried. The original observer, scalar verifier, freezes and receipts remain.

The prospectively frozen [causal-trace rules](CAUSAL_TRACE_RULES.md) exclude only the draft sampler's unused return ID from causal equality: draft-simple actually consumes sorted candidate[0]. Raw return IDs are retained, alongside actual proposal IDs, full vectors, top candidates, target decisions, accepted/correction/bonus events, pending ownership and KV reconciliation. This is not a claim of byte-identical unconsumed sampler returns. CPU NumPy batching remains outside native execution/the request clock and matched the preserved scalar audit on all 24 old workers, all 65,536 F16 bit patterns and 65,543 F32 cases. [CPU equivalence](CPU_AUDITOR_EQUIVALENCE.json), [CPU finalizer fixture](CPU_FINALIZER_TEST.json).

## Complete resource and slot ledger

| Stage | Workers | Requests | Owned native seconds |
|---|---:|---:|---:|
| Old-input calibration | 24 | 48 | 288.097030 |
| E1 qualification | 101 | 202 | 1,659.030477 |
| E2: 384 warmups +384 measurements | 384 | 768 | 5,015.223266 |
| Total this UUID | **509** | **1,018** | **6,962.350772** |
| NOT_RUN within maximum | **379** | **758** | — |
| Registered maximum | **888** | **1,776** | **54,000**, including 900 cleanup reserve |

All 509 exits are verified, with no watchdog failure, missing lifetime, unfinished charged request or raw-capture audit failure. Windows exit code1 follows the registered controlled termination after requests; exit verification and watchdog status determine cleanup success. Maximum observed worker lifetime is 44.207315 seconds, below the 600-second timeout. The frozen native bounds are 24 GiB RSS, 64 GiB run-root storage, 16 GiB free-space headroom and 85°C pre-worker temperature gate. Peak RSS and continuous peak GPU temperature are not measured quantities here. Final native raw inventory: **9,094 files /13,998,764,924 bytes**. CPU preparation/audit/transport remain separate from these native lifetimes; their original receipts and reservations are preserved.

Storage relocation retained the same UUID, all calibration bytes and all charges. Historical reference E2 charges remain separately recorded at 324 workers /1,620 requests /4,968.994058 seconds; the prior S0 UUID `02760d19-15c7-4bd8-ba48-28df4a7854af` remains six vocabulary-only processes /zero model requests /40.470422 seconds. These are inherited ledger components, not a claim to summarize every historical project cost. No old session is pooled into the new estimates.

[Resource ledger](results/RESOURCE_LEDGER.json), [all 1,776 request slots](results/ALL_1776_SLOTS.json), [all 888 worker slots](results/ALL_888_WORKERS.json), [actual charge order](results/ACTUAL_EXECUTION_ORDER.json), [process lifetimes](results/PROCESS_LIFETIMES.json), [verification](results/VERIFICATION.json) and [raw SHA256 inventory](results/RAW_FILE_MANIFEST.jsonl) make every optional, failed and unstarted slot visible.

## Evidence and paper disposition

[RAW_ACCESS.json](RAW_ACCESS.json) is the final access descriptor for complete raw vectors/masks/native traces, original requests/responses, stdout/stderr, host/module/cleanup receipts, registrations, sources and lossless archive manifests. Model weights and third-party numerical DLL bytes are excluded from transport; their frozen identities remain. [PAPER_ADDENDUM.md](PAPER_ADDENDUM.md) states the supported scope and unresolved reference/strong-baseline limitations.

The independent CPU reconstruction is reproducible on the registered Windows host, using a fresh output directory:

```text
python -B benchmarks/rtx_jsa_closeout_v1/revision_a/finalize.py --config benchmarks/rtx_jsa_closeout_v1/revision_a/F0B_EXECUTION.json --out <fresh-output-directory>
```

`finalize.py` is the same source frozen before E1/E2. `derive_results.py` adds readable coverage/counterexample/resource summaries; it launches no native process. Final result/delivery artifacts were added only after all timing ended. The matrix is closed without a candidate patch, tolerance change, input refill, model/k/precision/hardware expansion, merge or manuscript/arXiv submission. AI assistance: Codex implemented and executed this authorized finite closeout and its CPU audit/delivery tooling.
