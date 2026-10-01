# v0.8.6 delivery

The final source includes the author-requested humanizer pass. Original B570
prospective complete-trajectory prediction is the main result; fork intervention,
RTX program reproduction and qualified cost retain their separate roles.
R86-01 through R86-13 are COMPLETE; see the per-item revision response.
No new model inference or hardware measurement was performed.

Starting HEAD: `dccbbb53e1f91d3239e2075336100795dd6daa1e`.
Starting main: `98e8470f2559f78335de8d3473997d21b4bb55b8`.
Initial convergence content: `70dd1a527b011aa2866d5f5c803d5f722c644bab`.
Authoritative final source/content: `da8d5739eb108de7f35d3a3cfbd954d42462f2e0`.
Branch: `paper/mlsys2027-convergence-v0.8.6`.
PR base: `paper/mlsys2027-evidence-integration-v0.8.5`, dependent on Draft
[PR #44](https://github.com/leecdiang/HeteroSpec/pull/44), whose unchanged HEAD
was rechecked. Main is not represented as containing v0.8.6.
The subsequent artifacts/QA/handover commit contains this document and manifest;
its final HEAD is queried after commit and reported externally in the PR and
final author report, avoiding a self-containing commit claim.

## Exact artifacts

| Role | File in manuscript/output | Bytes | SHA256 |
|---|---|---|---|
| main | `manuscript-v0.8.6.pdf` | 277351 | `c303a71f4313d24e7ee2e31a63bf2b9aace529158b4800b57cdd4c4921275d20` |
| appendix | `appendix-v0.8.6.pdf` | 236457 | `7ec01a3d017ff61d2ceb969621fe6fdbc24bf8c849cbda1e8cbf6e8605819470` |
| hardware-only | `hardware-only-v0.8.6.pdf` | 268033 | `a45f55c07d88006a605f61676e4455548cde51e7eead775137c20361e84c0b54` |
| anonymous-source | `overleaf-convergence-v0.8.6.zip` | 126328 | `4715bfee7ecca99788a1ad4239ed98c94642f0e5aa2bd578bf63a66af1b0a8da` |
| anonymous-evidence | `anonymous-evidence-index-v0.8.6.zip` | 158338 | `7b83b97bea19c5d0ddf28d1cec49f103165849bff8a76ef5fac1da6de3a0f00f` |

Source dependency digest: `4ffe4058501bf9f102993525d4febae2db1a647c90416dc1189b6e1322ef5637`.
FINAL_ARTIFACT_MANIFEST_V086.json contains the canonical dependency mapping,
environment, per-artifact identity and check scope. CLEAN_ZIP_REBUILD_V086_QA.json
records the intentional canonical-to-ZIP comment/path transformations and hashes.
All 43 data members plus the manifest are checked. Two independent empty
extractions compile main/appendix and the internal proof with fresh aux/bbl files.
Every page's raw extracted text is exactly equal without normalization. This
is not a claim of independently built PDF byte equality.

Main: 10 body + 2 reference pages. Separate appendix: 12 pages. Internal
hardware-only proof: 9 body + 2 reference pages; it removes the runtime section
while retaining full-paper summaries and is not a submission paper. Appendix
adds raw-record tables, H2 input/witness audit and exact evidence navigation;
its two-page growth is substantive. The official CFP was checked on 2026-10-01:
[MLSys 2027 research CFP](https://mlsys.org/Conferences/2027/CallForResearchPapers).
All five vendor style files match the linked official archive byte for byte;
fonts/sizes/spacing/margins were not compressed.

## Actually executed verification

| Scope | Current status | Actual extent |
|---|---|---|
| Historical numerical/runtime/M4 secondary/Figure 3 | RERUN_PASS | 228 / 136 / 638 / 71 checks; original scientific assertions preserved, receipt outputs redirected only |
| Current convergence | RERUN_PASS | 488 checks and 8 rejecting counterexamples; raw-input identity, endpoints, estimators, pairing, directions and new derived values |
| Archive families | RERUN_PASS | All 9 accessible families; 13 entry executions including the explicit unadapted failure below |
| Unmodified B570 verifier on POSIX | RERUN_FAIL | Windows basename parsing only; Path.name-only adapter passes scientific assertions without changing original entry |
| H2 input audit | RERUN_PASS | Allowlisted inputs/local decisions, actual bonus/rejection slices, six retained negative witnesses; file/CPU checks only |
| Anonymous compact package | RERUN_PASS | Original arrays element-identical; all old scientific predicates; stdlib recomputation of new post-study inputs |
| Build/PDF/anonymity/visual | RERUN_PASS | Two fresh ZIP builds; full embedded fonts and 19 complete references; all 35 final pages viewed individually |
| Protected identity | RERUN_PASS | 3,351 protected files, no unexpected difference; original checkout and peeled scientific tag unchanged |
| Other old reviews/closeouts | PRIOR_RECEIPT_ONLY | Read as historical context, not newly executed QA |
| Old v085 fixed-word integration gate | NOT_APPLICABLE | Current prose differs; unchanged numeric/endpoint/array/negative assertions and new current checks executed |
| 358H runtime raw / exact old v084 sequence ZIP | UNAVAILABLE | Accurate absence preserved; processed 358H components and original 72 B570 arrays remain checkable |

The original 26 stdout/stderr logs are preserved byte for byte in the
**author-only** ARCHIVE_VERIFIER_RECEIPTS_V086.zip; its INDEX records arguments,
entry hashes and exit statuses. It is excluded from both anonymous ZIPs.
VISUAL_QA_V086.json/.md bind all delivered PDF and render hashes. Underfull
warnings remain recorded and were accepted after reading the final pages;
no overfull boxes, missing glyphs, duplicate labels or unresolved references
remain. Humanizer checks preserve every numeric literal, scientific macro,
citation, label and inline mathematical expression in the 14 edited files;
manual review also checks meaning and limitations.

## Added existing-record analyses

B570: all 216 raw-logit rows show numeric changes within all 72 runs. Median
absolute top-one delta is 0.06954383850097656 logits; minimum UB1/UB128 top-two
margins are 0.22905731201171875/0.20034408569335938. No raw top-one or immediate
decision changes. Six continuation-sensitive prompts first diverge 10–50
positions after their forks, all repeat-stable with capped endpoints. These
are correlated records from a separate cohort, not an explanation of old H1.

M4: medians are reconstructed from all 540 raw observations. Target-only wins
on 2/60 prompts; Guard falls back at round 8 in all six corresponding runs but
still loses to target-only on those prompt medians. Always/oracle is
1.0006919671212657. New stratified secondary intervals are Guard/Always
[1.0134733136394232, 1.0422920562267102] and Always/oracle
[1.0, 1.0018293110370748], seed 2026100101 with 10,000 draws. All original
pooled primary and standalone secondary CIs remain unchanged; no transition
cost is inferred.

358H: all processed components give conditional zero-draft/residual bounds
0.8274529834243383 CPU and 0.8351858523671982 NPU. They fix measured progress,
target work and baseline totals, with nonnegative other costs. These are
arithmetic total-time bounds, not prompt-GM bounds or measured optimization,
replay-only or persistence gains.

RTX: 180 original times give median-of-prompt-median times 1907.9175 ms target
and 2923.3248 ms serialized. The original hook p99 is 0.6 microseconds under
10-microsecond and 1%-of-shortest-R0 thresholds; it does not bound all logging.
Committed-ID event counts agree for all 90 pairs, while full-file line/byte
counts differ. They include initialization outside the timer and imply no
logging cancellation. Original instrumented target/serialized result remains
0.6458157742698285 with CI [0.629802205379344, 0.6598843928244866]; the sealed
original's one-ulp-higher value is separately retained.

No unresolved new validity error was identified for the current limited
claims. Importance and transfer remain open review questions. Original
single-stack H1, sampled fork scope, shared RTX numerical routines, missing
same-set UB2 competitor, instrumented cost boundary, fixed 358H accounting
assumptions and M4 negative incremental benefit remain explicit limitations.
Named current review attachments were absent; vote history comes from the
user prompt and is not attributed to unseen reports. No new formal or mock
scoring, merge, tag/release, submission or messaging was performed.

Next: author review of these exact artifacts, followed by an independent
submission-level review only when separately requested by the author.
