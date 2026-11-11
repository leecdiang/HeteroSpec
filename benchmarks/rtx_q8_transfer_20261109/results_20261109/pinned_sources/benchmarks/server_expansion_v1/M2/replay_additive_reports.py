"""Reproduce width/cost reports from an immutable public M2 text archive.

Only host paths and raw-to-derived byte identities are rebound. Numeric fields,
recorded clocks and analysis functions are unchanged. No model/native execution.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024**2), b''):
            h.update(b)
    return h.hexdigest()


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--m2-source', type=Path, required=True)
    p.add_argument('--expected-dir', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = out / 'extracted'
    root.mkdir()
    reader = load('public_stream_reader', a.m2_source / 'replay_public.py')
    width = load('fixed_width_analyzer', a.m2_source / 'width_analysis.py')
    costs = load('fixed_physical_cost_analyzer', a.m2_source / 'physical_costs.py')
    scope = json.loads((a.archive / 'EXPORT_SCOPE.json').read_text())
    ti = json.loads((a.archive / 'TEXT_INDEX.json').read_text())
    for name, key in [('scientific-records.json.gz', 'bundle_sha256'), ('TEXT_INDEX.json', 'text_index_sha256'), ('BINARY_CAPTURE_INDEX.json', 'binary_index_sha256')]:
        assert sha(a.archive / name) == scope[key]
    index = {x['path']: x for x in ti['files']}
    seen = set()
    for record in reader.records(a.archive / 'scientific-records.json.gz'):
        key = record['path']
        assert key not in seen and key in index
        seen.add(key)
        b = record['text'].encode('utf8')
        row = index[key]
        assert len(b) == row['exported_bytes'] and hashlib.sha256(b).hexdigest() == row['exported_sha256']
        if key.startswith(('m2-run-01/', 'm2-run-02/', 'm2-run-03/')) or key == 'm2-audit-03/STATUS.json':
            assert not Path(key).is_absolute() and '..' not in Path(key).parts
            dest = root / key
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as f:
                f.write(b)
    assert len(seen) == len(index) == scope['text_files']

    # The unchanged cost analyzer reads its original ledger out paths. Bind only
    # the already-sanitized $WORKSPACE prefix to this fresh extraction directory.
    original_path = costs.Path

    def rebound_path(value):
        text = str(value)
        if text.startswith('$WORKSPACE/'):
            return root / text[len('$WORKSPACE/'):]
        return original_path(value)

    def raw_identity(path):
        key = str(path.relative_to(root))
        row = index[key]
        assert path.stat().st_size == row['exported_bytes'] and sha(path) == row['exported_sha256']
        return row['raw_sha256']

    costs.Path = rebound_path
    costs.sha = raw_identity
    c = costs.analyze(root)
    w = width.analyze(root / 'm2-run-03', a.archive / 'TEXT_INDEX.json')
    for name, value in [('PHYSICAL_AND_COMPLETE_COSTS.json', c), ('WIDTH_RESULTS.json', w)]:
        expected = json.loads((a.expected_dir / name).read_text())
        assert canonical(value) == canonical(expected), name
        with (out / name).open('x') as f:
            json.dump(value, f, indent=2, allow_nan=False)
            f.write('\n')
    proof = dict(passed=True, public_records_byte_verified=len(seen),
        complete_width_and_cost_reports_reproduced=True,
        width_report_sha256=sha(out / 'WIDTH_RESULTS.json'), cost_report_sha256=sha(out / 'PHYSICAL_AND_COMPLETE_COSTS.json'),
        archive_sha256=scope['bundle_sha256'], workspace_placeholder_rebound=True,
        raw_sha_identities_rebound_only_after_derived_byte_checks=True, numerical_fields_or_clocks_modified=False,
        new_native_jobs=0, model_forwards=0,
        scope='Fixed width/cost arithmetic from complete public derived records. Scalar-R row accounting remains contract-derived and failed incomplete physical receipts remain unknown. Not GPU allocation or numerical state requalification.')
    (out / 'CHECKED.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof), flush=True)


if __name__ == '__main__':
    main()
