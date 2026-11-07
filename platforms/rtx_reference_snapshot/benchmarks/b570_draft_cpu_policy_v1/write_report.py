from pathlib import Path
import json
r=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
a=read(r/"ANALYSIS.json");st=read(r/"STAGE_SUMMARY.json");q=read(r/"QUALIFICATION_RECHECK.json");l=read(r/"BUDGET_LEDGER.json")
table="\n".join(f'| {x["input_id"]} | {100*(1-x["service_DRAFT1_over_dualBASE"]):+.3f}% | {x["service_DRAFT1_over_R"]:.4f} | {100*(x["service_BASEA_over_BASEB"]-1):+.3f}% |'for x in a["per_input"])
passed=a["decision"]=="PRACTICAL_FINITE_PANEL_SCREEN_PASS"
recommend="Retain draft CPU1 as a qualified lower-cost policy for this fixed domain; do not generalize without additional admission."if passed else"Do not promote draft CPU1 as a performance improvement; retain the original policy and this negative controlled result."
text=f"""# B570 draft CPU parallelism: exact-reference controlled result

**{a["decision"]}**

One factor changed: draft context CPU thread parameters8 ->1. Target stays8; runtime DLLs, GPU kernels, weights, q1 prefill, QB layout, sampling and state protocol are unchanged. See SOURCE_AUDIT.md for the source and OpenMP build evidence. A disposable ggml pool object is not proof that OS worker threads are recreated; no persistent-threadpool variant was run.

Preregistered before GPU execution in `8c0d082debf279c8c23bccb12088fcee19ff37e8`, with qualification and estimator committed before timing in `e126060f85de0c42d9846c780fc5c158e5ccbb32`. Scientific parent is PR134 `51febaddcf49bb18565e568cf964a6e5c78876c9`.

## Reference and measurement

All four fixed inputs pass. **346 candidate target/draft full-logit vectors match the original PR134 QB files byte for byte**, including rejected verification rows. Complete IDs/EOG/length/terminal/stop and speculative cycle traces remain identical. No replacement reference or inherited performance PASS.

Four qualification requests precede four independent timing processes. Each timing process runs four registered warmups and16 measured requests: **16 warmups and64 measured requests**. Every measured endpoint/state trace passes. BASE_A and BASE_B are identical QB threads8 implementations. DRAFT1 is the candidate; R is target-only8 with draft weights resident.

| Input | DRAFT1 service reduction vs dual-BASE | DRAFT1 / R service | BASE_A / BASE_B imbalance |
|---|---:|---:|---:|
{table}

Equal-input geometric-mean DRAFT1/dual-BASE service ratio: **{a["service_DRAFT1_over_dualBASE"]:.8f}**; reduction **{100*(1-a["service_DRAFT1_over_dualBASE"]):+.4f}%**.
Request-only ratio: **{a["request_DRAFT1_over_dualBASE"]:.8f}**.
DRAFT1/target-only service ratio: **{a["service_DRAFT1_over_R"]:.8f}**.
Largest input-aggregate A/A imbalance: **{100*a["largest_aggregate_AA_imbalance"]:.4f}%**; registered practical screen: **{100*a["threshold"]:.4f}%**.
Per-session panel ratios: `{a["per_session_ratios"]}`.

Primary analysis uses paired service ratios, equal input weighting and all16 blocks. No outlier removal or stopping for significance. Four fixed exposed inputs, one model pair/machine/date: descriptive finite-panel estimates, no population confidence interval or equivalence claim.

## Locating costs

Registered synchronized host phase fields give descriptive arithmetic means:

- Baseline draft prefill: **{st["draft_prefill_BASE_seconds"]:.6f}s**; DRAFT1 draft prefill: **{st["draft_prefill_DRAFT1_seconds"]:.6f}s**, reduction **{100*st["draft_prefill_reduction"]:.3f}%**.
- DRAFT1 total draft prefill/decode: **{st["draft_decode_plus_prefill_DRAFT1_seconds"]:.6f}s**.
- Baseline target verification: **{st["target_verify_BASE_seconds"]:.6f}s**; DRAFT1 target verification: **{st["target_verify_DRAFT1_seconds"]:.6f}s**.

The intervention changes CPU backend parallelism policy, not the mathematical/GPU mapping. A performance effect can support that policy as a contributor in this environment; it cannot isolate OS thread creation, OpenMP runtime internals, CPU/GPU contention or a physical GPU bottleneck by itself. The scope of thread count1 is draft CPU computation, not a native-process thread cap.

Subsequent source inspection found that GET_ROWS/SET_ROWS already request one task and the graph planner clamps worker count to the maximum task count. Changing the context parameter therefore need not change actual worker count in the embedding-only CPU subgraph. The experiment tests a parameter policy; it does not establish that fewer workers actually ran. This weakens the original overhead hypothesis and is retained alongside the negative measurement.

**Disposition:** {recommend}

## Full cost boundary

Primary service includes fresh context creation/graph reservation, prefills, generation, host logits/sampling, state updates, synchronization and context destruction. Shared model load is separately recorded. No node observer or raw-vector writes in timed requests; comparisons/file output follow the timer. Request-only and phase costs remain secondary.

Token-by-token prefill remains unchanged. Warmup uses the old16-token prompt; it is separately recorded and checked. Driver cache coldness, all-shape cache residency and background-machine exclusivity are not established. This is post-registered-warmup fresh-context service, not cold boot or a proven production software ceiling.

## Paper implication

This study refines PR134's software baseline through an explicit one-factor counterfactual. Preserve PR134's original evidence and the current result separately. Neither numerical admission nor reduced thread count alone is a speedup claim. Draft economics must still be assessed against contemporary R, not historical timings. Do not infer a hardware accelerator opportunity from the expensive draft phase alone.

## Evidence

Candidate346 raw vectors remain locally archived with full hashes and sizes. Compact archive includes all native result/progress/geometry JSON, logs and receipts. This is local full-byte recheck, not external raw-data certification.

Conservative whole-parent charge: **{l["new_charged_seconds"]:.7f}s**; preserved prior1817.8040152s; all-history **{l["all_history_cumulative_seconds"]:.7f}s**. No actor, RTL, CPU8 expansion or merge.
"""
(r/"RESULT.md").write_text(text,encoding="utf-8")
(r/"PAPER_ADDENDUM.md").write_text(f"""# Draft CPU policy counterfactual

On the same four-input B570 panel, we changed only the draft context CPU thread parameters from eight to one while retaining the target policy and frozen GPU implementation. All346 full target/draft logits vectors remained byte-identical to the prior QB reference, with identical complete endpoints and state traces. In64 balanced measured requests with16 separately recorded warmups and identical-implementation controls, the candidate/dual-baseline service ratio was{a["service_DRAFT1_over_dualBASE"]:.6f}; its ratio to target-only was{a["service_DRAFT1_over_R"]:.6f}. The predeclared practical screen returned {a["decision"]}. Draft prefill averaged{st["draft_prefill_BASE_seconds"]:.3f}s in the baseline and{st["draft_prefill_DRAFT1_seconds"]:.3f}s under the candidate.

This is a finite exposed-input, single-date CPU-policy intervention, not a general thread-count recommendation or GPU bottleneck diagnosis. Full service includes context lifetime but excludes shared model loading. Keep this result separate from the original PR134 timing and the RTX request benefits.
""",encoding="utf-8")
print(text[:4200])
