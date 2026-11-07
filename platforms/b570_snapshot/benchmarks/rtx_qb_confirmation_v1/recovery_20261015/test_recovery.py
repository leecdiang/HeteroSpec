"""No native calls: reject any started coordinate or changed budget history."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import admit_and_run as r

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        for s in range(5):(self.root/f'SESSION-{s}-COMPLETE.json').write_text('{}')
        self.events=[dict(slot=f's0/load/{i}',kind='load') for i in range(270)]+[dict(slot=f's0/request/{i}',kind='request') for i in range(1350)]
    def tearDown(self):self.temp.cleanup()
    def guard(self):
        with patch.object(r,'OUT',self.root),patch.object(r.e,'Ledger',return_value=SimpleNamespace(events=self.events,owned=lambda:4149.035876499896)):
            return r.untouched()
    def test_untouched_original_budget_admitted(self):self.guard()
    def test_receipt_or_lock_rejected(self):
        for name in ('SESSION-5.json','EXECUTION.lock'):
            p=self.root/name;p.write_text('{}')
            with self.assertRaises(ValueError):self.guard()
            p.unlink()
    def test_any_started_scientific_slot_rejected(self):
        self.events[0]['slot']='s5/Qwen/b00'
        with self.assertRaises(ValueError):self.guard()
    def test_unexpected_history_or_missing_previous_rejected(self):
        self.events.pop()
        with self.assertRaises(ValueError):self.guard()
        (self.root/'SESSION-4-COMPLETE.json').unlink()
        with self.assertRaises(ValueError):self.guard()
if __name__=='__main__':unittest.main(verbosity=2)
