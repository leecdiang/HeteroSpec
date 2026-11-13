"""Finalize delivery metadata only after all original assets and access checks pass."""
import hashlib
import json
from pathlib import Path
import shutil

import resume_remote_evidence_v2 as delivery

WORK = Path(__file__).parent
HERE = WORK / 'HeteroSpec/benchmarks/rtx_jsa_closeout_v1/revision_a'
FOLDER = Path('D:/hs144-evidence-e5c03228')


def main():
    complete = delivery.read(FOLDER / 'REMOTE_RESUME_COMPLETE.json')
    probes = delivery.read(FOLDER / 'REMOTE_ACCESS_PROBES_V2.json')
    run = Path(complete['transport_run'])
    authorization = delivery.read(run / 'AUTHORIZATION.json')
    index = delivery.read(FOLDER / 'ARCHIVES.json')
    expected = {row['name']: row for row in index['archives']}
    for name in ['ARCHIVES.json', 'FILES.json']:
        expected[name] = {'bytes': (FOLDER/name).stat().st_size, 'sha256': delivery.sha(FOLDER/name)}
    assert len(expected) == 17 and len(index['archives']) == 15
    assert complete['status'] == 'COMPLETE_DRAFT_RELEASE_ASSET_DELIVERY'
    assert probes['status'] == 'PASS_ALL_17_AUTHENTICATED_ASSET_ACCESS'
    assert set(complete['assets']) == set(probes['assets']) == set(expected)
    assert delivery.sha(FOLDER/'ARCHIVES.json') == authorization['archive_manifest_sha256']
    assert delivery.sha(FOLDER/'FILES.json') == authorization['file_manifest_sha256']
    pins = authorization['unchanged_scientific_files']
    assert all(delivery.sha(HERE/name) == digest for name, digest in pins.items())
    assert delivery.sha(WORK/authorization.get('driver_source','resume_remote_evidence_v2.py')) == authorization['driver_sha256']
    release = delivery.api(f'repos/{delivery.REPO}/releases/{delivery.RELEASE_ID}')
    assert release['draft'] and release['target_commitish'] == delivery.EXECUTION
    remote = delivery.assets()
    assert len(remote) == 17 and {a['name'] for a in remote} == set(expected)
    live_receipts = {}
    for asset in remote:
        name = asset['name']
        live_receipts[name] = delivery.receipt(asset, expected[name])
        assert probes['assets'][name]['asset_id'] == asset['id']
        assert probes['assets'][name]['sha256'] == expected[name]['sha256']
        assert all(check['exact_byte_match'] and check['http_status'] in (200,206)
                   for check in probes['assets'][name]['payload_checks'])

    history = HERE/'results/delivery_20261022'
    history.mkdir(exist_ok=True)
    for old, name in [('results/DELIVERY_DISPOSITION.json','PRIOR_DELIVERY_DISPOSITION.json'),
                      ('RAW_ACCESS.json','PRIOR_RAW_ACCESS.json')]:
        target = history/name
        if not target.exists():
            shutil.copyfile(HERE/old, target)
    # Exact transport attempts, including interrupted attempts, remain auditable.
    for source in run.iterdir():
        if source.suffix in ('.json','.txt'):
            shutil.copyfile(source, history/source.name)
    for prior in list(FOLDER.glob('REMOTE_RESUME_20261022_*'))+list(FOLDER.glob('REMOTE_FINISH_20261022_*')):
        if prior==run:continue
        destination=history/prior.name;destination.mkdir(exist_ok=True)
        for source in prior.iterdir():
            if source.suffix in ['.json','.txt']:shutil.copyfile(source,destination/source.name)
    for source in list(FOLDER.glob('PRIMARY_DELIVERY_RETIREMENT_V*.json'))+list(FOLDER.glob('LEGACY_REPAIR_RETIREMENT_V*.json')):
        shutil.copyfile(source,history/source.name)
    supplemental_runs = list(FOLDER.glob('SUPPLEMENTAL_TRANSPORT_20261022_*')) + list(FOLDER.glob('PARALLEL_TRANSPORT_20261022_*'))
    for supplemental in supplemental_runs:
        assert (supplemental/'FINAL.json').exists(), 'Supplemental transport still active'
        destination = history/supplemental.name
        destination.mkdir(exist_ok=True)
        for source in supplemental.iterdir():
            if source.suffix in ('.json','.txt'):
                shutil.copyfile(source, destination/source.name)
    for repair in FOLDER.glob('REPAIR_007_TRANSPORT_20261022_*'):
        destination=history/repair.name;destination.mkdir(exist_ok=True)
        for source in repair.iterdir():
            if source.suffix in ['.json','.txt']:shutil.copyfile(source,destination/source.name)
    queue_receipt = FOLDER/'TRANSPORT_QUEUE_COORDINATION.json'
    if queue_receipt.exists():
        assert delivery.read(queue_receipt)['status'] in ['RESUMED','NO_PAUSE_NEEDED']
        for source in FOLDER.glob('TRANSPORT_QUEUE_*'):
            if source.suffix in ['.json','.log']:
                shutil.copyfile(source,history/source.name)
    lease_v3 = FOLDER/'TRANSPORT_QUEUE_COORDINATION_V3.json'
    if lease_v3.exists():
        assert delivery.read(lease_v3)['status']=='RESUMED'
        for name in ['REPAIR_007_COORDINATION.json','PARALLEL_WORKER_GUARD.json','REPAIR_TRANSPORT_DEADLINE_EXTENSION.json']:
            if (FOLDER/name).exists():assert delivery.read(FOLDER/name)['status']=='RESUMED'
        for pattern in ['TRANSPORT_QUEUE_*','PARALLEL_TRANSPORT*.json','PARALLEL_TRANSPORT.log','PARALLEL_WORKER_GUARD.json','REPAIR_007_COORDINATION.json','REPAIR_007_WATCHDOG.log','REPAIR_TRANSPORT_DEADLINE_EXTENSION.json']:
            for source in FOLDER.glob(pattern):
                if source.is_file():shutil.copyfile(source,history/source.name)
    source_dir = history/'source_snapshot'
    source_dir.mkdir(exist_ok=True)
    for name in ['resume_remote_evidence_v2.py','probe_remote_access_v2.py','supplement_remote_delivery_v2.py','coordinate_transport_queue_v2.py','coordinate_transport_queue_v3.py','parallel_remaining_delivery_v3.py','repair_007_delivery_v3.py','guard_parallel_worker_v3.py','extend_repair_transport_deadline_v3.py','complete_release_metadata_v2.py','finalize_remote_delivery_v2.py']:
        shutil.copyfile(WORK/name, source_dir/name)
    if authorization.get('driver_source') in ['finish_remote_delivery_v4.py','finish_remote_delivery_v5.py','finish_remote_delivery_v6.py']:
        for name in ['finish_remote_delivery_v4.py','finish_remote_delivery_v5.py',authorization['driver_source']]:
            shutil.copyfile(WORK/name,source_dir/name)
    delivery.save(source_dir/'CONTEXT.json', {
        'scope': 'Post-execution delivery scripts as invoked from the original workspace work directory; source snapshots, not a replacement for frozen study scripts.',
        'original_work_directory': str(WORK), 'native_launches': 0,
        'final_delivery_driver': authorization.get('driver_source','resume_remote_evidence_v2.py'),
        'historical_sources': 'Earlier driver versions and their errors are preserved for audit. Use the current complete receipts for delivery status; no archived transport program is a new experiment authorization.',
        'optional_transport_dependency': 'psutil 7.2.2 installed only into the task work/transport_support directory; the frozen scientific virtual environment was not changed.',
        'source_sha256': {p.name: delivery.sha(p) for p in source_dir.glob('*.py')}})
    attempts=[]
    for path in sorted(history.rglob('*.receipt.json')):
        row=delivery.read(path)
        if 'curl_exit' in row:
            attempts.append({'receipt':path.relative_to(history).as_posix(),
                **{key:row.get(key) for key in ['name','attempt','utc','curl_exit','http_code','size_upload','seconds']}})
    delivery.save(history/'TRANSPORT_OVERVIEW.json', {
        'status':'CURRENT_COMPLETE_REMOTE_RECEIPTS_SUPERSEDE_HISTORICAL_TRANSPORT_FAILURES',
        'native_launches':0,'final_driver':authorization.get('driver_source','resume_remote_evidence_v2.py'),
        'current_status_receipt':'../UPLOAD_RECEIPTS.json',
        'interpretation':'These are evidence-transfer commands only. Reported client upload bytes do not by themselves establish remote completeness. Slow-link/response timeouts, controlled driver retirements, and curl2 unsupported-option rejections are preserved. Only exact live server size/SHA256 plus separately scoped authenticated payload checks establish the current complete delivery. No model/native experiment was retried.',
        'attempt_receipts':attempts})

    receipt = {**complete, 'assets': dict(sorted(live_receipts.items())),
        'checked_utc': delivery.now(), 'verified_assets': 17, 'total_assets': 17,
        'authenticated_payload_access_verified_assets': 17,
        'payload_access_receipt': 'REMOTE_ACCESS_PROBES_V2.json',
        'payload_access_receipt_sha256': delivery.sha(FOLDER/'REMOTE_ACCESS_PROBES_V2.json'),
        'verification_scope': probes['verification_scope'],
        'background_uploads': 'NONE; all original assets complete',
        'disposition': 'All 15 original ZIPs and both indexes uploaded byte-for-byte and verified on the original draft release. Prior partial delivery receipts are preserved as historical records.',
        'original_archive_bytes': sum(row['bytes'] for row in index['archives']),
        'packaged_file_count': index['files'], 'packaged_uncompressed_bytes': index['original_bytes'],
        'this_resume_new_archive_shards': 13,
        'historical_transport_receipts': 'delivery_20261022/',
        'prior_partial_delivery_commit': '3305b39ffcb723782acac9693e4d0213dd832152'}
    delivery.save(FOLDER/'UPLOAD_RECEIPTS.json', receipt)
    shutil.copyfile(FOLDER/'UPLOAD_RECEIPTS.json', HERE/'results/UPLOAD_RECEIPTS.json')
    shutil.copyfile(FOLDER/'REMOTE_ACCESS_PROBES_V2.json', HERE/'results/REMOTE_ACCESS_PROBES_V2.json')
    delivery.save(FOLDER/'DRAFT_RELEASE.json', release)
    delivery.save(HERE/'results/DRAFT_RELEASE.json', release)

    descriptor = delivery.read(HERE/'RAW_ACCESS.json')
    descriptor['status'] = 'COMPLETE_AUTHENTICATED_REMOTE_AND_LOCAL_RAW_ACCESS'
    descriptor['delivery_route'] = 'All original raw evidence is available in 15 byte-identical draft-release ZIP assets plus both indexes. Complete persistent owner-readable local access is also preserved.'
    descriptor['remote_access'] = {
        'status': receipt['status'], 'verified_archive_shards': 15, 'total_archive_shards': 15,
        'verified_index_assets': 2, 'verified_assets': 17, 'not_remotely_verified': [],
        'background_uploads': receipt['background_uploads'],
        'draft': True, 'release_id': delivery.RELEASE_ID, 'release_url': release['html_url'],
        'tag_name': release['tag_name'], 'target_commit': delivery.EXECUTION,
        'authentication': 'GitHub draft-release permissions apply: authenticated owner/collaborator access. Use each stable asset API URL with Accept: application/octet-stream. Authenticate only to api.github.com; do not forward credentials to redirected storage.',
        'download_instructions': 'Download ARCHIVES.json, FILES.json and all 15 named ZIPs. Verify every archive byte count and SHA256 against ARCHIVES.json; extract all ZIPs into one new directory and verify every path, byte count and SHA256 in FILES.json. No experiment execution is needed.',
        'receipt_file': 'results/UPLOAD_RECEIPTS.json',
        'payload_access_receipt': 'results/REMOTE_ACCESS_PROBES_V2.json',
        'verification_scope': probes['verification_scope'],
        'assets': receipt['assets']}
    delivery.save(HERE/'RAW_ACCESS.json', descriptor)
    outputs = WORK.parent/'outputs'
    outputs.mkdir(exist_ok=True)
    delivery.save(outputs/'RTX_CLOSEOUT_ACCESS.json', descriptor)
    prior = delivery.read(history/'PRIOR_DELIVERY_DISPOSITION.json')
    disposition = {**prior, 'status': 'CLOSED_COMPLETE_SCIENTIFIC_STUDY_AND_REMOTE_RAW_ACCESS',
        'raw_delivery': 'All 15 original lossless ZIPs and both indexes are complete on the authenticated draft release. Complete local raw, ZIPs and previously SHA256-verified fresh extraction are preserved.',
        'remote_delivery': receipt['status'], 'verified_remote_archive_shards': 15,
        'verified_remote_index_assets': 2, 'remote_verification': probes['verification_scope'],
        'remote_access_probes': 'REMOTE_ACCESS_PROBES_V2.json',
        'background_upload_driver_pids': [], 'optional_delivery_native_launches': 0,
        'current_delivery_receipt': 'UPLOAD_RECEIPTS.json',
        'superseded_partial_disposition': 'delivery_20261022/PRIOR_DELIVERY_DISPOSITION.json',
        'current_transport_overview': 'delivery_20261022/TRANSPORT_OVERVIEW.json',
        'remote_completion_utc': receipt['checked_utc']}
    delivery.save(HERE/'results/DELIVERY_DISPOSITION.json', disposition)
    completion = {'status': 'PASS_REMOTE_RAW_EVIDENCE_COMPLETION', 'utc': delivery.now(),
        'study_uuid': delivery.STUDY, 'execution_commit': delivery.EXECUTION,
        'release_id': delivery.RELEASE_ID, 'draft': True, 'native_launches': 0,
        'original_zip_shards': 15, 'new_zip_shards_this_resume': 13, 'index_assets': 2,
        'full_server_digest_and_size_matches': 17, 'authenticated_payload_access_matches': 17,
        'verification_scope': probes['verification_scope'], 'scientific_pins_unchanged': pins,
        'archive_manifest_sha256': delivery.sha(FOLDER/'ARCHIVES.json'),
        'file_manifest_sha256': delivery.sha(FOLDER/'FILES.json'),
        'receipt_sha256': delivery.sha(HERE/'results/UPLOAD_RECEIPTS.json'),
        'raw_access_descriptor_sha256': delivery.sha(HERE/'RAW_ACCESS.json'),
        'draft_release_snapshot_sha256': delivery.sha(HERE/'results/DRAFT_RELEASE.json'),
        'access_probe_receipt_sha256': delivery.sha(HERE/'results/REMOTE_ACCESS_PROBES_V2.json'),
        'receipt_files': {p.relative_to(history).as_posix(): delivery.sha(p) for p in sorted(history.rglob('*')) if p.is_file()},
        'no_experiment_rerun': True, 'no_scientific_criteria_change': True}
    delivery.save(HERE/'results/REMOTE_COMPLETION.json', completion)
    readme_path = HERE/'README.md'
    readme = readme_path.read_text(encoding='utf-8')
    paragraph = '\nRemote evidence delivery completed on 2026-10-22: all **15 original ZIP shards and both indexes** are present on the authenticated [draft release](%s). [Upload receipts](results/UPLOAD_RECEIPTS.json) match every full server SHA256 and byte count; [access probes](results/REMOTE_ACCESS_PROBES_V2.json) compare the full small archive index and the first/last 64 KiB of every other asset to the local originals. These bounded reads do not claim full remote ZIP readback or remote re-extraction. [Completion](results/REMOTE_COMPLETION.json) preserves the unchanged scientific pins and prior partial/failed transport receipts. No experiment was rerun.\n' % release['html_url']
    assert 'Remote evidence delivery completed on 2026-10-22:' not in readme
    readme_path.write_text(readme + paragraph, encoding='utf-8', newline='\n')
    assert all(delivery.sha(HERE/name) == digest for name, digest in pins.items())
    print(json.dumps({'status': completion['status'], 'assets': 17, 'archive_shards': 15,
                      'no_experiment_rerun': True, 'receipt_sha256': completion['receipt_sha256']}, indent=2))


if __name__ == '__main__':
    main()
