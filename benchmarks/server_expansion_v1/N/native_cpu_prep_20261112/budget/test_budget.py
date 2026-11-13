import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from budget import MockBudget, Blocked

class TestBudget(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        self.m = dict(mode='CPU_MOCK_ONLY', run_id='synthetic-only', source_sha256='a'*64,
                      deadline_epoch=200, limits=dict(requests=2, rows=5, placements=1),
                      request_rows={'a':3, 'b':2, 'c':2})
        self.b = MockBudget(self.p, self.m, clock=lambda:100)
    def tearDown(self):
        self.b.close(); self.tmp.cleanup()
    def test_no_default_authorization(self):
        m=copy.deepcopy(self.m); del m['mode']
        with self.assertRaises(Blocked): MockBudget(self.p/'x',m)
    def test_native_always_denied(self):
        with self.assertRaises(Blocked): self.b.admit_native(approved=True)
    def test_requests_never_reused(self):
        self.b.begin_request('a')
        with self.assertRaises(Blocked): self.b.begin_request('a')
    def test_unknown_request(self):
        with self.assertRaises(Blocked): self.b.begin_request('other')
    def test_global_request_cap(self):
        self.b.begin_request('a'); self.b.begin_request('b')
        with self.assertRaises(Blocked): self.b.begin_request('c')
    def test_per_request_rows(self):
        self.b.begin_request('a'); self.b.reserve_rows('a',3)
        with self.assertRaises(Blocked): self.b.reserve_rows('a',1)
    def test_no_rows_before_request(self):
        with self.assertRaises(Blocked): self.b.reserve_rows('a',1)
    def test_noninteger_rows(self):
        self.b.begin_request('a')
        for n in (True, -1, 0, 0.5):
            with self.assertRaises(Blocked): self.b.reserve_rows('a',n)
    def test_placement_cap(self):
        self.b.reserve_mock_placement('p')
        with self.assertRaises(Blocked): self.b.reserve_mock_placement('p2')
    def test_lock(self):
        with self.assertRaises(BlockingIOError): MockBudget(self.p,self.m)
    def test_resume_preserves_spend(self):
        self.b.begin_request('a'); self.b.reserve_rows('a',3); self.b.close()
        self.b=MockBudget(self.p,self.m,clock=lambda:100)
        self.assertEqual(self.b.counts,dict(requests=1,rows=3,placements=0))
        with self.assertRaises(Blocked): self.b.begin_request('a')
    def test_changed_run_cannot_reset(self):
        self.b.close(); m=copy.deepcopy(self.m); m['run_id']='new'
        with self.assertRaises(Blocked): MockBudget(self.p,m)
    def test_changed_cap_cannot_reset(self):
        self.b.close(); m=copy.deepcopy(self.m); m['limits']['rows']=100
        with self.assertRaises(Blocked): MockBudget(self.p,m)
    def test_timeout(self):
        self.b.clock=lambda:200
        with self.assertRaises(Blocked): self.b.begin_request('a')
    def test_monotonic_timeout_despite_wall_rollback(self):
        self.b.clock=lambda:1
        self.b.monotonic=lambda:self.b.monotonic_deadline
        with self.assertRaises(Blocked): self.b.begin_request('a')
    def test_partial_write_poison(self):
        self.b.write=lambda fd,data:os.write(fd,data[:3])
        with self.assertRaises(OSError): self.b.begin_request('a')
        with self.assertRaises(Blocked): self.b.begin_request('b')
        self.b.close()
        with self.assertRaises(Blocked): MockBudget(self.p,self.m)
    def test_sync_failure_poison(self):
        def failure(fd): raise OSError('injected fsync')
        self.b.sync=failure
        with self.assertRaises(OSError): self.b.begin_request('a')
        self.b.close()
        with self.assertRaises(Blocked): MockBudget(self.p,self.m)
    def test_complete_record_uncertain_marker(self):
        self.b.begin_request('a'); self.b.close()
        (self.p/'UNCERTAIN').write_text('crash')
        with self.assertRaises(Blocked): MockBudget(self.p,self.m)
    def test_partial_ledger(self):
        self.b.close()
        with (self.p/'ledger.jsonl').open('ab') as f:f.write(b'{')
        with self.assertRaises(Blocked): MockBudget(self.p,self.m)
    def test_corrupt_duplicate(self):
        self.b.begin_request('a'); self.b.close()
        with (self.p/'ledger.jsonl').open('ab') as f:f.write(b'{"kind":"request","id":"a"}\n')
        with self.assertRaises(Blocked): MockBudget(self.p,self.m)
    def test_failed_mock_work_not_refunded(self):
        self.b.begin_request('a'); self.b.reserve_rows('a',3)
        try:raise RuntimeError('mock forward fails after reservation')
        except RuntimeError:pass
        self.assertEqual(self.b.counts['rows'],3)
    def test_global_rows_cap(self):
        self.b.close(); m=copy.deepcopy(self.m);m['limits']['rows']=3
        self.b=MockBudget(self.p/'small',m,clock=lambda:100)
        self.b.begin_request('a');self.b.reserve_rows('a',3);self.b.begin_request('b')
        with self.assertRaises(Blocked):self.b.reserve_rows('b',1)

if __name__=='__main__':unittest.main(verbosity=2)
