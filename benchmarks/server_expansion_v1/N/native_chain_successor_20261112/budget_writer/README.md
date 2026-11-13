# Budget and raw transport integration preparation

This directory supplies standard-C++/POSIX components for the separately guarded native chain. It does not grant admission. `ProductionGate` is final and every native entry method permanently throws in this build. A concrete `ProductionGate&` must be required by actual backend/producer/capture factories, in addition to any optional `BudgetHooks&` accounting object. Passing a `DurableMockBudget` through a base interface must never unlock an actual llama/GGML call.

No model, vocabulary-only model, backend, native context, placement or forward was executed to test these components. Only `test_mock.cpp` and the independently authored standard-only mock executable were run. Their dynamic dependencies contain only libstdc++, libgcc_s and libc. The actual native-linked executables are not these test programs and must not be executed during CPU preparation.

## Boundary API

`hooks.hpp` defines synchronous hooks before backend initialization, model loading, context creation, placement, request opening, actual decode rows and named mutations, plus terminal request completion and poisoning. The actual backend reserves rows once immediately before each real decode; an outer lifecycle meter must not double-charge or replace actual widths with an optimistic append estimate. Native factories must test their concrete production gate before accounting and before any native/library side effect.

Request completion follows successful raw capture. A setup request can close immediately before opening its continuation; an episode-final request stays active through the actual final reset and reset capture. `before_mutation` deliberately rejects arbitrary post-finish mutations. An error after a previous row/mutation poisons the attempt; no second decode, fallback retry, new context or new request may hide that work.

## Durable mock coordinator

`DurableMockBudget` is explicitly a CPU mock coordinator, not a production admission verifier. Configuration supplies a fixed run/source identity, fixed wall deadline, all six request/row/backend/model/context/placement ceilings and the exact per-request row map. There are no granted defaults. A monotonic deadline prevents wall-clock rollback from extending the current process window.

The coordinator creates a fresh exclusive directory, `STATE`, immutable `MANIFEST`, locked `LOCK` and hash-chained `ledger.tsv`. Each reservation is validated, marked `UNCERTAIN`, written and fsynced before work. A short metadata/journal write is uncertain and is not retried. Only after commit and directory fsync is the uncertainty marker removed and the in-memory state advanced. Any validation, deadline or I/O failure poisons the coordinator, including a row-ceiling rejection after earlier rows. Failed consumption is never refunded.

Opening an existing directory/STATE for execution always fails, including a sealed attempt. `inspect()` only locks and replays immutable identity, sequence, SHA-256 chain and counters. It never issues a permit. In-flight STATE, an unsealed run, partial record, checksum conflict, `UNCERTAIN` or `POISONED` requires manual reconciliation and cannot resume. Abrupt process exit leaves charged requests/rows and active identity visible. A completed mock ledger is sealed for inspection only. New CPU fixture directories do not authorize a new real experiment or reset any canonical A5000 ledger.

## Streaming raw transport

`StreamCapture` receives a trusted absolute non-symlink root, unique capture ID, exact identity, explicit byte/file/chunk bounds and accounting hooks. It creates no capture files before the gate/mutation check. It streams caller-owned host chunks synchronously, validates finite F16LE/F32LE scalar bits and shape/length, hashes all bytes and writes/fsyncs immutable files. The caller must keep the host view stable until the call returns and must fence actual native reads before supplying it. No model buffer pointer survives the call; no full-capacity K/V copy is retained in this writer.

`begin_tensor`, `append_host_chunk`, `finish_tensor` produce full-byte descriptors with explicit dtype, dimensions, axes, byte length and transport SHA. The caller is responsible for extracting actual native layout and active positions. `canonical_numeric=true` identifies the declared numeric transport format; it does not prove that the native source, positions or arithmetic are correct. In particular, native transposed-V columns must never be labeled token rows.

`begin_blob` can preserve an actual serialized native state packet as `OPAQUE_NATIVE_STATE`. It is explicitly noncanonical and cannot replace the full-vector/active-KV numerical comparison. If a future adapter keeps both an opaque packet and a canonical reconstruction, their duplicate disk cost needs a new complete capture calculation; it cannot silently inherit an old bound.

The writer publishes caller metadata as `SNAPSHOT.json`, then a commit-last raw transport receipt. Its own schema always says `native_qualified=false`; the writer neither fabricates a valid native snapshot nor certifies the caller's JSON. Raw-file, marker, metadata, pending/complete hardlink, ownership and reset files all count toward the actual file/storage bound. The old proposed32 files/request is not automatically established by this generic transport layout.

Any short/zero/failed raw write, length/shape/nonfinite rejection, constructor collision or commit error preserves partial files, marks uncertainty and poisons accounting. Positive raw short writes may finish synchronously; zero/invalid writes stop. A COMPLETE transport filename alone is insufficient: consumers also require no capture uncertainty, valid native snapshot/coverage evidence and a clean canonical ledger. Failed final fsync cannot be promoted to successful qualification.

## CPU evidence and limits

`CPU_MOCK_RECEIPT_02.json` binds the current tested header/source hashes and ELF identities. The component suite passed52 checks both normally and with `-DNDEBUG`, and current-header independent source `review/independent_budget_writer_mock.cpp` passed8 separately authored groups. `IPC_MOCK_RECEIPT.json` adds17 normal and17 NDEBUG private-broker groups; `CLI_MOCK_RECEIPT.json` records syntax/identity-only validation of the standalone CPU coordinator. The earlier `CPU_MOCK_RECEIPT.json` is retained as a historical epoch, not a current-source certificate. The first compile attempt failed a `-Werror=misleading-indentation` check; explicit braces fixed it in a new source snapshot, while the failed snapshot and partial mock artifacts were retained. No native-linked binary was run to obtain any of these results.

These tests cover SHA known vectors, permanent native denial, durable reservations, active-request/row/placement ceilings, monotonic timeout, process-crash inspection, no reentry/refund, short journal/fsync failures, stable raw bytes, zero active-KV transport, nonfinite rejection and partial writer failures. They do not establish real native budget enforcement, exact model placement, runtime memory peaks, actual active-KV extraction, numerical qualification or elapsed GPU performance. The real entrypoint wiring, admitted canonical coordinator and full source/model/reference gates remain separate requirements.
