"""Check whether diagnostics perturb the natural uninstrumented trajectory."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--epoch', type=Path, required=True)
    p.add_argument('--baseline-epoch', type=Path)
    p.add_argument('--unit', required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    unit = a.epoch / 'units' / a.unit
    receipt = json.loads((unit / 'RECEIPT.json').read_text())
    assert receipt['success'] and receipt['active_processes_after_wait'] == 0
    cells = []
    for slot in json.loads((unit / 'SLOTS.json').read_text()):
        folder = unit / 'native' / slot['slot_id']
        baseline = (a.baseline_epoch or a.epoch) / 'units/development/native/dev' / f"i{slot['source_index']:02d}" / slot['arm'] / 'native/heavy'
        actual = json.loads(folder.with_suffix('.json').read_text())
        old = json.loads(baseline.with_suffix('.json').read_text())
        fields = ('ids', 'eog', 'length', 'terminal_id', 'stop_reason', 'cycles',
                  'target_final_kv', 'draft_final_kv')
        vectors = {}
        for role in ('target', 'draft'):
            oldnames = {p.name for p in (baseline / role).glob('*.f32')}
            newnames = {p.name for p in (folder / role).glob('*.f32')}
            assert oldnames == newnames
            for name in sorted(oldnames):
                vectors[f'{role}/{name}'] = sha(baseline / role / name) == sha(folder / role / name)
        states = {role: sha(baseline / f'{role}_final.state') == sha(folder / f'{role}_final.state')
                  for role in ('target', 'draft')}
        cells.append({'slot': slot['slot_id'], 'record_sha256': sha(folder.with_suffix('.json')),
                      'natural_fields_equal': {k: actual[k] == old[k] for k in fields},
                      'vectors': vectors, 'final_states_equal': states})
    passed = all(all(c['natural_fields_equal'].values()) and all(c['vectors'].values())
                 and all(c['final_states_equal'].values()) for c in cells)
    report = {'status': 'OBSERVER_CONTROL_PASS' if passed else 'OBSERVER_CONTROL_FAILED',
              'unit': a.unit, 'cells': cells, 'receipt_sha256': sha(unit / 'RECEIPT.json')}
    with a.out.open('x') as f:
        json.dump(report, f, indent=2)
    print(report['status'])


if __name__ == '__main__':
    main()
