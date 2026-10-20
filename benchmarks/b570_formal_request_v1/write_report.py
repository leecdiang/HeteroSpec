from pathlib import Path
import json
r=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
a=read(r/"ANALYSIS.json");q=read(r/"QUALIFICATION_RECHECK.json");l=read(r/"BUDGET_LEDGER.json")
table="\n".join(f'| {x["input_id"]} | {100*(1-x["service_QB_over_dualPQ"]):+.3f}% | {x["service_QB_over_R"]:.4f} | {100*(x["service_PQA_over_PQB"]-1):+.3f}% |'for x in a["per_input"])
qt="\n".join(f'| {x["input"]} | {x["tokens"]} / {x["stop"]} | {x["cycles"]} | {x["accepted"]} | {x["full_logit_pairs"]} | {",".join(str(g[0])for g in x["geometry"])} |'for x in q["rows"])
text=f"""# B570 formal finite-panel result

**{a["decision"]}**

This is a completed prospectively registered finite-panel experiment, not an unseen-input or cross-date confirmation. Preregistration/source freeze commit: `809851f26e7a8f8e230aa26ecba8e639b97e5728`, created before GPU execution. Parent scientific candidate: PR133 `34787ab56f0ae8b533d18fe02db2d37e8ebb63a4`.

## Reference admission

All four registered inputs pass complete native endpoint equivalence between R, PQ and QB: token IDs, EOG flags, length, terminal token and stop reason. All PQ/QB saved full logits vectors, including discarded verification rows and draft proposal vectors, match byte for byte. All complete PQ/QB cycle traces match. Qualification covers actual q2/GQA32:8 across36 target layers on B570.

| Existing input | Tokens / stop | Verify cycles | Accepted proposals | Full-logit pairs | Actual physical key |
|---|---:|---:|---:|---:|---|
{qt}

The four explicit input-ID sequences come from the project's existing PROMPT_TOKENS archive. They are exposed inputs, selected before this experiment for short/long geometry, not chosen using their new outputs or timing. Their chat-formatted input identities differ from PR133's raw HumanEval/42 prompt. R_e is a prospective q1/64-token reference for these sequences; historical R and16-token qualification remain unchanged. The cap is64, not a forced64-token output: natural EOG is honored.

## Clean full costs

Four independent native processes execute four explicit warmups and16 measured requests each: **64 measured requests plus16 warmups**, after12 qualification requests. All measured endpoints match their registered R_e, and all speculative cycle traces match the qualification trace. PQ_A/PQ_B call exactly the same implementation.

| Input | QB reduction vs dual-PQ, service | QB / target-only service | PQ_A / PQ_B imbalance |
|---|---:|---:|---:|
{table}

Primary equal-input geometric-mean service ratio QB/dual-PQ: **{a["service_QB_over_dualPQ"]:.8f}**, reduction **{100*(1-a["service_QB_over_dualPQ"]):+.4f}%**.
Request-only secondary ratio: **{a["request_QB_over_dualPQ"]:.8f}**.
QB/target-only service ratio (separate draft economics): **{a["service_QB_over_R"]:.8f}**.
Largest aggregate per-input A/A imbalance: **{100*a["largest_aggregate_AA_imbalance"]:.4f}%**.
Registered practical threshold: **{100*a["threshold"]:.4f}%**.
Per-process paired panel ratios: `{a["per_session_ratios"]}`.

The predeclared screen requires a reduction above both2% and A/A imbalance, and QB below dual-PQ in every process-level panel aggregate. This engineering screen is not a hypothesis test or equivalence test. All paired blocks are reported in TIMING_TABLE.csv; no outlier removal, favorable subset selection, population confidence interval or optional stopping is used. Repeated processes do not create additional independent workloads.

## Cost and implementation boundaries

Primary `service_seconds` includes fresh context creation/graph reservation, target and draft prefill as applicable, generation, sampling, state maintenance, synchronization and context destruction. Shared model loading is measured separately. Request-only time excludes context lifetime overhead. Host full-logit copying, finite checks and cycle-record construction are included; post-request comparisons and file output are excluded. No node observer or raw-vector file writes run in timed requests.

Each process warms every arm with the previously qualified16-token prompt, checking the complete reference and trace; warmup costs are retained separately. This separates registered warmup from measurement but does not claim machine cold boot or flushed driver caches. Processes execute sequentially on the user's B570; exclusive machine ownership/background-load control is not established.

Phase fields are synchronized host wall durations around existing decode calls, separated by role/phase. There is no additional GPU synchronization relative to the inherited host. Host/other residual is explicitly unassigned. These fields are neither GPU kernel active time nor a critical-path proof, and their ratios cannot establish a physical bandwidth bottleneck.

The frozen q1 reference uses token-by-token prefill. Draft weights remain resident even for target-only R, but R creates no draft context. This is a reference-matched standalone request bridge, not an optimized production serving implementation or a proven software ceiling. The study evaluates layout and draft economics under this declared execution policy; it does not claim no faster software implementation can exist.

## Paper conclusion

The result extends the B570 evidence from a single16-token key256 bridge to four registered inputs with a64-token cap, natural EOG, and observed key256/512. It supports backend and stateful-request migration under the stated reference. Cost benefit is a separate outcome governed by the reported ratios and failed/passed screen; bytewise equality alone is not acceleration evidence.

Under PR130's paper structure, place this result in State Formation and Backend Transfer and Real-Request Scope/Mapping Costs. Retain the existing RTX E2 gains with their original population and scope; do not pool the B570 panel with them. Do not reopen QH micrographs or infer a new accelerator. A physical hardware opportunity still requires an optimized software baseline, a stable residual and causal resource evidence.

## Evidence and accounting

All8 native processes return normally with complete capture and no deadline kill. Whole-parent charge this study: **{l["new_charged_seconds"]:.7f}s**; prior **401.2123575s** remains unchanged; combined historical charge **{l["all_history_cumulative_seconds"]:.7f}s**. Charges include loading/cleanup and are not GPU-active seconds.

COMPACT_EVIDENCE.zip preserves all result/progress/geometry JSON, logs and receipts. RAW_LOGITS_MANIFEST.json enumerates full vectors by size/SHA256. Full vectors are additionally archived locally; LOCAL_ARCHIVE.json pins that archive and explicitly records that it is not hosted on GitHub. This is local execution plus CPU recheck, not independent external raw-data certification.

No actor, RTL, CPU8 expansion or PR merge.
"""
(r/"RESULT.md").write_text(text,encoding="utf-8")
paper=f"""# Paper-ready evidence addendum: B570 finite request panel

Use with PR130's reference-preserving QB method and backend/cost chapters. Do not replace existing RTX request benefits.

## Candidate English paragraph

We further evaluated the Vulkan port in a prospectively fixed four-input Qwen3 request panel, using a 64-token output cap and natural end-of-generation termination. A target-only q1 reference, serial-query attention (PQ), and query-to-batch attention (QB) produced identical complete native endpoints. PQ and QB additionally matched all saved full logits vectors byte for byte and agreed on the complete speculative state traces. The observed verification graphs used q=2 and physical key extents256/512 with32 query heads and8 KV heads. We then measured64 requests in four independent process sessions, with16 separately reported warmup requests and identical-implementation PQ controls. The equal-input geometric-mean QB/dual-PQ service ratio was {a["service_QB_over_dualPQ"]:.6f}; the QB/target-only ratio was {a["service_QB_over_R"]:.6f}. The registered practical-benefit screen returned {a["decision"]}. These results establish reference-preserving migration for this finite panel, while keeping semantic admission distinct from measured request benefit.

## Required accompanying limitations

Four previously exposed inputs, one model pair, one machine/date, k=1 and one bounded reference policy. Token-by-token prefill; shared loaded models; service window includes fresh context lifetime but excludes shared model loading. No population confidence interval, equivalence claim, serving-wide qualification or hardware mechanism attribution. Complete raw vectors remain at the original machine; compact metadata and hashes are in this repository.

## Figure/table data

Use TIMING_TABLE.csv for per-input/per-process paired ratios and ANALYSIS.json for full service/request/stage rows, including warmups. All16 paired blocks must remain visible. A/A controls and target-only economics should accompany the QB/PQ panel; do not publish a headline speedup alone.
"""
(r/"PAPER_ADDENDUM.md").write_text(paper,encoding="utf-8")
print(text[:4000])
