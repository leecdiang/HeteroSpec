"""Adversarial parser/interval checks using genuine development raw as baseline.

These unit assertions are NOT new Windows injection cases or confirmation rows.
"""
import copy,json,unittest
from pathlib import Path
from common import BASE
from raw_audit import verify_watch_buffers,decode_notifications
from coverage import boundary_tests,evaluate
class RawAuditChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[json.loads(x) for x in (BASE/'runs/dev2-full-1/external/WATCH.jsonl').read_text(encoding='utf-8').splitlines()]
    def test_real_baseline(self):self.assertTrue(verify_watch_buffers(self.rows))
    def test_missing_raw_decision_rejected(self):
        rows=copy.deepcopy(self.rows);rows.pop(next(i for i,r in enumerate(rows) if r['event']=='NOTIFY_DECISION'));self.assertFalse(verify_watch_buffers(rows))
    def test_wrong_raw_action_rejected(self):
        rows=copy.deepcopy(self.rows);next(r for r in rows if r['event']=='NOTIFY_DECISION')['action']=99;self.assertFalse(verify_watch_buffers(rows))
    def test_wrong_target_rejected(self):
        rows=copy.deepcopy(self.rows);next(r for r in rows if r['event']=='NOTIFY_DECISION')['canonical']='c:\\wrong';self.assertFalse(verify_watch_buffers(rows))
    def test_sealed_write_cannot_become_allowed(self):
        rows=copy.deepcopy(self.rows);next(r for r in rows if r['event']=='NOTIFY_DECISION' and not r['allowed'])['allowed']=True;self.assertFalse(verify_watch_buffers(rows))
    def test_incomplete_raw_notification_rejected(self):
        with self.assertRaises(AssertionError):decode_notifications(b'\x01')
    def test_three_exact_boundaries(self):self.assertEqual([r['valid'] for r in boundary_tests()],[True,True,False])
    def test_missing_samples_never_qualified(self):self.assertFalse(evaluate([],0,100)['valid'])
    def test_terminal_gap_not_removed(self):
        rows=[dict(event='READ_BEGIN',begin_ns=0),dict(event='READ_END',begin_ns=0,end_ns=1)]
        self.assertFalse(evaluate(rows,0,1000000001)['valid'])
    def test_long_read_not_instantaneous(self):
        rows=[dict(event='READ_BEGIN',begin_ns=0),dict(event='READ_END',begin_ns=0,end_ns=1000000001)]
        self.assertFalse(evaluate(rows,0,1000000001)['valid'])
if __name__=='__main__':unittest.main()
