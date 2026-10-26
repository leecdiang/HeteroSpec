# RTX native reproduction and matched deployment bridge

Execution follows PR #146, pinned at `d18d85191136ef2128f2d82fd43be153bbc5d1f4`.
This is a new runtime cohort using the twelve exposed Qwen3 inputs. It does not
resolve the separate PR #142 long-input protocol, replace E2, or alter manuscript
measurements.

## Build and reproduction

Commands below run from the repository root, with Python 3.11+ on the RTX host.
`ROOT` is a **new, empty execution directory** outside Git. Historical dependencies
are content-addressed in the recovery receipt. Current host paths are discovery
defaults, not evidence of file identity; `rtx_recover.py` verifies archive members,
both model hashes and all twenty-one external numerical libraries before use.

```text
python scripts/native_reproduction/rtx_recover.py ROOT
python scripts/native_reproduction/rtx_build.py ROOT
python scripts/native_reproduction/rtx_stage.py ROOT
python scripts/native_reproduction/rtx_request_smoke.py ROOT
python scripts/native_reproduction/rtx_bridge/build.py ROOT --name bridge-build-v2
python scripts/native_reproduction/rtx_bridge/qualify.py ROOT prepare
python scripts/native_reproduction/rtx_bridge/run.py ROOT ROOT/QUALIFICATION_SLOTS.json qualification-v2 --timeout 1500
python scripts/native_reproduction/rtx_bridge/qualify.py ROOT qualification-v2
```

The clean build rebuilds **all core/frontend objects** from the recovered source.
It intentionally loads the original external CUDA/BLAS/ggml DLLs. It is not a
claim that CUDA kernels or NVIDIA libraries were rebuilt from source, nor that
the new executable equals the historical executable byte for byte. Original
and metadata4 executable/source identities are preserved separately. Only Qwen3
uses this new bridge; no new SmolLM2/Llama native qualification is implied.

The historical source ZIP has SHA256
`62086688fc095be2654ae25aad2c7780c94db8617db5a6a9f71504f49897bf7e`;
metadata4 has SHA256
`36be0d738ad5d29579b75825f68337003eb127405cc5418abc566cb07718a4d8`.
Their ordered repository fragments are under
`benchmarks/rtx_querylayout_mechanism_v1` at
`3235d44c26edd92db33e574094c26af8e29d2452`.
The source inventories are the original `f974589d...` and metadata4 `720ba352...`
identities from the build manifests; the recovery checks every indexed member.
External numerical-library bytes and model weights are not redistributed here.

Stage fixture selection was fixed before its new replay: E1 context 002,
`Qwen_l00_prefill_q3`, layer0, GSM8K/test/443. Q/K/V/mask spans, original shape,
stride and operation parameters are preserved. The original and clean-built
replayers each execute MQ/PQ/QB twice. Every QK/softmax/AV stage is compared with
the authenticated historical own-arm output; MQ own-path and PQ/QB identity
are checked separately. This is one real fixture, not a new 72-context study.

The HTTP smoke uses the original and rebuilt server for one complete R/PQ/QB
request each. It preserves the submitted token IDs, formatted text, parameters,
full responses, native logs, actual module paths and owned-process receipts.
The source script manages only its own processes and binds localhost.

## New bridge contract

One executable implements both k values and both lifecycles. Both model weights
remain resident. Fresh creates/reserves and destroys contexts inside the complete
service timer; resident clears KV metadata and retains contexts. PQ and QB use
separate resident context pairs, so switching layouts cannot reuse a graph with
a cache key that omits the layout. k changes the logical verification width;
the target caller UB stays4 and draft UB stays1. Both lifecycles share all input,
prefill, greedy verification, correction/bonus, trimming and result construction.
The resident pairs persist across both k values; every input is prefetched anew.

All full-vocabulary vectors, including rejected/unexamined verification rows,
are retained in separate heavy qualification. Independent Python checks compare
full endpoints, stop state, complete speculative state and full raw hashes.
The observer records actual target-layer geometry, key/mask strides and GPU
placement. It does not convert logical row counts into hardware kernel counts.

The formal driver disables counters and callback/readback, after a small
counter-on/off pilot. Native backend logging remains enabled identically in all
cells and is part of the measured deployment. Debug graph warmup/reuse messages
are not a complete capture/instantiate/replay/eager/fallback ledger; no CUDA
Graph causal attribution follows.

Formal execution requires a committed freeze and verifies its pinned inputs.
Each process attempt has an immutable output directory, unique slots, an atomic
checkpoint and bounded owned lifetime. Completed attempts are hash-checked on
resume. An unaccounted running process requires reconciliation before restart.
The fixed schedule and statistical methods are in `FREEZE.json`, not inferred
from observed effects. Analysis rejects duplicate/missing blocks and unequal
timed endpoints/state. File output and reference checks are outside the timer.

## Recorded engineering interruption

The first 204-slot qualification attempt stopped after 135 native requests when
Windows rejected replacement of the very large aggregate JSON. No formal slot
had started. Exact OS error was not retained by that version; concurrent reading
is a plausible cause, not a proven diagnosis. The entire attempt, binaries,
source and raw records remain intact. v2 adds bounded sharing-error retries and
keeps complete per-request geometry while removing its duplication from the
aggregate. It reruns the entire qualification under a new executable identity.
It does not merge partial v1 and v2 observations into one qualifying session.

## Statistical scope

The fixed budget uses six independently loaded process sessions on one date.
The four cells have 864 measurements and72 explicitly charged warmups, balanced
arm permutations and cell position. Process-session clustered bootstrap intervals
preserve the four-cell pairing; the four primary intervals use Bonferroni
familywise coverage. k/lifecycle/interaction contrasts are secondary. All A/A,
input regressions, block reversals, per-session signs and chronological/omit-one
sensitivities remain visible. A single date cannot establish date-level robustness.
