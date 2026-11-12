# Read-only environment and provenance audit

The observed device is NVIDIA GeForce RTX 5070 Ti Laptop GPU, UUID
`GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd`, physical index 0, 12,227 MiB,
driver 616.92. No compute process was reported by the read-only `nvidia-smi`
snapshot. The legacy `D:/HeteroSpec-PC/RTX_EXPERIMENT.lock` was absent.
Neither observation establishes an exclusive GPU window.

The original #221 execution thread is **UNVERIFIED**. The app's `list_threads`
request failed with MCP error -32000. The parent verified the remote draft head
as `af436df989570ad882db65bd8a4b265b9e8cfdae`; the remote root `AGENTS.md`
returned 404. Local source copies have their own llama.cpp `AGENTS.md`, retained
read-only; no changes or submissions to upstream llama.cpp were performed.
No model worker or CUDA kernel was launched by this audit.

`LEGACY_LEDGER_AUDIT.json` contains copied-ledger queries and before/after hashes
for the three legacy main ledger files. All three match the published pins,
and remain byte-identical. Published cumulative totals are 2,716 requests and
2,872,841 reserved target/draft rows; qualification used 500 of 512 slots.
The first supplementary worker retains its original FAILED status despite its
four successful native requests. No budgets or refunds are carried into the
new epoch. The copies were queried locally so the originals were not opened by
SQLite. Sidecar identities are preserved separately in the audit.

`DISK_IDENTITIES.json` independently rehashes the historical R, loop4-v2 and
packed-v2 executables and their pinned DLL files. All disk identities match
their BUILD.json pins. The Qwen3-8B Q8_0 target is 8,709,518,112 bytes with hash
`408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`;
the Qwen3-0.6B Q8_0 draft is 639,446,688 bytes with hash
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
A metadata-only GGUF reader found 151,936 tokens in each, with identical
canonical-JSON vocabulary fingerprint. This audit did not load these models.

Historical receipts bind F16 K/V, target context 1024/batch1024/ubatch32 and
reserve8, draft ubatch4/output1, disabled flash attention, greedy live proposals,
NATIVE prompt/draft producers and all model layers plus output on the same RTX.
These are historical bindings; they do not qualify a newly built executable.
Actual loaded DLL paths/hashes, placement, dispatch and graph reuse must be
recorded again in the new native epoch. The inspected host-core CMake caches
set GGML_CUDA=OFF and GGML_CUDA_GRAPHS=ON, so they cannot establish the imported
CUDA DLL's graph build policy. `SUMMARY.json` records that distinction.

Portable CUDA 12.9 (nvcc V12.9.86), MSVC 14.44.35207, SDK 10.0.26100.0, Python
3.11.9 and Zig 0.16.0 are available at the exact paths in the manifests. Only
the version commands were executed. D: and E: were used read-only; all written
audit evidence stays in this independent workspace directory.

`recovered_operand/PROVENANCE.json` binds one **derived q8 replay**: the first
eight contiguous columns of a real q32 projection capture from
`E:/rtx170/witness-8B/native`. The historical q8 backend-loop4 and packed replay
outputs match in all 131,072 bytes. This is useful for CPU/build preparation;
it does **not** meet the requirement for a newly admitted actual q8 projection
capture, and its old timings are not Round 1 timings. The full weight and raw
binary files are local inputs and must not be published in the source package.
