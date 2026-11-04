"""Meaningful integrity/coverage checks for later native-study reporting."""
from pathlib import Path
import copy
import importlib.util
import json
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('native_followup', ROOT / 'scripts/generate_native_followup.py')
NATIVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NATIVE)


class NativeFollowupChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = NATIVE.csv_rows(ROOT / NATIVE.DATA / 'rtx_bridge/TIMING.csv')
        cls.freeze = NATIVE.read_json(ROOT / NATIVE.DATA / 'rtx_bridge/FREEZE.json')

    def test_exact_source_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / NATIVE.DATA, root / NATIVE.DATA)
            path = root / NATIVE.DATA / 'rtx_bridge/TIMING.csv'
            path.write_bytes(path.read_bytes().replace(b'1.7693144', b'1.7693145', 1))
            with self.assertRaisesRegex(ValueError, 'source Git blob mismatch'):
                NATIVE.authenticate(root)

    def test_missing_measurement_rejected(self):
        rows = self.rows.copy()
        del rows[next(i for i, row in enumerate(rows) if row['category'] == 'measurement')]
        with self.assertRaisesRegex(ValueError, 'missing or extra bridge timing rows'):
            NATIVE.reconstruct_bridge(rows, self.freeze)

    def test_duplicate_replaces_missing_slot_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[-1] = rows[-2].copy()
        with self.assertRaisesRegex(ValueError, 'duplicate bridge slot'):
            NATIVE.reconstruct_bridge(rows, self.freeze)

    def test_generated_mutation_rejected_without_regeneration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / NATIVE.DATA, root / NATIVE.DATA)
            (root / 'tables').mkdir()
            for name in ['native_bridge.tex', 'heldout_transfer.tex']:
                shutil.copyfile(ROOT / 'tables' / name, root / 'tables' / name)
            path = root / NATIVE.DATA / 'DERIVED.json'
            changed = json.loads(path.read_text())
            changed['rtx_bridge']['cells'][0]['ratio'] += .01
            path.write_text(json.dumps(changed))
            before = path.read_bytes()
            def check(name, passed):
                if not passed:
                    raise ValueError(name)
            with self.assertRaisesRegex(ValueError, 'Native follow-up source/derived consistency'):
                NATIVE.verify(check, root)
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
