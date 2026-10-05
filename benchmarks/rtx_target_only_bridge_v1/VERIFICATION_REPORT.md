# Independent offline verification

Status:PASS. Source-bound raw verifier reconstructed171/171 formal records,
checked1596 per-run files by SHA256/length, and recomputed
every complete-array, endpoint/joint, task-unit, first-divergence, positional
difference, repetition-stability and historical-bridge table. It imports no
controller capture/parser/comparison helper, and does not trust controller PASS
flags. Engineering12 is separately reparsed; diagnostics0, failed attempts0.

Exact cohort/queue/condition/order checks passed for19tasks x3conditions x3repeats.
Input prompt bytes and every raw prefill ID match the pinned tokenizer/input contract.
Inclusive EOG/cap128, runtime generation counts, raw decoded byte pieces and complete
transcripts agree. Complete selected-attempt file inventories refer to one attempt
only, with append-only hash-chained ledger start/success bindings. No abandoned
capture was combined with a later result. Seven negative tests cover early EOS,
cap overshoot/EOG128 dual markers/missing markers, duplicate keys, mixed attempts
and truncated capture. Separate strict-JSON checks reject duplicate object keys.

Additive settings audit checked183 engineering/formal
records and122 native handoffs: raw F16-K/V contexts,
non-unified KV, target greedy settings, no warmup/cache reuse, native draft k2/
explicit24/24 thread flags, and original first-sample -> pending -> transfer ->
continuation sample ordering. Every logged model numerical threadpool is24;
raw system-info reports target24/batch24. HTTP housekeeping threads23 are separate.
Actual CUDA0 target37/37 and native draft29/29 offload, ctx4096/batch2048/FAoff,
condition-specific UB contexts and fresh cached-token counts are directly checked.
Every native handoff retains byte-identical source-before/destination/source-after
snapshots, full151936-float pending logits, positions and sampler clone metadata.
Opaque sampler bytes are unobserved. U2 has only target arguments/load/context and
no draft-load/speculative-init or transfer variable; no arbitrary internal-call
tracing claim is made.

Post-matrix local hash readback passed all80 model/data/runtime/
native/tokenizer asset bindings, and GPUUUID/driver/OS match preparation. Source,
freeze/protocol/cohort/input/asset bindings remain intact. Retrospective lead was
recomputed using pinned oldU2/reference arrays and114 CAS-restored old native logs;
oldN0/N1 arrays also match the pinned independent neutral export. HistoricalU2
12thread versus fresh24thread is observational, not thread causality.

Content-hash consistency and Git object membership do not independently authenticate
omitted weight/runtime bytes, original physical execution, or absolute experiment
time. Asset hash checks are local, not independent model reruns. No GPU was used by
the offline verification, no outcome retry or numerical code repair occurred.

## Archive/delivery checks

Raw evidence packaging and all-part remote readback/clean restoration are completed
separately after this pre-archive report snapshot. See ARCHIVE_RECEIPT.json,
REMOTE_READBACK.json and DELIVERY_RECEIPT.json for their exact final coverage.
Those receipts are later Git objects; they are not claimed to be inside the raw
archive they describe. Restoration rechecks parts, joined archive, every CAS blob
and logical file, then repeats the frozen formal verifier/settings audit. Compared
scientific result fields must remain exactly equal. Git-backed raw parts have no
Actions-artifact expiry, while access depends on repository permission/availability.

The additive delivery builder completes the inventory for every frozen file,
including.gitignore and the copied ledger.JSONL. This is packaging-only; frozen
runner/parser/protocol bytes and all actual execution remain unchanged. The original
frozen builder is retained; no failed model batch or formal restart is involved.
