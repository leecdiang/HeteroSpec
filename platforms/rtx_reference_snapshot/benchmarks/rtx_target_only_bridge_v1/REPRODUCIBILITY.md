# Reproduce and restore the bounded study

Pinned parent is PR54 commit16aeada781c475c9641e09c90e93fb0a0e136c34.
The delivered branch is codex/rtx-target-only-bridge-v1. Read the actual PR/head and
delivery receipts; do not substitute a moving branch tip for a fixed source identity.
No historical evidence or frozen manuscript is modified. Model/runtime bytes are
intentionally omitted and must come from the exact existing authorized assets;
do not download substitutes and call them comparable.

## Offline raw evidence restoration

The raw archive follows the repository's content-addressed CAS convention.
`artifacts/rtx_target_only_bridge_v1/ARCHIVE.json` binds ordered48MiB parts,
total size/SHA256, logical-file count, and unique blobs. MANIFEST.json binds every
logical file. Keep all parts and scripts at the delivered Git commit. Use an empty
short destination. Python3.11+, no GPU/model/runtime/network is needed after download.

```powershell
python scripts/platform/rtx_target_only_bridge_v1/package.py restore --root . --dest C:/Evidence/rtx-bridge
python C:/Evidence/rtx-bridge/scripts/platform/rtx_target_only_bridge_v1/verify.py --root C:/Evidence/rtx-bridge --namespace formal --output C:/Evidence/rtx-bridge-check
python C:/Evidence/rtx-bridge/scripts/platform/rtx_target_only_bridge_v1/settings_audit.py --root C:/Evidence/rtx-bridge
```

The archive contains all newly executed engineering/formal selected records, full
raw logs/transcripts/traces/first-pending KV/logits, attempt ledger, heartbeat and
process bindings, restored historical114 native logs/results and38 input files,
source-bound oldU2/reference array exports, protocol/freeze/qualification snapshots,
and verifier/scripts. Compact arrays, comparisons, per-task CSV and exact hashes
are also directly reviewable in Git. Final packaging/readback/PR receipts are later
Git objects, outside the raw snapshot; do not require circular archive membership.
Git-backed parts have repository retention rather than transient Actions-artifact
retention. They still require repository access and continued repository availability.

Restoration hashes every part, joined archive, CAS blob and logical file and rejects
unsafe paths. The offline verifier reparses raw IDs/input IDs/endpoints and verifies
selected-attempt bindings, machine-recorded settings, native transfer witnesses and
all tables. This authenticates content consistency. It does not independently
authenticate the original machine, omitted weights/runtime bytes, or absolute time.

## Local execution / resume

Existing asset root: D:/HeteroSpec-PC. Existing qualified native root:
D:/HeteroSpec-RTX-Target-V1/work/rtx-target-v1/native-build/bin. Study worktree:
C:/Users/ASUS/Documents/Codex/2026-10-05/w/work/bridge. New raw working directory:
work/rtx-target-only-bridge-v1. Python:D:/HeteroSpec-PC/python311/python.exe.
Each actual argv/environment lives in selected START/result/PROCESS artifacts.

```powershell
D:/HeteroSpec-PC/python311/python.exe scripts/platform/rtx_target_only_bridge_v1/runner.py formal
```

Resume verifies the immutable freeze, prior record/file hashes and owned process
identities. Valid complete keys are reused without model execution. Pending keys
take the next separate attempt, with bounded infrastructure retries; completed
scientific mismatches never rerun. Inspect SELECTED_ATTEMPTS, ATTEMPT_LEDGER,
HEARTBEAT, LOCK history and formal-COMPLETE first. Never launch concurrent workers.
Preparation/freeze are one-time operations and refuse duplicate execution.
No routine model rerun is needed for delivered completed evidence.

New-machine reproduction cannot simply reuse the old absolute paths or bypass a
qualification gate. Preserve exact asset hashes and compare environment differences;
this delivery makes no portable performance or cross-device equivalence claim.
