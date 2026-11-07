# Author handover v0.8.6

The v0.8.6 non-experimental convergence revision and requested humanizer pass
are complete. Read the exact main and separate appendix first, then the
revision response and claim/evidence maps. Original B570 draft-free prospective
full-trajectory prediction is the center: 72/72 on 24 repeat-stable prompts ×3,
including all 12 runs of four reference-divergent prompts, versus reference/live
60/72. Predicting a blocked path does not make it a lossless replacement.
The forks, RTX programs and cost studies answer separate questions.

## Version identity

Starting/base HEAD: `dccbbb53e1f91d3239e2075336100795dd6daa1e`.
Starting main: `98e8470f2559f78335de8d3473997d21b4bb55b8`.
Initial implementation content: `70dd1a527b011aa2866d5f5c803d5f722c644bab`.
Final humanizer-edited source/content: `da8d5739eb108de7f35d3a3cfbd954d42462f2e0`.
Branch: `paper/mlsys2027-convergence-v0.8.6`.
New Draft PR base: `paper/mlsys2027-evidence-integration-v0.8.5`, with dependency
[PR #44](https://github.com/leecdiang/HeteroSpec/pull/44). Its head remains the
starting dccbbb53e1f91d3239e2075336100795dd6daa1e and it remains Draft/unmerged.
The artifacts/QA/handover commit follows the source commit. Final delivery HEAD
and the new Draft PR URL are queried after that commit and recorded in the PR
and final author report; this file does not invent its own containing SHA.

Original checkout `/Users/lee/Projects/HeteroSpec` stays on
`paper/mlsys2027-reviewer-convergence-v0.8.3` at
`8a6e1b4649e6b678ebb4b5e11894c0ddd537d354`, with unchanged clean state.
Scientific tag `mlsys2027-v0.8-author-freeze` still peels to
`1d3b556c93b477680788dfd1eb0737dfe9eee28c`. Actual comparisons preserve 3,351
baseline files: frozen numbers, code/protocols/raw evidence, arrays, earlier
PDFs/ZIPs/receipts/reviews, Figure 3 and official vendor styles. There are no
unexpected differences. Explicit current prose/table/entry changes are listed
in PROTECTED_OBJECTS_V086.json and the source dependency mapping.

## Author review map

R86-01–13 are COMPLETE, with implementation locations and results in
REVISION_RESPONSE_V086.md. CLAIM_AND_CAMPAIGN_MAP_V086.md links headline claims
to cohorts, references, inputs, endpoints and timers. FREEZE_CAPABILITY_MAP_V086
separates source/policy, predictions/tapes, acknowledgement, first-live and
analysis objects, including the M4 wrong build-manifest field and recovered
actual calibration-freeze link. Original error and STOPPED markers remain.
FIRST_PAGE_STORY_AUDIT_V086.md checks the central result and bounded use;
STOPPING_RULE_V086.md records completion without predicting acceptance.

HUMANIZER_PASS_V086.md documents the author's requested style edit. The pass
rewrites abstract announcements, stiff phrasing and repeated qualifications
in 14 current TeX files. Every numeric literal, scientific macro, citation,
label and inline formula matches the pre-style source; semantic review also
preserves conditions and uncertainty. It does not provide an AI-detector score.

REVIEW_CONTINUITY_AUDIT_V086.md retains independent review history: v083 R1/R3/R5
Weak Accept, R6 Accept, R2/R4 Weak Reject, composite Weak Accept; v085 five Weak
Reject and one Weak Accept, composite Weak Reject. Same role labels do not
identify fixed reviewers. The three named new review attachments were absent,
so v085 votes are attributed to the supplied prompt and no unread report
content is invented. No new six-reviewer or simulated acceptance scoring was run.

## Delivered documents and evidence

Main has 10 body +2 reference pages; appendix 12; internal hardware-only proof
9 body +2 references. The proof only tests section removal and references;
it retains full-paper summaries and is not a submission manuscript. Appendix
growth adds H2 input/event witnesses, raw-record analyses and exact evidence
entries. The official 2027 CFP was checked; references do not count toward the
10-page main body and there is no stated separate-appendix page cap. All five
vendor style files equal the officially linked archive. No typography or
margin compression was used.

Use evidence/FINAL_ARTIFACT_MANIFEST_V086.json and DELIVERY_V086.md for full
lengths/SHA256 and source dependency digest `4ffe4058501bf9f102993525d4febae2db1a647c90416dc1189b6e1322ef5637`. The five outputs are
under manuscript/output; no old output was replaced. The source ZIP has all
43 data dependencies plus its hash manifest. Two independent empty extractions
build main, appendix and the internal proof, with fresh aux/bbl; raw page text
matches exactly without normalization. All 35 final pages were individually
rendered and inspected after the humanizer pass, bound by final PDF/PNG hashes.
PDF text/metadata/actions and source/evidence ZIPs are anonymous; 19 bibliography
entries retain full author lists, all fonts are embedded, and no unresolved
citations/references, duplicate labels, missing glyphs or overfull boxes remain.
Underfull warnings are retained and judged readable in the final page inspection.

The compact anonymous evidence ZIP retains original arrays element by element
and adds post-study inputs, results, CSVs and a standard-library calculator.
Extract it and run `python3 -B verify.py`. The source ZIP needs only TeX;
extract into an empty directory and run `latexmk -pdf main.tex` and
`latexmk -pdf appendix.tex`. The unchanged full anonymous H2 capsule remains
`anonymous-a5919b59342ecc68bd5f57d3c2b192edf62933b2645924381c3765dd50beb369.tar.gz`,
60,152,666 bytes, SHA256 equal to that filename digest. The compact index
identifies its separate program/tape/event entry. Author paths, review files,
repository/PR identities and original timestamps stay outside both anonymous
ZIPs. Hashes/ordinals do not certify original absolute chronology or omitted
weights/runtime/compiler/driver bytes.

## Recomputed existing records

B570 uses all 216 raw-logit rows over 72 correlated runs. Median absolute
top-one delta is 0.06954383850097656 logits; minimum retained top-two margins
are 0.22905731201171875 UB1 and 0.20034408569335938 UB128. Raw top-one and
immediate decisions remain unchanged. All six sensitive prompts first diverge
10–50 positions after their fork, stable over all three repetitions with capped
endpoints. KV byte/length/position checks and existing clone/R0 controls are
specified; opaque sampler bytes and omitted binary identity are not asserted.
This new cohort cannot explain old H1's four tasks or a single-block restoration.

M4 medians come from all 540 raw held-out observations and match all original
60 rows. Target-only beats Always on 2/60 prompts, both Spec-Bench; all six
Guard runs fall back at round 8 but their Guard medians still lose to Target.
Always/oracle is 1.0006919671212657. New family-stratified secondary bootstrap
uses seed 2026100101 and 10,000 draws: Guard/Always CI
[1.0134733136394232,1.0422920562267102], Always/oracle CI
[1.0,1.0018293110370748]. Original pooled primary/secondary streams and CIs are
unchanged. Oracle choice is hindsight between two measured fixed modes, with
no dynamic-policy or transition-cost claim.

358H all processed components give CPU/NPU zero-draft-and-residual bounds
0.8274529834243383/0.8351858523671982. They hold only at fixed measured progress,
target work, baseline totals and nonnegative other costs. They are arithmetic
total-time bounds, not prompt-GM bounds, an optimization experiment or a
measurement of separable replay/persistence savings.

RTX 180 times retain the 30×3 pairing. Median-of-prompt-median latencies are
1907.9175 ms Target and 2923.3248 ms Serialized. Empty-hook p99 is 0.6 microseconds
against 10-microsecond and 1%-of-shortest-R0 thresholds, not a bound on all
logging. Complete native logs have differing line/byte counts while committed-ID
event counts match all 90 pairs; they include initialization outside the timer
and do not imply logging-cost cancellation. Primary instrumented result remains
0.6458157742698285 with the original CI/seed/order. The sealed original's
one-ulp-higher value remains separately recorded. No qualified same-study
batched timing or logging-free production estimate is claimed.

## Execution scope and remaining judgment

Current scientific checks: 488 plus 8 rejecting counterexamples. Historical
numerical/runtime/M4 secondary/Figure 3 checks: 228/136/638/71. All nine accessible
archive families were personally rerun with file/CPU entries. The 13 entry runs
include 12 zero exits and the retained original B570 POSIX basename failure;
Path.name-only adaptation passes its scientific checks. Original stdout/stderr
are preserved in author-only ARCHIVE_VERIFIER_RECEIPTS_V086.zip, excluded from
anonymous exports. H2 source/allowlist/local-decision review includes actual
bonus/rejection slices and six existing negative witnesses, with no model run.

Other earlier reviews/closeouts remain PRIOR_RECEIPT_ONLY. v085 fixed-word
integration checks are NOT_APPLICABLE to new prose; underlying unchanged
scientific predicates and current gates are executed. 358H runtime raw traces
and exact old v084 sequence ZIP are UNAVAILABLE. Original 72 arrays and processed
component records remain separately checkable. No old PASS is presented as
this round's execution.

No unresolved new validity error is identified for the current limited claims.
The contribution's importance relative to known path sensitivity remains open.
Single-stack H1 scope, sampled fork states, failed RTX H1 transfer, shared H2
numerical routines/missing same-set UB2 competitor, instrumented cost boundary,
conditional 358H accounting and negative M4 incremental benefit remain explicit
research limits. They do not turn this revision into an open-ended experimental
program. No new inference, measurement, predictor discovery, reserved selection,
merge, tag/release, submission or messages occurred.

Next is author review of these exact artifacts. Independent submission-level
review is a separate next request; none has been started automatically.
