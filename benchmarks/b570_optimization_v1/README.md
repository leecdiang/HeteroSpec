# B570 PR85 feasibility and bounded stop

Execution plan: PR85 at `840ef5fef96068e0e40eee434d89d07bbad6a592`. New result branch; previous #82/#84 evidence is preserved.

The actual B570 SDK memory template compiled after a retained CPU-only field correction. All numerical DLLs match the restored #82 originals. Fifteen plan source blobs,307 restored private source files and the full #82 CAS restoration were independently checked. Hardware/driver/display/power inventory is bound.

8 actual zero-forward load combinations are recorded; independent parser checks: 730. All7 memory guard mutations were rejected. CPU planning selftests passed19 tests.

| Actual configuration | Loaded dedicated headroom (MiB) | Native zero-forward status |
|---|---:|---|
| QWEN_Q4 | 485.84375 | BLOCKED_INSUFFICIENT_LOADED_HEADROOM |
| QWEN_Q4_UB128_OUT1 | 438.71875 | BLOCKED_INSUFFICIENT_LOADED_HEADROOM |
| QWEN_Q4_UB32 | 489.34375 | BLOCKED_INSUFFICIENT_LOADED_HEADROOM |
| QWEN_Q4_UB32_OUT1 | 503.46875 | BLOCKED_INSUFFICIENT_LOADED_HEADROOM |
| QWEN_Q4_UB512 | 352.53125 | BLOCKED_INSUFFICIENT_LOADED_HEADROOM |
| QWEN_Q4_UB512_OUT1 | 443.53125 | BLOCKED_INSUFFICIENT_LOADED_HEADROOM |
| QWEN_Q8 | 301.40625 | BLOCKED_INSUFFICIENT_LOADED_HEADROOM |
| QWEN_Q8_UB32_OUT1 | 288.09375 | BLOCKED_INSUFFICIENT_LOADED_HEADROOM |

## Current family decisions

- Qwen: `BLOCKED_LOADED_HEADROOM_OR_LOAD_ERROR`; 8/8 zero-forward load combinations,0/640 engineering requests,0/800 confirmation requests,qualified ratio=null.
- Llama: `PENDING_PINNED_TARGET_ASSET_AND_ACTUAL_LOAD`; 0/8 zero-forward load combinations,0/640 engineering requests,0/800 confirmation requests,qualified ratio=null.

Dedicated headroom is calculated from the actual model-owning worker PID's device-local heap only. The separate system heap is retained and never added to device-local free bytes. Required minimum is536,870,912 bytes (512MiB). File-size estimates and another process's usage are not load proof.

The probe directly loads model/context without a prompt, hidden common warmup or llama_decode/encode import. Actual stderr verifies complete layer offload and Vulkan KV placement. Source, versions, binary imports and raw load logs support the zero-forward claim. Loaded-only passes, if any, do not admit a performance claim before the untouched native output/peak/reset/capture gates.

No fastest ordinary was selected, no candidate scored, no complete-output or speed comparison exists. There are0 token-generation starts/retries, no formal slots and no F0B. Full exposure audit and F0A/F0B seals would be required before future inference; mandatory source/exclusion context is recovered without creating a new cohort.

## Reviewable commands and costs

CPU-only verification: `python code/verify_loads.py <fresh-restored-root>`. The planning tool selftests and static plan can be rerun from the PR85 base. `RESTORE.md` will record the final content-addressed restoration command.

The hash-bound `code/load_controller.py` is a serial zero-forward loading controller, not a certified inference runner. Its CLI accepts one of the declared family/draft/UB/output-reservation combinations, verifies actual model bytes before launch, refuses overwrite/retry, records fsynced START/END and prevents a ninth load per family. The inherited earlier direct preparation loads are transparently retained. A stopped configuration cannot be sent token inputs by this binary.

Observed zero-forward native load intervals are about seconds, not an estimate of inference throughput. No measured forward rate exists from which to estimate a complete optimization/confirmation run. Whole study elapsed time is conservatively charged as each family's owned-GPU-lifetime upper bound, including CPU/download time.

Separate new CAS packaging, actual fresh restoration and remote Git readback remain tracked in the delivery receipt. No automatic merge, manuscript edit, backend upgrade, offload fallback or target-precision change is authorized by this result.
