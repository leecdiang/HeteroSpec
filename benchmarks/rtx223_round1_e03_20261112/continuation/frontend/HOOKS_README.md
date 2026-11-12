# Native evidence and host timeline hooks

Latest generated source: `hooked_frontend_v7/`, bound by `HOOK_SOURCE_v7.json`.
Earlier generated versions and their build records remain separate. Generation
reads the copied, identity-verified dynamic request prototype and the current
actual-q8 capture header; it does not modify the historical frontend or cores.

The new request recorder starts before the request guards/reset and ends after
final target/draft synchronization, terminal capture, result construction and
teardown. Context operations record host spans for reset, target/draft prefill,
draft, verification, sampling, synchronization, reconciliation and state
evidence; the target planner records planning. Nested spans must be partitioned
exclusively. The complete enclosing interval remains authoritative. Capture
costs are included when capture is enabled and are not clean serving prices.

`diagnostic_costs.py` accepts the additional `state` category in a private copy
of the host cost reader. It always reports `performance_admitted: false` and
does not expose service pairing. Its two focused CPU tests pass ordinary Python
and `-O`. They check nested state/sync attribution and reject using this
capture adapter for a clean record. Existing native/CPU qualification results
are not rerun by those tests.

Every requested output is copied immediately after its decode, before any next
decode/trim can replace the underlying logits. This includes the final draft
proposal's output even if the logical request never samples it. Files and
records contain all vocabulary floats, owner/generation, request row position,
mask, call/phase and SHA-256. Sample files are additionally retained for the
consumer trace. The state capture covers target and draft initial state,
target state before each verify, both untrimmed states, committed states after
trim and terminal state, without adding a decode to materialize a pending
terminal token.

Native geometry records actual dense cell occupancy, positions, exclusive
sequence-0 ownership, shift status and attention extent. The private physical
head is not directly read. When a one-row `phase_append_requirements` probe
succeeds, its bound native predicate proves head equals the recorded used
count; otherwise the head field is null and must not pass head qualification.
This is capture evidence, not clean dispatch/placement admission.

Every Context has a monotonic owner ID/generation and an invalid flag. Reset,
decode, sampling and trim failures poison that Context. A request guard also
poisons both resident owners on any unsuccessful exit, including failures in
capture, guards or reconciliation. Fresh-owner raw pointers are nulled before
explicit teardown so an exception after teardown cannot dereference a freed
owner. `--selftest` checks the shared owner-status and timeline components
before DLL/backend/model initialization; it also tests the exact capture byte
ceiling and one-byte-over refusal without writing files. `--selftest-json PATH`
additionally writes one fresh multiline UTF8 JSON fixture through the actual
global JSON writer, rereads it in binary mode, checks exact encoded/file/
reserved/written byte equality and refuses one extra byte at the exact limit.
It retains the fixture and performs no model/backend/GPU work.

Every instrumented binary/JSON evidence write reserves bytes before opening
the output. Reservations survive failed writes. The same counter covers the
actual-q8 capture header and legacy sample/capture.txt writers. JSON uses binary
output mode so Windows newline conversion cannot exceed the reserved byte count.
The job must
supply `evidence_capture_byte_reservation` in `(0, 2 GiB]` before backend/model
initialization. Replaced JSON versions count cumulatively, which is
conservative relative to final retained file size. Stdout/stderr remain an
external supervisor responsibility, and profiling is refused by this adapter.
The parent must enforce the shared budget family's remaining capture allowance
and retain any failure even if the child lacks bytes for its own failure JSON.

The actual-q8 capture callback is enabled only by an explicit job contract.
An optional Capture owns its scope; callback handling precedes the historical
capture-only observer, and successful job completion requires the requested
capture to have actually completed. The before/after loaded-module paths are
also recorded with file sizes and disk SHA-256. These are hashes of files at
loaded paths, not hashes of executing memory. External source/executable/model/
DLL identity admission remains required.

`read_hooks.py` is an offline byte/state reader. It requires an external frozen
row set, vocabulary, cycle count, stage geometry and metadata hashes, and parses
raw native F16 state with the strict reader. It cannot invent a frozen real
reference, qualify C's runtime integration, certify all 66 native cases,
attest actual dispatch or count every backend kernel launch. Those remain
separate gates. A compiled binary or successful `--selftest` supplies no model,
GPU correctness, acceptance-chain or performance result.
