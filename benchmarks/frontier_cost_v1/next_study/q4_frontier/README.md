# A bounded q4 reference frontier diagnostic

This is a new CPU legality diagnostic, prepared after the existing q1-reference
test rejected q2. That rejection did not test whether q4 and q8 can share a
stronger local execution contract. The present reference is explicitly the same
CPU deployment executing q4+q4. It does **not** inherit the historical paper's R
qualification, production correctness, or a performance claim.

Here q4 and q8 mean four or eight token rows in an operation. They do not denote
4-bit or 8-bit quantization: this fixed fixture uses F32 weights and F16 KV.

## Frozen panel and required observations

The input histories are the existing controlled synthetic cases of length 248
and 252. Prefix tokens are `(3 + 7*i) % 128`, operation tokens are
`(P + 5 + 11*i) % 128`, and the common continuation token is 37. Every arm starts
from its own fresh context with the same width-32 LOCAL prefix producer.
All histories, operation rows and continuations are **forced known tokens**.
They do not assert natural acceptance, all-accepted sampling, EOG, CAP, or the
probability of such events.

Within each history, these arms run in the listed order:

| Arm | Native operation schedule | Active final frontier | Shared full vocabulary rows | Comparison |
| --- | --- | --- | --- | --- |
| macro_reference | q4 + q4 | P + 8 | 8 | Explicit diagnostic reference |
| macro_reference_repeat | q4 + q4 | P + 8 | 8 | Own-path repeat vs reference |
| macro_wide | q8 | P + 8 | 8 | vs reference |
| frontier4_reference | q4 | P + 4 | 4 | Explicit short reference |
| frontier4_wide_trim | q8, then trim | P + 4 | First 4 | vs short reference |
| frontier5_reference_materialize | q4 + q1 | P + 5 | First 4 | Explicit forced materialization reference |
| frontier5_wide_trim | q8, then trim | P + 5 | First 4 | vs materialization reference |

The common contract contains full vocabulary vectors, serialized **active**
sequence state and native dense geometry. It checks the initial prefix, the
shared requested output rows, the common active final frontier and one common
forced q1 continuation, including that continuation's vector and state. State
export contains the active sequence's cells; inactive dead KV bytes are outside
this contract. Native geometry includes active count/positions, extent and the
actual native append guard requiring head == next.

For frontier5, the q1 input physically materializes the fixed fifth token.
The original frontend requests and copies that q1 output, and this diagnostic
saves it. **The fifth vector is an additional diagnostic, not a shared consumer
obligation.** A difference in it alone cannot fail the main contract. All actual
operation rows still use the unmodified frontend's requested-output mask.
Consequently, this is a common-frontier confluence diagnostic, not production
q8 full-request-mask equivalence. The worker that consumes all k+1 rows is not
certified by projecting this comparison to four rows.

Comparison uses exact bytes and exact native geometry, with finite full primary
vectors required. All generated vectors, including unconsumed extras, are saved
for inspection. A finite check over extras is reported only as a diagnostic.
There is no tolerance-based numerical success, argmax-only substitution, or
token-only criterion.

## Global fail-stop and exact resource ceiling

A mismatch or guard failure stops the entire job. The next arm and subsequent
history are not run. Checks occur after the initial capture, shared operation
vectors, common frontier and continuation. If shared vectors already differ,
no trim or continuation is attempted. All available capture bytes and the
failed check remain in the output directory. There is no automatic retry.

If macro_wide fails its 8-row contract, frontier4 and frontier5 are **NOT_RUN**.
They do not inherit failure: only later rows could differ. A valid macro also
does not automatically qualify either shortened frontier or q1 materialization.

For each history P, seven prefix producers cost `7 * ceil(P/32) = 56` decode
calls; operations and continuations add 17 calls. Rows are `7P + 56`. The full
upper bound is therefore:

| Resource | Maximum |
| --- | ---: |
| Tiny F32 model loads | 1 |
| Fresh contexts | 14 |
| Native decode API calls, including all prefixes and continuations | 146 |
| Target rows, including all prefixes and continuations | 3,612 |
| Trim calls | 4 |
| Content-addressed raw blob bytes | 256 MiB |
| Owned native child wall limit | 180 seconds |

The decode-call ceiling counts outer native decode API attempts. Physical
decode widths/calls are also recorded and independently checked; the frozen
LOCAL profile maps each outer call to one physical group. Prefix calls are
counted using the native `target_prefill_*` fields in addition
to `target_*`. Reserved and observed calls/rows are separate, so an exception
does not silently count unexecuted work as observed. Model loads and trim calls
are separately counted. The runner can kill only its own native child and
preserves partial output on timeout or failure.

A native dense-append geometry rejection is reported separately from vector
or active-state byte mismatches. Read-only failure observations include used
cells, occupied end, extent and the native append requirement result. An empty
requirement result does not identify a specific hidden head value: that native
guard also checks stream, shift, SWA and dense mapping conditions.

No timing phase is present. The existing unmodified frontend internally calls
its clock, but this wrapper neither reports nor interprets those timings.
The runner's child wall duration is exclusively a timeout/resource receipt.
No service speedup, stage cost, broad CPU/GPU transfer, or 5% target is admitted.

## Provenance and preparation

The model is the existing untrained seed-178, two-layer, vocabulary-128 F32
fixture, SHA-256
`e4b4f329077cc07036a307566f652a35b10e6f41c3b7a98478f2dfca4b09c044`.
The wrapper includes the unchanged matched-cost probe, SHA-256
`4cc4c7114262bea71957e95478e963486a95cc416a0465d37bb897e971f838ec`,
from the previously published study. Its old main and timing functions are
not called. The build verifies all 3,539 original numerical-source members,
the complete reconstructed frontend and the four retained CPU libraries.
No numerical source or production gate is edited.

`protocol.py` contains the full fixed panel and identities. `PLAN.json` is a
host-only rendering. The eight public files can live together at any repository
path; dependencies are passed explicitly. Importing Python modules, printing
the plan, running host checks and compiling do not load a model.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 run.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_protocol -v
PYTHONDONTWRITEBYTECODE=1 python3 build.py --core CORE --frontend FRONTEND \
  --lib-dir CPU_LIB_DIR --legacy-dir PINNED_MATCHED_COST_DIR --out FRESH_BUILD_DIR
```

The build runs the C/C++ compilers and `ldd` only, not the produced binary.
Execution must wait until the source commit is published and independently
verified. The root creates a publication JSON with `commit` (exact 40-hex Git
commit), `remote_source_verified: true`, and `sources` (the exact eight-file
bytes/SHA-256 manifest). It then explicitly authorizes the single bounded run.
The runner checks that publication, the build, current sources, model and
dependencies all match before creating the native process.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 run.py --execute --build FRESH_BUILD_DIR \
  --model EXISTING_F32_MODEL --publication ROOT_VERIFIED_PUBLICATION.json \
  --out FRESH_RUN_DIR
PYTHONDONTWRITEBYTECODE=1 python3 verify.py FRESH_RUN_DIR --out FRESH_VERIFICATION.json
```

Only the second command's offline verifier computes the reviewable raw-byte
comparison receipt. It does not accept a recorded PASS flag as proof. It checks
blob hashes and contents, complete vector dimensions, exact native geometry,
stage/global accounting, source/library/model bindings, first-failure ordering
and absent branches. All reference captures are labeled as such; qualification
belongs only to the tested comparisons and forced continuations.
