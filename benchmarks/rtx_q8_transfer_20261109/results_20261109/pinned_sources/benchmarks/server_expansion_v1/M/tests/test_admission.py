"""Frozen identity must admit all distinct controls but reject slot retries."""
import os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_m1 as m

@unittest.skipUnless(os.environ.get('M1_RUNTIME'),'Set M1_RUNTIME to pinned Linux successor tools')
class Admission(unittest.TestCase):
    def setUp(self):
        m.load_runtime(Path(os.environ['M1_RUNTIME']));self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.job=self.root/'job.json';m.save(self.job,{'identical_request_bytes':True});self.builds={};self.frozen={'executables':{}}
        for core in ('loop4','packed'):
            path=self.root/(core+'.json');build={'role':core,'executable_sha256':core};m.save(path,build);self.builds[core]=(path,build);self.frozen['executables'][core]={'build':{'sha256':m.sha(path)}}
        self.workers=[{'id':f's{i//4}-{i%4}','core':['loop4','packed','loop4','packed'][i%4],'job':self.job.name,'job_sha256':m.sha(self.job)} for i in range(16)]
        self.plan=self.root/'PLAN.json';m.save(self.plan,dict(study='server_m_v1',panel='attribution',workers=self.workers,measurements=256,primers=32,arms=list(m.ARMS)))
        self.frozen['plan']={'path':str(self.plan),'sha256':m.sha(self.plan)}
    def admit(self,i,prior=(),core=None,out=None):
        w=self.workers[i];path,b=self.builds[core or w['core']];return m.confirmation_identity(self.frozen,path,b,self.job,out or self.root/'runs'/w['id'],prior)
    def reservation(self,i):
        return dict(phase='confirmation',out=str(self.root/'runs'/self.workers[i]['id']),job_sha256=m.sha(self.job),plan_sha256=m.sha(self.plan))
    def test_distinct_builds_same_request(self):self.assertEqual(self.admit(1,[self.reservation(0)])['confirmation_slot_id'],self.workers[1]['id'])
    def test_distinct_sessions_same_build_and_request(self):self.assertEqual(self.admit(4,[self.reservation(0)])['confirmation_slot_id'],self.workers[4]['id'])
    def test_no_same_slot_retry(self):
        with self.assertRaisesRegex(RuntimeError,'already reserved'):self.admit(0,[self.reservation(0)])
    def test_wrong_core(self):
        with self.assertRaisesRegex(RuntimeError,'Different numerical core'):self.admit(0,core='packed')
    def test_no_output_rename_bypass(self):
        with self.assertRaisesRegex(RuntimeError,'Unregistered'):self.admit(0,out=self.root/'runs/retry')
    def test_changed_plan(self):
        self.plan.write_text('{}')
        with self.assertRaisesRegex(RuntimeError,'plan changed'):self.admit(0)

if __name__=='__main__':unittest.main()
