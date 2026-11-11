"""Risk-directed CPU self-tests,including real Windows child timeout cleanup."""
import ctypes,itertools,json,math,os,struct,sys,time,unittest
from pathlib import Path
from common import V,load,save,sha
from analyze import paired,compare,aliases,summarize
from lifecycle import Child
class Tests(unittest.TestCase):
    def test_ratio_direction(self):self.assertAlmostEqual(paired(11,10)['ratio'],1.1);self.assertEqual(paired(11,10)['difference_us'],1)
    def test_negative_ratio(self):self.assertLess(paired(9,10)['ratio'],1)
    def test_zero_rejected(self):
        with self.assertRaises(AssertionError):paired(0,1)
    def test_empty_unknown(self):self.assertIsNone(summarize([])['median'])
    def test_tails(self):self.assertEqual(summarize([1]*19+[100])['max'],100)
    def test_full_bytes(self):self.assertFalse(compare(struct.pack('<ff',1,2),struct.pack('<ff',1,3))['exact'])
    def test_signed_zero(self):self.assertFalse(compare(struct.pack('<f',0.),struct.pack('<f',-0.))['exact'])
    def test_nonfinite(self):self.assertFalse(compare(struct.pack('<f',float('inf')),struct.pack('<f',1.))['finite'])
    def test_truncated(self):
        with self.assertRaises(AssertionError):compare(b'123',b'123')
    def test_alias(self):
        rows=[dict(id='input0',data=100,bytes=20),dict(id='node0',data=116,bytes=10,metadata_only=False,op='CONT')];self.assertEqual(aliases(dict(addresses=rows))[0]['bytes'],4)
    def test_nonalias(self):self.assertEqual(aliases(dict(addresses=[dict(id='input0',data=100,bytes=20),dict(id='node0',data=120,bytes=10,metadata_only=False,op='CONT')])),[])
    def test_six_orders(self):
        orders=list(itertools.permutations(['PQ','QB','QH_C']))
        for i in range(24):self.assertEqual(len({orders[(i+b)%6] for b in range(6)}),6)
    def test_geometry(self):
        s=load(Path(load(V/'LOCAL_RUN.json')['root'])/'RUN_SPEC.json');self.assertEqual(len({c['id'] for c in s['contexts']}),24);self.assertEqual({(c['family'],c['phase'],c['q']) for c in s['contexts']},set(itertools.product(['Qwen','SmolLM2','Llama'],['prefill','continuation'],range(1,5))))
    def test_QPC(self):
        f=ctypes.c_longlong();a=ctypes.c_longlong();b=ctypes.c_longlong();k=ctypes.windll.kernel32;self.assertTrue(k.QueryPerformanceFrequency(ctypes.byref(f)));k.QueryPerformanceCounter(ctypes.byref(a));time.sleep(.01);k.QueryPerformanceCounter(ctypes.byref(b));self.assertGreater(f.value,0);self.assertGreater(b.value,a.value);self.assertGreater((b.value-a.value)/f.value,.005)
    def test_real_child_cleanup(self):
        root=Path(load(V/'LOCAL_RUN.json')['root']);p=Path(os.environ['SystemRoot'])/'System32/conhost.exe';child=Child(dict(path=str(p),sha256=sha(p)));directory=root/'CPU_TIMEOUT';directory.mkdir(exist_ok=False)
        with self.assertRaises(BaseException):child.run([sys.executable,'-B','-c','import time;time.sleep(5)'],directory/'child',.15,os.environ.copy(),128*1024**2)
        child.terminate();self.assertIsNone(child.active);self.assertIsNone(child.job);self.assertIsNotNone(load(directory/'child.LIFETIME.json')['exit_code'])
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests);result=unittest.TextTestRunner(verbosity=2).run(suite);save(V/'CPU_TESTS.json',dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),GPU_calls=0,independent_external_review=False));sys.exit(not result.wasSuccessful())
