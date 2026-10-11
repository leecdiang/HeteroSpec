# B570 Llama memory follow-up v1

Execution of prospective [PR87](https://github.com/leecdiang/HeteroSpec/pull/87), exact design head `ab9dc1f935618931c3779f46a95f3b056b707457`. New study and budgets; PR85/86's original512MiB failures and11 old loads are preserved.

Both profiles have pinned, full SHA-verified target/draft assets and complete128256-token native vocabulary/EOG checks. STANDARD_Q6 uses Q6_K with512MiB; TIGHT_Q8 uses Q8_0/Q4_K_M with128MiB. No precision pooling or reference reuse.

Default `n_gpu_layers=999` leaves input embeddings in CPU_Mapped weight buffers. Those initial12 zero-forward probes are nonqualifying placement observations, despite full GPU-layer logs. The prospective worker explicitly maps every model tensor to Vulkan0 and emits actual weight allocation mappings. The next10 zero-forward probes use that placement. All22 probes remain paid and retained. Actual physical residency/paging remains UNKNOWN; no qualified GPU speed claim follows from budget, Vulkan buffer types or layer counts.

The resident worker implements raw cap/EOG commits, greedy sampling, fresh KV reset, four-output logical speculative verification, unrepaired native target partitions and inherited physical UB1 continuation partition repair. Ordinary and matched paths use the same profile target. Model arithmetic in restored GGML DLLs is unchanged; private llama phase-binding/observation source changes are retained. Upstream numerical module/checkpoint conversion commits remain NOT_CERTIFIED.

F0A freezes both profiles, source/binary bytes, thresholds, complete candidate space,12 exposed MBPP/GSM8K inputs, synthetic longest768-token prompt, history-ID audit, opaque prospective pool, budgets and native rejection checks. No token forward can run until actual remote Git archive/blob restoration verifies all frozen files. Held-out questions are not provided to the engineering selector; an exact-description audit would be required at F0B.

Status at initial publication: F0A prepared; engineering generation not started; no F0B or confirmation admission. This is a Draft result delivery, with raw diagnostics and stop reasons to be appended after execution. No manuscript changes or merge.
