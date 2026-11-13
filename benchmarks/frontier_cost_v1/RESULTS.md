# Implementation checks and the qualification boundary

These are controlled CPU implementation checks on 2026-11-11. No GPU model
request or new production-model performance experiment was executed.

## 1. Fresh build and source preservation

`prepare.py` acquired the pinned public source ZIP, reconstructed the Linux M2
frontend from pinned transformations, and compiled an unchanged CPU `llama`
library. All 3,547 selected numerical/frontend source members still matched
their authenticated bytes after compilation. Successful compilation was labeled
`BUILT_NOT_QUALIFIED`; the following tests supplied separate execution evidence.

See `implementation_checks/PREPARE_CHECK.json` and
`review/PREPARE_SOURCE_AUDIT.json`.

## 2. Deferred tail through the actual request layer: PASS

| Final paired matrix | Observed result |
|---|---:|
| Request pairs | 32 |
| Actual final CPU requests | 64 |
| Full frontend-read vector pairs | 552 |
| Active native sequence pairs | 272 |
| Compared bytes per side | 76,633,984 |
| Omitted final draft q1 calls | 29 |
| Required final draft q1 calls recovered | 19 |
| Dirty resident resets | 28 |
| Requests crossing the 256-cell extent | 4 |

The actual worker produced 20 CAP and 12 EOG terminations, including eight
all-accepted terminal cycles whose final draft KV had to be recovered. Correction
and bonus paths were exercised. A separate initial implementation preflight
performed one CPU request: the module total is 65, while the paired result above
uses only the final 64.

The independent audit read both sides of every saved event, recomputed argmax,
and reconstructed acceptance, stop, and keep logic without importing the primary
comparator. It did not filter events to obtain equality. Source, binary, model,
and the four actually loaded numerical-library identities were checked.

Scope: two newly generated, untrained F32 fixture variants; actual native greedy
vectors and EOS metadata; explicit token IDs. This does not establish natural
text tokenization, production-model quality, every inactive/padding byte, GPU
qualification, or a performance gain. The original production entry still
rejects CPU execution at its GPU-required gate before loading a model.

See `native_integration/RESULT_SUMMARY.json`,
`native_integration/INDEPENDENT_AUDIT.json`, and
`review/NATIVE_INTEGRATION_RAW_AUDIT.json`.

## 3. First nontrivial width candidate: UNQUALIFIED

The target-operation probe uses a different untrained F32 fixture. Its fixed
width sweep stopped at q2 at the first p248 history. The compared schedules were
two real q1 calls versus one real q2 call, all with the same M2 LOCAL frontend,
`n_ubatch=32`, output capacity, inputs, and initial checkpoint.

| Check | Observation |
|---|---|
| Initial active sequence | All 510,952 bytes identical |
| Initial/final/continuation geometry | Identical |
| Actual physical widths | Reference `{1: 2}`; candidate `{2: 1}` |
| Operation vectors | 242 of 256 FP32 entries differed |
| Maximum absolute vector difference | Approximately 1.994e-5 |
| Final active sequence | 43 bytes differed |
| Next continuation vector | 127 of 128 FP32 entries differed |
| Next continuation state | 43 bytes differed |
| Operation and continuation argmax | All still matched |
| Work before stopping | 3 contexts, 31 native decode API calls, 752 rows |
| Performance measurement records | 0 |

This is a concrete example in which checking only output tokens would miss the
contract violation. The arithmetic cause was not localized, and the result does
not imply that a CUDA q2 implementation has the same problem. The target recipe
was unchanged between the eager and deferred request arms in section 2; that is
why their successful comparison does not contradict this failed width change.

See `matched_cost/CPU_WIDTH_FAILURE.json` and
`review/MATCHED_FAILURE_RAW_AUDIT.json`.

## 4. Separate q1 implementation smoke: PASS

A separately declared q1-only profile exercised the measurement, reset, module
binding, and budget code that the failed width sweep had not reached. It used
10 contexts, 136 native decode API calls, and 3,524 rows. Its eight measurement
records cover both `first_after_fresh_context` and
`one_shape_warmup_then_reset`; all full-vector, state, and continuation checks
passed.

Both modes recorded one graph build and zero graph reuse per measured operation.
The second mode therefore must not be renamed a warmed graph or steady state.
It has no independent width candidate and supplies no width-speedup result.
Together, the two operation diagnostics used 13 contexts and 167 decode API
calls. These operation contexts are not counted as full speculative requests.

See `review/MATCHED_Q1_SMOKE_AUDIT.json`. The final host wrapper adds fixed model
identity and deadline checks after these native runs; its executed predecessor
is retained and its host-only changes are separately tested. A host-test pass
does not retroactively claim that the final wrapper ran a GPU model.

## 5. Next decision

Use the bounded, committed CUDA profile to determine whether each tested action
preserves that deployment's newly declared local reference. A mismatch stops
this profile; it does not silently substitute q1 microbatches or relax the
comparison. Only a qualified cost table can inform a later controller. The
complete-service baseline and historical-R bridge remain separate requirements.

The current release is suitable for a scoped research Draft PR. It is not ready
for a production merge, a 5% performance claim, or a claim of generality.
