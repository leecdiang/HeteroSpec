"""Actual retained evidence used for CPU negative auditor tests; never loads CUDA."""
import copy,json,shutil,tempfile,unittest
from pathlib import Path
from common import V,load,save
from prepare_rtx import root
from collect import audit
class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.source=next(p.parent for p in (root()/'attempts').glob('*/ENDED.json') if load(p.parent/'JOB.json')['stage']=='reference')
        self.job=load(self.source/'JOB.json');self.context=self.job['context'];self.temp=tempfile.TemporaryDirectory(prefix='hs121-cpu-evidence-');self.folder=Path(self.temp.name)/'native';shutil.copytree(self.source/'native',self.folder)
    def tearDown(self):self.temp.cleanup()
    def rewrite(self,name,change):
        p=self.folder/name;r=load(p);change(r);p.write_text(json.dumps(r),encoding='utf-8')
    def test_exact_reference_capture_not_candidate_pass(self):
        r,e=audit(self.folder,self.context,self.job);self.assertTrue(e['numerical_qualified']);self.assertEqual(r['status'],'REFERENCE_CAPTURE');self.assertIsNone(r['calls'][0]['ordinary_exact'])
    def test_reject_candidate_ordinary_bitflip(self):
        source=next(p.parent for p in (root()/'attempts').glob('*/ENDED.json') if load(p.parent/'JOB.json')['stage']=='qualification')
        job=load(source/'JOB.json');candidate=Path(self.temp.name)/'candidate';shutil.copytree(source/'native',candidate);r,e=audit(candidate,job['context'],job);self.assertTrue(e['numerical_qualified'])
        p=candidate/'ordinary_all.bin';b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
        with self.assertRaises(AssertionError):audit(candidate,job['context'],job)
    def test_reject_input_mutation(self):
        p=self.folder/'input_Q_after.bin';b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
        with self.assertRaises(AssertionError):audit(self.folder,self.context,self.job)
    def test_reject_truncated_output(self):
        p=self.folder/'ordinary_all.bin';p.write_bytes(p.read_bytes()[:-1])
        with self.assertRaises(AssertionError):audit(self.folder,self.context,self.job)
    def test_reject_bad_clock(self):
        self.rewrite('RECORD.json',lambda r:r['calls'][0].update(sync_return=r['calls'][0]['begin']-1))
        with self.assertRaises(AssertionError):audit(self.folder,self.context,self.job)
    def test_reject_wrong_placement(self):
        self.rewrite('GRAPH.json',lambda r:r['addresses'][0].update(CUDA_owned=False))
        with self.assertRaises(AssertionError):audit(self.folder,self.context,self.job)
    def test_reject_missing_import(self):
        self.rewrite('RECORD.json',lambda r:r['plugin_core_IAT'].pop())
        with self.assertRaises(AssertionError):audit(self.folder,self.context,self.job)
    def test_reject_support_failure(self):
        self.rewrite('GRAPH.json',lambda r:r['nodes'][0].update(CUDA_support=False))
        with self.assertRaises(AssertionError):audit(self.folder,self.context,self.job)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(EvidenceTests));save(V/'CPU_EVIDENCE_TESTS_REV2.json',dict(tests=result.testsRun,errors=len(result.errors),failures=len(result.failures),GPU_calls=0,actual_retained_evidence_used=True));assert result.wasSuccessful()
