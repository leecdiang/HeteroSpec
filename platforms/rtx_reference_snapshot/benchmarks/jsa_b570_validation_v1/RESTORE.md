# CPU restoration only

Use Python3.12 with NumPy, obtain all eight exact parts listed in CAS_INDEX.json from this result commit, and run:

`python benchmarks/jsa_b570_validation_v1/code/cas.py restore <fresh-checkout> <new-empty-restore-path> <receipt-path>`

This combines/checks every part, full archive SHA/CRC, every object and every logical file. It independently reruns A/B/D parsing, the actual-architecture KV/F32 reader and CPU closeout. No generation program is launched.

The original Qwen and fixed Smol model weights remain external, hash-bound paths in MODEL_CHOICE/QWEN_MODELS. Numerical runtime DLLs/executables and inherited frontend/private phase-binding sources are included. Verification also rereads the installed module paths recorded by the actual sessions; this restoration proves the present Windows/B570 host contract, rather than deployment on a different host. Original PR64 CAS is a separately verified historical dependency; new result arrays are in the new archive.

KV widths/layers come from actual target GGUF metadata, including SmolLLama shapes, not Qwen constants. Full float32 rows, every serialized byte and fp16 element are checked. Natural-state cross arrays are absent because the finite discovery had no trigger.

The controller enforced a conservative GPU-session budget including preflight overhead. ACTIVE_GPU_ACCOUNTING reconstructs actual Windows process-creation identities through observed post-exit receipts, an upper bound that excludes preflight. Host performance timers are unchanged.

Frozen F0 code remains mirrored in the archive. Later CPU-only readers/publishers are separately hash-bound and do not alter inference or replay requests. Fresh CPU rederivation must reproduce the sealed scientific matrix and counts.
