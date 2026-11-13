# Staged experiment protocol

**Terms:** TP means tensor parallelism; PP means pipeline parallelism; KV means key/value cache; BF16 is bfloat16; F16 is IEEE float16; F32 is IEEE float32; GQA means grouped-query attention; MLA means multi-head latent attention; MoE means mixture of experts; FA2 means FlashAttention 2; SM denotes NVIDIA streaming-multiprocessor architecture; P2P means GPU peer-to-peer access.

## Application question and contribution test

The application is a resident, single-host model service whose outputs must follow a fixed deployment reference. The user has eight 24 GiB A5000 GPUs and wants to know whether reference-constrained speculative verification can improve useful inference at a larger model and device scale.

The engineering goal is more than 5% reduction in resident end-to-end latency against the same-speculation strong baseline, not a guaranteed outcome or a rule for discarding data. Here, 5% reduction means H/S <0.95, equivalent to a speedup greater than 1/0.95≈1.05263. Cold worker/caller time is reported separately and must not be implied to improve.

The gap to test is not simply whether tensor parallelism or speculative decoding works. Mainstream engines already implement both and may already preserve batch-invariant arithmetic. The proposed contribution is a request/phase/state adapter that preserves an explicitly frozen distributed reference while exposing useful query parallelism, with incremental benefit measured against the engine's strongest compatible implementation. A successful port without incremental speedup is a capacity/correctness result; a microkernel win without request improvement is a mechanism result.

The study should proceed from source/support → repeated reference → operation correspondence → request state → cost → serving load. Each experiment answers one of these questions. Do not expand a large matrix merely to find a positive cell.

The 944-request panel below is the first engineering/scale-transition study. It is not sufficient evidence for broad framework applicability or representative >5% improvement. [The independent confirmation layer](PORTABLE_METHOD.md) adds a second architecture, both mainstream frameworks, task families, lengths, loads and restarted sessions.

## Frozen deployment

Before any measured panel, commit a new campaign registration containing:

- exact engine, adapter and dependency commits/build identities; model and tokenizer revisions, config/index and tensor-file hashes;
- hardware UUID/rank map, topology/P2P matrix, driver and clocks/power policy observed without unauthorized changes;
- precision, attention implementation, all collective paths and their size-dependent dispatch, graph/capture policy, numerical reference identity;
- context/output allocation, paged-KV block size, lookahead width, prefix-cache/chunked-prefill policy, scheduler limits, concurrency and worker lifetime;
- prompt bytes/token IDs and exposure inventory, preprocessing/template, seed, stopping/EOS rules, max output, proposer policy;
- complete job list, warmup/measured/qualification labels, resource window, memory and disk reservations, timeout and failure rules;
- cost ledger state, exact artifact schema and a CPU replay entry point.

There is no server allocation, host manifest, checkpoint freeze or execution registration in this PR. The user requested substantial computation, but that does not establish that these specific cards are idle or permit interference with #218. Acquire the existing scheduling/resource lock for the actual UUIDs, check concurrent work, and reserve a new campaign window. Do not reuse or alter old study ceilings. If no clean window exists, continue CPU work and report the resource conflict.

## Stage 0 unchanged engines

1. Inspect actual host capacity and source/toolchain compatibility.
2. Run the unmodified vLLM route with 14B BF16 TP2, 1024 allocated tokens, a small output cap and no learned draft. Save startup, memory and complete output receipts. Compare one independently built SGLang smoke only if its driver/backend requirements are satisfied.
3. Repeat scalar reference trajectories and test native invariant mode, including the collective paths actually selected.
4. Before TP4/8, repeat with 32B at the desired topology. A 32B BF16 TP2 checkpoint is not the fallback because its weight payload alone exceeds 24 GiB/rank.

These are support/correctness diagnostics, not speedup measurements. Installation or a successful import is not model execution. A greedy endpoint match is not full-state qualification.

## Stage 1 finite numerical qualification

Freeze the actual operands and incoming states from the selected model, including attention, input/output projections, MLP, norm/rotary and every reduction-bearing path. Compare scalar, native batch, strongest simple backend loop and grouped candidate where each exists. Include widths 1, 4 and 8 for diagnostics, inside/crossing actual page boundaries, short and longer allocated prefixes and near capacity. Report unsupported cells rather than changing their dtype or arithmetic silently.

At complete-model boundaries, capture full logits, all active per-rank K/V shards in canonical order, positions/lengths, block ownership, frontier/pending state and accepted output IDs. Require byte equality and finite values for the declared strict domain. Compare candidate to independent saved reference, not candidate to itself or to a reference regenerated after a failure. Digests locate artifacts; independently read/compare the full payload during qualification. Document special-value policy explicitly.

Exercise all acceptance and stopping transitions from INTEGRATION.md, including first and interior rejection, all accepted plus bonus, pending correction, EOS/cap, page allocation/rollback, cancellation and worker/rank failures. Concurrency starts at one; two interleaved requests and repeated slot reuse are a separate test before serving measurements. Test under ordinary Python and `-O` where Python validation is involved so safety checks do not depend on assertions.

Every topology, collective policy, graph mode, model, dtype or cache representation change creates a new qualification cell. Do not reuse Qwen3 GGUF gates for R1-Distill BF16. The entire required suite must be enumerated and budgeted before running; if the approved resource window cannot hold it, defer the cell rather than shrink coverage after failures.

## Stage 2 mechanism and implementation economics

For each source-justified operator opportunity use:

- **G:** straightforward runtime/graph per-row calls to the reference arithmetic;
- **B:** strongest simple backend loop, sharing preparation, buffers and submission where valid;
- **C:** grouped candidate with independent row semantics;
- **N:** existing optimized native batched operation, whenever it is reference-compatible.

The labels describe roles, not a requirement that every engine have all four implementations. If N already performs the same transformation, reuse it and assess only the adapter's incremental work. Do not slow B or N to reproduce an old comparison.

Measure actual kernel/quantization/normalization counts, allocations, copies, bytes, collectives and synchronizations. Count TP communication and state rollback. Separate diagnostic instrumentation from clean timing and verify that both execute the same admitted path. A launch count inferred from Python calls is insufficient for fused/opaque internals.

An Amdahl-style planning bound may use measured fractions only: if fraction f of original latency is affected and its speedup is s, ideal total speedup is `1 / ((1-f) + f/s)`, before added overhead. Define f and s when reported. This is a bound, not a predicted outcome; do not fill it with old Q4 or DeepInfer benchmark numbers. With added overhead h expressed as a fraction of baseline request time, estimated savings are `f*(1-1/s)-h`. To exceed 5%, f must exceed `0.05+h`, and s must exceed `f/(f-0.05-h)`. These are algebraic planning conditions, not measured facts. For illustration only, f=0.20 and h=0.01 require s>1.429; f=0.10 and h=0.01 require s>2.5. Profile the actual native speculative baseline first. Prioritize a bottleneck only when its measured fraction can plausibly clear this bound, while preserving all failed/negative candidates in the engineering log.

## Stage 3 fixed request panel

The initial clean proposal uses four arms, all on the same allocated target GPUs:

| Arm | Purpose |
|---|---|
| M_native | Strong unmodified target-only deployment baseline. It may have different arithmetic; report its separate reference and output/quality correspondence. |
| M_ref | Target-only under the frozen invariant/ordered reference, with native optimized eligible operations. |
| S_ref | Native n-gram speculation under that same reference and resource policy. |
| H_ref | Same proposer, proposals/policy and reference, adding only the qualified HeteroSpec adapter. |

All exactness arms must pass their full state gates. If native S_ref cannot satisfy the chosen reference, retain that failed gate and identify a compatible native verification implementation before claiming H/S improvement. An invalid comparator is not assigned a speedup value. Also retain the fastest ordinary engine's honest deployment comparison even when it is not exact to R_ref.

Eager mode is the initial correctness setting, not automatically the strongest deployment setting. Before clean timing, qualify and freeze the strongest common supported graph/capture policy on development inputs. Give both S_ref and H_ref every valid common optimization. If only a restricted graphs-off comparison is possible, label it as such and keep the optimized native deployment comparator; it cannot establish the broad practical goal by itself.

Start with maximum proposal length 3 (verification width up to 4, with the actual scheduled width logged). The target engine's bonus/correction handling determines which positions are present; do not infer physical width from a configuration label. N-gram drafting uses target token history and adds no learned checkpoint, reducing tokenizer and memory ambiguity. It can have low acceptance on code/math; report accepted tokens, proposed work and drafting costs. Low acceptance is not a reason to discard roots.

For future model drafting, vLLM's draft TP is constrained to 1 or target TP. Equal vocabulary size does not establish token-ID compatibility. Compare tokenizer files, actual mappings, specials, chat template and EOS behavior. A vanilla Qwen tokenizer must not replace the distilled model's tokenizer by name. Target TP4 + draft GPU1 is a five-GPU resource configuration, not equivalent to target TP8; record idle/reserved devices and give target-only the same resource envelope. Do not select a learned drafter using the clean evaluation roots.

### Proposed fixed schedule

- Companion 14B TP2: 6 new roots (3 code, 3 math), 4 arms, 2 rounds. This is a descriptive scale-transition check, not the main estimate.
- Main 32B TP4: 12 new roots (6 code, 6 math), 4 arms, 4 rounds.
- Main 32B TP8: the same 12 roots and same 4×4 schedule, only after TP8 qualification. These are repeated hardware conditions, not 24 independent roots.
- Use 4096 allocated tokens including output/lookahead/block rounding; cap companion output at 128 and main output at 512 tokens. Freeze exact input token lengths before admission. Do not silently truncate a prompt or extend output cap after results.
- Disable shared prefix caching in the primary panel. Each measured request has an identical-root immediate warmup from a reset request state; allocator/kernel warm state is retained as explicitly declared. A warmup is not a claim of universal steady state.
- One model worker per arm per round, with two declared primer requests, then the root sequence. Root order is frozen and shared across arms within each round. Use a balanced four-arm order such as `ABCD, BDAC, CADB, DCBA` for the four main rounds. Companion two-round order is recorded as incomplete balance.

Counts are explicit: companion 48 measured +48 warm +16 primers =112 requests in 8 workers. Each main topology has 192 measured +192 warm +32 primers =416 requests in 16 workers. The full proposed clean panel is **944 requests in 40 model workers**, excluding every support probe, reference, heavy qualification, failed attempt, build and optional extension. This is a design, not launched work or a borrowed budget. Register its full operation ledger before execution.

Reserve an initial engineering/qualification window separately from clean timing. Estimate total wall time using completed startup and diagnostic receipts, include closure margin and an explicit GPU-hour/disk limit, then admit a complete stage. Do not launch a partial panel that cannot finish within the booked window. No synthetic duration is substituted for missing measurements.

### Statistical analysis

The independent unit is the frozen input root. Repeated rounds, tokens, ranks and repeated topologies do not increase that N. Primary contrast is H_ref/S_ref resident service time at 32B TP8; TP4 is the prespecified scale companion. Secondary contrasts are H_ref/M_ref, M_ref/M_native and H_ref/M_native, with their different reference scopes explicit.

For root i and round r, let `rho(i,r) = T_H(i,r) / T_S(i,r)`, where T is complete resident service time from accepted request to terminal state. Compute mean log rho across rounds within root, then equally weight roots. Report the geometric ratio, raw milliseconds, every root, and a stratified root-bootstrap 95% interval with seed 20261110 and 10,000 resamples. State sample size and bootstrap limitations. The root-bootstrap interval is conditional on only four shared arm-worker rounds and does not capture general worker/session drift. Report per-round paired contrasts and worker-level thermal/startup diagnostics alongside it; do not describe this interval as covering all deployment variability. Broader session-generalization needs a separately frozen repeated-session study, not post hoc extra rounds. Report savings as `1-rho` and speedup as `1/rho`; do not mix their directions. Do not infer significance from repeated rounds as independent samples.

A ratio below one with an interval containing one is unresolved, not a positive headline. Report all prespecified comparisons and scope any multiplicity-sensitive claims. Do not add roots, rounds, widths or select graph modes because an interval is wide or the sign is unfavorable. If a revised hypothesis is worth testing, register a new held-out study after reporting this one.

Cross-TP strong scaling must use fixed-work replay if per-TP outputs diverge. Free-generation throughput at different TP references can still be reported, but generated lengths and trajectories are possible confounders. For M_native versus reference-constrained arms, different output IDs or EOS lengths invalidate a same-output latency claim. Report capped-request workload, generated lengths, truncation rate and task-completion/quality separately; use equal-work replay for an arithmetic-cost comparison. A 512-token cap can truncate reasoning and does not establish complete reasoning-task quality. Eight independent replicas measure aggregate throughput, not single-request model-parallel speedup; label such a control separately.

## Complete cost and failure accounting

Maintain append-only receipts with campaign/stage/job/attempt/source epoch, model load, warmup, measured/qualification role, rank IDs, start/end times, terminal status and artifact hashes. Count startup failures, out-of-memory, timeout, abandoned captures, recompiles and negative probes. No refunding failed requests or moving them out of the campaign denominator.

Report separately:

- model acquisition/conversion, compilation and load wall time;
- heavy qualification and artifact export/verification wall time and bytes;
- warmup/primer time and clean resident service time;
- full worker/caller elapsed time and complete campaign GPU-hours, including failed/idle reservations;
- time to first token, inter-token latency, output tokens/s, request latency and queueing under load;
- per-rank peak allocated/reserved memory, host RAM, communication bytes/latency and storage peak;
- sum of sampled GPU board energy only when calibrated; it is not whole-system energy. Otherwise report the measurement boundary or absence.

Synchronize all participating work at the measured request boundary using a defined coordinator clock/receipt protocol. Do not sum overlapping per-rank kernel times as elapsed service time. Record overlap and critical path rather than subtracting communication twice. Cold worker and resident-service rankings may differ.

Stop a cell on numerical mismatch, inconsistent rank state, unsupported fallback, memory breach, repeated unexplained timeout, resource interference or artifact failure. Retain the reason and exact source epoch. Repair is allowed in an explicitly new epoch with fresh affected qualification. Never resume a partially committed worker state as if it were clean.

## Later serving extension and presentation

Only after batch-1 state qualification, freeze a separate arrival/load study at concurrency 2/4/8, with bounded queueing, timeout and admission policy. Compare optimized native scheduling and speculation, not serialized per-request baselines. P50/P95/P99 require adequate request counts and a stated estimator; twelve roots alone do not justify reliable tail claims. Prefix reuse, dynamic batching and cancellation are new correctness dimensions.

Every figure should answer a stated application or mechanism question. Use consistent axes/ratio direction, units and comparable domains; distinguish measured data from estimates, failed/unsupported cells from missing cells, and confidence intervals from repeat ranges. Use color-blind-safe colors plus shapes/line styles, readable legends and consistent fonts/sizes, following the target venue template (Times New Roman where appropriate). Define tensor parallelism (TP), key/value (KV), every abbreviation and formula variable at first use. Keep negative results and scope limits adjacent to the conclusion they qualify.

The claim ladder is: supported load → finite numerical qualification → mechanism improvement → resident request benefit → serving benefit. Each requires its own evidence. This PR reaches only source research and CPU planning.
