# B570 producer × consumer boundary result

Completed 2026-10-29 (Asia/Shanghai). **152/152 primary requests executed,
B0=32 and B1=120; zero model-request retries, technical failures or missing coordinates.** All 32 controls
qualified before B1. The final independent CPU audit reports COMPLETE_ACCOUNTING,
no errors, 96 actual restored boundaries rehashed, and all 88 observer/own-path
comparisons passing. No additional model forwards, operator replays, or formal
performance measurements were added.

**Producer state changes local consumer reference eligibility in this bounded
clean-receiver experiment.** On two new long inputs, natural C1 preserves the same
strict R under both producers, while PQ/QB fail to preserve R after P1 and preserve
it after P4T. A third input changes its natural C1 endpoint as well as its
speculative endpoint when the producer changes. PQ/QB agreement alone is therefore
insufficient to establish serial-reference preservation.

## Complete fixed-denominator results

All eight P1+C1 endpoints match their independently executed UB1/output1 R.
P1 versus P4T changes both the serialized KV and complete initial FP32 vector
on **8/8** inputs. Within each producer, PQ versus QB matches the complete endpoint,
all cycles, and every full-vocabulary vector (including discarded verification
rows) on **16/16** input–producer pairs.

“Local” below means both PQ and QB. Equalities include full capped/EOG endpoints,
not a selected token or an answer-accuracy judgment.

| Input | Native IDs | P1 C1 = R | P4T C1 = R | P1 local = own C1 | P4T local = own C1 |
|---|---:|---|---|---|---|
| GSM8K/train/582 | 83 | yes | yes | yes | yes |
| GSM8K/train/4140 | 68 | yes | yes | yes | yes |
| GSM8K/train/1184 | 118 | yes | **no** | **no** | **no** |
| GSM8K/train/2279 | 68 | yes | yes | yes | yes |
| MATH500/test/prealgebra/1865.json | 265 | yes | yes | **no** | yes |
| MATH500/test/geometry/846.json | 274 | yes | yes | yes | yes |
| MATH500/test/prealgebra/1804.json | 343 | yes | yes | **no** | yes |
| MATH500/test/geometry/465.json | 302 | yes | yes | yes | yes |

- Five inputs have changed producer bytes but unchanged endpoints across all six
  producer–consumer scientific cells; all six match R.
- On prealgebra/1865 and prealgebra/1804, P1 PQ/QB first differ from their C1/R
  at output positions **5** and **25** respectively (one-based). P4T PQ/QB retain
  the unchanged C1/R endpoint. These are the clearest producer-conditioned
  eligibility examples, with the reference held fixed.
- On GSM8K/train/1184, P4T natural C1 first differs from R at output position
  **30**. P1 PQ/QB differ from their own C1 at **30**, and P4T PQ/QB differ from
  their own C1 at **32**. Changing producer also changes the PQ/QB endpoint.
  Both producers' C1 restore shams and off/heavy guards pass.

The complete [48-cell matrix](execution/MATRIX.csv),
[producer-state comparisons](execution/STATE_EFFECTS.csv), and
[counterexample endpoints](execution/COUNTEREXAMPLE_ENDPOINTS.json) retain all
coordinates. No successful subset replaces the eight-input denominator.

## Input binding and execution custody

The original unbound plan had no selected new inputs. A conservative accessible
history scan left the initial HumanEval/MBPP pool unable to fill either band.
GSM8K vocabulary-only tokenization then supplied no 256–352-token questions.
Both static stops were retained, followed by a committed
[pre-forward source amendment](INPUT_SOURCE_AMENDMENT.md) adding pinned original
MATH-500 problems. The final pool was frozen and ranked before any new forward.

The final scan covers 113,875 unique accessible files, with no unresolved read
errors. Six copies of two documented 22/23-byte failed archive transfers were
classified using their matching transport-failure receipts; unavailable bytes
were not claimed recovered. The final eligible counts were 7,135 short and ten
long candidates. The fixed hash rule selected four GSM8K and four MATH-500 inputs.
The panel is entirely mathematical; it is not a domain-by-length factorial or a
claim of absence from model training/unavailable external history. Original
problem strings, including any original Asymptote text, remain intact.

The native driver was compiled against the PR148/150 import libraries. The five
numerical DLLs remain byte identical to that qualified runtime. Actual executable,
model, source and loaded-module identities are retained in the freeze and
supervisor receipts. Native execution source commit:
`c5eb54ba` (full identity in execution/FREEZE.json). The primary plan canonical
SHA256 is `144a750624ee2d9f75108372e9134a86628340c606e3037b341527dc7cc5bf91`.
The primary ledger SHA256 is
`f6c1b7d4b423887b111a59cdd731c6588ea991e327f61bacab9f99e38c1f34d3`.

The 10 supervised model workers account for 1,371.25 owned seconds and
3,903,012,842 unique raw payload bytes, within the frozen resource limits.
These figures are resource accounting, not performance estimates.
Content-addressed deduplication followed actual native capture/readback.
`COMPLETE_QUALIFIED` in the immutable native ledger denotes completion and
evidence-contract qualification; reference equalities are recomputed separately
and the three scientific counterexamples above remain explicit.

## Scope and verification

These results establish a total effect of the defined producer boundary state
(KV plus initial logits), conditional on the boundary0 clean receiver. They do
not isolate KV as the sole cause, identify a particular failing operator, establish
all-q4 operator qualification, or establish natural integrated P4T speculative
production-path behavior. The eight-input counts are descriptive and support no
population-rate or formal performance inference.

The original 19 CPU contract tests plus two execution-custody tests passed.
Actual positive native evidence subsequently passed the independent historical
control and full-record/payload audits. The original CPU validator and protocol
remain byte unchanged. `analyze.py` produces the complete matrix after re-auditing;
`summarize_states.py` describes state/endpoint changes from that audited ledger.

The full evidence package contains frozen sources, all static selection attempts,
exact native inputs, the bound plan, primary records, complete vector/boundary
payloads, process/module receipts, and CPU audits. Models and numerical DLLs are
excluded. The [private evidence release](https://github.com/leecdiang/HeteroSpec/releases/tag/b570-producer-consumer-boundary-v1-20261029)
contains six ZIPs plus the manifest and package receipt. All eight assets were
downloaded through the authorized account, and all **6,826** extracted members
matched their original SHA256. Re-running the frozen CPU analysis and state
summary from that downloaded copy reproduced all eight audit/matrix/summary
files **byte for byte**, with 152 complete requests, B0 qualified, 48 qualified
scientific cells and zero audit errors.

See [access pins](delivery/ACCESS.json), [full readback](delivery/ROUNDTRIP.json),
[CPU reconstruction](delivery/CPU_READBACK.json), and [reproduction instructions](delivery/README.md).
This is same-account, same-machine delivery verification, not a second-machine
native qualification. [Transport recovery](delivery/TRANSPORT_RECOVERY.json)
records the upload interruptions and a failed large-volume transfer. Repartitioning
that volume preserved the complete member manifest and original payload bytes;
no model request was repeated or added.
