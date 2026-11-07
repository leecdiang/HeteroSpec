# B570 real-request bridge and corrected timestamp observer

The real-request scope check is complete for one exposed HumanEval prompt. The final diagnostic logger retains reference bytes, passes the unchanged coarse observer screen and accounts for the previously omitted final interval. It does not establish whole-workload qualification, a natural-request critical-path fraction or a physical hardware bottleneck.

## Actual changes

1. A small standalone native host loads the existing Qwen3-8B Q8_0 model on B570 and runs the unchanged 124-token HumanEval/42 input with ubatch1, F16 KV, FlashAttention off and a 16-token greedy cap. The first entry attempt failed because it used a dynamic-plugin ABI against linked backend registration. Removing those calls repaired the entry; that 0.1694517-second failure is preserved.
2. The Vulkan concurrent logger now emits a terminal timestamp and graph-end index, closing the final group. Previously its output-projection count was zero; the corrected count is 16 per request.
3. Group attribution now skips empty/non-compute nodes using the executor's predicate. This removes inactive n=0 operations from the tail label.

The backend repair changes only performance-logging paths. Shaders, arithmetic, model graph and sampling are unchanged. See `concurrent-logger.patch`. The final DLL SHA256 is `618f2f222791480b0536236ff84e6375dd2becface2c59e8adde9fe0d61a0685`. It retains PR128's scoped QB admission repair. The executable is unchanged across successful attempts; the initial host loader repair preceded them.

## Qualification and actual geometry

Across 11 successful native processes, 33 requests and 528 full logit arrays, CPU re-reading verifies all 151,936 logits per array byte-for-byte against the first new clean reference, plus greedy ID identity. This is one prompt repeated under observer/runtime controls, not 33 independent workload samples. One failed entry process remains in the ledger. All successful processes exit normally with complete capture; no deadline kill is requested.

The observed model has 36 layers, 32 Q heads and 8 KV heads, d=128. Its attention physical key extent is 256, q1; context capacity 1024 is not the executed key extent. The KQ/KQV metadata and runtime logs identify B570 placement. The model log reports 37/37 layers offloaded, while CPU-mapped storage also exists.

Thus the earlier Hq=Hkv=8, key1023–1025 micrograph cannot directly establish request benefit. This request does not exercise a q2/q4 mapping. No model optimization is enabled or claimed.

## Observer calibration and integrity

The fixed screen compares third-context medians of 15 dependent decode-completion times. Clean A/B and profile versus each clean must all fall within [0.90,1.10]. This is an exploratory necessary check, not statistical equivalence or per-op calibration. Clean/profile/clean processes use the same DLL within each final comparison.

| Observer | Profile overhead vs clean A / B | Coarse gate | Integrity |
|---|---:|---|---|
| Per-operation serial logger | +12.54% / +12.03% | FAIL | Perturbs execution |
| Original concurrent logger | +5.10% / +5.59% | PASS | Missing terminal group; NOT COMPLETE |
| Terminal-only repair | +7.88% / +7.15% | PASS | Tail labels include inactive nodes |
| Terminal + active-node repair | +7.01% / +6.96% | PASS | Counters and active labels pass |

Final clean/profile/clean medians are27.6675/29.6058/27.6794ms. These measure observer disturbance, not an algorithm speedup. First-context compilation, full-request raw capture and prefill timing are excluded from this median; their full costs still count toward the execution budget.

Every final profile-context table contains 5,004 QK, softmax, AV and CONT operations each: 36×(124+15). Each contains 16 positive-width output projections, with no n=0 matrix labels. Mixed groups are not divided among their members.

## Scoped device-cost result

The final third-context device timestamp subtotal is3.490070s over prefill plus continuation.

| Classification | Instrumented GPU subtotal |
|---|---:|
| Pure QK/softmax/AV core | 2.8005% |
| Mixed group containing QK | 0.0021% |
| Final recombination CONT | 0.4376% |
| Quantized matvec groups, including fused additions | 92.5152% |
| Other groups | 4.2445% |

The core's conservative mixed-group bound is[2.8005%,2.8026%]. This excludes Q/K/V and output projections, RoPE and cache updates; it is not “all attention.” Quantized groups include both attention projections and FFN. Operation names do not establish a DRAM-bandwidth or arithmetic bottleneck.

These are synchronized, instrumented GPU subtotals, not clean natural-request critical-path fractions. Even the final observer retains about 7% median overhead. Do not use these fractions in an Amdahl formula or claim an end-to-end optimization.

Decision: the present evidence does not justify an attention-mapping accelerator. Retain the fixed reference baseline and close the immediate QB/QH branch. A future physical study should begin with a new hypothesis about the observed projection workload and calibrated physical counters, not reuse these fractions as a hardware model.

## Budget and preservation

Starting cumulative charge was 53.7774511s. This follow-up charges193.0268920s across all attempts, including the failed entry, model initialization, diagnostics, raw capture and cleanup. Final cumulative charge is **246.8043431/300s**, leaving **53.1956569s**. No budget is reset.

All old roots remain intact. `COMPACT_EVIDENCE.zip` includes every stage's frozen design, source host, build/launch logs, process receipts, metadata and budget. `SOURCE_SNAPSHOT.zip` includes the parent and final backend sources. Full raw logits, model weights and DLLs remain local and are listed by hashes; they are not silently replaced by summaries.

`analyze_closeout.py` reruns the full CPU audit with the original local roots. It does not load GGML or a GPU. The compact ZIP supports metadata/counter review; its delivery is not external authentication of locally retained raw logits.

The backend was rebuilt with 147 unchanged precompiled shader objects. `BUILD_MANIFEST.json` binds them and the external headers/import libraries; this is not a fresh shader compilation or a self-contained remote build environment.

See `PAPER_ADDENDUM.md` and `OBSERVER_COSTS.svg` for paper integration. The existing manuscript directories were not overwritten. Actor, RTL, CPU8 and merges were not started. Formal PR127/F0 status remains unchanged.
