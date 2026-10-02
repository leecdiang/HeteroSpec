# RTX V4 independent raw-evidence closeout — 2026-10-02

**PASS.** All nine sealed RTX V4 capsules were retrieved from exact study HEAD `8f30449d51bca1fe4907c392c5c65d5cc0fbcd3f`, reconstructed from their indexed parts, and replayed with the original frozen offline verifier. A separate parser reconstructed all 57 native A-live arrays and 171 B arrays/QPC intervals, then recomputed the complete-cohort gates, per-prompt medians and frozen paired-prompt bootstrap. This closes the raw-access limitation of the earlier text-only review.

The work used CPU only. It downloaded no models/runtime binaries, launched no model process and made **zero new model forwards**. Original scientific files, source, arrays, tapes, manifests, failed states and the author-freeze tag were not modified. The author requested not to treat fan adjustment as a blocker; the existing protocol-amendment disclosure remains intact.

## Exact audit and evidence identities

| Role | Identity |
|---|---|
| Sealed scientific source HEAD | `8f30449d51bca1fe4907c392c5c65d5cc0fbcd3f` / PR #49 |
| Independent audit source commit | `2c37177d635eeefb46b13b5f11439389ba121e52` |
| Actual CPU execution | [Actions run 37015269566](https://github.com/leecdiang/HeteroSpec/actions/runs/37015269566), conclusion success |
| Downloaded readable audit artifact | ID `11229134738`, 326651 bytes, SHA-256 `580df21cfd72956c0f65228707f20c2a4c7dfc32ca9be56c6a45a532bfca7b90` |
| V3 terminal-history merge | `7f365f4fa87aedcebc2ae4cae5d8071b8223132d` / PR #48 |
| V4 completed-evidence merge | `4500d140d78f77d0e314044acab1ae8e68dec42f` / PR #49 |

The GitHub artifact expires after its retention period; the readable 45-file result is permanently copied under [RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002/](RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002/). Its two original phase manifests retain the exact bytes and SHA-256 of their members in the sealed author capsules. The capture reconstruction is explicitly derived, while full native logs stay in the original content-addressed capsules.

## Independently reproduced results

| A against native batched live | Full-array pairs | Wholly exact prompts | Mismatch prompts |
|---|---:|---:|---|
| UB1 reference | 51/57 | 17/19 | HumanEval/15, /18 |
| Target-only UB2 | 51/57 | 17/19 | HumanEval/15, /25 |
| Independent P/R (H2) | 57/57 | 19/19 | None |
| Fresh R-only replay | 57/57 | 19/19 | None |

UB2 and reference have equal aggregate counts but different counterexamples. These results reject only the predefined UB2 candidate's complete-cohort prediction claim, not every target-only method or the absence of any possible history-free predictor. H2 and R-only establish finite empirical matching, without necessity, uniqueness or minimality.

| B fresh matched path | Full-array gate | Status | Reference/candidate ratio | 95% paired-prompt CI |
|---|---:|---|---:|---|
| Batched k=2, UB2 | 51/57 | BLOCKED | null | null |
| Serialized k=2, UB1 | 57/57 | QUALIFIED | 0.6773510334393157 | [0.6616533074169811, 0.6918118724220993] |

The qualified serialized path is slower: geometric paired cost multiple 1.476339, with 0/19 prompts faster. All 171 measured B intervals were parsed from raw QPC endpoints; complete output arrays, termination, count, terminal ID, secondary-clock agreement, three-repeat medians and 10,000 frozen-seed bootstrap draws were checked. Failed-path speedup/CI remain null. The new cohort is not an optimization comparison against the old 0.646 result.

## Replayed capsules and validation scope

All nine engineering, pre-live and complete author/anonymous capsules passed actual fresh extraction, exact manifest/member hashing and the frozen offline verifier. Their full hashes, part retrievals, engineering gates, endpoint repair coverage, 15 raw/statistical negatives, 14 capture corruption fixtures, A/B results and author Git membership checks are retained in [ARCHIVE_REPLAY.json](RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002/ARCHIVE_REPLAY.json) and each original verifier stdout file.

The separate raw parser and statistics implementation are [scripts/audit/rtx_v4_raw_closeout.py](../../../scripts/audit/rtx_v4_raw_closeout.py); the reusable read-only workflow is [.github/workflows/rtx-v4-raw-closeout.yml](../../../.github/workflows/rtx-v4-raw-closeout.yml). The source was fixed before execution and its file bytes are preserved in this maintenance. Its inputs are pinned to the scientific HEAD above, irrespective of later main commits.

Key readable files:

- [CLOSEOUT.json](RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002/CLOSEOUT.json): actual run, source identity, all-nine PASS and zero-forward scope.
- [INDEPENDENT_RAW_RECOMPUTATION.json](RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002/INDEPENDENT_RAW_RECOMPUTATION.json): independently reproduced A/B outcomes.
- [A-live.ORIGINAL_RECORDS.json](RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002/A-live.ORIGINAL_RECORDS.json) and [B-formal.ORIGINAL_RECORDS.json](RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002/B-formal.ORIGINAL_RECORDS.json): exact original author phase manifests, not regenerated runs.
- The two RAW_MEMBER_CORRESPONDENCE files bind readable copies to original capsule members by SHA-256/length; FORMAL_CAPTURE_RECONSTRUCTION is a derived view, not a replacement for original native logs.
- REMOTE_RETRIEVAL records every fetched Git blob, sealed part SHA-256 and assembled package identity. Full raw logs/tapes remain in the unchanged original packages.

For text files larger than GitHub's Contents API inline limit, resolve the blob SHA from the Git tree and fetch the text blob, or read it in an ordinary checkout. Do not mistake an empty Contents response for an empty file.

## Repository closeout and next action

PR #48 retains V3's two actual capture failures and incomplete denominators; PR #49 contains the separately authorized V4 result. V3 failed prefixes are not pooled into V4. V4 comprises 19 exposure-conditioned prompts, 285 A conditions and 171 fresh B conditions; repetitions are not independent prompts. Both PRs merge directly to main.

The 3,435 baseline files and all 159 V3 additions / 219 V4 additions retain their science bytes at the evidence merges. This maintenance only adds independent audit source/results and updates living status documents. It does not modify TeX, macros, Figure 3, official styles, delivered PDFs/ZIPs, historical reports or the author-freeze tag. The manuscript remains v0.8.6; no v0.8.7 manuscript is claimed here.

Next is a new manuscript integration and independent submission review. No additional GPU study or positive-result search is required by this closeout. B570 dense scanning, new backends, 358H persistence and M4 variants remain deferred. Release/submission decisions stay separate.

The scope remains finite: shared numerical libraries, exposure-conditioned cohort, instrumented post-prefill latency, no throughput/energy claim. Offline archives cannot authenticate omitted external models/runtime/driver binaries or provide an independently trusted timestamp service. These are retained study boundaries, not newly discovered validation failures.
