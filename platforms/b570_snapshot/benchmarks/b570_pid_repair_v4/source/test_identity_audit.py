import copy,json,tempfile,unittest
from pathlib import Path
from audit_identity_stream import check
from process_registry import Registry
from test_process_registry import API,Journal
class Tests(unittest.TestCase):
    def fixture(self):
        a=API();j=Journal();r=Registry(a,j);r.root_key=(7,'100000000')
        j.emit('ROOT_CREATED_SUSPENDED',pid=7,created_filetime='100000000')
        for h in (1,2):
            a.add(h,h*100000000);r.create(7,h);r.complete_exit(r.exit_observed(7,0),0)
        j.emit('JOB_EMPTY',active_pids=[])
        receipt=dict(status='CLOSED',root_exit_code=0,error=None,all_observed_closed=True,observed=2,closed=2,lifetime_seconds=2)
        return j.rows,receipt
    def run_check(self,rows,receipt,churn=False,breakpoint=False,stdout='{}'):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'OS_EVENTS.jsonl').write_text('\n'.join(json.dumps(x) for x in rows));(p/'RECEIPT.json').write_text(json.dumps(receipt));(p/'stdout.log').write_text(stdout)
            return check(p,churn,breakpoint)
    def test_reused_identity_stream(self):
        rows,r=self.fixture();self.assertEqual(self.run_check(rows,r)['reused_pids'],1)
    def test_missing_raw_identity(self):
        rows,r=self.fixture();rows=[x for x in rows if x['event']!='PROCESS_CREATE_OBSERVED']
        with self.assertRaises(ValueError):self.run_check(rows,r)
    def test_unknown_exit(self):
        rows,r=self.fixture();rows.append(dict(event='EXIT_OBSERVED',pid=7,created_filetime='999',exit_code=0))
        with self.assertRaises(ValueError):self.run_check(rows,r)
    def test_receipt_count_false(self):
        rows,r=self.fixture();r['closed']=1
        with self.assertRaises(ValueError):self.run_check(rows,r)
    def test_missing_handle(self):
        rows,r=self.fixture();rows=[x for x in rows if x['event']!='HANDLE_CLOSED']
        with self.assertRaises(ValueError):self.run_check(rows,r)
    def test_wrong_lifetime(self):
        rows,r=self.fixture();next(x for x in rows if x['event']=='PROCESS_CLOSED')['exit_filetime']='1'
        with self.assertRaises(ValueError):self.run_check(rows,r)
    def test_wrong_root(self):
        rows,r=self.fixture();rows[0]['created_filetime']='999'
        with self.assertRaises(ValueError):self.run_check(rows,r)
    def test_receipt_contradicts_actual_root_exit(self):
        rows,r=self.fixture()
        for row in rows:
            if row['event'] in ('EXIT_OBSERVED','PROCESS_CLOSED') and row['created_filetime']=='100000000':row['exit_code']=7
        with self.assertRaisesRegex(ValueError,'root exit contradiction'):self.run_check(rows,r)
    def test_native_breakpoint_audit(self):
        rows,r=self.fixture();r['root_exit_code']=7
        for row in rows:
            if row['event'] in ('EXIT_OBSERVED','PROCESS_CLOSED') and row['created_filetime']=='100000000':row['exit_code']=7
        rows.append(dict(event='EXCEPTION',pid=7,code=0x80000003,continuation=0x80010001))
        self.run_check(rows,r,breakpoint=True,stdout='APPLICATION_BREAKPOINT_BEGIN')
        with self.assertRaises(ValueError):self.run_check(rows,r,breakpoint=True,stdout='APPLICATION_BREAKPOINT_BEGIN APPLICATION_BREAKPOINT_SWALLOWED')
    def test_application_fault_cannot_pass_success_mode(self):
        rows,r=self.fixture();r['root_exit_code']=7
        for row in rows:
            if row['event'] in ('EXIT_OBSERVED','PROCESS_CLOSED') and row['created_filetime']=='100000000':row['exit_code']=7
        with self.assertRaisesRegex(ValueError,'expected root outcome'):self.run_check(rows,r)
    def test_churn_missing_workers(self):
        rows,r=self.fixture()
        with self.assertRaises(ValueError):self.run_check(rows,r,True)
if __name__=='__main__':unittest.main()
