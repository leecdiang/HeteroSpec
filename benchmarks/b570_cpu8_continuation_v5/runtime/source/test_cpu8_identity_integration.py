"""Production exception/identity integration tests using retained native raw streams."""
import sys,json,copy,unittest
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve()
sys.path[:0]=[str(ROOT/'source'),str(ROOT/'src/rev2')]
import cpu8_audit
class Tests(unittest.TestCase):
    def setUp(self):
        self.rows=[json.loads(x) for x in (ROOT/'processes/review-smoke-ok/OS_EVENTS.jsonl').read_bytes().splitlines()]
    def test_real_native_loader_records(self):
        self.assertGreater(cpu8_audit.exception_check(self.rows),0)
    def test_loader_continuation_mutation_rejected(self):
        row=next(x for x in self.rows if x['event']=='EXCEPTION');row['continuation']=0x80010001
        with self.assertRaisesRegex(AssertionError,'continuation'):cpu8_audit.exception_check(self.rows)
    def test_swallowed_application_breakpoint_rejected(self):
        i=next(i for i,x in enumerate(self.rows) if x['event']=='EXCEPTION')
        self.rows.insert(i+1,dict(self.rows[i],continuation=0x00010002))
        with self.assertRaisesRegex(AssertionError,'continuation'):cpu8_audit.exception_check(self.rows)
    def test_unknown_exception_identity_rejected(self):
        self.rows.insert(0,dict(event='EXCEPTION',pid=999999,code=0x80000003,first_chance=1,continuation=0x00010002))
        with self.assertRaisesRegex(AssertionError,'identity missing'):cpu8_audit.exception_check(self.rows)
    def test_actual_retired_pid_reuse_recording(self):
        rows=[json.loads(x) for x in (ROOT/'processes/review-churn/OS_EVENTS.jsonl').read_bytes().splitlines()]
        self.assertGreater(cpu8_audit.exception_check(rows),0)
        identities=[(x['pid'],x['created_filetime']) for x in rows if x['event']=='PROCESS_CREATE']
        self.assertLess(len({x[0] for x in identities}),len(identities))
suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests);result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(0 if result.wasSuccessful() else 1)
