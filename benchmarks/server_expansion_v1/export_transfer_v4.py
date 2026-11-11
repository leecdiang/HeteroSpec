"""Export completed Linux transfer evidence without modifying frozen run trees.

Public text is a sanitized derivative. Every included private raw text hash and
every native capture hash remain explicit; private captures are not public data.
External support records require a reviewed exact-file manifest, never a glob.
"""
from pathlib import Path, PurePosixPath
import argparse, fcntl, gzip, hashlib, json, re, sys, time

ROOT_FILES = (
    'ledger.jsonl', 'MODEL_STRUCTURES.json', 'PREPARED.json',
    'REFERENCE_ADAPTER.json', 'PRIOR_ACCOUNTING.private.json',
    'CONTINUATION-02-SOURCE_FREEZE.private.json', 'CONTINUATION-02-STATUS.json',
    'CONTINUATION-03-SOURCE_FREEZE.private.json', 'CONTINUATION-03-STATUS.json',
    'FORMAL_STAGE_STATUS-01.json',
)
SUFFIXES = {'.json', '.jsonl', '.log', '.txt'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('work', 'runtime', 'builds', 'completion', 'support_manifest', 'out'):
        parser.add_argument('--' + key.replace('_', '-'), type=Path, required=True)
    parser.add_argument('--allow-retained-failure', action='store_true')
    args = parser.parse_args()
    sys.path.insert(0, str(args.runtime.resolve()))
    from common import need, read, save, sha

    work, out = args.work.resolve(), args.out.resolve()
    # Same mutex as all GPU pipelines. Full byte reads and compression cannot
    # overlap a timing window, even when exporting another completed lane.
    queue_start = time.monotonic()
    with (work.parent / 'STUDY_SCHEDULING.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        start = time.monotonic()
        completion = read(args.completion)
        positive = completion['status'] in ('COMPLETE', 'QUALIFIED_FORMAL_NOT_RUN')
        retained_failure = completion['status'] in ('FAILED_SCOPE_RETAINED',
            'QUALIFIED_WITH_RETAINED_FORMAL_FAILURE', 'QUALIFIED_WITH_RETAINED_PRIMARY_FAILURE')
        need(positive or (args.allow_retained_failure and retained_failure),
             'Explicit terminal scope required; failure export grants no numerical or performance pass')
        need(not out.exists() and not out.is_relative_to(work), 'Fresh external output')
        chosen = {}

        def add(name, path):
            name = str(name)
            rel = PurePosixPath(name)
            need(not rel.is_absolute() and '..' not in rel.parts, 'Unsafe public name')
            need(name not in chosen and path.is_file(), 'Duplicate/missing evidence: ' + name)
            need(path.suffix in SUFFIXES, 'Only reviewed text support records')
            chosen[name] = path

        for name in ROOT_FILES:
            if (work / name).is_file():
                add(name, work / name)
        directories = [work / name for name in ('inputs-01', 'inputs-formal-01', 'reference-01', 'panel-01')]
        directories += sorted(p for p in work.glob('inputs-formal-*') if p.is_dir() and p.name!='inputs-formal-01')
        directories += sorted(p for p in work.glob('qualification-*') if p.is_dir())
        directories += sorted(p for p in work.glob('capability-negatives-*') if p.is_dir())
        for directory in directories:
            for path in sorted(directory.rglob('*')):
                if path.is_file() and path.suffix in SUFFIXES:
                    add(path.relative_to(work), path)
        # A tiny semantic fixture is included; full native vocabulary/model
        # metadata dumps in preparation directories are deliberately excluded.
        for path in sorted(work.glob('termination-fixture-*/FIXTURE.json')):
            add(path.relative_to(work), path)
        for role in ('reference', 'loop4', 'packed'):
            for name in ('BUILD.json', 'DEPENDENCIES.json', 'compile/command.json',
                         'compile/stdout.log', 'link/command.json', 'link/stdout.log'):
                path = args.builds.resolve() / role / name
                if path.exists():
                    add('support/builds/' + role + '/' + name, path)
        manifest = read(args.support_manifest)
        need(manifest['schema'] == 'linux-transfer.exact-support-files.v1', 'Reviewed manifest')
        for row in manifest['files']:
            path = Path(row['source']).resolve()
            need(sha(path) == row['sha256'], 'Support evidence changed: ' + row['name'])
            add('support/' + row['name'], path)
        need(any(p.resolve() == args.completion.resolve() for p in chosen.values()),
             'Manifest must include actual terminal completion receipt')

        def clean(text):
            for old, new in ((str(work.parent), '<PRIVATE_ROOT>'),
                             (str(Path.home()), '<HOME>')):
                text = text.replace(old, new)
            text = re.sub(r'GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',
                          '<ALLOCATED_GPU_UUID>', text)
            return re.sub(r'("(?:allocation_id|authorization_id)"\s*:\s*)"[^"\n]*"',
                          r'\1"<EXPLICIT_PRIVATE_ALLOCATION>"', text)

        records, index = [], []
        for name, path in sorted(chosen.items()):
            raw = path.read_bytes()
            text = raw.decode('utf8')
            public = clean(text)
            need(not re.search(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])', public),
                 'Unreviewed IPv4-shaped value: ' + name)
            need(not any(s in public for s in ('X-Amz-', 'https://cdn-lfs', 'xet-hf',
                                               'Authorization: Bearer', 'ghp_', 'github_pat_')),
                 'Network or credential material entered allowlist: ' + name)
            if path.suffix == '.json':
                json.loads(public)
            if path.suffix == '.jsonl':
                for line in public.splitlines():
                    json.loads(line)
            encoded = public.encode()
            records.append(dict(path=name, text=public))
            index.append(dict(path=name, raw_bytes=len(raw),
                              raw_sha256=hashlib.sha256(raw).hexdigest(),
                              exported_bytes=len(encoded),
                              exported_sha256=hashlib.sha256(encoded).hexdigest(),
                              transformed=text != public))

        binaries = []
        capture_roots = [work / 'reference-01', work / 'panel-01']
        capture_roots += sorted(p for p in work.glob('qualification-*') if p.is_dir())
        for directory in capture_roots:
            for path in sorted(directory.rglob('*')):
                if path.is_file() and path.suffix in ('.f32', '.bin'):
                    binaries.append(dict(path=str(path.relative_to(work)),
                                         bytes=path.stat().st_size, sha256=sha(path)))
        out.mkdir(parents=True)
        data = json.dumps(dict(schema='linux-transfer.public-text-bundle.v1', records=records),
                          ensure_ascii=False, separators=(',', ':')).encode()
        bundle = out / 'scientific-records.json.gz'
        with bundle.open('xb') as stream:
            with gzip.GzipFile(filename='', fileobj=stream, mode='wb', mtime=0) as z:
                z.write(data)
        save(out / 'TEXT_INDEX.json', dict(files=index, bundle_sha256=sha(bundle),
             uncompressed_bytes=len(data), public_text_is_derived=True))
        save(out / 'BINARY_CAPTURE_INDEX.json', dict(files=binaries, count=len(binaries),
             bytes=sum(x['bytes'] for x in binaries), public_raw_capture_archive=False,
             scope='Every .f32/.bin under this lane reference, all retained qualification epochs and panel; raw bytes read locally'))
        save(out / 'EXPORT_SCOPE.json', dict(text_files=len(index), binary_captures=len(binaries),
             raw_records_retained_privately=True, original_hash_fields_unchanged=True,
             text_index_sha256=sha(out / 'TEXT_INDEX.json'),
             binary_index_sha256=sha(out / 'BINARY_CAPTURE_INDEX.json'), bundle_sha256=sha(bundle),
             exporter_sha256=sha(Path(__file__)),
             qualified_predecessor_exporter_sha256=sha(args.runtime / 'export_evidence.py'),
             support_manifest_private_sha256=sha(args.support_manifest),
             terminal_scope=completion['status'],
             finite_qualification_passed=completion.get('finite_qualification_passed'),
             formal_performance_status=completion.get('formal_performance_status'),
             retained_failure_export=retained_failure,
             numerical_or_performance_qualification_granted_by_export=False,
             no_public_binary_archive_readback_claim=True,
             excluded=['host inventory/configuration', 'credentials', 'network download logs',
                       'model weights/full vocabulary dumps', 'other users/processes',
                       'compiled executables/numerical archives']))
        # Retain the same mutex through the second, independent full-byte read.
        # This verifies private capture storage, not a public binary download.
        from readback_export import verify
        readback = verify(out, raw_work=work)
        readback.update(queue_wait_s=start - queue_start,
                        export_and_private_readback_inclusive_s=time.monotonic() - start,
                        excluded_from_native_service=True)
        save(out / 'LOCAL_READBACK.json', readback)
        print(json.dumps(dict(text_files=len(index), binary_captures=len(binaries),
                              bundle_bytes=bundle.stat().st_size)), flush=True)


if __name__ == '__main__':
    main()
