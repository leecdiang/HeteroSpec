"""Seal genuine E2 freeze-drift stop and blocked E1 without scientific starts."""
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import experiment as e
import export_e2_checkpoint as export

LIVE=Path('D:/hs-qb-confirmation-v02')
OUT=Path('D:/hs104c15')
REPO=Path(__file__).resolve().parents[2]

def write_csv(path,rows):
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def extract(archive,target):
    target.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        e.require(all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist()),'archive escape')
        z.extractall(target)

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,default=OUT)
    parser.add_argument('--prior-delivery-failure-log',type=Path)
    args=parser.parse_args()
    global_out=args.out
    # A new output directory preserves any prior CPU/transport delivery failure.
    globals()['OUT']=global_out
    OUT.mkdir(exist_ok=False)
    if args.prior_delivery_failure_log:
        shutil.copyfile(args.prior_delivery_failure_log,OUT/'PRIOR_DELIVERY_FAILURE.log')
    e.require(not (LIVE/'SESSION-5.json').exists() and not (LIVE/'EXECUTION.lock').exists(),'unexpected active scientific slot')
    check=e.read(LIVE/'resumption_20261015/FREEZE_RECHECK.json')
    bad=[x for x in check['checks'] if x['status']!='PASS']
    e.require(len(bad)==1 and bad[0]['path'].endswith('python.exe'),'unexpected drift scope')
    # Authenticated, independently fetched original raw archive, not a local copy.
    route='repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_qb_confirmation_v1/progress_s0_s4_v02/RAW_E2_S0_S4.zip?ref=50e64c7c8a2ac69fd59fd4b80310687754deb071'
    with (OUT/'REMOTE_PRIOR.zip').open('xb') as f:
        subprocess.run(['gh','api',route,'-H','Accept: application/vnd.github.raw','-H','Accept-Encoding: identity'],stdout=f,check=True)
    expected=e.read(Path(__file__).parent/'progress_s0_s4_v02/ARCHIVE_RESTORE.json')['archive_sha256']
    e.require(e.sha(OUT/'REMOTE_PRIOR.zip')==expected,'remote raw archive differs')
    restored=OUT/'remote';extract(OUT/'REMOTE_PRIOR.zip',restored)
    manifest=e.read(restored/'RAW_ARCHIVE_MANIFEST.json')
    for item in manifest['files']:
        p=restored/item['path'];e.require(p.stat().st_size==item['bytes'] and e.sha(p)==item['sha256'],'remote member differs')
    cmd=[sys.executable,'-B','-c','from pathlib import Path;import export_e2_checkpoint as x;import experiment as e;'
         'e.save(Path("REMOTE_RECALC.json"),x.checkpoint_analysis(Path("../data").resolve(),"D:/hs-qb-confirmation-v02"))']
    r=subprocess.run(cmd,cwd=restored/'analysis_scripts',capture_output=True)
    e.require(r.returncode==0,r.stderr.decode(errors='replace'))
    body=(restored/'analysis_scripts/REMOTE_RECALC.json').read_bytes()
    e.require(body==(restored/'PARTIAL_ANALYSIS.json').read_bytes(),'remote independent analysis differs')
    result=export.checkpoint_analysis(LIVE)
    e.require(e.encoded(result)==body,'current and remote record analysis differ')
    e.save(OUT/'REMOTE_RESTORE.json',dict(status='PASS',authenticated_archive=True,archive_sha256=expected,
                                        members_checked=len(manifest['files']),separate_interpreter=True,
                                        analysis_bitwise_equal=True,external_auditor=False))
    # Preserve every immutable request/control record including later cancellation.
    data=OUT/'data';shutil.copytree(restored/'data',data)
    shutil.copytree(LIVE/'resumption_20261015',data/'resumption_20261015')
    shutil.copyfile(LIVE/'USER_CANCELLED_AUTOMATIC_ATTENDANCE.json',data/'USER_CANCELLED_AUTOMATIC_ATTENDANCE.json')
    script=OUT/'analysis_scripts';shutil.copytree(restored/'analysis_scripts',script)
    shutil.copyfile(__file__,script/Path(__file__).name)
    result.update(terminal_status='STOPPED_FROZEN_INTERPRETER_DRIFT',E1_status='BLOCKED_E2_GATE',
                  new_native_requests=0,new_native_workers=0,new_operator_starts=0)
    e.save(OUT/'ANALYSIS.json',result)
    events=[e.read(p) for p in (data/'ledger').glob('*.json')]
    records=[e.read(p) for p in (data/'runs').rglob('RECORD.json')]
    slots={x['slot'] for x in events if x['kind']!='load'}
    rows=[]
    for b in e.read(data/'PLAN.json')['blocks']:
        for task,kind,slot in [(None,'warmup',b['id']+'/WARM')]+[(t,'reference' if b['arm']=='R' else 'comparison',b['id']+'|'+t) for t in b['tasks']]:
            rows.append(dict(session=b['session'],family=b['family'],arm=b['arm'],task=task or '',kind=kind,
                             slot=slot,status='COMPLETED' if slot in slots else 'UNSTARTED_FREEZE_DRIFT'))
    write_csv(OUT/'ALL_SLOTS.csv',rows)
    tasks=[];sessions=[]
    for c in result['comparisons']:
        for row in c['task_ratios']:tasks.append(dict(family=c['family'],path=c['path'],**row))
        for row in c['session_log_contrasts']:sessions.append(dict(family=c['family'],path=c['path'],**row))
    write_csv(OUT/'TASK_CONTRASTS.csv',tasks);write_csv(OUT/'SESSION_CONTRASTS.csv',sessions)
    keys=('target_prefill_calls','target_continuation_calls','draft_prefill_calls','draft_continuation_caller_calls',
          'physical_micrograph_calls','physical_micrograph_rows','target_verification_calls','target_replay_calls')
    counters={k:sum(r.get('workload',{}).get(k,0) for r in records) for k in keys}
    e.save(OUT/'COUNTS.json',dict(native_workers=270,native_requests=1350,warmups=270,comparisons=720,references=360,
                                 unstarted_workers=54,unstarted_requests=270,E1_unstarted_contexts=72,
                                 E1_requests=0,E1_operator_starts=0,new_native_workers=0,new_native_requests=0,
                                 new_model_forwards=0,new_operator_starts=0,
                                 owned_seconds=sum(e.read(p)['seconds'] for p in (data/'runs').rglob('LIFETIME.json')),
                                 observed_counters=counters,
                                 logical_model_caller_invocations=sum(counters[k] for k in keys[:4]),
                                 hardware_kernel_starts='UNKNOWN',all_auxiliary_OS_process_starts='NOT_GLOBALLY_CAPTURED'))
    e.save(OUT/'TERMINAL.json',dict(E2='STOPPED_FROZEN_INTERPRETER_DRIFT',E1='BLOCKED_E2_GATE',utc=e.utc(),
                                  expected_python_sha256=bad[0]['expected_sha256'],actual_python_sha256=bad[0]['actual_sha256'],
                                  completed_sessions=list(range(5)),scientific_failures=0,session5_started=False,
                                  six_cluster_estimate=None,original_F0_unchanged=True,
                                  raw_restoration='PASS',independent_CPU_reanalysis='PASS',owned_native_tasks_active=0))
    counts=e.read(OUT/'COUNTS.json')
    text=f'''# PR104 terminal evidence seal — 2026-10-15

E2: **STOPPED_FROZEN_INTERPRETER_DRIFT**. E1: **BLOCKED_E2_GATE**. These are genuine stop/block outcomes, not completed experiments or scientific success.

Sessions 0–4 completed: 270 native workers, 1,350 native requests (720 comparisons, 360 serial references, 270 warmups), {counts['owned_seconds']:.6f} native owned seconds. Session 5 remains entirely unstarted: 54 workers and 270 requests. E1 has zero starts; all 72 contexts, 216-request ceiling and 432-operator ceiling remain unused and cannot be transferred. This resumption added zero native processes, requests, model forwards or operator starts. Raw workload counters are in COUNTS.json; physical micrograph calls are not hardware kernel launches. Global auxiliary OS process counts were not comprehensively captured and are not invented.

At the October 15 pre-start check, the frozen Python executable at its fixed path changed from `{bad[0]['expected_sha256']}` to `{bad[0]['actual_sha256']}`. Both files are 107,312 bytes; the current interpreter reports Python 3.12.14. Every other frozen file passed, including models, numerical DLLs, native executables, NVIDIA driver binary and scientific source. Bounded local runtime-cache searches found no original-byte interpreter. No global environment was overwritten, no F0 changed and no scientific gate bypassed. This is not a network failure or a scientific retry. Although the time-spacing threshold has now arrived, byte admission failed before SESSION-5.json or any native load.

Scientific request failures/output mismatches in the 1,350 retained records: zero. Invalid output contracts, workload errors and heavy-observer flags: zero. The original Phase 0 routing failure, pre-scientific authenticated transport EOF, CPU export path-length failure, user-requested idle cancellation and this interpreter-drift stop are all retained and separately labeled.

Original scientific F0: `49b992b2ed1cabd05fad6e234cad2d3418c2b65a`; transport supplement: `e06dc8df53622eddd3f9306addbeaf428cdb3548`; prior checkpoint: `50e64c7c8a2ac69fd59fd4b80310687754deb071`; original routing failure: `ccfbc2e4c3ab3026a6bbec5caf4c98646781913c`. None was rewritten.

All six family×M/C aggregate speed ratios and six-cluster uncertainty intervals are **WITHHELD**. The full original R criterion is not qualified across six sessions; the observed five sessions' endpoints and native output contracts are stable/equal. Available per-session log contrasts, all task ratios/regressions/reversals and all 1,620 planned slots remain in CSV/ANALYSIS.json. The 1.02 threshold is unchanged but cannot classify a qualified six-session result. No request-level bootstrap or five-session replacement aggregate was used. E1 bitwise equality, max error, ULP, first divergence and numerical geometry qualification are unavailable because its E2 gate is closed.

The authenticated remote 22.55 MB prior raw archive was fetched independently from GitHub at the pinned checkpoint. All 8,478 members passed length/SHA-256 checks in a fresh short-path directory. A separate interpreter used restored code/data and reproduced the partial CPU analysis byte-for-byte; the current live immutable data analysis also matched. REMOTE_RESTORE.json records the checks. A second fresh-directory restoration of this terminal archive is separately recorded. Both checks occurred on this host, not by an external auditor. Model weights and DLL bytes are excluded; their immutable identities and actual loaded-module receipts are retained.

This execution supplies no completed cross-date PQ/QB evidence and no new E1 mechanism evidence for the paper claim. It neither confirms nor refutes lower-cost local repair preserving speculative-decoding economics. Kernel identity/reduction tree, universal equivalence, new-input and cross-device generalization remain unsupported. Prior empirical values and PR102/main are unchanged. All owned native tasks have ended. The terminal seal permits the separately authorized bounded CPU-only PR110 study; it does not promote PR104 to a successful experiment.
'''
    (OUT/'RESULT.md').write_text(text,encoding='utf-8')
    files=[p for p in sorted(OUT.rglob('*')) if p.is_file() and 'remote' not in p.relative_to(OUT).parts and p.name!='REMOTE_PRIOR.zip']
    manifest=dict(schema=1,status='TERMINAL_STOP_EVIDENCE',files=[dict(path=p.relative_to(OUT).as_posix(),bytes=p.stat().st_size,sha256=e.sha(p)) for p in files])
    e.save(OUT/'RAW_MANIFEST.json',manifest)
    with zipfile.ZipFile(OUT/'RAW_TERMINAL.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in files+[OUT/'RAW_MANIFEST.json']:z.write(p,p.relative_to(OUT).as_posix())
    fresh=Path(str(OUT)+'_finalrestore');extract(OUT/'RAW_TERMINAL.zip',fresh)
    for item in manifest['files']:
        p=fresh/item['path'];e.require(e.sha(p)==item['sha256'] and p.stat().st_size==item['bytes'],'terminal restoration differs')
    # Recompute from the terminal archive using its restored driver and raw data.
    cmd[-1]=cmd[-1].replace('REMOTE_RECALC.json','TERMINAL_RECALC.json')
    r=subprocess.run(cmd,cwd=fresh/'analysis_scripts',capture_output=True)
    e.require(r.returncode==0,r.stderr.decode(errors='replace'))
    recalculated=fresh/'analysis_scripts/TERMINAL_RECALC.json'
    if not recalculated.exists():recalculated=fresh/'analysis_scripts/REMOTE_RECALC.json'
    e.require(recalculated.read_bytes()==body,'terminal independent analysis differs')
    e.save(OUT/'TERMINAL_RESTORE.json',dict(status='PASS',archive_sha256=e.sha(OUT/'RAW_TERMINAL.zip'),
                                         members_checked=len(manifest['files']),analysis_bitwise_equal=True,
                                         independent_interpreter=True,external_auditor=False))
    e.save(LIVE/'resumption_20261015/TERMINAL.json',e.read(OUT/'TERMINAL.json'))
    print(json.dumps(dict(status='TERMINAL_SEALED',counts=counts,archive_bytes=(OUT/'RAW_TERMINAL.zip').stat().st_size),indent=2))

if __name__=='__main__':main()
