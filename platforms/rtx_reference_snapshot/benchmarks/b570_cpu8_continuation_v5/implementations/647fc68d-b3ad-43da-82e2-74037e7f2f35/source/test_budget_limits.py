"""Actual portable guard/verifier counterexamples; no time waiting or OS child cases."""
import sys,json,unittest,datetime
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve();sys.path.insert(0,str(ROOT/'src/rev2'));sys.path.insert(0,str(ROOT/'source'))
from guards import wall_budget,revision_budget,reconcile_development_attempts
from source_guard import d0_now,actual_d0
class Limits(unittest.TestCase):
    def setUp(self):
        self.a={'first_preparation_utc':'2026-10-18T00:00:00Z'};self.f={'frozen_utc':'2026-10-18T00:20:00Z'};self.r=[dict(revision=0,run='development/r0',case_attempts=3,registered_utc='2026-10-18T00:10:00Z')];self.s=dict(started_utc='2026-10-18T00:21:00Z',begin_ns=1000000000);self.w=dict(task_elapsed_before_watchdog_seconds=1260,begin_ns=1000000000,end_ns=10801000000000);self.c=dict(observed_utc='2026-10-18T03:30:00Z',task_elapsed_seconds=12600,restoration_verified=True,tool_exit_verified=True)
    def call(self):return wall_budget(self.a,self.f,self.r,self.s,self.w,self.c)
    def test_positive(self):self.assertEqual(self.call()['task_through_completion_seconds'],12600)
    def test_22000(self):
        self.w['task_elapsed_before_watchdog_seconds']=22000
        with self.assertRaises(ValueError):self.call()
    def test_d0_5401(self):
        self.f['frozen_utc']='2026-10-18T01:30:01Z'
        with self.assertRaisesRegex(ValueError,'90_MINUTE'):self.call()
    def test_revision_four(self):
        self.r[0]['revision']=3
        with self.assertRaises(ValueError):self.call()
    def test_duplicate(self):
        self.r.append(self.r[0])
        with self.assertRaises(ValueError):self.call()
    def test_missing(self):
        del self.w['task_elapsed_before_watchdog_seconds']
        with self.assertRaises(KeyError):self.call()
    def test_nan(self):
        self.w['task_elapsed_before_watchdog_seconds']=float('nan')
        with self.assertRaises(ValueError):self.call()
    def test_infinity(self):
        self.w['task_elapsed_before_watchdog_seconds']=float('inf')
        with self.assertRaises(ValueError):self.call()
    def test_six_hour(self):
        self.c.update(observed_utc='2026-10-18T06:00:01Z',task_elapsed_seconds=21601)
        with self.assertRaises(ValueError):self.call()
    def test_delivery_1801(self):
        self.c.update(observed_utc='2026-10-18T03:51:01Z',task_elapsed_seconds=13861)
        with self.assertRaises(ValueError):self.call()
    def test_not_restored(self):
        self.c['restoration_verified']=False
        with self.assertRaises(ValueError):self.call()
suite=unittest.defaultTestLoader.loadTestsFromTestCase(Limits);result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(0 if result.wasSuccessful() else 1)
