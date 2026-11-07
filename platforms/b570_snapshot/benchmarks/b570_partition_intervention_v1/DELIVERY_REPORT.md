# Completed V1 delivery

## New measurements and bounded conclusion

Engineering qualification passed all 24 fresh R0 executions. The reserved experiment completed its frozen 24 prompts × 3 repetitions, retaining all 72 runs and 72 eligible forks. The checkpoint rule was the first verification block starting with at least 64 committed IDs. All raw score records differed across UB1 and UB128 (72 executions, 24 prompts), while raw top-1 IDs and actual immediate target decisions stayed identical (0 differing executions or prompts; 195 paired actual decision events). Downstream complete committed-ID trajectories differed in 18 executions on 6 prompts.

The result is `SCORE_OR_DOWNSTREAM_EFFECT_WITHOUT_IMMEDIATE_DECISION_EFFECT_AT_SAMPLED_CHECKPOINTS`. It does not support an immediate decision effect at the sampled block, nor an all-endpoint NO_EFFECT conclusion. Later trajectory differences remain a separately reported secondary endpoint. The causal scope is the tested, byte-checked live fork states and the frozen continuation policy; no unique numerical operation or other GPU is identified. Repetitions and within-prompt decision events are correlated.

## Validation and portable evidence

Host pre/post byte and environment audits passed. The official independent verifier passed 24,677 checks, including 252 serialized KV metadata records, with zero errors. It was rerun successfully after clean reconstruction and extraction of the archive; all 888 manifest files passed byte-length and SHA256 checks. Retained Git objects also passed file-membership and parent-ancestry checks. Three isolated corruption fixtures had been rejected before formal measurement.

The archive is 2,457,530,689 bytes in 49 ordered, SHA256-addressed parts. Concatenated archive SHA256:

`d3a56911abd76f121475b83861ef7fe7927308af1812f5400e5060e117b3bfb1`

Its content head is `46fdbf40118050e457015376eaac54d2b272d393`. Packaging and this delivery report necessarily follow that head and are not included inside their own archive. Consult `PACKAGING_NOTES.md` and the artifact `ARCHIVE.json` for reconstruction and the official verifier command. Models and runtime binaries are excluded from the public bundle; offline checks cannot authenticate omitted bytes. Sampler identity relies on the pinned recursive clone implementation, recorded chain/seed/history, and same-partition R0 continuation controls rather than unavailable opaque sampler serialization.

## Provenance and review

Frozen formal source/input/schedule commit: `0ce09349bc12c0818584f47e0c24d03111258cc1`.
Execution record commit: `f685e44`.
Closeout commit: `3d34d0c`.
Packaging adapter/documentation commit: `46fdbf4`.

Draft PR: https://github.com/leecdiang/HeteroSpec/pull/41. Keep it draft and unmerged. All changes are additions in the three new V1 directories. The original checkout remains clean at `4e16e4589cba75a39f2ce90ad7f30b4152901217`; historical B570 evidence and manuscript files are unchanged. No reserved replacements, parameter search, timing/energy campaign, or manuscript inference was performed.
