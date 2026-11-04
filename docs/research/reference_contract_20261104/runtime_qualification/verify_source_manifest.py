#!/usr/bin/env python3
"""Verify the read-only inspected native source identity; no build or GPU use."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path,
                        default=os.environ.get('HETEROSPEC_NATIVE_SOURCE'))
    parser.add_argument('--source-kit', type=Path)
    args = parser.parse_args()
    if args.source is None:
        parser.error('pass --source or set HETEROSPEC_NATIVE_SOURCE')
    source = Path(args.source).resolve()
    manifest = json.loads(Path(__file__).with_name('source_manifest.json').read_text())
    failures = []
    for name, expected in manifest['files'].items():
        path = source / name
        if not path.is_file() or digest(path) != expected:
            failures.append(name)
    if args.source_kit and digest(args.source_kit) != manifest['source_kit_sha256']:
        failures.append('source-kit archive')
    result = {'status': 'FAIL' if failures else 'PASS',
              'source_files_checked': len(manifest['files']),
              'source_kit_checked': args.source_kit is not None,
              'mismatches': failures, 'semantic_proof': False,
              'native_execution': False, 'gpu_execution': False}
    print(json.dumps(result, indent=2))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
