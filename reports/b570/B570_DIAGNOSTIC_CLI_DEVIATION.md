# B570 Diagnostic CLI Compatibility Deviation

## Invalid diagnostic attempt

`work/b570/diagnostic-v1-20260912-141235` is retained as **CONFIGURATION_ERROR / NO SCIENTIFIC RESULT**. Its primary failure was the invalid llama-bench argument `-ngl all`; the later watchdog `FAILED_INFRASTRUCTURE` state was secondary to the already-exited controller. The attempted PP2/PP1 command was rejected during argument parsing, before model loading or model inference. It produced no valid V2 cell, HumanEval output, or fallback result.

## Compatibility repair

The b10839 `llama-bench --help` contract defines `-ngl, --n-gpu-layers <n>` as numeric. The diagnostic runner now encodes the already-frozen full-target-offload semantic as `-ngl 99`. It also omits `-fitt off`: in this build `-fitt` accepts a numeric MiB margin, while omission selects the documented default `off` state.

The non-formal verbose smoke command was:

```text
llama-bench.exe -v -m Qwen3-8B-Q8_0.gguf -dev Vulkan0 -ngl 99 -fa off -p 1,2 -n 0 -d 1 -b 512 -ub 2 -r 1 -o json
```

It exited 0 and logged all of the following:

- `using device Vulkan0 (Intel(R) Arc(TM) B570 Graphics)`
- `offloaded 37/37 layers to GPU`
- `Vulkan0 model buffer size = 7669.77 MiB`
- JSON placement metadata: `n_gpu_layers=99`, `devices=Vulkan0`

Formal microbenchmark cells additionally fail closed unless their verbose log contains the 37/37 line and their JSON metadata records numeric layer request 99 on Vulkan0. This repair changes CLI encoding only: runtime, model, backend, device, full-offload semantics, contexts, batch/ubatch, repetitions, and timing definition are unchanged.

Smoke evidence remains in the non-formal local directory `work/b570/smoke/llama-bench-ngl99-verbose-20260912-165744/`; it is not promoted as scientific data.
