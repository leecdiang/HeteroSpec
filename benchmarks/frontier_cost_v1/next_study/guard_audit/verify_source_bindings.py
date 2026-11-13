#!/usr/bin/env python3
"""Verify static audit byte/region bindings. This is not a numerical qualification.

No compilation, native libraries, model files, network access, or GPU access.
Only source files named by the audit manifest are read. Outputs are fresh files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(args):
    matrix_bytes = args.matrix.read_bytes()
    matrix = json.loads(matrix_bytes)
    archive_bytes = args.source_zip.read_bytes()
    if sha(archive_bytes) != matrix['archive']['sha256']:
        raise ValueError('archive byte identity differs from audited release')
    if len(archive_bytes) != matrix['archive']['bytes']:
        raise ValueError('archive length differs')
    data, checked, skipped = {}, [], []
    with zipfile.ZipFile(args.source_zip) as archive:
        manifest = json.loads(archive.read('SOURCE_ASSET_MANIFEST.json'))
        for source in matrix['source_files']:
            sid = source['id']
            if source['kind'] == 'release_zip_member':
                member = source['member']
                blob = archive.read(member)
                if sha(blob) != manifest['files'][member]['sha256']:
                    raise ValueError(f'{sid}: archive manifest mismatch')
                twin = source.get('packed_twin')
                if twin:
                    twin_bytes = archive.read(twin['member'])
                    if sha(twin_bytes) != twin['sha256']:
                        raise ValueError(f'{sid}: packed twin mismatch')
                    if (twin_bytes == blob) != twin['byte_identical']:
                        raise ValueError(f'{sid}: twin equality mismatch')
            elif source['kind'] == 'reconstructed_frontend':
                if args.candidate_frontend is None:
                    skipped.append(sid)
                    continue
                # The manifest uses simple basenames, never traversal paths.
                basename = Path(source['file'])
                if len(basename.parts) != 1 or basename.name in ('.', '..'):
                    raise ValueError('invalid frontend basename')
                blob = (args.candidate_frontend / basename).read_bytes()
            else:
                raise ValueError('unknown source binding kind')
            if sha(blob) != source['sha256'] or len(blob) != source['bytes']:
                raise ValueError(f'{sid}: audited byte identity differs')
            data[sid] = blob.decode().splitlines()
            checked.append(dict(id=sid, sha256=sha(blob), bytes=len(blob)))
    region_count = 0
    for guard in matrix['guards']:
        for ref in guard['source_refs']:
            if ref['source'] in skipped:
                continue
            source = next(s for s in matrix['source_files'] if s['id'] == ref['source'])
            if source['sha256'] != ref['sha256']:
                raise ValueError('guard file SHA differs from source table')
            lines = data[ref['source']]
            first, last = ref['line_start'], ref['line_end']
            if not (1 <= first <= last <= len(lines)):
                raise ValueError('invalid source region')
            excerpt = '\n'.join(lines[first-1:last]) + '\n'
            if sha(excerpt.encode()) != ref['normalized_excerpt_sha256']:
                raise ValueError('source region differs')
            if not all(anchor in excerpt for anchor in ref['anchors']):
                raise ValueError('source anchor missing')
            region_count += 1
    paper = 'NOT_SUPPLIED'
    if args.paper_method:
        if sha(args.paper_method.read_bytes()) != matrix['paper']['sha256']:
            raise ValueError('method manuscript differs from audited bytes')
        paper = 'BYTE_IDENTITY_VERIFIED'
    return dict(schema='heterospec.static-source-binding-receipt.v1',
        status='STATIC_BINDINGS_VERIFIED' if not skipped else 'RELEASE_STATIC_BINDINGS_VERIFIED_M2_NOT_SUPPLIED',
        matrix_sha256=sha(matrix_bytes), archive_sha256=sha(archive_bytes),
        checked_sources=checked, skipped_sources=skipped, checked_regions=region_count,
        paper_binding=paper, model_runs=0, native_runs=0, gpu_runs=0,
        source_identity_does_not_establish_numerical_equivalence=True,
        source_identity_does_not_establish_runtime_guard_effectiveness=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path, default=Path(__file__).with_name('GUARD_MATRIX.json'))
    parser.add_argument('--source-zip', required=True, type=Path)
    parser.add_argument('--candidate-frontend', type=Path)
    parser.add_argument('--paper-method', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    receipt = verify(args)
    # Exclusive creation keeps previous evidence immutable.
    with args.out.open('x') as stream:
        stream.write(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(status=receipt['status'], sources=len(receipt['checked_sources']),
        regions=receipt['checked_regions'], model_runs=0, native_runs=0, gpu_runs=0)))


if __name__ == '__main__':
    main()
