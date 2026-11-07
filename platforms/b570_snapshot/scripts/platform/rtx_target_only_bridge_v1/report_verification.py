"""Produce human-readable verification and resumable handover after complete CPU checks."""
from common import *
def main():
    s=load(DOC/'RESULTS.json');settings=load(DOC/'SETTINGS_AUDIT.json');assets=load(DOC/'ASSET_POSTCHECK.json');assert s['formal']==171 and s['status']==settings['status']==assets['status']=='PASS'
    text=f'''# Independent offline verification

Status:PASS. Source-bound raw verifier reconstructed171/171 formal records,
checked{s['checked_file_hashes']} per-run files by SHA256/length, and recomputed
every complete-array, endpoint/joint, task-unit, first-divergence, positional
difference, repetition-stability and historical-bridge table. It imports no
controller capture/parser/comparison helper, and does not trust controller PASS
flags. Engineering12 is separately reparsed; diagnostics0, failed attempts0.

Exact cohort/queue/condition/order checks passed for19tasks x3conditions x3repeats.
Input prompt bytes and every raw prefill ID match the pinned tokenizer/input contract.
Inclusive EOG/cap128, runtime generation counts, raw decoded byte pieces and complete
transcripts agree. Complete selected-attempt file inventories refer to one attempt
only, with append-only hash-chained ledger start/success bindings. No abandoned
capture was combined with a later result. Seven negative tests cover early EOS,
cap overshoot/EOG128 dual markers/missing markers, duplicate keys, mixed attempts
and truncated capture. Separate strict-JSON checks reject duplicate object keys.

Additive settings audit checked{settings['raw_settings_records']} engineering/formal
records and{settings['handoffs_checked']} native handoffs: raw F16-K/V contexts,
non-unified KV, target greedy settings, no warmup/cache reuse, native draft k2/
explicit24/24 thread flags, and original first-sample -> pending -> transfer ->
continuation sample ordering. Every logged model numerical threadpool is24;
raw system-info reports target24/batch24. HTTP housekeeping threads23 are separate.
Actual CUDA0 target37/37 and native draft29/29 offload, ctx4096/batch2048/FAoff,
condition-specific UB contexts and fresh cached-token counts are directly checked.
Every native handoff retains byte-identical source-before/destination/source-after
snapshots, full151936-float pending logits, positions and sampler clone metadata.
Opaque sampler bytes are unobserved. U2 has only target arguments/load/context and
no draft-load/speculative-init or transfer variable; no arbitrary internal-call
tracing claim is made.

Post-matrix local hash readback passed all{assets['files_checked']} model/data/runtime/
native/tokenizer asset bindings, and GPUUUID/driver/OS match preparation. Source,
freeze/protocol/cohort/input/asset bindings remain intact. Retrospective lead was
recomputed using pinned oldU2/reference arrays and114 CAS-restored old native logs;
oldN0/N1 arrays also match the pinned independent neutral export. HistoricalU2
12thread versus fresh24thread is observational, not thread causality.

Content-hash consistency and Git object membership do not independently authenticate
omitted weight/runtime bytes, original physical execution, or absolute experiment
time. Asset hash checks are local, not independent model reruns. No GPU was used by
the offline verification, no outcome retry or numerical code repair occurred.

## Archive/delivery checks

Raw evidence packaging and all-part remote readback/clean restoration are completed
separately after this pre-archive report snapshot. See ARCHIVE_RECEIPT.json,
REMOTE_READBACK.json and DELIVERY_RECEIPT.json for their exact final coverage.
Those receipts are later Git objects; they are not claimed to be inside the raw
archive they describe. Restoration rechecks parts, joined archive, every CAS blob
and logical file, then repeats the frozen formal verifier/settings audit. Compared
scientific result fields must remain exactly equal. Git-backed raw parts have no
Actions-artifact expiry, while access depends on repository permission/availability.

The additive delivery builder completes the inventory for every frozen file,
including.gitignore and the copied ledger.JSONL. This is packaging-only; frozen
runner/parser/protocol bytes and all actual execution remain unchanged. The original
frozen builder is retained; no failed model batch or formal restart is involved.
'''
    (DOC/'VERIFICATION_REPORT.md').write_text(text,encoding='utf-8',newline='\n')
    hand=f'''# Exact study handover

Scientific state:{s['outcome']}; formal171/171; engineering12; diagnostic0;
failed attempts0; formal restarts0. Current worktree:
C:/Users/ASUS/Documents/Codex/2026-10-05/w/work/bridge.
Branch:codex/rtx-target-only-bridge-v1; pinned base:
codex/manuscript-intervention-reconstruction-v010 at{PIN}.
Freeze:{load(DOC/'FREEZE_RECEIPT.json')['commit']}; receipt committed before formal.
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
'''
    (DOC/'HANDOVER.md').write_text(hand,encoding='utf-8',newline='\n')
    print(json.dumps({'status':'REPORTS_WRITTEN','formal':171}),flush=True)
if __name__=='__main__':main()
