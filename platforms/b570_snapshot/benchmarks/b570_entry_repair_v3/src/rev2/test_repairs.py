"""Portable regression checks: no Windows API claims and no historical writes."""
import ast
import copy
import datetime
import json
from pathlib import Path
import tempfile
import unittest
from guards import FrozenBaseline, ProgressGuard, digest, wall_budget, revision_budget, admit_development_case, reconcile_development_attempts

HERE=Path(__file__).parent

class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'actor.py').write_text('original')
        self.freeze={'files':{'actor.py':digest(b'original')}}
        self.write();self.expected=digest((self.root/'CAPABILITY_FREEZE.json').read_bytes())
        self.guard=FrozenBaseline(self.root,self.expected)
    def write(self):
        (self.root/'CAPABILITY_FREEZE.json').write_text(json.dumps(self.freeze))
    def test_unchanged(self):self.guard.check();self.guard.check()
    def test_source_only(self):
        (self.root/'actor.py').write_text('changed')
        with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT'):self.guard.check()
    def test_source_and_rehashed_manifest(self):
        (self.root/'actor.py').write_text('changed');self.freeze['files']['actor.py']=digest(b'changed');self.write()
        with self.assertRaisesRegex(ValueError,'FREEZE_REPLACED'):self.guard.check()
    def test_replaced_before_child_start(self):
        self.freeze['extra']='replacement';self.write()
        with self.assertRaisesRegex(ValueError,'initial freeze'):FrozenBaseline(self.root,self.expected)
    def test_missing_initial_pin(self):
        with self.assertRaises(ValueError):FrozenBaseline(self.root,None)
    def test_manifest_only_replacement(self):
        self.freeze['extra']=1;self.write()
        with self.assertRaises(ValueError):self.guard.check()

class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.row=dict(pid=42,created_filetime='123',progress_seq=1,progress_ns=1_000_000_000)
        self.guard=ProgressGuard(42,'123')
    def test_healthy_unchanged_then_advance(self):
        self.guard.check(self.row,2_000_000_000);self.guard.check(self.row,3_000_000_000)
        self.guard.check(dict(self.row,progress_seq=2,progress_ns=3_000_000_000),4_000_000_000)
    def test_suspended_watchdog(self):
        self.guard.check(self.row,1_000_000_000)
        with self.assertRaisesRegex(ValueError,'STALE'):self.guard.check(self.row,6_000_000_001)
    def test_future(self):
        with self.assertRaises(ValueError):self.guard.check(self.row,0)
    def test_wrong_pid(self):
        with self.assertRaises(ValueError):self.guard.check(dict(self.row,pid=43),1_000_000_000)
    def test_pid_reuse(self):
        with self.assertRaises(ValueError):self.guard.check(dict(self.row,created_filetime='124'),1_000_000_000)
    def test_replay(self):
        self.guard.check(dict(self.row,progress_seq=2,progress_ns=2_000_000_000),2_000_000_000)
        with self.assertRaises(ValueError):self.guard.check(self.row,3_000_000_000)
    def test_seq_without_clock_progress(self):
        self.guard.check(self.row,1_000_000_000)
        with self.assertRaises(ValueError):self.guard.check(dict(self.row,progress_seq=2),2_000_000_000)
    def test_real_tick_stops_before_next_case(self):
        # Execute the actual tick + case AST: a stale but still-alive/RSS-readable watchdog.
        source=ast.parse((HERE/'supervisor.py').read_text())
        mod=ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in ('tick','case')],type_ignores=[])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'WATCHDOG_PROGRESS.json').write_text(json.dumps(self.row))
            from types import SimpleNamespace
            env=dict(now=lambda:16_000_000_000,need=lambda v,m: None if v else (_ for _ in ()).throw(ValueError(m)),a=SimpleNamespace(deadline_ns=99_000_000_000,mode='development'),alive=lambda h:True,watchdog_h=42,RUN=root,json=json,progress_guard=self.guard,historical_starts=0,actor_starts=0,historical_life=0,actor_life=0,last_sample=None,last_heartbeat=0)
            exec(compile(mod,'supervisor.py','exec'),env)
            with self.assertRaisesRegex(ValueError,'STALE'):env['case']('C1','must-not-start')
            self.assertFalse((root/'must-not-start').exists())

class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.acq={'first_preparation_utc':'2026-10-18T00:00:00+00:00'}
        self.freeze={'frozen_utc':'2026-10-18T00:20:00+00:00'}
        self.reg=[dict(revision=0,run='development/r0-a1',case_attempts=3,registered_utc='2026-10-18T00:10:00+00:00')]
        self.start=dict(started_utc='2026-10-18T00:21:00+00:00',begin_ns=1_000_000_000)
        self.receipt=dict(task_elapsed_before_watchdog_seconds=1260,begin_ns=1_000_000_000,end_ns=10801_000_000_000)
        self.complete=dict(observed_utc='2026-10-18T03:30:00+00:00',task_elapsed_seconds=12600,restoration_verified=True,tool_exit_verified=True)
    def check(self):return wall_budget(self.acq,self.freeze,self.reg,self.start,self.receipt,self.complete)
    def test_valid(self):self.assertEqual(self.check()['task_through_completion_seconds'],12600)
    def test_actual_counterexample_22000(self):
        self.receipt['task_elapsed_before_watchdog_seconds']=22000
        with self.assertRaises(ValueError):self.check()
    def test_consistent_over_six_hours(self):
        self.start['started_utc']='2026-10-18T05:00:00+00:00';self.receipt['task_elapsed_before_watchdog_seconds']=18000
        with self.assertRaisesRegex(ValueError,'6_HOUR'):self.check()
    def test_development_over_90_minutes(self):
        self.freeze['frozen_utc']='2026-10-18T01:30:01+00:00'
        with self.assertRaisesRegex(ValueError,'90_MINUTE'):self.check()
    def test_fourth_revision(self):
        self.reg.append(dict(self.reg[0],revision=3,run='development/r3-a1'))
        with self.assertRaisesRegex(ValueError,'revision'):self.check()
    def test_duplicate_run(self):
        self.reg.append(self.reg[0])
        with self.assertRaisesRegex(ValueError,'duplicate'):self.check()
    def test_too_many_attempts(self):
        self.reg[0]['case_attempts']=21
        with self.assertRaises(ValueError):self.check()
    def test_delivery_over_30_minutes(self):
        self.complete.update(observed_utc='2026-10-18T04:00:00+00:00',task_elapsed_seconds=14400)
        with self.assertRaisesRegex(ValueError,'30_MINUTE'):self.check()
    def test_final_over_six_hours(self):
        self.complete.update(observed_utc='2026-10-18T06:00:01+00:00',task_elapsed_seconds=21601)
        with self.assertRaisesRegex(ValueError,'6_HOUR'):self.check()
    def test_nonfinite(self):
        self.receipt['task_elapsed_before_watchdog_seconds']=float('nan')
        with self.assertRaises(ValueError):self.check()
    def test_reversed_clock(self):
        self.freeze['frozen_utc']='2026-10-17T23:00:00+00:00'
        with self.assertRaises(ValueError):self.check()
    def test_missing_finalization_prerequisite(self):
        self.complete['restoration_verified']=False
        with self.assertRaises(ValueError):self.check()
    def test_completion_before_end(self):
        self.complete.update(observed_utc='2026-10-18T02:00:00+00:00',task_elapsed_seconds=7200)
        with self.assertRaises(ValueError):self.check()


class ActualAttemptTests(unittest.TestCase):
    def test_runtime_cannot_admit_second_case_with_one_reserved(self):
        self.assertEqual(admit_development_case(0,1),1)
        with self.assertRaisesRegex(ValueError,'EXHAUSTED'):admit_development_case(1,1)
    def test_seven_under_reserved_runs_cannot_execute_21_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);regs=[]
            for i in range(7):
                rel='development/r0-a'+str(i);regs.append(dict(revision=0,run=rel,case_attempts=1))
                for j in range(3):
                    folder=root/rel/str(j);folder.mkdir(parents=True)
                    (folder/'EVENTS.jsonl').write_text(json.dumps(dict(event='CASE_BEGIN'))+'\n'+json.dumps(dict(event='CASE_ERROR'))+'\n')
            with self.assertRaisesRegex(ValueError,'actual attempts exceed'):reconcile_development_attempts(root,regs)
    def test_failed_cases_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'development/r0-a1/failure';folder.mkdir(parents=True)
            (folder/'EVENTS.jsonl').write_text('{"event":"CASE_BEGIN"}\n{"event":"CASE_ERROR"}\n')
            self.assertEqual(reconcile_development_attempts(root,[dict(revision=0,run='development/r0-a1',case_attempts=1)]),1)

if __name__=='__main__':unittest.main()

