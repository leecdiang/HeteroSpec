# RTX independent proposal replay V2 closeout

Status: **PROSPECTIVE_REPLAY_MATCH_DISCRIMINATING**.

Starting main: `f8290281156f6b3de8fbc8b44fd10a4afa7bcd89`. Branch: `experiment/rtx-independent-proposal-replay-v2`. The final closeout head is the draft PR head; content/packaging/closeout identities are recorded separately to avoid self-referential hashes.

## Reached executions

| Phase | Completed conditions | Valid |
|---|---:|---:|
| reference-qualification | 180 | 180 |
| discovery | 108 | 108 |
| pre-live | 216 | 216 |
| live | 72 | 72 |

Engineering additionally preserves 27 valid complete conditions, one failed pre-model binding attempt, and three constructed partial contexts. Together with 180 reference engineering conditions, this is 208 engineering attempts, 207 valid. Vocabulary-only tokenization of the 24 reserved inputs created no decode/context forward.

Reserved selection rank: HumanEval/160, HumanEval/45, HumanEval/149, HumanEval/17, HumanEval/6, HumanEval/72, HumanEval/33, HumanEval/121, HumanEval/130, HumanEval/12, HumanEval/4, HumanEval/55, HumanEval/69, HumanEval/14, HumanEval/61, HumanEval/135, HumanEval/100, HumanEval/117, HumanEval/22, HumanEval/7, HumanEval/23, HumanEval/95, HumanEval/88, HumanEval/37.

## Freeze chronology

| Checkpoint | Commit | Remote acknowledgement UTC |
|---|---|---|
| F0 | bf1ed281c6225b0abb22309997cf667184ac93fa | 2026-10-01T06:22:42.770679+00:00 |
| F1 | 0d2a695ab7f8e1538fd48412aaa8e3fa2ed43ebb | 2026-10-01T06:41:41.661558+00:00 |
| F2 | 2f3ab91238c00bfb03ce75bd239861e0965b6acd | 2026-10-01T07:16:25.545950+00:00 |

First reserved live process record: 2026-10-01T07:16:57.403993+00:00. F2 exact remote archive retrieval, when reached, is retained in its receipt and independently checked before live.

## Formal paired arrays

| Comparison | Matching pairs | Distinct wholly matching prompts |
|---|---:|---:|
| H2_live | 72/72 | 24/24 |
| R_ONLY_live | 72/72 | 24/24 |
| reference_live | 60/72 | 20/24 |
| H2_R_ONLY | 72/72 | 24/24 |

Actual reference-divergent prompts: 4. All repeats stable: True. Every first differing position and ID is listed in FORMAL_REPORT.md/json.

## Verification and limits

Reference engineering independently verifies 90/90 complete arrays and prompt arrays. Endpoint/state qualification, six verifier negatives plus one pre-launch guard negative, and four logging observer pairs pass. Scientific stage verification and clean archive reconstruction receipts are separate machine-readable files.

- ENGINEERING_ARCHIVE: `artifacts/rtx_independent_proposal_replay_v2/engineering-374331b39709a513f9b1b049a7e3a8327210aa50d3b792d34fb847cd7986d4c6.tar.gz`; SHA256 `374331b39709a513f9b1b049a7e3a8327210aa50d3b792d34fb847cd7986d4c6`.
- PRE_LIVE_ARCHIVE: `artifacts/rtx_independent_proposal_replay_v2/pre-live-7595603dca47ed5f9a03762562ba466e216bb364478fc782a4e065793c395255.tar.gz`; SHA256 `7595603dca47ed5f9a03762562ba466e216bb364478fc782a4e065793c395255`.

Complete reconstruction: extract the complete tar.gz into a new directory, then run `python -B EXTRACTED/frozen_source/scripts/platform/rtx_independent_proposal_replay_v2/offline.py EXTRACTED`. This validates exact file inventory, all reached phase evidence, Git membership proofs and the reached formal endpoint; no GPU or network is required. Anonymous capsule uses the same standard-library entry point; it is derived recomputation evidence and does not authenticate original chronology.

## Interpretation

- Shared original llama.cpp/GGML/CUDA numerical runtime; independently orchestrated draft-simple/greedy state machines replicate much of original algorithm.
- Application RPC and actual single-model load evidence; no adversarial OS-wide file-access trace.
- Full sampled-row logits hashes and top scores retained, full logits omitted.
- Git byte membership and server acknowledgement retained; host timestamps are not an independent trusted clock.
- External weight/runtime/compiler/driver bytes omitted and not authenticated by offline verifier.
- Finite selected prompts on one pinned RTX Windows CUDA stack; no target-only sufficiency, unique kernel, cross-device cause or performance claim.
- Anonymous derived content cannot independently prove original remote chronology.

No paper files were changed. This new draft PR is for author review; existing PRs #40/#41/#42 were neither modified nor merged. Manuscript integration requires the author to assess this V2 result and its limits.
