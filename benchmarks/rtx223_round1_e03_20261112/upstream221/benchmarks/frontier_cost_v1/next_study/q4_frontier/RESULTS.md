# q4 reference frontier diagnostic: bounded CPU result

**The preregistered diagnostic passed both controlled histories.** In this
fixed synthetic CPU deployment, q8 matched q4+q4 on all eight shared full
vocabulary vectors, active state, native geometry and the common forced
continuation. The q8-to-frontier4 and q8-to-frontier5 comparisons also passed
their separately specified contracts. This establishes a small, concrete
legality result worth following up; it establishes no service speedup or
production qualification. The exact observations and receipt identities are
in [PUBLIC_RESULT.json](PUBLIC_RESULT.json).

Here **q4 and q8 mean token-row widths**, not 4-bit and 8-bit weights. The model
is the retained untrained, two-layer F32 synthetic fixture with vocabulary 128;
KV storage is F16. The backend is CPU, with one thread, LOCAL lowering,
`n_ubatch=32`, `n_ctx=1024`, non-Flash attention and a fixed width-32 prefix
producer. The histories have lengths 248 and 252 and use known forced tokens.
The continuation is the same forced token 37. No natural acceptance event was
observed or inferred.

## Preregistered contracts and observed results

The source was committed and its eight files checked against remote Git blobs
**before** the single native run:
[`ef2766327e7821fe188d1ad788b2c3b05531eb9a`](https://github.com/leecdiang/HeteroSpec/commit/ef2766327e7821fe188d1ad788b2c3b05531eb9a).
The [protocol](PLAN.json) and [method description](README.md) remain unchanged
after execution. Each arm used a fresh context and the same prefix producer.
The q4+q4 reference is explicitly a same-deployment diagnostic reference; it
does not inherit the paper's historical R qualification.

| Comparison | Shared operation vectors | Active frontier | P248 | P252 |
| --- | ---: | --- | --- | --- |
| Independent q4+q4 repeat vs q4+q4 | All 8 rows | P + 8 | PASS | PASS |
| q8 vs q4+q4 | All 8 rows | P + 8 | PASS | PASS |
| q8 trimmed to 4 vs q4 | First 4 rows | P + 4 | PASS | PASS |
| q8 trimmed to 5 vs q4+q1 materialization | First 4 rows | P + 5 | PASS | PASS |

Every PASS includes the full shared vocabulary vectors, byte-identical active
sequence state and exact native geometry at the initial and common final
frontiers, plus the full vector, active state and geometry after the common
forced continuation. The q4+q1 reference materializes the fixed fifth input;
it does not claim that this input was naturally accepted. Geometry checked
dense position/sequence ownership, active extent and the native append guard.
Inactive KV cells outside the active sequence are not part of the state
contract. [PUBLIC_RESULT.json](PUBLIC_RESULT.json) records each primary check.

The eight comparisons include two own-path repeats and six comparisons across
schedules or frontiers. They compare **56 full vocabulary row pairs**, or 7,168
float-value pairs, **24 active-state pairs** and **24 native-geometry pairs**.
These are counts of comparison obligations, not independent statistical
samples or a general correctness proof.

## The fifth vector differs, while the specified consumer contract passes

This distinction was fixed before execution. In the frontier5 case, the
reference q4 call supplies the four shared consumer outputs, then q1
materializes the fifth input into state. The unmodified frontend requests and
copies the fifth output. The diagnostic saves that output but does **not**
make it an additional shared consumer obligation.

The fifth vector differs between q4+q1 and the q8 path in both histories:

| History | Differing float entries / 128 | Full fifth vector equal | Argmax equal, diagnostic only | Maximum absolute difference |
| --- | ---: | --- | --- | ---: |
| P248 | 117 / 128 | No | Yes, token 13 | 3.5762786865234375e-7 |
| P252 | 128 / 128 | No | Yes, token 14 | 3.889203071594238e-6 |

`differing_float_count` counts entries with unequal four-byte float
representations; the numerically unequal-entry counts are also 117 and 128.
These diagnostics were recomputed offline from the saved 512-byte vectors.
All generated operation vectors were finite. Raw-vector hashes and the exact
values above are bound in [PUBLIC_RESULT.json](PUBLIC_RESULT.json).

**Equal argmax does not establish full-vector contract compatibility.** These
fifth-vector differences would matter to a consumer that requires that output.
Their exclusion here was a preregistered consumer boundary, not a relaxation
chosen after observing the result. The production worker's full k+1 requested
output contract has not been qualified. This result cannot be used to remove
an existing output obligation, weaken the paper's existing contract, or change
the original production gate.

## Work and evidence accounting

One owned native child was launched, with no retry. It exited successfully
without reaching its 180-second resource limit. The complete frozen panel ran:

| Resource | Observed | Preregistered maximum |
| --- | ---: | ---: |
| Synthetic model loads | 1 | 1 |
| Fresh contexts | 14 | 14 |
| Outer native decode calls, including prefixes and continuations | 146 | 146 |
| Physical decode groups | 146 | 146 implied by the frozen LOCAL panel |
| Target rows, including prefixes and continuations | 3,612 | 3,612 |
| Trim calls | 4 | 4 |
| Content-addressed raw bytes | 7,385,976 | 268,435,456 |
| Unique raw blobs | 30 | Subject to byte ceiling |

Reserved and attempted calls/rows match exactly. The frozen offline verifier
recomputed blob identities and byte comparisons, complete vector dimensions,
finite diagnostics, native geometry, both directions of stage/counter
accounting, physical width histograms, per-arm trim obligations, source/model/
library bindings and fail-stop order. It returned `verified: true` with
`native_status: DIAGNOSTIC_PASS`. The independent reviewer separately inspected
the protocol before execution; independent post-run audit is recorded by the
parent study rather than presumed from this producer's verifier invocation.

The numerical source, frontend, four CPU libraries, model and eight published
diagnostic files remained bound to their frozen identities. No numerical
source or production gate was changed. Six host-only admission/receipt tests
also passed before model execution. The original native receipts, job, build,
binary, logs and raw blobs are preserved in the private evidence bundle. Only
the explicit public allowlist is intended for Git.

## Research consequence and remaining gates

The prior q1-reference failure could not answer whether q4 and q8 share a
valid execution path. This run supplies positive evidence for that distinct
question in the fixed CPU fixture. It also demonstrates why operation outputs,
active-state materialization and future consumers need separate obligations:
the shared four outputs and state/continuation can agree even when an extra
physically produced output differs.

The result supports investigating a consumer-aware frontier policy as a
candidate mechanism. It does not authorize a production policy to discard a
requested row. The next study must derive its consumers from the actual worker
and request lifecycle, then qualify the resulting contract against the chosen
reference before any cost or service comparison. The two forced histories,
one continuation per path and F32 synthetic model do not establish natural
acceptance, trained-model behavior, GPU behavior, arbitrary frontiers, other
layouts or lengths, or historical R compatibility.

No operation or service timing was admitted. Reducing the number of native
calls in one operation schedule is an observed work fact, not a measured speed
improvement. State capture also conditions this diagnostic and is not a clean
serving benchmark. The 5% target therefore remains unproven. A follow-up must
first pass the real-model/request contract, then obtain matched-state costs
and complete service measurements against the strongest qualified baseline.
