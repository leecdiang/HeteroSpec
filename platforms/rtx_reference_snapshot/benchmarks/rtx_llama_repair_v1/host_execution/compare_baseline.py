"""Read-only comparison against authenticated PR151 records and complete vectors."""
import argparse
import array
import hashlib
import json
import math
from pathlib import Path


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def endpoint(r):
    return {k: r[k] for k in ('ids', 'eog', 'length', 'terminal_id', 'stop_reason')}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--epoch', type=Path, required=True)
    p.add_argument('--history', type=Path, required=True)
    p.add_argument('--raw', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    manifest = a.history / 'REQUESTS.original.jsonl'
    assert digest(manifest) == '2e52aee27acb551f3f3556a566ec5f83b123aa0d50a9c01da3666ac33a2fa4b9'
    old = {}
    for line in manifest.read_text().splitlines():
        row = json.loads(line)
        if row['stage'] == 'diagnostic_A1' and row['observer'] == 'heavy':
            old[row['input_id'], row['arm']] = row
    folder = a.epoch / 'units/development/native'
    slots = json.loads((a.epoch / 'units/development/SLOTS.json').read_text())
    cells = []
    for slot in slots:
        if slot['observer'] != 'heavy':
            continue
        arm = slot['arm']
        if arm not in ('R', 'C_PQ', 'C_QB') or slot['repair']['prefill'] != 'native':
            continue
        pin = old[slot['input_id'], arm]
        op = a.raw / pin['raw_native_record']['path']
        assert digest(op) == pin['raw_native_record']['sha256']
        np = folder / (slot['slot_id'] + '.json')
        original, candidate = json.loads(op.read_text()), json.loads(np.read_text())
        vectors = []
        for v in pin['raw_vectors']:
            ov = a.raw / v['path']
            assert digest(ov) == v['sha256']
            rel = ov.relative_to(op.with_suffix(''))
            nv = np.with_suffix('') / rel
            values = array.array('f', nv.read_bytes())
            assert len(values) == 128256 and all(math.isfinite(x) for x in values)
            vectors.append({'file': str(rel), 'old': v['sha256'], 'new': digest(nv)})
        cells.append({'input': slot['input_id'], 'arm': arm,
                      'endpoint_equal': endpoint(original) == endpoint(candidate),
                      'vectors_checked': len(vectors),
                      'all_complete_vectors_equal': all(v['old'] == v['new'] for v in vectors),
                      'vectors': vectors, 'record_sha256': digest(np)})
    assert len(cells) == 9
    result = {'status': 'BASELINE_HISTORICAL_COMPARISON', 'cells': cells,
              'all_endpoints_equal_historical': all(c['endpoint_equal'] for c in cells),
              'all_vectors_equal_historical': all(c['all_complete_vectors_equal'] for c in cells)}
    with a.out.open('x') as f:
        json.dump(result, f, indent=2)
    print({k: v for k, v in result.items() if k != 'cells'})


if __name__ == '__main__':
    main()
