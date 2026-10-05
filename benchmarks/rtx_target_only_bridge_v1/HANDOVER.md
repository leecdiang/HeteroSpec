# Exact study handover

Scientific state:SUPPORTED_ON_EXPOSED_COHORT; formal171/171; engineering12; diagnostic0;
failed attempts0; formal restarts0. Current worktree:
C:/Users/ASUS/Documents/Codex/2026-10-05/w/work/bridge.
Branch:codex/rtx-target-only-bridge-v1; pinned base:
codex/manuscript-intervention-reconstruction-v010 at16aeada781c475c9641e09c90e93fb0a0e136c34.
Freeze:564398820b747674e6ba1bc131e6738e5fda1459; receipt committed before formal.
Original D:/HeteroSpec-PC checkout and D:/HeteroSpec-RTX-Target-V1 old evidence
remain unchanged. Models are Qwen3-8B-Q8_0.gguf and Qwen3-0.6B-Q8_0.gguf; all
exact SHA256/runtime/device identities are in ASSET_ENVIRONMENT/ASSET_POSTCHECK.
Native qualified binary is the exact old native-build/bin/llama-cli.exe.

Local raw:work/rtx-target-only-bridge-v1. SELECTED_ATTEMPTS.json and
ATTEMPT_LEDGER.jsonl bind every first successful attempt; formal-COMPLETE.json
marks completion. HEARTBEAT contains the final measured process state; controller
lock is renamed LOCK.finished after exit. No worker needs continuation and no
process is claimed to run after completion. Repeat execution command skips valid
selected keys after freeze/file checks; it does not regenerate completed outcomes.

CPU verification:
```powershell
D:/HeteroSpec-PC/python311/python.exe scripts/platform/rtx_target_only_bridge_v1/verify.py --namespace formal --output work/rtx-target-only-bridge-v1/formal-verify
D:/HeteroSpec-PC/python311/python.exe scripts/platform/rtx_target_only_bridge_v1/settings_audit.py
```

All compact arrays/results, task tables, salient facts, full comparison details,
protocol/input/asset identities, qualification and freeze remain reviewable in Git.
Raw archive parts/index/manifest are under artifacts/rtx_target_only_bridge_v1;
restore/verify commands are in REPRODUCIBILITY.md. Packaging/readback/PR receipts
record delivered content commits, separately from immutable raw snapshot.

Remaining scientific limits:exposed19task cohort, one model pair/backend,
unobserved U2 internal state and later live-prefix KV, opaque sampler, local-only
asset/execution/time authentication. No speed/energy/VRAM/functionality/general
equivalence/reference-restoration claim. No manuscript changes or merge.
If Git transport/readback/PR fails, preserve exact commits/parts and PR_BODY.md;
repair transport without rerunning any model. Final delivery status is in
DELIVERY_RECEIPT.json; a missing receipt means delivery still pending, not science
incomplete. No routine execution authorization is missing.
