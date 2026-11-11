# B570 prefill intervention: independent reconstruction audit

Reviewed repository head: `3a0d3c9eb1c8778141bf546b5cdd25ad1e5243e4` (PR #53).
Review date: 2026-10-04. Decision: **the bounded B570 prediction and recovery results are supported**.
This is a fresh CPU reparse of existing evidence, not a model-forward experiment.

## Evidence used and independence

The previous `b570_prefill_review_20261004/REVIEW_REPORT.md` identifies a completed
read-only archive audit at Actions run `37178393741`, source
`c962c56fc6a2fb5772f1143bb7e348da018b165f`. This review retrieved artifact
`11293269625` anew through the GitHub connector. Its ZIP SHA256 is
`b671205e03a4bac7a2411a0dff2de46823860d924ed5bba3792854cc496159a9`;
the 2,742-file raw subset SHA256 is
`c920c75f04399f01bcd720c800cb76dd272f5791499d6b25a1d164317e260e1a`.
Both match the earlier receipt.

The newly written [reparse.py](reparse.py) imports only the Python standard
library and no study collector/verifier. It reads all 360 formal and 120 G0 raw
captures, individual starts/results, command lines, stderr logs, prompt ID files,
the ledger, and the complete prediction seal. It independently reapplies the
endpoint contract and compares full token arrays, EOG flags, and endpoint labels.
The derived result is [DERIVED.json](DERIVED.json): **122,764 assertions passed**.
The assertion count describes this parser's checks, not extra experimental units.
It rehashes 2,181 available result-linked files across formal and G0 execution.

Protocol, freeze, manifest and all eight execution sources were separately fetched
at the exact PR #53 head. They match the subset byte for byte and match the frozen
SHA256 values. The original `benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS.json`
was also fetched at that head; SHA256
`0201ccd1f67492510d34be567aa83f1c38d3bd1f162a970c05d3cea9d3957826`
matches the original authority. All 216 new R/T0/N0 complete ID arrays match its
reference or predicted arrays directly, as well as the historical-expected file.

The earlier audit's reconstruction of the full 1,473,070,703-byte archive and
authentication of all 4,073 manifest files are **inherited evidence**, not work
repeated here. The returned subset omits binary KV and pending-logit dumps. This
pass checks the equality of their recorded digest identities and transfer metadata;
independent byte authentication of those binary dumps comes from the earlier full
archive audit. No new claim of full archive restoration is made.

## Directly recomputed publication values

| Comparison | Repetitions | Unique tasks |
|---|---:|---:|
| Baseline target-only T0 versus native N0 | 72/72 | 24/24 |
| Sealed candidate target-only T1 versus native N1 | 72/72 | 24/24 |
| Baseline native N0 versus reference R | 60/72 | 20/24 |
| Candidate native N1 versus reference R | 72/72 | 24/24 |
| Native output unchanged by intervention, N0 versus N1 | 60/72 | 20/24 |
| Divergent to agreeing reference transition | 12/12 diagnostic repetitions | 4/4 diagnostic tasks |
| Agreeing to divergent reference transition | 0/60 control repetitions | 0/20 control tasks |

The four recoveries are HumanEval/134, /42, /145 and /138. Their baseline native
arrays diverge from R in each repeat and their candidate native arrays equal R in
each repeat. The other 20 tasks retain identical complete native outputs. All
24 tasks repeat stably in all five conditions. Three repeats demonstrate stability;
the experiment contains **24 previously exposed tasks**, not 72 independent or
unseen prompts.

All 360 formal outputs end at CAP128. The general endpoint implementation also
supports inclusive first runtime EOG, but this cohort supplies no formal EOG-ending
unit. Raw native overshoot is retained and excluded only according to the declared
contract: total overshoot is 60 IDs in N0 and 63 IDs in N1. This is complete
trajectory agreement under a specified finite endpoint; it is not HumanEval
functional correctness or unconstrained completion equivalence.

## Intervention, controls and forecast order

Source inspection and capture traces agree that the candidate changes target
prefill UB capacity from 1 to 128, samples the pending first target ID in the source
prefill context once, and transfers serialized state plus a cloned post-sample
sampler to a UB1 continuation context. Both baseline and candidate execute this
handoff; the intervention cannot be described as changing KV bytes alone.
All 288 formal handoff records agree on preserved positions, equal consumed state
size, unchanged source state, identical recorded KV digests, matching sampler chain,
history and seed, and the carried pending ID/EOG matching the first committed ID.
Sampler bytes remain opaque: qualification uses source behavior and sham equality.

Native initialization uses a separate target prefill parameter copy; draft policy,
target continuation UB1, k=2 and the existing speculative control flow remain fixed.
Commands select Vulkan0 and complete GPU layer offload; each formal/G0 log identifies
Intel Arc B570 and 37/37 target model layers offloaded. Native arguments/environment
contain the prompt, assets, output paths and fixed policy, without T1 prediction
arrays or a future-token tape. This documents ordinary process input isolation,
not adversarial isolation on a shared host.

The G0 plain/sham controls comprise 30 pairs (five tasks, three repetitions,
target-only and native). Every pair matches in complete output, all commit scores
and decisions, and complete decode/KV trace. In addition, 75 original/new baseline
pair comparisons match across the G0 variants. Every formal unit has one valid
attempt; no failed formal attempt or output-selected retry was found.

The seal contains all 72 T1 result identities and complete arrays, and its protocol,
manifest and freeze hashes match the fixed authority. Every prediction result hash
checks. The ledger prefix hash checks; the seal hash checks; all 72 native candidate
starts occur after the local seal. Individual result timestamps place every T1 end
before the seal and every N1 start after it. All tasks had prior exposure. The
chronology supports a locally sealed forecast before candidate native measurement;
the GitHub upload happened afterward and is not a certified absolute pre-live
timestamp.

## Executed path, contribution and limits

Caller grouping is deliberately preserved, not made identical between the smaller
reproducer and native process. For HumanEval/134 (148 prompt IDs), T1 uses caller
length [148] with occupied graph-token counts [128,20]; N1 uses callers [147,1]
with counts [128,19,1]. T0 and N0 use occupied one-token graphs. Every formal trace
matches its declared caller grouping and occupied graph-token partition. Subsequent
candidate target and draft decoding use UB1. These observations support transfer
of the output prediction across preserved frontends, not identity of all backend
shapes or identification of a unique Vulkan kernel cause.

The B570 result demonstrates a successful bounded prefill intervention: four
reference-divergent trajectories recover while 20 controls retain their output,
and the smaller target-only execution predicts every candidate native contract.
It supports a stage-dependent diagnostic argument when combined with separately
audited RTX verification-stage results. It does not independently establish a
cross-platform repair method, universal qualification, necessity of prefill policy,
or a guarantee that all interventions improve reference agreement.

Scope remains one model pair, one B570 Vulkan stack and an exposed finite cohort.
Omitted model/runtime/driver bytes, opaque sampler serialization, the disclosed OS
build change and shared-host chronology limit independent authentication. The
freshly requalified baselines address measured regression on this cohort, not all
possible effects of the OS change. No speed, energy, production gain or debugging
time saving follows from this evidence. The separate late-fork cohort must not be
pooled with this intervention as a necessity proof. No source evidence was modified,
and no GPU run, merge, release or tag was performed for this review.

## Endpoint clarification for manuscript reconstruction

The three data levels must be distinguished. The original `capture.json` stores
the **untruncated native committed array** in `ids`, parallel `eog` flags, and one
entry per committed ID in `commits`. The collector's `result.json` stores the
**complete contract array** in `ids`, its `eog` flags and endpoint, together with
`raw_overshoot = len(raw_capture_ids) - len(contract_ids)`. The reconstruction
export `RAW_OUTPUT_ARRAYS.json` contains those complete contract arrays; all 360
exported arrays have exactly 128 IDs and endpoint CAP128. It does not contain the
native extra committed suffix. `RAW_OUTPUT_PROVENANCE.json` identifies the original
capture, its digest, raw length and overshoot; the original capture remains the
authority for the untruncated array.

| Condition | Raw captures of length 128 | Length 129 | Length 130 | Extra IDs beyond contract, summed across 72 units |
|---|---:|---:|---:|---:|
| N0 | 33 | 18 | 21 | 60 |
| N1 | 33 | 15 | 24 | 63 |
| R | 72 | 0 | 0 | 0 |
| T0 | 72 | 0 | 0 | 0 |
| T1 | 72 | 0 | 0 | 0 |

These totals are directly recomputed from raw `capture.json['ids']` and checked
against both the count of `commits` and `result.json['raw_overshoot']`. They are not
a mismatch between a printed generation count and a trace count. In the frozen
`native.cpp`, lines 437–442 commit the sampled/accepted/bonus token and increment
`n_predict`; line 501 tests `n_predict > params.n_predict` after the speculative
round. The native command uses `--n-predict 127`. Finishing that round may therefore
commit 128, 129 or 130 IDs before stopping. The existing collector in frozen
`controller.py`, lines 49–54, selects the first runtime-EOG position inclusively,
capped at 128, and computes the retained suffix count. For example,
`formal/HumanEval_77-N0-r1/result.json` records raw overshoot 2; its original capture
has 130 IDs and 130 commit entries, while its contract array contains 128 IDs.

The equality claims 72/72, 60/72 and the 20 no-op tasks concern **every ID and the
endpoint within the declared finite comparison contract**, not equality of the
entire untruncated native process output. Extra suffixes remain present in archived
raw captures and are outside the compared contract. The manuscript should use:

> Agreement compares every ID and the endpoint within the inclusive-first-EOG/cap128
> contract; untruncated native captures retain any IDs committed beyond that
> endpoint for audit.

“Complete committed arrays preserve raw overshoot” is ambiguous if attached to the
comparison arrays and should be replaced by that explicit distinction. No equality
of post-contract suffixes is needed for, or implied by, the published agreement and
no-op counts.
