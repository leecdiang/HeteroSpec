# RTX: one bounded active-rechunk challenge

Date: 2026-11-04. Target: IEEE TPDS. Status: design and CPU tooling only.
Scientific parent: PR174 `aa7ff4e64752be3de0d7974febbce453ae3a96c0`.
Entry: read this file and REVIEW.md, then run `coverage.py` on saved data.

## Decision and question

Close the representative PR174 study with its negative AUTO result. Do not retrain AUTO, add sessions to that panel, or change its sample weights. The remaining question is narrower: **when restarting a full-width caller actually changes the execution schedule, does it remove the benefit of attention-local cuts, and what part of complete service changes?**

The published 32-root panel has four local-cut activations but only one WB-cut/WB-rechunk schedule difference. At H=205 and append=84, their widths are [32,19,13,20] and [32,19,32,1]; both have four calls. A name or call count alone therefore does not establish a distinct comparator. This study is a conditional structural challenge, not a replacement estimate of ordinary traffic performance. It must be reported even when the simple caller wins.

## A. Saved-data opportunity census; zero GPU requests

Use the existing full `common-census.json` (6423 eligible natural paths), common-panel.json, and retained exposure records. Do not re-tokenize or run the model merely to do this census. Reconstruct ordered (physical head, width) sequences for QB, WB-cut and WB-rechunk. Report paths, roots, differing sequences, differing call counts and tile fragmentation separately. Granule1 is the actual deployment; granule32/64 scenarios remain hypothetical.

Build `exclusions.json` with `root_ids` and nonempty `evidence` identifying all earlier model-exposed roots, including provisional/failed engineering epochs. The script also excludes all44 original calibration/test roots, protecting the running B570 experiment. Validate exclusions against saved job inputs; a declaration alone does not certify them.

Run `python coverage.py common-census.json common-panel.json exclusions.json coverage.json`. This selects one hash-ranked natural path per root BEFORE conditioning on unequal WB schedules, then ranks unexposed qualifying roots with the fixed seed. It does not inspect output, latency, winning arm or answer quality. No padding, truncation, manufactured prefix, changed cache granule or replacement of selected failures is allowed.

If fewer than four unexposed root representatives have unequal schedules, STOP with a CPU-only opportunity report. This is a resource decision, not a power criterion. Otherwise select at most eight roots. Publish source, exclusion, panel and timing-code hashes before any new selected output. Do not broaden the corpus or invent more favorable offsets to fill the panel.

## B. Native conditional comparison

Keep PR174 Qwen3-8B Q8_0, all-GPU target-only, C4096, F16 KV, non-flash, qmax32, greedy cap128/native EOG, tokenizer/template, original scalar oracle, exact-token prefix snapshots and file-backed lifecycle. Use the unchanged packed numerical core in every candidate. No draft, new model, new GPU, AUTO or numerical-kernel optimization belongs in this study.

Arms: QB, WB-cut, WB-rechunk. Starting states, appended token sequence, output flags and stopping semantics are identical within a root. Reuse the implemented caller, not a synthetic imitation. Assert the observed full ordered call sequence against the selected CPU plan. All original paths and results remain immutable; use fresh result directories and a new result branch from this design PR.

For n selected roots (4<=n<=8):
- Two independent original-reference runs per root: 2n requests.
- Candidate heavy-vector and observer-off qualification for each of three arms: 6n requests. Compare committed full-vocabulary bytes, token sequence, positions, final state and intended call sequence. Never substitute endpoint-only equality.
- Two separately loaded paired sessions, all roots and three arms, immediate same-arm warmup before every measurement: 12n requests, comprising 6n formal and 6n warmup requests. Rotate all six arm orders deterministically across root/session blocks; freeze the order before timings.
Total scientific requests: 20n, at most160. All-stage cap: 200, leaving at most40 pre-freeze engineering requests, charged including failed/incomplete starts. No numerical retries or replacement roots in the frozen scientific panel. Source repairs that change arithmetic or policy require a new decision; do not silently restart this panel.

## Cost and interpretation

Keep complete receipt-to-response service as an outcome, including actual file read/index/reset/lookup/import, policy/planning, append, continuation, synchronization and response commit. Retain setup, model load, snapshot creation and host-owned totals separately. Do not switch to a host-memory cache to rescue the speed ratio.

Add synchronized, nonoverlapping timestamp boundaries after native state import is ready, after the final appended query completes, and at response completion. Report append execution including its planning/graph work, subsequent continuation, and complete service. Inspect observer overhead before freeze. Existing cumulative `append_from_receipt_s` and `import_s` are not isolated kernel phases; do not subtract their geometric means or infer disk/PCIe costs. Tracing is separate from primary timing; existing qualification calls can record the actual caller widths.

The primary mechanistic comparison is QB versus WB-rechunk on this explicitly conditioned cohort. WB-cut distinguishes the effect of restarting chunk alignment from the effect of moving the cut. Report every root and both session directions, paired geometric ratios and absolute paired time differences for append and full service. A root bootstrap may be a descriptive uncertainty summary, with the small root count stated. No three-percent pass target, no significance-driven repeats, and no population-average claim from this selected cohort. A service loss stays a loss even when append gets faster.

## Stop and integration decisions

1. No adequate natural schedule-distinguishing support: stop before GPU and report the coverage boundary.
2. WB-rechunk matches/beats QB: prefer the simple caller where appropriate; keep reduction-preserving arithmetic as the shared contribution. Do not launch another rescue benchmark.
3. QB helps append but not service: retain the conditional mechanism result and its limited practical contribution.
4. QB helps both: state only the conditional deployment/workload claim; do not replace PR174's representative null result.
5. Numerical mismatch: retain it and halt this panel; no useful-performance claim from the passing subset.

After this single bounded study, stop RTX GPU work and synthesize with B570. Do not touch PR175, rerun the original44 roots, change the submitted arXiv, rename the repository, merge branches or rent a GPU.

## Deliverables

A separate result PR with the full output-free census and denominators, exclusion provenance, frozen selection/source identity, observed call sequences, numeric comparisons, disjoint phase and service costs, all failures, request count and one conclusion that can change the method choice. Portable source and existing artifact tools are sufficient; do not turn packaging into another experiment campaign. If Phase A stops, a CPU-only result is completion.
