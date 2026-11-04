from pathlib import Path
import importlib.util,tempfile,unittest,copy
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('compare',ROOT/'scripts/reference_baselines/compare.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class CompareTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  files={'input_bytes':b'prompt','logits_f32':bytes(5*3*4),'kv_state_bytes':b'kv','continuation_logits_f32':bytes(3*4),'continuation_tokens_i32':bytes(4)}
  arms={}
  for arm in module.ARMS:
   entry={'runtime_binary_sha256':'b'*64,'returncode':0,'fallbacks':0,'observed_marked_nodes':1}
   for name,data in files.items():
    path=arm+'-'+name;(self.root/path).write_bytes(data);entry[name]=path
   arms[arm]=entry
  self.manifest={'status':'executed','provenance':dict(backend='cuda',model_sha256='a'*64,device_uuid='testfixture',driver='driver',toolkit='toolkit',reference_binary_sha256='b'*64,runtime_binary_sha256={arm:'b'*64 for arm in module.ARMS}),
   'cases':[{'id':'synthetic-protocol-fixture','q':5,'vocab':3,'continuation_steps':1,'arms':arms}]}
 def tearDown(self):self.tmp.cleanup()
 def test_equal_fixture(self):self.assertEqual(module.compare(self.manifest,self.root)['status'],'FINITE_CAPTURE_EQUAL')
 def test_bit_difference_rejects(self):
  path=self.root/self.manifest['cases'][0]['arms']['backend_loop4']['logits_f32'];path.write_bytes(b'\x80'+bytes(59));self.assertEqual(module.compare(self.manifest,self.root)['status'],'REJECTED_MISMATCH')
 def test_truncated_rejects(self):
  path=self.root/self.manifest['cases'][0]['arms']['packed']['continuation_tokens_i32'];path.write_bytes(b'x')
  with self.assertRaises(ValueError):module.compare(self.manifest,self.root)
 def test_no_execution_rejects(self):
  self.manifest['status']='not_run'
  with self.assertRaises(ValueError):module.compare(self.manifest,self.root)
 def test_missing_arm_rejects(self):
  del self.manifest['cases'][0]['arms']['packed']
  with self.assertRaises(ValueError):module.compare(self.manifest,self.root)
 def test_fallback_rejects(self):
  self.manifest['cases'][0]['arms']['backend_loop4']['fallbacks']=1
  with self.assertRaises(ValueError):module.compare(self.manifest,self.root)
 def test_no_marked_node_rejects(self):
  self.manifest['cases'][0]['arms']['backend_loop4']['observed_marked_nodes']=0
  with self.assertRaises(ValueError):module.compare(self.manifest,self.root)
 def test_wrong_reference_pin_rejects(self):
  self.manifest['provenance']['reference_binary_sha256']='c'*64
  with self.assertRaises(ValueError):module.compare(self.manifest,self.root)
 def test_wrong_arm_pin_rejects(self):
  self.manifest['cases'][0]['arms']['packed']['runtime_binary_sha256']='c'*64
  with self.assertRaises(ValueError):module.compare(self.manifest,self.root)
 def test_boolean_success_rejects(self):
  self.manifest['cases'][0]['arms']['packed']['returncode']=False
  with self.assertRaises(ValueError):module.compare(self.manifest,self.root)
 def test_wrong_backend_rejects(self):
  self.manifest['provenance']['backend']='cpu'
  with self.assertRaises(ValueError):module.compare(self.manifest,self.root)
if __name__=='__main__':unittest.main()
