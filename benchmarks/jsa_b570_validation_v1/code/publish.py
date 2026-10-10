"""Publish lightweight provenance derived from sealed payloads; no forward."""
from pathlib import Path
import json,hashlib,shutil
R=Path('C:/hs/jsa-b570-run-v1');P=Path('C:/hs/jsa-b570-v1/benchmarks/jsa_b570_validation_v1')
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,x):(P/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
rows=[];modules={};devices=[]
for p in sorted((R/'sessions').iterdir()):
 row={n:load(p/n) for n in ['SESSION.json','SESSION_LOAD.json','SESSION_CLOSE.json','DEVICE_PREFLIGHT.json','MODULES.json']};rows.append(row);modules[p.name]=row['MODULES.json']
 if (p/'ENVIRONMENT.json').exists():devices.append(dict(session=p.name,record=load(p/'ENVIRONMENT.json')))
save('SESSION_BINDINGS.json',rows);save('MODULE_BINDINGS.json',modules);save('DEVICE_BINDINGS.json',devices)
shutil.copyfile(R/'LOCAL_CAS_RESTORE.json',P/'LOCAL_CAS_RESTORE.json')
readme='''# Independent B570 second-family validation

Result Draft PR #82 executes PR #81 at exact plan head `0a95a64805536323b0e8ae11784eaab150f91dcf`.

All560 requests completed:32 Qwen bridge,128 SmolLM2 discovery/capture controls,384 formal and16 warmups. Zero failures/missing/retries. All four arms qualified at the first-runtime-EOG-inclusive-or128 endpoint on the full24-task/four-round panel. N and C have raw suffix differences, so endpoint qualification is not complete raw equality.

Qualified host-request GM baseline/C: R/C **0.546138908**, M/C **0.561561946**, N/C **12.905834161**. C is about1.83 times the ordinary R cost; all24 tasks in all4 rounds were slower than R. Natural-state diagnostics were **NO_TRIGGER**. No cross-date or production-robustness claim.

[Chinese report](REPORT.zh-CN.md), [decision](DECISION.json), [complete matrix and per-task costs](D_VERIFICATION.json), [counts](COUNTS.json), [independent verification](INDEPENDENT_VERIFICATION.json), [full KV/F32 check](STATE_FLOAT_VERIFICATION.json), [negative guards](NEGATIVE_CONTRACT_TESTS.json).

[F0](F0.json) and [remote freeze receipt](REMOTE_FREEZE_RECEIPT.json) precede every Smol forward. Confirmation [reservation recheck](CONFIRMATION_RESERVATION_RECHECK.json) retained the frozen panel. [Ledger](LEDGER.jsonl) contains every START/COMPLETE; actual [sessions](SESSION_BINDINGS.json), [modules](MODULE_BINDINGS.json), [devices](DEVICE_BINDINGS.json) and [timers](TIMER_BINDINGS.json) are bound. [Preparation deviations](PREPARATION_DEVIATIONS.json) retain rejected static transport/CPU assumptions without scientific reruns.

[CAS index](CAS_INDEX.json) maps8 Git-hosted SHA256 parts to a392608205-byte ZIP and3319 logical files. [Local fresh restore](LOCAL_CAS_RESTORE.json) rederived every result identically. Final remote restoration/readback is reported separately in REMOTE_READBACK.json and DELIVERY_REPORT.md; DECISION.json was sealed before transport. No automatic merge/manuscript edits/release.
'''
(P/'README.md').write_text(readme,encoding='utf8')
restore='''# CPU restoration only

Use Python3.12 with NumPy, obtain all eight exact parts listed in CAS_INDEX.json from this result commit, and run:

`python benchmarks/jsa_b570_validation_v1/code/cas.py restore <fresh-checkout> <new-empty-restore-path> <receipt-path>`

This combines/checks every part, full archive SHA/CRC, every object and every logical file. It independently reruns A/B/D parsing, the actual-architecture KV/F32 reader and CPU closeout. No generation program is launched.

The original Qwen and fixed Smol model weights remain external, hash-bound paths in MODEL_CHOICE/QWEN_MODELS. Numerical runtime DLLs/executables and inherited frontend/private phase-binding sources are included. Verification also rereads the installed module paths recorded by the actual sessions; this restoration proves the present Windows/B570 host contract, rather than deployment on a different host. Original PR64 CAS is a separately verified historical dependency; new result arrays are in the new archive.

KV widths/layers come from actual target GGUF metadata, including SmolLLama shapes, not Qwen constants. Full float32 rows, every serialized byte and fp16 element are checked. Natural-state cross arrays are absent because the finite discovery had no trigger.

The controller enforced a conservative GPU-session budget including preflight overhead. ACTIVE_GPU_ACCOUNTING reconstructs actual Windows process-creation identities through observed post-exit receipts, an upper bound that excludes preflight. Host performance timers are unchanged.

Frozen F0 code remains mirrored in the archive. Later CPU-only readers/publishers are separately hash-bound and do not alter inference or replay requests. Fresh CPU rederivation must reproduce the sealed scientific matrix and counts.
'''
(P/'RESTORE.md').write_text(restore,encoding='utf8')
files={}
for p in sorted(P.rglob('*')):
 if p.is_file() and '__pycache__' not in p.parts and p.name not in ['PUBLIC_FILE_MANIFEST.json','REMOTE_READBACK.json','DELIVERY_REPORT.md']:files[p.relative_to(P).as_posix()]=dict(sha256=sha(p),bytes=p.stat().st_size)
save('PUBLIC_FILE_MANIFEST.json',dict(files=files,scope='Lightweight result/source/provenance bytes; CAS parts separately SHA-bound by CAS_INDEX. Receipt cannot bind its own future commit.'))
print('Published',len(files),'light files and',len(rows),'session bindings',flush=True)
