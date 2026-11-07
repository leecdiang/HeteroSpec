# Independent RTX evidence review for manuscript v0.10.0

Review object: PR #53 head `3a0d3c9eb1c8778141bf546b5cdd25ad1e5243e4`.
Base: `6a3a7e2483d5b13a24518d27b8c1ff3eafaac08f`. Frozen scientific implementation:
`3b0044ed7fb3ce86fc97b8a822eea198a31ed5c2`. Access date: 2026-10-04 UTC.

**Review status: QUALIFIED_PASS.** All supplied archive, frozen-source, complete
formal raw-output, endpoint, selected-attempt, handoff, sham, graph and ordering checks
passed. The qualification concerns omitted weights/runtime binary bytes and the
limited strength of experimental timing/causal inference, not an unresolved raw
comparison. No numerical discrepancy was found.

## Independence and access scope

This review directly accessed the exact Git objects, protocol/cohort/queue, execution
and observer source, historical mapping, qualification and engineering records,
prediction seal/readback metadata, omissions and delivery recovery records. The
reviewer wrote a second standard-library-only parser,
`scripts/audit/rtx_reconstruction_v010.py`, importing no experiment helpers.
Native IDs come from native logging fields; H IDs come from target wire responses,
with proposals cross-checked against the separately logged live proposer and tape.
Reported IDs/endpoints are checked against these raw reconstructions, never used as
the parser's source of the generated sequence.

CPU-only GitHub Actions provides authenticated access to the large private archive.
The runner performs a fresh CAS restore, hashes every part/blob/logical file, resolves
only the complete attempt named by each `result.files`, and performs raw comparisons.
The author's frozen independent verifier is then run as a separate validation path.
No model forward, GPU run, sampling search, cohort modification, or original evidence
edit is part of this review. Reports preserve audit-tool failures and corrections.

## Archive and frozen-source checks

The independently downloaded restoration receipt records 24 main parts,
1,205,757,106 compressed bytes, archive SHA256
`ee545bda11c9c0622d589024e4805fb1f1d3f3f0cbcd9c5551aeb22258733482`,
15,192 logical files and 10,846 unique CAS blobs. Each logical file was materialized
in an initially empty directory and checked by length and SHA256. CAS hardlinks
retain separate logical paths without unnecessarily duplicating their bytes.
`restore-first-pass/RESTORED_FILES.json` preserves the full independent inventory.

The freeze binds 3,695 files, including 116 critical files. Six top-level bindings
(protocol, cohort, queue, effective G0, fixtures and asset/environment manifest) match
independently fetched Git bytes. All 18 RTX study source files have identical Git
blob IDs at the implementation commit and reviewed PR head; see
`IMPLEMENTATION_GIT_BINDINGS.json`. Subsequent transport-recovery helpers are
separate artifacts, rather than retroactive changes to the frozen scientific code.

The 24 MBPP formal task IDs are exactly positions 7–30 in the independently
recomputed SHA256 ordering of 254 eligible sanitized MBPP tasks; the preceding six
tasks are engineering tasks excluded from formal denominators. The exposure audit
binds 2,543 project records and two indexed project ZIP archives. Its code scans
eligible text inference records inside archives but does not wholly decode all
archive members or inspect model training. 'New' means no known project execution
exposure within this declared scope. It does not establish training holdout or an
unbiased sample of the complete benchmark.

## Contracts, handoff, shams and configuration

The H application/API orchestrator receives the prompt, fixed assets and bounded
per-round pending/proposal messages. The proposer produces its own live draft IDs;
target verify requests use exactly those IDs and the locally committed past prefix.
The worker's explicit allowlist rejects reference IDs, future native outputs and
sealed answer tapes. Native execution independently opens its prompt/models and
fixed parameters and runs its own live draft. Its commands do not import H tapes or
reference/prediction IDs. This is application/orchestration independence: H and
native share pinned numerical routines. The native frontend/core is rebuilt and
qualified; the CUDA backend is retained. It is not a fully independent numerical
implementation or a universal backend predictor.

The target handoff occurs after the first pending token has been sampled and
accepted once in the source. The source state is serialized, transferred to the
destination, and compared with a post-transfer source snapshot. Captures retain
source-before/destination/source-after KV bytes, pending logits, sequence positions,
pending ID and sampler clone metadata. The destination does not resample the pending
token. Opaque sampler state cannot be serialized: byte equality of the sampler is
not a reviewed claim. Pinned cloning, seed/history/chain witnesses and behavioral
sham controls bound the available evidence.

The declared native plain/sham predicate deliberately excludes overwritten random
draft draws, event sequence bookkeeping, startup module paths and transfer-only
events. The native draft sampler first populates candidate probabilities, then the
code sorts them and uses candidate 0 as the actual proposal. Its raw distribution
draw is overwritten. The predicate retains actual sorted proposals, target selected
IDs/scores, draft top scores, caller tokens/positions/masks, observed graph dimensions
and rollback positions. H wire comparisons retain actual proposal choices/scores,
excluding transfer bookkeeping and optional logit-payload storage fields. Neither
predicate licenses a claim that every raw field or every sampler byte is equal.
Full output-array/endpoint equality is checked separately. This finite sham control
does not prove equivalence on untested prompts or all internal states.

Historical native templates omitted thread arguments and effectively selected 12
threads despite their descriptive document saying 24. This study explicitly sets
24/24 threads. Its effective G0 combines 75 native outputs rerun at explicit 24 with
45 unchanged H outputs reused from their identified captures: 120 effective arrays,
30 plain/sham pairs. The older default-thread qualification and pilots remain
distinct. This correction must accompany historical configuration descriptions; no
old raw record is rewritten. Historical/global-UB1 comparisons cannot isolate a
single necessary stage or eliminate all effective-setting confounds.

Graph shape comes from captured `attn_norm-0` occupied-token dimensions and
`result_output` output dimensions. Caller batch length, UB capacity and occupied
tokens are different quantities. Formal original-reference R did not gain graph
callbacks; graph claims belong to observed H/N paths and separately identified G0
controls.

## Prospective ordering and retained failures

The prediction seal binds all 258 H0/H1 output records, complete arrays/endpoints,
their own proposal tapes and scientific identity hashes. The remote-readback receipt
names immutable Git commit `de912fe446d5d1b0b5faae0d76a317a98bad7cc0`, prediction archive
blob `c0269bf53ea8370b2810f360a1932c1d48c4d54b`, 522 transported files and archive SHA256
`cc27b87e8b5dcff009c0d00e367b33f713a0d2ec882c5dc09b5b3068cf4e2fb2`.
The local hash-chained ledger supports seal/readback-before-native ordering. Immutable
remote content membership strengthens that evidence, but does not independently
authenticate the absolute wall-clock time at which local processes executed.
Prospective testing is therefore distinguished from formal independent preregistration
and trusted external experiment timing.

Pre-freeze failures include a Windows GBK source-decoding failure and a qualification
comparison that concatenated an abandoned `/18 N_sham r2` attempt with its complete
replacement. The corrected selector binds the complete attempt by `result.files`;
abandoned attempts and helper versions are preserved. This is a preparation-stage
bookkeeping correction, not a retry to change a scientific disagreement. Delivery
failures include HTTP502, interrupted/timeout transport, Windows MAX_PATH restoration
and parsing a failed transport response; subsequent helpers selected valid responses.
They occurred after measurement and did not require model reruns or frozen-source
changes. The pre-archive report snapshot and later final Git report/receipts are
different snapshots; the final report is not incorrectly required to be inside an
archive whose own hash it describes.

## Results and allowable claims

The independent raw parser and separate frozen author parser both passed. All 645
formal units use one complete selected attempt each, with zero failed formal attempts.
Every one of the 43 tasks is stable across its three observations in all five
conditions. The author parser reports 11,987 checks; its full counts match the
reviewer's recomputation.

| Cohort | H0/N0 | H1/N1 | N0/R | N1/R | N0/N1 |
|---|---:|---:|---:|---:|---:|
| Old 19 HumanEval tasks × 3 | 57/57 | 57/57 | 51/57 | 51/57 | 51/57 |
| New 24 MBPP tasks × 3 | 72/72 | 72/72 | 66/72 | 66/72 | 69/72 |

Task transitions are 16 match→match, one mismatch→match (/15), one match→mismatch
(/25), one mismatch→mismatch (/18) in the old cohort; 22 match→match and two
mismatch→mismatch (/463, /304) in the new cohort. Combined H0/N0 and H1/N1 each
match 129/129 observations; reference agreement remains 117/129 before and after.
The unchanged aggregate masks the offsetting /15 restoration and /25 regression.

Direct N0/N1 comparisons resolve the ambiguous persistent cases. HumanEval/18 is
an output no-op: all three arrays contain identical 69 IDs with EOS endpoints.
MBPP/463 is also an output no-op: identical 109-ID EOS arrays. MBPP/304 changes its
trajectory in every repetition: at zero-based index 33 (generated token 34), N0
contains ID 488 and N1 ID 481. Both arrays contain 47 IDs and end at EOS. It is a
persistent reference deviation with a changed trajectory, not an output no-op.
Full exact arrays and per-repetition endpoint/difference details are retained.

Effective G0 raw recomputation passes all 120 arrays and 30 projected plain/sham
pairs, with 75 explicit-24 native reruns and 45 reused unchanged H outputs. All 171
old R/H0/N0 arrays/endpoints match their historical bindings. All 516 formal H/N
handoffs have byte-consistent captured KV snapshots, preserved pending IDs/logits
and positions, with the stated opaque-sampler limitation. Target-continuation
occupied graph tokens are actually observed as [1] in H1/N1, compared with [1,2]
in H0/N0; caller continuation lengths remain [1,3]. These are observations, not
capacity-based inference.

The hash-chained ledger places prediction sealing at sequence 784, remote-readback
pass at 786 and first formal native start at 788. All 258 predictions and their
bound results precede native execution under that recorded ordering. An additional
independent CPU-only audit directly checked the exact remote archive at its named
Git commit: SHA256, Git blob SHA1, all 522 members and their lengths/hashes match the
transport manifest. This does not extend the wall-clock timing claim.

The full 15,192-file clean restore and all 645 complete raw attempts were inspected
by the independently authored program on the authenticated CPU runner. Locally
retained downloads include every raw-derived output array, all selected-attempt
file bindings and complete log/wire/trace/tape captures for the five salient tasks'
first repetitions. All 25 retained complete captures were independently reparsed locally and matched
the remotely audited exact arrays. CAS hardlinks were materialized to their exact
bytes before compact export; the initial export-only error and fix are preserved. Large KV witness bytes were
hashed on the CPU runner; their independent hashes are retained locally. This
physical download subset does not change the full remote raw-audit coverage.

The candidate **fails its original reference-recovery plus no-new-regression
objective**. Complete prediction closure is supported, including prediction of the
new deviation, while uniform restoration is not. Target-continuation UB2→UB1 alone
did not reproduce the historical global-UB1 reference agreement under this study's
controlled configuration. This preserves /15's restoration and the historical
thread-setting distinction; it does not identify a necessary missing stage.

The primary target remains reference recovery with no new regression. Prediction
closure and reference recovery are separate tests. Repair/regression mean a change
in complete output agreement with the specified original CLI reference, not functional
program correctness, HumanEval pass rate, user experience, performance or energy.
Repeated observations assess stability on 43 task units; 129 repetitions are not
129 independently sampled tasks, and H0/N0 plus H1/N1 are not 258 independent tasks.

## Unavailable byte authentication and unsupported extensions

Model weights, original external runtime files and newly compiled binaries are
deliberately omitted from the downloadable archive. Their manifests record
identities, placement, loaded-module paths and hashes, but this review cannot
independently hash bytes that are not supplied. Offline archive verification and
author-side runtime readback do not become an independent model re-execution.
This limitation qualifies the review even when every supplied scientific record
and raw paired output passes.

No common predictor or common intervention is claimed to transfer universally
between RTX and B570; their input contracts, stages, stacks and cohorts differ.
The RTX continuation-only candidate does not identify prefill or draft necessity,
an interaction term, a unique kernel cause, or a stage-dependence law. Current
intervention records do not contain a qualified speed/energy comparison; historic
RTX timing is a separate configuration and instrumented post-prefill measurement.

## Commands and output locations

```
python scripts/audit/rtx_reconstruction_v010.py restore --root . --dest /tmp/rtx-review-restored --output /tmp/rtx-review-output
python scripts/audit/rtx_reconstruction_v010.py audit --root /tmp/rtx-review-restored --output /tmp/rtx-review-output
python scripts/platform/rtx_target_verification_intervention_v1/independent_verify.py --root /tmp/rtx-review-restored --output /tmp/rtx-review-output/author-parser-crosscheck
```

Remote audit branch: `codex/rtx-reconstruction-v010-offline-audit`, based on the exact
PR #53 review head. `AUDIT_WORKFLOW.yml` retains the CPU workflow. The first complete
clean-restore run is 37195288354; `AUDIT_TOOL_CORRECTIONS.json` records the reviewer's
timing-regex correction before scientific comparisons. Completed independent raw/author crosscheck run:
`https://github.com/leecdiang/HeteroSpec/actions/runs/37195517731`, audit commit
`344913d95866589d31668fec684dfa01614816a7`. Complete output artifact 11300741759
(SHA256 `61cb3872541bc678956da07ee4534d72c989b2ba28663ae7c01f61b08b8038b1`).
A lightweight, CPU-only compact-delivery step retained all JSON/CSV outputs and the
25 complete salient raw captures: run 37196128453, artifact 11300592616
(SHA256 `80cd8b52ea247d70a76ad84d991889cf62532eb041ac232d68b2f621a8cf6ffd`).
The separate exact remote-seal content audit is run 37195633621, artifact 11300364697
(SHA256 `62c89bc98de75dd108998594097273c24d62b514e822a7723bd6502c07ea68f5`).
These are offline processing/delivery runs, not additional model experiments.

Machine-readable outputs: `RECOMPUTATION.json`, `DERIVED.json`,
`TASK_TRANSITIONS.json/csv`, `RAW_OUTPUT_ARRAYS.json`,
`FORMAL_ARRAYS_NEUTRAL.json` (all 645 complete committed arrays/endpoints),
`SELECTED_ATTEMPTS.json`, `SOURCE_BINDINGS.json`, `TRANSFER_WITNESSES.json`,
`SHAM_WITNESSES.json`, `REMOTE_SEALED_MEMBERS.json`, and
`LOCAL_RAW_SPOT_RECHECK.json`. The raw captured subset is
`SELECTED_RAW_CASES.tar.gz`; full author-parser comparison outputs remain in
`author-parser-crosscheck/`.

The optional anonymous array export can be recomputed without private paths:

```
python scripts/audit/verify_rtx_export_v010.py --arrays paper/mlsys2027/reviews/reconstruction_v010/rtx/FORMAL_ARRAYS_NEUTRAL.json --output /tmp/RTX_NEUTRAL_RECOMPUTATION.json
```

This exported-array verifier passes all645 records and reproduces every finite count
and task transition. It does not substitute for the raw logger/source/chronology
audit. `CLAIM_MATRIX_RTX.json` maps the reviewed RTX claims, configuration, scope,
raw paths/SHA and derived inputs to manuscript methods/results/appendix locations.
