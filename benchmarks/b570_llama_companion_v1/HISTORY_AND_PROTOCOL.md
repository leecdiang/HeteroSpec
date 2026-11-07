# Evidence-led cross-platform protocol

## Primary sources inspected before design

1. RTX PR144, `3305b39f:benchmarks/rtx_jsa_closeout_v1/revision_a/RESULT.md`: CodeContests/valid/108 has737 prompt tokens; PQ/QB agree mutually and first disagree with R at zero-based output81. Earlier eight Llama cells passed; later three and timing did not run. This is not a length threshold.
2. RTX PR151, `29511ed9:benchmarks/rtx_scope_transfer_v1/sidecar_execution/diagnostic/{STATUS,AUDIT,EXECUTION_IDENTITY}.json`:54 requests and5916 vectors; M_PQ preserves R under both P1 and P4_NATIVE, while C_PQ/C_QB fail under both. These recipes did NOT import a common state. The operator cause remained unknown.
3. RTX PR159 `38b3d3d`: its24 Llama regression requests reproduce the old behavior including the known failure. The Qwen head-normalization offload/RoPE result is not Llama evidence.
4. B570 `022babfa:benchmarks/b570_final_causal_closeout_v1/{RESULTS.md,PROTOCOL_LIMITATIONS.json}`: a distinct Meta-Llama-3.1-8B Q6_K partition study.133 requests and40 operator calls; only32 operator calls passed own-path controls. Eight MUL calls used post-consumer aliased operands and were excluded. Projection differences and state interventions are historical findings, not this Q8/k3 root cause; shader/pipeline identity was unknown.
5. B570 native kit at `41cb7504`, also in base `022babfa`: old formal.exe is Qwen3 Q8, k1, local q2, short key256/512 request integration. The general query-view helper is not a numerical certificate. Its scoped AV-preserving shader and request bridge do not automatically admit q3 or key768/1024.
6. B570 PR152 `022babfa`:152 producer-consumer requests,48 scientific cells,39 strict-R matches; two fixed-R producer effects and a distinct GSM8K/1184 counterexample. This is not a Llama repair and not a timing dataset.

Complete immutable hashes and original source recovery are read by history.py/source.py. No bulk historical vector download or B570 forward was performed in the authoring environment. The first host phase recovers and audits the raw history.

## Scientific question and platform roles

RTX PR160 leads Llama root-cause development. B570 works in parallel on the same model/request semantics: independent history audit, Vulkan port, baseline, and mechanism transfer. It must not wait idly for RTX and must not independently guess a Qwen-style fix.

Same weights/quantization, tokenizer/template, prompt IDs, k3, ctx1024, F16 KV, non-flash, greedy/EOG/cap128. Thread counts, source overlays, actual execution backend and memory placement are recorded differences. Local output-preservation tests use R_Vulkan. CUDA R and Vulkan R need not be equal; heterogeneous opaque checkpoints are not interchangeable. Compare relative costs within each platform; do not pool raw seconds or present a controlled GPU ranking when placement/runtime differ.

## Before first forward

Build a genuinely separate stock numerical oracle from upstream `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`. The observation-export bridge is not a graph/arithmetic patch and has heavy/off controls. Freeze executable, every actual numerical library/shader build, compiler flags, Vulkan driver/module identities and the selected placement. Never rebuild or retune this oracle after seeing candidate outputs. Keep original B570 Q6 and Qwen references intact.

Target Q8 SHA256 `9da71c45c90a821809821244d4971e5e5dfad7eb091f0b8ff0546392393b6283`,8540775840 bytes; draft SHA256 `432f310a77f4650a88d0fd59ecdd7cebed8d684bafea53cbff0473542964f0c3`,1321083008 bytes. No model download is claimed here. Acquire the exact licensed files through existing authorized assets, rehash, compare vocab/EOG mappings. Do not substitute Q6_K because it fits.

The old backend bridge cannot cover the737-token failure. The candidate source contains a proposed q2/3/4 and n256/512/768/1024 admission extension preserving the existing AV shader's arithmetic/broadcast mechanism. It is explicitly UNQUALIFIED until the host builds it and verifies real-input operation and request controls. Admission is not repair. A generic reshape domain does not prove Vulkan kernel support.

Capacity profiles are predeclared and output-blind. If full target+draft residency fails, CPU draft is the next profile, followed by fixed partial target offload. Freeze one selected profile before local R outputs. Describe mixed residency honestly. Device budget polling is sampled API evidence, not proof of continuous physical residency or absence of all paging.

## Baseline and development

Known failure and controls: CodeContests/valid/108, CodeContests/valid/43, GSM8K/test/496. Reuse exact token IDs/caps. Baseline is6 local-oracle +30 candidate requests =36. Verify source R repeatability, heavy/off endpoints, candidate R full vectors and all requested local graph paths. Candidate mismatch does not terminate research.

Three legitimate branches:

- Shared failure: locate the local Vulkan divergence from actual decisions/state, test whether RTX's mechanism also applies. Do not assume equal output indices imply equal causes.
- No trigger: validate non-regression and explain actual execution conditions. This is an external portability/negative-control result, not a second repair success. Preserve baseline even if the later RTX rule changes.
- Different failure: perform Vulkan-specific mechanism work and present it separately. A common reference-preserving interface can have different backend implementations; two unrelated PASS labels are not proof of one universal patch.

The new q1/multiquery probe restores identical candidate state and positions into clean receivers; it first proves its own multiquery path against natural execution and proves live-state nonmutation. Capture controls must pass before interpretation. A common token prefix alone is not a common internal state. First differing output is not necessarily the first internal difference. Align real layer/position/row roles, not text occurrence order. Past a rejected draft token, subsequent verification rows are conditional suffixes, not natural-reference decisions.

If consumers diverge from the same state, localize layer then operator, including actual scheduler assignment. Capture operands at their producing nodes or before any in-place consumer. Preserve parameters, dtype, layout/stride, position, mask and native backend/pipeline identity when available. Require own-path replay before changing one backend/kernel/shape factor. If consumers agree, investigate state production/reconciliation instead. An invalid diagnostic is fixed as instrumentation; it is not a model failure.

Structural fixes may change dispatch, kernel, arithmetic, state recovery or cache compatibility when justified. Prohibit task IDs, answer tokens, specific output offsets, model-name exception tables, successful-subset timing and an empirical margin cutoff sold as a guarantee. A serial fallback may be a correctness control or explicit candidate whose total cost is reported; it cannot silently supply oracle answers or be called an acceleration without benefit.

## Development resources and freedom

User authorizes ordinary engineering repair and substantial mechanism iteration without repeated approval. Initial reservation16384 work credits and604800 seconds is renewable through a reasoned hash-chained EXTEND record. No small numerical-retry ceiling, mandatory overnight date or result-dependent deadline. Agent may extend before launch; counters, failed attempts and exposure records never reset. Per-worker finite safety bounds, disk/RAM/VRAM reserves, process containment and cleanup remain required. Increase a legitimate reservation rather than terminate promising work solely at a low quota.

Credits include model requests and explicitly reserved extra probe/operator work; completed natural model requests are counted separately. Reconcile interrupted attempts and actual PIDs before releasing locks. Ordinary CPU auditor/report fixes reuse existing raw wherever possible instead of requesting expensive duplicate forwards.

## Freeze, cross-platform coordination and confirmation

Before confirmation: mechanism/ablation or documented nontrigger rationale, unchanged old local R, actual observation/probe controls, and regression of existing supported paths. The source extends a previously Qwen-qualified Vulkan domain: recheck original B570 Qwen controls with correct new scope activation. This adapter is host work; simply linking old formal.exe, which sets HS_REQUEST_LAYOUT, is not sufficient for the new exported setter.

Default independent Vulkan panel:24 new natural inputs, code/math ×128–384/512–768 native tokens, six per cell;12 allowed only with a prospective rationale. No padding, repeats or truncation to manufacture cells. Exclude task/text/token exposures from BOTH platforms and old studies. If a common RTX/Vulkan panel is desired, both candidate mechanisms must be frozen before either platform exposes its outputs. Otherwise clearly label independent or externally exposed transfer panels. Do not block the currently running RTX study.

48 stock-oracle references +240 candidate qualification requests; candidate R full logits must match the frozen oracle. Complete endpoint and logical-transaction checks are mandatory; PQ/QB vector/state correspondence is a separate audited property, not a replacement oracle. After every slot qualifies, six periods ×24 inputs ×six arms =864 measurements plus864 same-arm warmups. With12 inputs, counts halve. Model load separate; context setup/teardown, prefill, corrections, state repair, synchronization and assembly all included. No trace/probe or heavy observer in timings.

Williams order balances absolute positions, every ordered adjacent pair within blocks and A/A relative order3/3 per input. Record process/warmup boundaries; do not claim perfect control of all thermal or carryover effects. Within each block average C_PQ_A/B arithmetically, then use equally weighted log ratios across inputs and periods. Report QB/PQ, same-layout M/C and R-normalized costs separately. Practical layout screen: reduction exceeds max(2%, largest symmetric per-input aggregate A/A deviation) and all periods favor QB. Retain reversals; no post-result session extension or request-level population CI.

A failed confirmation panel is exposed. Continued development is authorized, but another genuinely unseen panel is required for a new frozen candidate. Never swap references or pick successful inputs. A full-output failure is not answered by changing the paper's wording.

## Delivery and remaining work

Separate result PR, no automatic merges/paper updates. Publish all candidates/failures, exact native builds, source changes, model/runtime pins, complete matrices, raw vectors/states, operator controls, resource and exposure ledgers, independent CPU reconstruction, and authorized fresh remote archive/member readback. Local readback and same-host audit are not third-party scientific replication.

Implemented code is substantial but not a native qualification: Windows build, actual Vulkan capacity/domain checks, operator-specific replay after localization, evidence-led numerical repair, old-path regression integration and driver/shader identity capture require the execution agent. Keep these statuses explicit.
