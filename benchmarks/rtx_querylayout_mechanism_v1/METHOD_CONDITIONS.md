# Query-layout method and admission

Authority is the fresh authenticated PR94/PR91 archive. See ANCESTRY_RESTORE.json and the complete, line-addressable source in the indexed source package. No parent observation or numerical backend library is edited. AI assisted this private experimental implementation; no contribution to upstream llama.cpp is submitted.

## Mathematical mapping and its limits

After the native permutations, Q has shape (d,q,h,1), with strides nb[0..3]. QB views Q as (d,1,h,q) using the original query stride nb[1] as its fourth-axis stride. Thus address_QB(i,0,a,j) = base + i*nb[0] + a*nb[2] + j*nb[1] = address_MQ(i,j,a,0). The mask address is likewise preserved by (nKV,q,1,1) -> (nKV,1,1,q). K and V retain their actual native strides and single KV stream; head broadcast uses the original GQA ratio. PQ slices each original query and mask column, applies the historical attention subgraph, and concatenates query outputs in original order. This proves value/index mapping under mathematical attention, not identical floating-point reduction or CUDA scheduling.

Study admission requires the exact pinned Qwen3 or dense Llama architecture, non-flash attention, one sequence/KV stream, at most4 occupied queries, compatible head dimensions and integer GQA ratio, F32 Q/mask and F16 K/V, no attention bias/sinks/MLA value projection. Source hard assertions and actual captured ne/nb/dtypes are reported separately. Unobserved architectures, stream layouts, bias/ALiBi/sinks/MLA, widths above4 and other precisions are NOT_SUPPORTED, not general preservation claims. The mask may retain padded columns; its original stride, values and first q logical columns are used.

## Source bindings

- src/llama-graph.cpp build_attn_mha: historical HS_ATTENTION_SINGLE_QUERY subgraph, now selected by immutable PQ layout and active phase scope; subsequent native Q/K/V permutation and QB views; native mul_mat, soft_max_ext, value mul_mat and contiguous recombination. No CUDA arithmetic source or numerical DLL changes.
- src/hs_scope.h: immutable mask bits target prefill1/continuation2, draft prefill4/continuation8; RAII restores the previous active flag. layout95 is immutable per process (QB/PQ/GS).
- common/hs_observer.h: scope enters before capture-disabled native decode. Diagnostic callback asks for layer0 QK/softmax/AV only; counts mode has no scheduler callback, tensor reads, extra synchronization or elapsed hooks.
- src/llama-graph.h allow_reuse: active-layout flag mismatch rejects the cached topology before other geometry checks. Fixed per-process implementation cannot change between requests. An exposed mask1 negative control records actual native flag-mismatch rejection; it is not a tuning candidate.
- src/llama-context.cpp decode memory init_batch: GS uses physical microbatch1 for the entire active target query, retaining configured caller UB4/output capacity4 and the existing output extraction, positions and KV handling. This serializes projections, attention, output projection and FFN for each target query. It is distinct from QB and from changing only an attention flag. Draft remains the original UB1 path; no state transplant or reference answer assistance.
- QB/PQ keep original non-attention batching. R uses ordinary UB1. All C arms keep k3 draft proposal, acceptance, rollback, pending-token and terminal rules.

## Frozen host and observation contract

RTX5070Ti Laptop, exact fresh full GGUF and21DLL hashes, ctx1024, requested logical batch2048/effective1024, F16 KV, full GPU offload, FAoff,24threads, greedy seed123, cap128, original target-template-once native IDs and EOG authority. Runtime loaded logs/module bytes/output capacity and actual target/draft graph work are checked per worker. Baseline physical UB is1; declared repair callers use UB4; GS physical target width is1 even for a multirow caller. No hidden prompt warmup or prompt-cache reuse.

The complete nonstreaming request timer includes JSON encoding, HTTP submission, full JSON/native IDs/stop parsing and endpoint validation. Artifact writes, source/model/module hashes and attestation are outside it. Diagnostic heavy capture is excluded from P2; no overhead subtraction or component-time fitting. Adjacent sessions are not independent dates.

## P1 snapshot and kernel scope

Two archived M0-divergent and two agreeing controls per family are deterministically selected by frozen IDs, preferring one each domain where available. The first multiquery layer0 prefill and first target verification/continuation boundary are selected, at most24 contexts. Original Q/K/V/mask spans, strides, pointers, cache bounds, caller geometry and native QK/softmax/AV bytes are retained. The emitted native trace binds positions, committed prefix and pending token. No fresh/blind-input claim.

Each MQ/PQ/QB replay copies those same spans to the pinned CUDA backend and bitwise checks GPU input readback, then uses the same native operator parameters. Outputs are canonicalized to common logical indexing for comparison. Standalone own-path MQ replay must be checked against native captured outputs; a mismatch limits causal/native correspondence. Fused post-mask scores are NOT_COMPARABLE because the native softmax does not expose that intermediate. Operator argmax is not a synthesized model decision/logit. Native sampled logits/top2 margins are separate trace evidence.

Actual operation/backend/dtype/geometry/pointer dispatch is recorded from native callbacks and real CUDA0 replay. No Nsight/CUPTI executable is installed at preflight; kernel symbol, launch/grid/block, cuBLAS algorithm and reduction scheduling remain UNKNOWN. Source dispatch branches or graph names do not establish a kernel schedule. Supported numerical correspondence is distinct from a scheduling-equivalence claim.

## Prospective budgets and hard stops

P0_PLAN.json freezes selection and a25181.4914112-second owned-process reserve derived only from prior R maxima; all three families are admitted before new outputs. Diagnostic/engineering at most512 full native requests,24 snapshot contexts and216 operator starts; formal at most2016 and84 warmups; owned GPU-process cap12hours. Actual loads/failures/replay processes are separately counted and timed. Started slots are immutable and never retried. No implementation/mask/k/precision/panel change after F0A to chase results. Missing or nonqualified arms retain null paired costs; only provably independent valid arms continue. Local and fresh authenticated remote restoration plus independent CPU validation are required for result completion.
