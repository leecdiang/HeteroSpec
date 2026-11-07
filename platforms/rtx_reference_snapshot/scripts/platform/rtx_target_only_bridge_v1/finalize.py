"""Final durable delivery metadata after authenticated readback and clean verification."""
from common import *
def main():
    s=load(DOC/'RESULTS.json');restore=load(DOC/'ARCHIVE_RECEIPT.json');remote=load(DOC/'REMOTE_READBACK.json');index=load(ROOT/'artifacts/rtx_target_only_bridge_v1/ARCHIVE.json')
    assert s['formal']==171 and restore['status']==remote['status']=='PASS' and all(restore['scientific_outputs_byte_equal'].values())
    save(DOC/'DELIVERY_RECEIPT.json',{'status':'EVIDENCE_VERIFIED_READY_FOR_DRAFT','scientific_outcome':s['outcome'],'formal':171,'engineering':12,'diagnostic_generations':0,'failed_model_attempts':0,'remote_content_commit':remote['commit'],'archive_sha256':index['sha256'],'archive_bytes':index['bytes'],'parts':len(index['parts']),'logical_files':restore['logical_files'],'all_part_remote_readback':'PASS','clean_restore_independent_verification':'PASS','outputs_byte_equal':restore['scientific_outputs_byte_equal'],'transport_failures':{'gh_raw_requests':3,'identity_header_probe':1,'binary_reader':0,'model_reruns':0},'utc':now(),'scope':'model/runtime binaries omitted; local asset authentication and content integrity are distinct from independently authenticated machine execution/time'})
    text=f'''# Verification and delivery

**PASS.** The independent CPU parser reconstructed all 171 fresh formal records from raw selected logs/traces and verified 1,596 per-run file bindings. It imports no controller capture/comparison helper and does not use its PASS flags. All exact keys, prompt bytes/prefill IDs, settings, full committed arrays, endpoints, transcript bytes, native handoffs, repetition stability, historical bridges and comparison tables pass.

Engineering was separately audited (12 runs). Seven negative tests passed: truncated capture, duplicate keys, mixed attempts, early EOS and cap/marker risks. A separate strict-JSON settings audit covers 183 engineering/formal records and 122 native handoffs; it checks F16 KV, non-unified contexts, greedy settings, exact queue/order, draft k=2 and 24/24 thread flags, and the first-sample/pending/transfer sequence. U2 has one loaded target/context and no draft argument/load/speculative initialization or transfer. No arbitrary internal function-call tracing is claimed.

All 80 local model/data/runtime/native/tokenizer bindings match after execution. GPU UUID, driver and OS match preparation. The unchanged qualified instrumentation is reused with the documented local four-task smoke coverage; the old 120-array/30-sham campaign was not rerun. The historical lead reparses 114 restored native logs and uses the pinned old U2/reference array export, with its 12-thread caveat.

The frozen reason-only endpoint metric remains explicit. The supplementary full boundary is (length, EOS/limit reason, terminal ID): U2/N1 57/57; U2/N0 and N0/N1 54/57. Joint array/boundary agreement remains 57/57, 51/57 and 51/57. /15's different lengths are visible; /25 differs in IDs with the same boundary. All 60 recorded uncommitted target samples are retained outside committed-array equality.

## Actual archive/readback coverage

All **11** new Git-backed parts, the index and manifest were downloaded from the authenticated repository at `{remote['commit']}`. Every length/hash matches. Joined archive: **{index['bytes']:,} bytes**, SHA256 `{index['sha256']}`. Clean restoration checked every CAS blob and all **{restore['logical_files']:,} logical files**.

The frozen verifier was executed from the restored source against the restored evidence and again passed all 171 records. SUMMARY, ARRAYS, WITNESSES, COMPARISONS, RETROSPECTIVE_LEAD, task CSV, supplementary settings and strict-boundary outputs are byte-identical to the original independent audit. The settings checker only adds an external output-path option to avoid rewriting restored hardlinks; its predicates are unchanged. Supplementary boundary code/tables and later final reports/receipts are separate Git objects; the raw snapshot contains the earlier explicitly labelled reason-only table. No frozen execution code, argv, selected outcome or denominator changed.

Transport failures were retained: three gh raw API attempts returned `transform: short source buffer` and only two bytes; an identity-header diagnostic also failed. A binary-safe reader of the same authorized API succeeded. Credentials stayed in memory and were never written. Failure bodies/logs are in delivery_failures/ and READBACK_FAILURES.json. No GPU run was repeated to repair transport.

Git-backed parts avoid temporary Actions-artifact expiry, but require repository access and continued repository availability. Hash consistency/Git membership do not independently authenticate omitted weights/runtime binaries, the physical execution or absolute experiment clock. Opaque sampler bytes, later live-prefix KV and U2 internal state remain unavailable. No performance/energy/VRAM or universal equivalence claim follows.
'''
    (DOC/'VERIFICATION_REPORT.md').write_text(text,encoding='utf-8',newline='\n')
    hand=f'''# Exact handover

Scientific state: **{s['outcome']}**. Formal 171/171; engineering 12; additional diagnostics 0; failed model attempts/retries/restarts 0. All-part authenticated readback, clean 2,276-file restoration and independent verification pass. The mandatory Draft PR is the next delivery step; its final identity is recorded in DELIVERY_RECEIPT.json after creation.

Branch: `codex/rtx-target-only-bridge-v1`. Base: `codex/manuscript-intervention-reconstruction-v010`, exact source `{PIN}` (PR #54). Freeze: `{load(DOC/'FREEZE_RECEIPT.json')['commit']}`; receipt committed before formal execution. Raw artifact content commit: `{remote['commit']}`. Existing manuscript, old evidence, PR #53/#54 and original checkouts are unchanged.

Local worktree: C:/Users/ASUS/Documents/Codex/2026-10-05/w/work/bridge.
New raw: work/rtx-target-only-bridge-v1. Existing assets: D:/HeteroSpec-PC.
Existing qualified native binary: D:/HeteroSpec-RTX-Target-V1/work/rtx-target-v1/native-build/bin/llama-cli.exe.
Python: D:/HeteroSpec-PC/python311/python.exe.
Remote downloaded parts: C:/Users/ASUS/Documents/Codex/2026-10-05/w/work/readback.
Clean restored raw: C:/Users/ASUS/Documents/Codex/2026-10-05/w/work/r.
Restored audit: C:/Users/ASUS/Documents/Codex/2026-10-05/w/work/restored-check.

The runner exited successfully and its lock is in LOCK.finished history. No GPU process is pending. SELECTED_ATTEMPTS and ATTEMPT_LEDGER bind first valid attempts; formal-COMPLETE records completion. The old heartbeat is a final process observation, not proof of a live worker. Do not regenerate complete keys: the resume command validates and skips them.

```powershell
D:/HeteroSpec-PC/python311/python.exe scripts/platform/rtx_target_only_bridge_v1/runner.py formal
D:/HeteroSpec-PC/python311/python.exe scripts/platform/rtx_target_only_bridge_v1/verify.py --namespace formal --output work/rtx-target-only-bridge-v1/formal-verify
```

REPRODUCIBILITY.md gives CPU-only archive restoration. Compact arrays/tables/identities/reports are directly in Git; full raw uses artifacts/rtx_target_only_bridge_v1. The final artifact manifest binds delivered files. Transport recovery changes only delivery tooling, and strict boundary reporting is additive; frozen code and primary outcomes remain preserved.

Recommendation: stop this new-method novelty route. Ordinary U2 suffices on the tested exposed cohort and reference restoration still fails on /25 and /18. No new study is launched. Remaining scientific limits are the exposed 19-task scope, one model pair/backend, unavailable later live state/U2 internals, opaque sampler and local-only machine/time authentication. There is no remaining hardware, qualification or evidence-delivery blocker.

If the final PR operation fails, retain exact commits, parts and PR_BODY.md and repair only GitHub delivery. Do not rerun models or merge. A created PR remains Draft and unmerged.
'''
    (DOC/'HANDOVER.md').write_text(hand,encoding='utf-8',newline='\n')
    print(json.dumps({'status':'READY_FOR_DRAFT','archive_files':2276,'formal':171}),flush=True)
if __name__=='__main__':main()
