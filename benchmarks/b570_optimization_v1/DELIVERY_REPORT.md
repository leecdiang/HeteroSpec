# Complete delivery of a boundary stop

Delivery status: **COMPLETE_BOUNDARY_STOP**. This is an actual platform-feasibility stop, with zero generated requests; it is not a performance negative or a positive-result certification.

PR85 plan head: `840ef5fef96068e0e40eee434d89d07bbad6a592`.
Actual fresh GitHub source/CAS head: `973ea0cebf72bc064407aa425188a83df4be0951`.
Remote full restoration/readback passed at `2026-10-11T07:14:14Z`. The separate receipt/report and raw-cache whitespace attribute are published in a subsequent metadata-only commit, whose final head and changed Git blobs are checked independently.

All11 zero-forward load attempts are retained (Qwen8, Llama3, including one explicitly charged memory-log repair). Both family pairs failed the declared512MiB dedicated-memory gate or native budget check. The closest observed Qwen Q4/UB32/single-output load had527,925,248 bytes (503.47MiB); Llama Q4/UB32 had219,439,104 bytes (209.27MiB), and repaired Llama Q8 draft-weight loading recorded budget-minus-usage−218,660,902 bytes. Native full layer/KV loading is checked where a complete pair load exists; first Q8 Llama startup remains an explicitly retained partial/error record.

Engineering budget was conservatively charged8/640 Qwen and3/640 Llama units for zero-forward loads, in addition to the independent8-load cap. There were0 generation, warmup, formal or auxiliary decode starts. No ordinary or candidate was selected; complete-output, native batched/rollback, engineering-peak/no-spill and performance gates remain NOT_TESTED with every qualified ratio null.

Independent CPU verification passed**561,324 checks**, mostly actual full-vocabulary row comparisons, plus model hashes, same-PID dedicated-heap calculations, corrected native intervals and seven refused safety/provenance mutations. The separate design selftests passed19 cases. All six fixed model files were fully rehashed. Native observed intervals total74.336 seconds; they exclude process/Vulkan startup, so the entire serial study wall was conservatively used for lifecycle budgeting. Original erroneous CPU summaries/source and every native negative record are retained.

Canonical archive SHA256: `7ab3f2920e170f5f65f373ccdbef4772667502c2c414dfeed3c08516e8fe5b46`, **30,238,265 bytes /104 logical files /101 objects /1 Git part**. Both actual local and fresh GitHub restorations verified all part/archive CRC/SHA, object/file bytes,15 original source blobs, executed source/binary versions and unchanged inherited numerical DLLs. Independent rederivation was identical apart from receipt UTC; no model was forwarded. All73 selected public/CAS Git files matched local worktree, fresh GitHub worktree and actual Git blob bytes.

[中文报告](REPORT.zh-CN.md), [remote receipt](REMOTE_READBACK.json), [local receipt](LOCAL_RESTORE.json), [CAS index](CAS_INDEX.json), [restore/dependency scope](RESTORE.md).

The sealed DECISION preserves its pre-transport pending-delivery field. This report and the transport receipts close delivery without rewriting those native/scientific bytes. Six exact GGUF files and the independently restored historical#82 CAS remain external hash-bound dependencies. Result PR#86 remains Draft/unmerged.
