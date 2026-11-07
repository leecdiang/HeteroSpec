# RTX query-layout result

Design #95; authenticated #94/#91 ancestry. Exposed tasks and two adjacent sessions; no new-input or cross-date claim.

Counts: {"formal_started": 2016, "formal_completed": 2016, "formal_registered": 2016, "formal_missing": 0, "warm_started": 42, "diagnostic_engineering_started": 333, "load_starts": 82, "operator_starts": 216, "all_native_completed": 2387, "owned_GPU_seconds": 6326.667263199633}

## Same-reference native qualification and request cost

|Family|Pair|Qualified|Cost ratio|Regressions|
|---|---|---|---:|---|
|Qwen|M_PQ/M_QB|True|1.026676|GSM8K/test/141, GSM8K/test/322|
|Qwen|C_PQ/C_QB|True|1.043676|none|
|Qwen|M_GS/M_QB|True|1.330106|none|
|Qwen|C_GS/C_QB|True|2.143525|none|
|Qwen|M_QB/C_QB|True|1.143749|MBPP/413|
|Qwen|R/M_QB|True|1.334051|none|
|Qwen|R/C_QB|True|1.525820|none|
|SmolLM2|M_PQ/M_QB|True|1.038478|none|
|SmolLM2|C_PQ/C_QB|True|1.068111|none|
|SmolLM2|M_GS/M_QB|True|1.366008|none|
|SmolLM2|C_GS/C_QB|True|1.462530|none|
|SmolLM2|M_QB/C_QB|True|0.633948|MBPP/123, MBPP/140, MBPP/255, MBPP/401, MBPP/413, MBPP/418, GSM8K/test/111, GSM8K/test/120, GSM8K/test/1308, GSM8K/test/141, GSM8K/test/322, GSM8K/test/443|
|SmolLM2|R/M_QB|True|1.369890|none|
|SmolLM2|R/C_QB|True|0.868439|MBPP/123, MBPP/140, MBPP/401, MBPP/418, GSM8K/test/111, GSM8K/test/120, GSM8K/test/1308, GSM8K/test/141, GSM8K/test/322, GSM8K/test/443|
|Llama|M_PQ/M_QB|True|1.013407|MBPP/418|
|Llama|C_PQ/C_QB|True|1.021848|GSM8K/test/120, GSM8K/test/141|
|Llama|M_GS/M_QB|True|1.411508|none|
|Llama|C_GS/C_QB|True|2.175941|none|
|Llama|M_QB/C_QB|True|1.116620|MBPP/418|
|Llama|R/M_QB|True|1.426161|none|
|Llama|R/C_QB|True|1.592480|none|

PQ/QB and GS/QB >1 favor QB as consistency-repair implementation. M_QB/C_QB is incremental draft value; R ratios are complete same-reference request comparisons, not isolated repair component times. Absolute per-task/session medians, domains, every regression, mismatch and missing slot are in RESULTS.json.

## Mechanism and limits

{"status": "SUPPORTED", "contexts": 24, "expected_contexts": 24, "own_path_correspondence": true, "native_model_decision_claim": "UNRESOLVED", "kernel_scheduling": "UNKNOWN"}

Actual captured bytes and independent arithmetic comparison are archived. Runtime operation dispatch is real; kernel symbol, algorithm and launch scheduling remain UNKNOWN. Fused post-mask scores are NOT_COMPARABLE. No synthetic full-path logits or reduction-order proof. Capture-on/off and own-path correspondence are separate controls; failures narrow native causal inference. Historical MBPP229 q6/8 geometry is NOT_ADMITTED by frozen q<=4/k3 scope.

MODEL_TIMING_UNAVAILABLE remains true. No formal-wall-time fitting, energy, throughput or component-cost attribution.

## Scientific closeout

|Statement|Status|Allowed scope|
|---|---|---|
|QB and PQ bitwise attention arithmetic match at these captured contexts only|SUPPORTED|Only sampled actual identical-input operator contexts; no CUDA reduction-order or full-model bitwise proof|
|Kernel-level schedule equivalence|UNRESOLVED|Runtime dispatch recorded; kernel scheduling UNKNOWN|
|Component-time predictor|UNRESOLVED|MODEL_TIMING_UNAVAILABLE; no wall-time fitting|
|Qwen M_PQ/M_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Qwen C_PQ/C_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Qwen M_GS/M_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Qwen C_GS/C_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Qwen M_QB/C_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Qwen R/M_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Qwen R/C_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|SmolLM2 M_PQ/M_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|SmolLM2 C_PQ/C_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|SmolLM2 M_GS/M_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|SmolLM2 C_GS/C_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|SmolLM2 M_QB/C_QB request-cost ratio >1|REFUTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|SmolLM2 R/M_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|SmolLM2 R/C_QB request-cost ratio >1|REFUTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Llama M_PQ/M_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Llama C_PQ/C_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Llama M_GS/M_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Llama C_GS/C_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Llama M_QB/C_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Llama R/M_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|
|Llama R/C_QB request-cost ratio >1|SUPPORTED|Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled|

## Reproduction

Run the standalone stdlib audit95_v02.py against repository and local directories reconstructed from RAW_EVIDENCE. ZIP INDEX.json covers every retained logical byte. SOURCE_RUNTIME.zip has its own complete index; the inherited PR91 scientific archive and source/runtime are preserved as immutable nested archives. Independent local and freshly authenticated GitHub-byte restoration receipts are mandatory. Failed attempts and started slots are retained; there are no formal retries. No parent archive, manuscript, main or release was modified.


## Preserved implementation and delivery faults

Four original Smol/Llama PQ warm failures remain charged and were never retried. Prospective V02 changes only the host graph capacity bound by the predeclared maximum q=4; all numerical DLLs and operators are unchanged. QB eligibility was recovered from existing final tensor aliases and twelve exact outputs, without GPU reruns. Original frozen files remain immutable. V03 repairs only parent-archive inclusion and auditor metadata after all 2016 formal requests completed; the failed archive index, manifest, original reports and controller failure are retained. See IMPLEMENTATION_FAULT_CORRECTION.json, RESOURCE_CORRECTION.json and DELIVERY_CORRECTION_V03.json.
