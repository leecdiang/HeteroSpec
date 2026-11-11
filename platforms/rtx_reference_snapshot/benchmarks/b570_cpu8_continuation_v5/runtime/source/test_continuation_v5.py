import copy,hashlib,json,tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/rev2'))
from evidence_contract import manifest_check,watchdog_check,member
from continuation_policy import POLICY,review_id
from guards import revision_budget,wall_budget
class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'failed.log').write_bytes(b'failed');self.row=dict(path='failed.log',bytes=6,sha256=hashlib.sha256(b'failed').hexdigest());self.save([self.row])
    def save(self,rows): (self.root/'MANIFEST.json').write_text(json.dumps(dict(files=rows)))
    def check(self):return manifest_check(self.root,'MANIFEST.json')
    def test_external_reference(self):
        for path in ['../outside.json',str(self.root/'failed.log')]:
            with self.assertRaises(ValueError):member(self.root,path)
    def test_reference_alias(self):
        (self.root/'alias').symlink_to(self.root/'failed.log')
        with self.assertRaises(ValueError):member(self.root,'alias')
    def test_exact(self):self.assertEqual(self.check()['members'],1)
    def test_unlisted_failure(self):
        (self.root/'extra-failure.log').write_text('failure')
        with self.assertRaises(ValueError):self.check()
    def test_omitted_listed_file(self):
        self.save([])
        with self.assertRaises(ValueError):self.check()
    def test_duplicate(self):
        self.save([self.row,self.row])
        with self.assertRaises(ValueError):self.check()
    def test_content(self):
        (self.root/'failed.log').write_bytes(b'passed')
        with self.assertRaises(ValueError):self.check()
    def test_symlink(self):
        (self.root/'alias').symlink_to(self.root/'failed.log')
        with self.assertRaises(ValueError):self.check()
    def test_manifest_cannot_hide_itself_as_member(self):
        self.save([self.row,dict(path='MANIFEST.json',bytes=0,sha256='x')])
        with self.assertRaises(ValueError):self.check()
class ClosureTests(unittest.TestCase):
    def setUp(self):
        self.times=dict(created_filetime='100',exit_filetime='200',kernel_100ns='1',user_100ns='2')
        self.receipt=dict(status='WATCHDOG_CLOSED',error=None,begin_ns=10,end_ns=90,watchdog_pid=7,supervisor_pid=8,supervisor_exit_code=0,supervisor_os_times=self.times,outer_job_empty=True,owned_handles_closed=True)
        self.events=[dict(event='WATCHDOG_START',pid=7,begin_ns=10,at_ns=20),dict(event='SUPERVISOR_CREATED_SUSPENDED',pid=8,created_filetime='100',at_ns=30),dict(event='SUPERVISOR_OS_EXIT',pid=8,exit_code=0,at_ns=80,**self.times),dict(event='WATCHDOG_END',at_ns=100,receipt=copy.deepcopy(self.receipt))]
        self.events[2:2]=[dict(event='OUTER_JOB_ASSIGNED',pid=8,at_ns=31),dict(event='SUPERVISOR_RESUMED',pid=8,at_ns=32),dict(event='HANDLE_CLOSED',handle_kind='supervisor_primary_thread',at_ns=33)]
        self.events[-1:-1]=[dict(event='OUTER_JOB_EMPTY',active_pids=[],at_ns=81),dict(event='HANDLE_CLOSED',handle_kind='supervisor_process',at_ns=82),dict(event='HANDLE_CLOSED',handle_kind='outer_job',at_ns=83)]
        for i,x in enumerate(self.events):x['seq']=i+1
        self.sup=[dict(at_ns=40),dict(at_ns=70)]
    def check(self):return watchdog_check(self.events,self.receipt,self.sup)
    def test_raw_match(self):self.assertEqual(self.check()['end_ns'],90)
    def test_changed_receipt_end(self):
        self.receipt['end_ns']=50
        with self.assertRaises(ValueError):self.check()
    def test_both_ends_before_actual_exit(self):
        self.receipt['end_ns']=50;self.events[-1]['receipt']=copy.deepcopy(self.receipt)
        with self.assertRaises(ValueError):self.check()
    def test_supervisor_after_end(self):
        self.sup[-1]['at_ns']=95
        with self.assertRaises(ValueError):self.check()
    def test_os_identity(self):
        next(x for x in self.events if x['event']=='SUPERVISOR_OS_EXIT')['created_filetime']='99'
        with self.assertRaises(ValueError):self.check()
    def test_raw_gap(self):
        self.events[2]['seq']=99
        with self.assertRaises(ValueError):self.check()
    def test_missing_raw_handle(self):
        self.events=[x for x in self.events if x.get('handle_kind')!='outer_job']
        for i,x in enumerate(self.events):x['seq']=i+1
        with self.assertRaises(ValueError):self.check()
    def test_missing_raw_empty(self):
        self.events=[x for x in self.events if x['event']!='OUTER_JOB_EMPTY']
        for i,x in enumerate(self.events):x['seq']=i+1
        with self.assertRaises(ValueError):self.check()
    def test_nonempty_job(self):
        next(x for x in self.events if x['event']=='OUTER_JOB_EMPTY')['active_pids']=[99]
        with self.assertRaises(ValueError):self.check()
    def test_duplicate_close(self):
        self.events.insert(-1,dict(event='HANDLE_CLOSED',handle_kind='outer_job',at_ns=84))
        for i,x in enumerate(self.events):x['seq']=i+1
        with self.assertRaises(ValueError):self.check()
    def test_missing_end(self):
        self.events.pop()
        with self.assertRaises(ValueError):self.check()
class PolicyTests(unittest.TestCase):
    def regs(self):return [dict(revision=i,run='r'+str(i),case_attempts=1,registered_utc='2026-10-18T00:01:00Z') for i in range(25)]
    def test_more_than_two_reviews(self):self.assertTrue(review_id('full-review-37',POLICY))
    def test_bad_review_path(self):self.assertFalse(review_id('../full-review-3',POLICY))
    def test_old_review_rule_retained(self):self.assertFalse(review_id('full-review-3',None))
    def test_no_arbitrary_count_stop(self):self.assertEqual(revision_budget(self.regs(),POLICY)['reserved_attempts'],25)
    def test_duplicate_still_rejected(self):
        rows=self.regs();rows.append(rows[0])
        with self.assertRaises(ValueError):revision_budget(rows,POLICY)
    def test_original_count_rule_retained(self):
        with self.assertRaises(ValueError):revision_budget(self.regs())
    def test_four_hour_development(self):
        acq=dict(first_preparation_utc='2026-10-18T00:00:00Z');f=dict(frozen_utc='2026-10-18T04:00:00Z',continuation_policy=POLICY);start=dict(started_utc=f['frozen_utc'],begin_ns=0);receipt=dict(task_elapsed_before_watchdog_seconds=14400,begin_ns=0,end_ns=1)
        self.assertEqual(wall_budget(acq,f,self.regs(),start,receipt)['development_seconds'],14400)
    def test_total_budget_still_enforced(self):
        acq=dict(first_preparation_utc='2026-10-18T00:00:00Z');f=dict(frozen_utc='2026-10-18T04:00:00Z',continuation_policy=POLICY);start=dict(started_utc=f['frozen_utc'],begin_ns=0);receipt=dict(task_elapsed_before_watchdog_seconds=14400,begin_ns=0,end_ns=8000*10**9)
        with self.assertRaises(ValueError):wall_budget(acq,f,self.regs(),start,receipt)
if __name__=='__main__':unittest.main()
