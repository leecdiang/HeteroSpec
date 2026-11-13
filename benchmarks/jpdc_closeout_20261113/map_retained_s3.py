"""Read-only content-alias inventory. Never restores or deletes a capture."""
import argparse
import csv
import gzip
import hashlib
import io
import json
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--deleted-log', type=Path, required=True)
    parser.add_argument('--study-root', type=Path, required=True,
                        help='Original execution directory containing S3 and S3_QUAL')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Fresh derived output required')
    index_bytes = args.index.read_bytes()
    index = json.loads(index_bytes)['withheld_numeric_payloads']
    deleted = {json.loads(line)['path'] for line in args.deleted_log.read_text().splitlines()}
    candidates = defaultdict(list)
    removed = []
    for entry in index:
        logical = Path(entry['logical_id'])
        if logical.is_absolute() or '..' in logical.parts:
            raise ValueError('Unsafe index path')
        path = args.study_root / logical.relative_to('data')
        if str(path) in deleted:
            removed.append(entry)
        elif path.is_file() and path.stat().st_size == entry['bytes']:
            candidates[entry['sha256'], entry['bytes']].append(entry['logical_id'])
    mapping = []
    for entry in sorted(removed, key=lambda x: x['logical_id']):
        sources = candidates.get((entry['sha256'], entry['bytes']), [])
        if not sources:
            raise ValueError('No retained candidate for: ' + entry['logical_id'])
        source = min(sources, key=lambda x: ('-repeat0/' not in x, x))
        mapping.append(dict(deleted_logical_id=entry['logical_id'],
                            retained_logical_id=source, bytes=entry['bytes'],
                            historical_sha256=entry['sha256']))
    # Deliberately bounded content verification, not a full-history hash pass.
    selected = []
    for pattern in ('R-root00-repeat1/', 'bridge-root03-B/', 'bridge-root06-C/'):
        selected.append(next(x for x in mapping if pattern in x['deleted_logical_id']))
    samples = []
    for item in selected:
        source = args.study_root / Path(item['retained_logical_id']).relative_to('data')
        before = source.stat()
        digest = hashlib.sha256()
        with source.open('rb') as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                digest.update(block)
        after = source.stat()
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError('Source changed during sample read')
        if digest.hexdigest() != item['historical_sha256']:
            raise ValueError('Sample bytes differ from historical index')
        samples.append(dict(item, fresh_sha256=digest.hexdigest(), status='PASS_CURRENT_CONTENT'))
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=list(mapping[0]))
    writer.writeheader()
    writer.writerows(mapping)
    compressed = gzip.compress(text.getvalue().encode(), mtime=0)
    unique = {(x['historical_sha256'], x['bytes']) for x in mapping}
    summary = dict(status='ALL_DELETED_INDEX_ENTRIES_HAVE_RETAINED_CANDIDATES',
                   deleted_index_entries=len(removed), mapped_entries=len(mapping),
                   logical_bytes=sum(x['bytes'] for x in mapping),
                   unique_candidate_content_bytes=sum(n for _, n in unique),
                   input_numeric_index_sha256=hashlib.sha256(index_bytes).hexdigest(),
                   mapping_gzip_sha256=hashlib.sha256(compressed).hexdigest(),
                   content_check='THREE_SAMPLES_ONLY_NOT_FULL_CANDIDATE_HASH_VALIDATION',
                   samples=samples, model_calls=0, restored_files=0, deleted_files=0,
                   limitation='Historical SHA+size and current existence identify recovery candidates; verify every source hash before claiming full original-byte recovery. Reconstruction is not another GPU capture or numerical qualification.')
    args.out.mkdir(parents=True)
    (args.out / 'S3_COPY_MAP.csv.gz').write_bytes(compressed)
    (args.out / 'S3_COPY_COVERAGE.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: summary[k] for k in ('status', 'mapped_entries', 'unique_candidate_content_bytes')}))


if __name__ == '__main__':
    main()
