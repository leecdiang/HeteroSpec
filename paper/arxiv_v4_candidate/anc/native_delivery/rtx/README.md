# RTX native material delivery

Requested by PR145 `NATIVE_DELIVERY_PROMPT.md` at `bc5157c46a2999b5716e9968cc5b5571e4e6e930`.
Result baseline: PR147 `3429e2c49626c30e4a406a517a3e8a030aea9c7f`.
This is the RTX source host's delivery; B570/PR148 is a separate source-host package.

## Stable entry and integrity

[Immutable material directory](https://github.com/leecdiang/HeteroSpec/tree/3999a95dd8f7fd29ae68b04ca46b8e95107c246c/benchmarks/rtx_native_delivery_20261026)
· [Minimum commands and dependency guide](https://github.com/leecdiang/HeteroSpec/blob/3999a95dd8f7fd29ae68b04ca46b8e95107c246c/scripts/native_reproduction/rtx_delivery/README.md)
· [Machine-readable access](ACCESS.json)
· [Remote download verification](REMOTE_VERIFICATION.json)

The repository is private; existing repository **read** permission and ordinary
Git authentication are sufficient. The immutable material commit is
`3999a95dd8f7fd29ae68b04ca46b8e95107c246c`. No draft release, external hosting
account, local drive mapping or model upload is required.

| Artifact | Size/count | Integrity |
|---|---:|---|
| Reassembled `RTX_NATIVE_DELIVERY.zip` | 473,187,187 bytes | SHA256 `1b3aa913be73db8be50d7cc28f6e733ad5b4b1a52862a3838920933ea70978a0` |
| Ordered transport parts | 12 (at most 40 MiB each) | [PARTS.json](PARTS.json) |
| Expanded ZIP members | 785; 546,936,474 bytes | [MEMBERS.json](MEMBERS.json), including original hashes and source |
| Exact external runtime and model dependencies | 21 DLLs; 2 GGUFs | [DEPENDENCIES.json](DEPENDENCIES.json) |

Fresh download and CPU verification, in PowerShell (choose new directories):

```powershell
git clone --filter=blob:none --no-checkout --single-branch --branch windows/rtx-native-delivery-20261026 https://github.com/leecdiang/HeteroSpec.git C:/repro/rtx-materials
Set-Location C:/repro/rtx-materials
git sparse-checkout init --cone
git sparse-checkout set benchmarks/rtx_native_delivery_20261026 scripts/native_reproduction/rtx_delivery
git checkout --detach 3999a95dd8f7fd29ae68b04ca46b8e95107c246c
python scripts/native_reproduction/rtx_delivery/delivery.py restore benchmarks/rtx_native_delivery_20261026/PARTS.json C:/repro/rtx-delivery
```

`restore` checks all part/whole hashes, all 785 members, and the CPU audit.
The source ZIP additionally has its own 3542-member index, checked by `prepare`.
See the linked guide for exact upstream downloads, model hashes, path parameters,
and separately opt-in native replay commands. No native command was executed
in this delivery task.

## Delivered and verified

- Original source/executable capsule; true E1 q3/layer0 fixture; MQ own-path and
  PQ/QB stage references. Core/frontend rebuilding remains distinct from the
  pinned numerical DLLs; no kernel rebuild is claimed.
- Complete existing R/PQ/QB records for GSM8K/test/443, including 704 raw full
  vocabulary vectors and the historical E2 reference. All 288 PQ/QB vector pairs
  match; discarded rows and full speculative state are retained.
- Six historical/rebuilt HTTP responses, 936 existing formal request records,
  original qualification and audit receipts. Their recorded results are preserved.
- Fresh upstream download of both b10839 CUDA 12.4 archives; all 21 DLLs match
  the historical hashes. Weights have pinned official GGUF URLs/revisions and
  require no conversion. Dependency bytes stay external.
- Fresh Git download, ZIP extraction and CPU audit; new-directory runtime
  preparation with exact local weights and downloaded DLLs. This is same-host
  transport verification, not an independently provisioned second-machine run.
- Eight CPU regression tests, including corrupted members/parts, duplicate or
  escaping paths, overwrite refusal and Windows deep paths. A copied reference
  with a deliberately changed vector byte is rejected by the request auditor.

## Only locally retained / external dependencies

The 26.9-GB full source-host collection, other inputs' heavy vectors, complete
build trees and interrupted v1 native attempt remain locally retained under
PR147's [RAW_ACCESS.json](../rtx_native_bridge_20261026/results/RAW_ACCESS.json)
and hashed inventory. This minimum kit does not label them externally delivered.
The initial packaging preparation that exposed Windows path-length limits also
remains preserved; extended-path extraction fixes that issue.

The recipient must independently download the two exact model weights and two
upstream runtime archives and supply its Windows GPU driver/toolchain. No
necessary byte or acquisition route is missing for this RTX minimum kit. This
does not settle B570 delivery, rebuild CUDA kernels, merge the result PR, or
change any scientific measurement. Native processes/performance experiments
started by this packaging task: **0**.
