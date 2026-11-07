"""Seal and restore a partial E2 checkpoint without touching live experiment files."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
import experiment as e

def checkpoint_analysis(root, original_root=None):
    """Read-only path translation for archived hashes and executable locations.

    Frozen JSON and raw receipts remain unchanged. The original executable path
    is checked against the frozen root before translating the command view.
    """
    if original_root is None:
        answer=e.analyze(root)
    else:
        original_root=Path(original_root).resolve()
        old_sha,old_read=e.sha,e.read
        def mapped_sha(path):
            path=Path(path).resolve()
            return old_sha(root/path.relative_to(original_root) if path.is_relative_to(original_root) else path)
        def mapped_read(path):
            path=Path(path);body=old_read(path)
            if path.name=='COMMAND.json':
                route=old_read(path.parent/'RUNTIME_ROUTE.json')
                expected=str((original_root/'native/build/bin'/route['binary']).resolve())
                e.require(body['command'][0]==expected,'archived original executable command differs')
                body['command'][0]=str((root/'native/build/bin'/route['binary']).resolve())
            return body
        e.sha,e.read=mapped_sha,mapped_read
        try:answer=e.analyze(root)
        finally:e.sha,e.read=old_sha,old_read
    # The inherited hardcoded code-bundle flag does not describe a live archive.
    answer.pop('new_gpu_results_bundled_with_code',None)
    return answer

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--live',type=Path,required=True);p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--restore',type=Path,required=True)
    p.add_argument('--preserve-export-failure-log',type=Path)
    a=p.parse_args();live=a.live.resolve();checkpoint=a.checkpoint.resolve();restore=a.restore.resolve()
    e.require(not (live/'SESSION-5.json').exists(),'this checkpoint is specifically sessions0..4')
    e.require(all((live/f'SESSION-{s}-COMPLETE.json').exists() for s in range(5)),'five sessions must be complete')
    e.require(not (live/'EXECUTION.lock').exists(),'no active scientific session allowed while sealing')
    checkpoint.mkdir(parents=True,exist_ok=False);data=checkpoint/'data';data.mkdir()
    if a.preserve_export_failure_log:
        failures=checkpoint/'export_failures';failures.mkdir()
        shutil.copyfile(a.preserve_export_failure_log,failures/'attempt_01.log')
        e.save(failures/'attempt_01.json',dict(status='CPU_EXPORT_FAILED',reason='Windows destination path length limit',
                                            scientific_requests_started=0,scientific_retries=0,
                                            original_attempt_files_retained=True))
    # All ledgers, requests, failed control attempts and stop analyses are retained.
    for directory in ('blocks','cooldown','ledger','runs','monitor','transport_recovery_20261014'):
        if (live/directory).exists():shutil.copytree(live/directory,data/directory)
    for source in live.iterdir():
        if source.is_file() and source.suffix in ('.json','.log','.md'):
            shutil.copyfile(source,data/source.name)
    binaries=data/'native/build/bin';binaries.mkdir(parents=True)
    for name in ('llama-server.exe','llama-server-pq-metadata4.exe'):
        shutil.copyfile(live/'native/build/bin'/name,binaries/name)
    code=checkpoint/'analysis_scripts';code.mkdir()
    for source in Path(__file__).parent.glob('*.py'):shutil.copyfile(source,code/source.name)
    # Tests and the original failure audit depend on these immutable fixtures.
    shutil.copytree(Path(__file__).parent/'execution_20261014',code/'execution_20261014')
    for name in ('README.md','RUNTIME_ADAPTER_AMENDMENT.md','E2_TRANSPORT_AMENDMENT.md'):
        shutil.copyfile(Path(__file__).parent/name,code/name)
    analysis=checkpoint_analysis(live)
    e.require(all(r['estimate'] is None for r in analysis['comparisons']),'aggregate cannot be admitted with five sessions')
    e.save(checkpoint/'PARTIAL_ANALYSIS.json',analysis)
    events=[e.read(f) for f in (data/'ledger').glob('*.json')]
    records=[e.read(f) for f in (data/'runs').rglob('RECORD.json')]
    summary=dict(status='PARTIAL_E2_WAITING_FOR_SESSION5',completed_sessions=list(range(5)),
                 request_starts=sum(x['kind']!='load' for x in events),completed_records=len(records),
                 warmups=sum(r['warmup'] for r in records),workers=sum(x['kind']=='load' for x in events),
                 scientific_request_failures=len(list((data/'runs').rglob('FAILED.json'))),
                 invalid_contracts=sum(not r['contract_valid'] for r in records),
                 workload_errors=sum(bool(r['workload_error']) for r in records),
                 heavy_observers=sum(any(r['observation'].values()) for r in records),
                 output_mismatches=sum(len(r['mismatches']) for r in analysis['comparisons']),
                 pre_scientific_transport_failures=1,E1_started=False,
                 session5_earliest_utc='2026-10-15T04:27:07.394219+00:00',
                 base_freeze_commit='49b992b2ed1cabd05fad6e234cad2d3418c2b65a',
                 transport_amendment_commit='e06dc8df53622eddd3f9306addbeaf428cdb3548',
                 native_owned_seconds=sum(e.read(f)['seconds'] for f in (data/'runs').rglob('LIFETIME.json')),
                 aggregate_estimates_withheld=True,models_or_numerical_DLLs_in_archive=False)
    e.require(summary['request_starts']==summary['completed_records']==1350 and summary['workers']==270,'checkpoint accounting differs')
    e.save(checkpoint/'PROGRESS.json',summary)
    files=[f for f in sorted(checkpoint.rglob('*')) if f.is_file()]
    manifest=dict(schema=1,status=summary['status'],original_live_root=str(live),
                  scientific_requests=1350,whole_request_cap=1620,
                  files=[dict(path=f.relative_to(checkpoint).as_posix(),bytes=f.stat().st_size,sha256=e.sha(f)) for f in files],
                  exclusions='No model weights or numerical DLL bytes; their frozen identities and loaded-module receipts are retained. Manifest excludes itself; restoration receipt is external.')
    e.save(checkpoint/'RAW_ARCHIVE_MANIFEST.json',manifest)
    archive=checkpoint/'RAW_E2_S0_S4.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for f in files+[checkpoint/'RAW_ARCHIVE_MANIFEST.json']:z.write(f,f.relative_to(checkpoint).as_posix())
    restore.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        e.require(all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist()),'unsafe archive path')
        z.extractall(restore)
    for item in manifest['files']:
        f=restore/item['path']
        e.require(f.stat().st_size==item['bytes'] and e.sha(f)==item['sha256'],'restored member differs')
    # Independent interpreter, using only the restored source and data.
    import subprocess,sys
    command=[sys.executable,'-B','-c',
             'from pathlib import Path;import export_e2_checkpoint as x;import experiment as e;'
             'e.save(Path("RESTORED_ANALYSIS.json"),x.checkpoint_analysis(Path("../data").resolve(),'+repr(str(live))+'))']
    result=subprocess.run(command,cwd=restore/'analysis_scripts',capture_output=True)
    e.require(result.returncode==0,'restored analysis failed: '+result.stderr.decode(errors='replace'))
    restored_body=(restore/'analysis_scripts/RESTORED_ANALYSIS.json').read_bytes()
    e.require(restored_body==(checkpoint/'PARTIAL_ANALYSIS.json').read_bytes(),'restored analysis differs')
    e.save(checkpoint/'ARCHIVE_RESTORE.json',dict(status='PASS',members_checked=len(manifest['files']),
                                               archive_sha256=e.sha(archive),archive_bytes=archive.stat().st_size,
                                               analysis_bitwise_equal=True,separate_interpreter=True,
                                               external_auditor=False,source_archive_has_no_model_weights=True,
                                               live_frozen_files_modified=False))
    report='''# PR104 interim execution checkpoint — sessions 0–4

**Partial E2; final session 5 pending. E1 has not started.**

Five sessions completed: 1,350 native request starts and completed records, including 270 excluded warmups, from 270 fresh workers. Measured requests comprise 720 PQ/QB comparisons and 360 serial references. Zero scientific request failures, output mismatches, invalid output contracts, workload errors or heavy-observer flags were found. Closed native owned time: 4,149.036 seconds of the unchanged 43,200-second cap.

| Session | Started, China time | Completed, China time | Requests |
|---:|---|---|---:|
| 0 | October 14 12:27:07 | October 14 12:56:45 | 270 |
| 1 | October 14 13:56:54 | October 14 14:26:52 | 270 |
| 2 | October 14 15:27:01 | October 14 15:57:05 | 270 |
| 3 | October 14 16:57:15 | October 14 17:27:27 | 270 |
| 4 | October 14 18:53:55 | October 14 19:23:23 | 270 |
| 5 | Not started; earliest October 15 12:27:07 | Pending | 0 |

The first session-4 controller launch failed during authenticated GitHub freeze readback with network EOF before a session receipt, native load or scientific slot existed. That launch, original supervisor failure and stop analysis are retained in full. A separate prospective transport supplement was committed and authenticated before invoking the untouched session. Scientific retries: zero. The original Phase 0 failure at ccfbc2e is also retained unchanged.

The original E2 freeze remains 49b992b2ed1cabd05fad6e234cad2d3418c2b65a, with transport supplement e06dc8df53622eddd3f9306addbeaf428cdb3548. Tasks, token IDs, arms, AB/BA schedule, six sessions, budgets, timers, models, DLLs and family-specific binaries are unchanged. Session 5 retains the >=24-hour first-to-last rule and >=one-hour previous-completion rule. Automatic attendance remains active.

Every aggregate PQ/QB estimate is withheld because all six sessions and the final time-block gate are required. PARTIAL_ANALYSIS.json retains all available task/session contrasts and missing session-5 coordinates; this checkpoint makes no practical-improvement or equivalence claim. E1 numerical values, ULP and first divergence are unavailable because E1 is gated on complete E2. This checkpoint neither confirms nor refutes the paper's QB economics claim. It does not establish blind/new-input, cross-device or universal equivalence, kernel identity or reduction-tree identity.

RAW_E2_S0_S4.zip contains all current ledgers, block exports, raw request/worker records, cooldowns, environment/module/PID receipts, failed control attempts, freeze/readback records, the two selected native executables and analysis sources. Model weights and numerical DLL bytes are excluded; their hashes and loaded-module verification receipts remain. RAW_ARCHIVE_MANIFEST.json binds every member. ARCHIVE_RESTORE.json confirms a fresh-directory byte restoration and a separate-interpreter CPU recomputation matching the partial analysis byte-for-byte, on the same host; this is not an external auditor.

This is an immutable interim checkpoint, not the final scientific delivery. Historical RTX results, main and PR102 were not modified. PR104 remains Draft.
'''
    (checkpoint/'RESULT.md').write_text(report,encoding='utf-8',newline='\n')
    print(json.dumps(dict(requests=1350,status=summary['status'],archive_bytes=archive.stat().st_size,
                          manifest_members=len(manifest['files']),archive_restore='PASS'),indent=2))

if __name__=='__main__':main()
