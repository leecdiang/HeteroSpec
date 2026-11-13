"""Snapshot saved successor text and numeric inventory; never launches a model.

Run only at a quiet panel boundary. Original numerical files remain on the host.
Public mode uses the original S3 path/UUID transform and retains original hashes
as historical commitments; INDEX describes the transformed public file bytes.
"""
import argparse
import gzip
import json
from pathlib import Path
import sys
import tarfile


def main(campaign, out, public):
    if out.exists():
        raise ValueError('Fresh packet directory required')
    config = json.loads((campaign / 'CONFIG.private.json').read_text())
    sys.path.insert(0, str(campaign / 'source'))
    from native import sha, write, utc
    from adapter import need
    sys.path.insert(0, str(Path(config['original_source']) / 'execution_s3_v1'))
    from public_text import transform
    out.mkdir(parents=True)
    index = []; numeric = {}; samples = []; source_commits = {}

    def copy_text(source, relative):
        text = source.read_text()
        if public:
            text = transform(text, campaign.parent)
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    for section in ('outputs', 'plans', 'source', 'source_dates'):
        for source in sorted((campaign / section).rglob('*')):
            if source.is_symlink() or not source.is_file() or '__pycache__' in source.parts:
                continue
            relative = Path('data') / section / source.relative_to(campaign / section)
            if '.private.' in source.name:
                if source.name == 'RESOURCE.private.jsonl':
                    samples.extend(json.loads(line) for line in source.read_text().splitlines())
                if source.name == 'GRANT.private.json':
                    source_commits[source.parent.name] = json.loads(source.read_text())['successor_source_commit']
                continue
            if source.suffix in ('.bin', '.f32'):
                numeric[relative.as_posix()] = dict(bytes=source.stat().st_size, sha256=sha(source), retained=True)
            elif source.suffix in ('.json', '.jsonl', '.log', '.txt', '.py', '.js', '.md'):
                copy_text(source, relative)
            else:
                need(source.suffix == '.lock', 'Classify unexpected saved payload: ' + str(source))
    for pattern in ('SOURCE_READBACK*.json', 'INPUT_RULE_REPLAY.json', 'STORAGE_CALCULATION*.json',
                    'PREPARATION_FAILURES.json', 'ALL_NATIVE_CPU_ECHO.json', 'CPU_TESTS*.log', 'R2_CPU_TESTS*.log', 'campaign*.log'):
        for source in sorted(campaign.glob(pattern)):
            copy_text(source, Path('data/metadata') / source.name)
    need(sha(config['state_profile']) == config['state_profile_sha256'], 'Original state profile changed')
    copy_text(Path(config['state_profile']), Path('data/STATE_PROFILE.json'))
    write(out / 'data/NUMERIC_INVENTORY.json', numeric)
    write(out / 'data/EXECUTION_SOURCE_COMMITS.json', source_commits)
    write(out / 'data/IDENTITIES.json', dict(initial_H_source_commit=config['source_commit'],
          model_sha256=config['model']['sha256'], model_bytes=config['model']['bytes'],
          native_ELF_sha256={k:config['executables'][k]['sha256'] for k in ('R', 'model')},
          state_profile_sha256=config['state_profile_sha256'],
          prior_S1_certificate_sha256=config['S1_certificate_sha256'],
          planned_requests=444, request_ceiling=468, row_ceiling=149760,
          model_completion_time_limit=None, native_arithmetic_changed=False))
    if samples:
        write(out / 'data/RESOURCE_SUMMARY.json', dict(samples=len(samples),
              min_sampled_gpu_free_bytes=min(s['gpu_free_bytes'] for s in samples),
              max_sampled_gpu_used_bytes=max(int(s['selected_gpu'][2])*1024**2 for s in samples),
              min_sampled_ram_available_bytes=min(s['mem_available_bytes'] for s in samples),
              min_sampled_disk_free_bytes=min(s['disk_free_bytes'] for s in samples),
              max_sampled_host_load_fraction=max(s['host_load_fraction'] for s in samples),
              scope='Sampled existing resource checks; not continuous peak measurements'))
    protected = {p:sha(p)==digest for p,digest in config['protected_files'].items()}
    need(all(protected.values()), 'Protected historical file changed; preserve and investigate')
    write(out / 'data/PROTECTED_AUDIT.json', dict(files=len(protected), all_unchanged=True,
          scope='Original source plus historical STATE and journal; checked against retained original commitments'))
    for source in sorted((campaign / 'reporting').glob('*.js')):
        copy_text(source, Path('source') / source.name)
    for source in sorted(out.rglob('*')):
        if source.is_file():
            index.append(dict(path=source.relative_to(out).as_posix(), bytes=source.stat().st_size, sha256=sha(source)))
    write(out / 'INDEX.json', dict(schema='hs.s3.successor.saved-text.v1', snapshot_utc=utc(), public=public,
          files=index, numeric_retained_files=len(numeric), numeric_retained_bytes=sum(x['bytes'] for x in numeric.values()),
          limitations=['No numerical tensors distributed; inventory describes retained host files only',
                      'Successfully compared intermediate KV may have been disposed; full proof and disposal inventories remain',
                      'Public mode transforms original path/UUID text and does not claim original path-dependent hash replay']))
    archive = out.parent / (out.name + '.tar.gz')
    need(not archive.exists(), 'Fresh archive path required')
    with archive.open('xb') as raw, gzip.GzipFile(fileobj=raw, filename='', mode='wb', mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode='w|') as tar:
            for source in sorted(out.rglob('*')):
                if not source.is_file(): continue
                info = tar.gettarinfo(str(source), arcname=source.relative_to(out).as_posix())
                info.uid=info.gid=0; info.uname=info.gname=''; info.mtime=0; info.mode=0o644
                with source.open('rb') as stream: tar.addfile(info, stream)
    print(json.dumps(dict(archive=str(archive), bytes=archive.stat().st_size, sha256=sha(archive),
                         text_files=len(index), retained_numeric_files=len(numeric))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--public', action='store_true')
    args = parser.parse_args()
    main(args.campaign, args.out, args.public)
