# B570 prefill diagnostic v1: independent review and integration decision

Reviewed study head: `196ed563b36d0e16a3cdb667b6996a4afd98da1d`.
Reviewed tree: `5b6244891a5fe15d6dcc48cf76c775999dff08cb`.
Review date: 2026-10-04. Review decision: **suitable for repository integration**.
This is an evidence/code review, not a new conference acceptance score.

The new study completes the bounded intervention proposed after the v0.9.0
reassessment. It changes target prefill policy, carries the pending first sample
and qualified state into a UB1 continuation context, and tests the intervention
on native speculation after sealing target-only predictions. The four original
reference-divergent cases recover the specified complete reference output.
No material scientific or code issue blocking integration was found in this review.

## Independently checked results

| Result | Directly recomputed |
|---|---:|
| Formal valid units / planned units | 360 / 360 |
| Formal attempts / failed formal attempts | 360 / 0 |
| G0 qualification arrays | 120 / 120 |
| Plain versus sham trace/decision/score pairs | 30 / 30 |
| Original R/T0/N0 baseline regressions | 216 / 216 |
| T0 versus N0 complete IDs and endpoint | 72 / 72 |
| Sealed T1 versus subsequent N1 complete IDs and endpoint | 72 / 72 |
| N0 versus R | 60 / 72 |
| N1 versus R | 72 / 72 |
| Reference recovery in diagnostic tasks | 4 / 4 tasks; 12 / 12 repetitions |
| New reference regressions among controls | 0 / 20 tasks |
| Repeat-stable tasks across all five conditions | 24 / 24 |

The diagnostic tasks are HumanEval/134, /42, /145 and /138. The remaining
20 original tasks are regression controls. All 24 tasks were previously exposed;
three repetitions establish stability and do not create 72 independent prompts.
Matching covers the complete inclusive-first-EOG/cap128 contract, retaining
native overshoot in raw records. It is not a functional HumanEval pass rate.

## Review methods and provenance

1. The complete nontruncated Git trees were compared. All 4,015 pre-study
   blobs and modes are unchanged; 113 new blobs are added. The study has the
   v0.9.0 review delivery as an ancestor and contains no deletion of old evidence.
2. All eight execution source files match their formal FREEZE.json SHA256
   identities. The target frontend was mechanically regenerated from the fixed
   original harness and matched the frozen new target source byte for byte.
3. A fresh read-only CPU job retrieved the 30 GitHub archive parts at the exact
   study tree, checked their Git and SHA256 identities, reconstructed the
   1,473,070,703-byte archive, and validated all 4,073 manifest files. Temporary
   hardlinks materialized duplicate CAS content without editing frozen evidence.
4. The frozen independent raw verifier ran in a shadow report directory:
   **182,736 recorded checks passed**, including all 360 formal raw arrays.
   Its recalculated result fields match the published summary.
5. A separately written local parser imported no study helper. It reread the
   returned full captures, attempt records and native logs; validated endpoints,
   prompt IDs, commands, B570 device and offload, all five conditions, transfer
   metadata, sampler/pending state, observed graph token counts, and the local
   ledger/seal hashes. It also recomputed all 120 G0 arrays and 30 sham pairs.
   Historical arrays were compared directly with the fixed original prediction
   file, SHA256 `0201ccd1f67492510d34be567aa83f1c38d3bd1f162a970c05d3cea9d3957826`.

The successful audit is [Actions run 37178393741](https://github.com/leecdiang/HeteroSpec/actions/runs/37178393741),
source `c962c56fc6a2fb5772f1143bb7e348da018b165f`. Returned artifact
SHA256: `b671205e03a4bac7a2411a0dff2de46823860d924ed5bba3792854cc496159a9`.
The full raw review subset retained 2,742 files; its SHA256 was checked before
local extraction. See [retrieval receipt](REVIEW_RETRIEVAL_RECEIPT.json),
[separate direct review](DIRECT_RAW_REVIEW.json), [tree scope](TREE_SCOPE_QA.json)
and [audit workflow](AUDIT_WORKFLOW.yml).

The first CPU audit [run 37177989994](https://github.com/leecdiang/HeteroSpec/actions/runs/37177989994)
failed. Its log-download endpoint returned 404, so this review does not assert
a confirmed root cause for that audit failure. The subsequent audit retained
failure receipts and avoided duplicate KV materialization; it passed without
changing study data, the frozen execution code or any scientific denominator.
This failure is separate from the zero failed formal study attempts.

## Source and control assessment

Native target initialization uses a separate prefill parameter copy. Draft UB
remains 1; native caller grouping, k2, rollback, sampler rules and subsequent
target policy remain fixed across N0/N1. The native process receives the prompt,
assets and configuration, without T1 arrays or a future-token tape.

State transfer samples the pending first ID once from the source prefill logits,
preserves those logits, clones the post-sample sampler, checks serialized state
and sequence positions, and consumes the pending ID without resampling missing
destination logits. Source state remains unchanged. Same-partition sham controls
match plain execution in complete outputs, decisions, scores and decode traces.
The intervention therefore includes its explicitly declared pending-sample
boundary; it is not described as an isolated KV-byte modification.

Actual graph observations distinguish UB capacity from occupied forward tokens.
For example, HumanEval/134 has 148 prompt IDs. Target-only T0/T1 retains one
148-ID caller: graph token counts change from 148 one-token graphs to [128,20].
Native N0/N1 retains callers [147,1]: N1 records graph token counts [128,19,1].
Both candidates return to UB1 continuation and produce matching full outputs.
This validates prediction transfer across the preserved callers; it does not
establish identical internal execution shapes or a unique Vulkan kernel cause.

The local ledger and its prefix hash support 72 T1 completions and seal before
the first N1. The source/asset/protocol and prediction hashes are bound to that
seal. The study's GitHub upload occurred after measurement, so it does not
independently certify the original pre-live absolute timestamp.

## Progress and timing

The retained host-local UTC records map to the following Beijing times:

| Stage | 2026-10-04, UTC+8 |
|---|---|
| Controller starts G0 pipeline | 01:23:14 |
| G0 passes; protocol/source freeze and formal baselines begin | 02:12:38 |
| All 72 T1 predictions locally sealed | 04:21:07 |
| Last formal unit finishes | 05:18:00 |
| Independent analysis and original capsule completion recorded | 05:37:46 |
| Author's remote restore receipt | 12:28:25 |
| Final reviewed delivery commit | 12:29:32 |

The formal measurement interval is about 3 hours 5 minutes; G0 through original
archival completion is about 4 hours 15 minutes. These are operational wall
times, not controlled speed or energy comparisons. The later upload/read-back
did not add model inference. Five pilot jobs remain outside formal and G0 counts.

## Effect on the paper's acceptance case

The v0.9.0 reassessment's main concern was that the simpler reproducer had not
guided a discriminating intervention verified on native execution. This study
now supplies that chain and a finite reference-recovery result. It strengthens
the practical diagnostic contribution beyond observational reproduction.

It also supports a useful bounded stage finding: a target-prefill policy change
can change the subsequent complete native trajectory even when continuation
returns to the previous UB1 policy. Recovery does not require retaining UB128
through native continuation in these four cases. The late-fork study uses a
different cohort and cannot be pooled with this experiment as a necessity proof.

The remaining issues are generality and importance: one model pair, one B570
Vulkan stack and 24 already exposed tasks; no unseen-model or platform transfer;
no demonstrated production gain or measured debugging-time saving. The new
cohort-level reference agreement is not a universal lossless qualification.
Omitted external model/runtime/driver bytes and opaque sampler serialization
remain unavailable for independent byte authentication. The OS build change is
disclosed and the original baselines were freshly requalified.

**Acceptance argument: materially strengthened; confident accept is not yet
established.** No updated whole-paper reviewer score or numerical acceptance
probability is assigned. The old 3/6 internal ratings remain historical.
The unchanged v0.9.0 PDFs do not yet present the new experiment. The highest-value
next revision is to integrate the prediction/intervention/native-recovery chain
into the contribution statement, results, a compact before/after table and
appendix controls, then review that exact new delivery. Additional broad
parameter searches are not justified by this review.

## Integration boundary

The study branch was uploaded but had no corresponding PR when reviewed; the
only open PR was #51, containing the previously reviewed v0.9.0 delivery.
The integration includes that ancestor delivery, this independently verified
study, review receipts and synchronized living status documents. Old study
arrays, frozen execution sources, review reports, primary estimators/CIs,
manuscript PDFs/ZIPs, official styles and the author-freeze tag are preserved.
The one-time audit workflow remains reproducible at its recorded commit and is
archived here rather than installed as an automatically repeating main workflow.
No new GPU experiment, release or conference submission is performed by this review.
