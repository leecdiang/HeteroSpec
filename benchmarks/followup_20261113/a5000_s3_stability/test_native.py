"""Budget and disposal checks without any CUDA/native process."""
import json
from pathlib import Path
import tempfile
import unittest

from native import Budget, prune_states


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.budget = Budget(self.root / 'requests.jsonl')

    def tearDown(self):
        self.temp.cleanup()

    def worker(self, name, requests, rows):
        return dict(worker_id=name, requests=requests, reserved_rows=rows, roles=[str(x) for x in range(requests)])

    def test_failed_worker_stays_charged(self):
        self.budget.reserve('H', self.worker('first', 176, 56320))
        self.budget.event(dict(event='EXIT', worker_id='first', error='failure'))
        with self.assertRaises(ValueError):
            self.budget.reserve('H', self.worker('next', 1, 1))

    def test_no_duplicate_launch(self):
        worker = self.worker('same', 1, 320)
        self.budget.reserve('R', worker)
        with self.assertRaises(ValueError): self.budget.reserve('R', worker)

    def test_no_cohort_transfer(self):
        self.budget.reserve('R', self.worker('R', 292, 93440))
        with self.assertRaises(ValueError): self.budget.reserve('R', self.worker('R2', 1, 1))
        self.budget.reserve('H', self.worker('H', 176, 56320))
        self.assertEqual(sum(x['requests'] for x in self.budget.entries()), 468)

    def test_rows_separate_from_requests(self):
        with self.assertRaises(ValueError): self.budget.reserve('R', self.worker('bad', 1, 93441))
        self.assertFalse(self.budget.path.exists())

    def test_disposal_preserves_vectors_and_required_state(self):
        keep = self.root / 'final/sequence.bin'
        discard = self.root / 'intermediate/sequence.bin'
        for path in [keep, discard, self.root / 'intermediate/frontier.f32']:
            path.parent.mkdir(exist_ok=True); path.write_bytes(b'raw')
        prune_states(self.root, {keep})
        self.assertTrue(keep.exists())
        self.assertFalse(discard.exists())
        self.assertTrue((discard.parent / 'frontier.f32').exists())
        self.assertEqual(json.loads((self.root / 'DISPOSAL.json').read_text())['files'][0]['bytes'], 3)


if __name__ == '__main__': unittest.main()
