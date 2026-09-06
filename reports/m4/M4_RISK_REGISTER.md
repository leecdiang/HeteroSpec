# M4 Feasibility Risk Register

| Risk | Likelihood / impact | Mitigation / decision |
|---|---|---|
| MLX-LM Qwen3 speculative token mismatch | Material / critical | Two-prompt then 12-prompt exact-token gate; fallback reproduction in llama.cpp; no timing promotion after mismatch. |
| Runtime API/version drift | Medium / high | Freeze only after M4 canary; record versions, model revisions and CLI help. |
| Unified-memory swap | Medium / high | Start with 8B pair; track pressure/swap; retain >=6 GiB headroom; no 20B. |
| Fanless thermal drift | High / high | Fixed warm-up/cooldown, counterbalanced order, thermal-state invalidation. |
| Telemetry domains absent or privileged | High / medium | Qualify `powermetrics`; publish aggregate-only limitation when necessary; never invent ANE/GPU watts. |
| Logger perturbs batch-1 latency | Medium / medium | Paired logger-on/off canary; separate power runs if perturbation >2%. |
| MPS silent CPU fallback | Medium / high | MPS is secondary; never enable `PYTORCH_ENABLE_MPS_FALLBACK` for formal data. |
| Quantization differs from Windows | Certain / medium | Treat each as architecture-specific practical configuration; compare within-platform relative speedup only. |
| Same-GPU target/draft contention | Medium / high | Native runtime first; collect acceptance and round costs; unified memory is not assumed free. |
| ANE conversion scope explosion | High / medium | Exclude from phase one; future Core ML qualification is a separate research question. |

## Go/no-go conclusion

**Conditional GO for a small architecture-control study; NO-GO for a low-effort direct port of the existing custom harness.** The likely engineering cost is low-to-moderate for a native MLX-LM adapter and existing analysis reuse, but high for reproducing CUDA/OpenVINO internals or adding ANE. The M4 earns third-platform status only after runtime, exactness, memory and telemetry qualification on the physical machine.

