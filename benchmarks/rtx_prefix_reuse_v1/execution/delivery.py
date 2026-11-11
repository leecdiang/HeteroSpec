"""Close out artifact transport and prepare-only replay, without model execution."""
from host import *
from datetime import datetime,timezone

m=read('F:/rtx172-delivery/raw-evidence.zip.parts.json')
names=[p['name'] for p in m['parts']]+['raw-evidence.zip.parts.json']
uploads={n:read(ROOT/(n+'.upload.json')) for n in names}
downloads={n:read(Path('F:/rtx172-restored-final')/(n+'.download.json')) for n in names}
assert all(r['code']==0 for r in uploads.values()) and all(r[-1]['code']==0 for r in downloads.values())
prepared=Path('F:/rtx172-prepared-replay');binding=read(prepared/'replay-binding.json')
assert binding['prepare_only'] and not list((prepared/'native').iterdir()) and not (prepared/'native.log').exists()
for p in (prepared/'snapshots').glob('*.bin'):assert sha(p)==p.stem
assert sum(read(p)['requests'] for p in ROOT.glob('*/launch.json'))==2026
assert not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
receipt=dict(utc=datetime.now(timezone.utc).isoformat(),status='NATIVE_STUDY_AND_RESTORED_DELIVERY_COMPLETE',release_id=433510372,raw_archive_sha256=m['sha256'],raw_bytes=m['bytes'],raw_parts=len(m['parts']),restored_archive=read(ROOT/'raw-evidence.zip.RESTORED_DOWNLOAD.json'),runtime_and_source=read(ROOT/'RESTORED_RUNTIME_VERIFICATION.json'),remote_asset_digests=sha(ROOT/'REMOTE_ASSET_VERIFICATION.json'),prepared_replay=binding,prepared_snapshot_files=len(list((prepared/'snapshots').glob('*.bin'))),additional_model_requests=0,third_party_native_replication=False,raw_upload_attempts=uploads,raw_download_attempts=downloads,transport_timing_scope='Per-transfer durations retain parallel attempts and retries; do not sum them as elapsed wall time. These are artifact transport costs, not model-request counts.')
put(ROOT/'DELIVERY.json',receipt);put(ROOT/'REPLAY_PREPARATION.json',binding)
print(json.dumps({k:receipt[k] for k in ('status','raw_parts','prepared_snapshot_files','additional_model_requests')},indent=2))
