# B570 Correctness Gate — Formal v2 Closeout

Run `formal-v2-20260912-122930` executed the six frozen prompts under preregistration commit `59185f24793eb2b852be0821295d13c44ad97636`. The earlier `formal-20260912-001606` attempt remains **INVALID / CONFIGURATION-BLOCKED** and is excluded from Vulkan correctness inference.

## Result

**CORRECTNESS = FAIL**

- normalized exact pairs: 9/18
- completed workload records: 36/36
- true mismatch records: 9
- contract: generated token IDs only, prompt excluded, maximum 128, raw CLI total-token counts excluded
- frozen configuration: Vulkan0 Arc B570; Qwen3-8B/Qwen3-0.6B Q8_0; greedy; k=2; ctx 1024; batch 512; ubatch 128; full offload

Telemetry was collected as supporting instrumentation at the qualified B570 board boundary. It does not retroactively change preregistration v2's `power_measurement=false` declaration.
