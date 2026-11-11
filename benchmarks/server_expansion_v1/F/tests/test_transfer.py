import sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from transfer_check import classify
class Transfer(unittest.TestCase):
 def baseline(self):return dict(rule_files={'rule.hpp':'a'},backend_files={'mmvq.cu':'b'},model_sha256='qwen')
 def test_unchanged(self):
  a=self.baseline();b=copy.deepcopy(a);b['model_sha256']='llama';self.assertTrue(classify(a,b)['zero_modification_claim_allowed'])
 def test_extended(self):
  a=self.baseline();b=copy.deepcopy(a);b['rule_files']['rule.hpp']='c';self.assertFalse(classify(a,b)['zero_modification_claim_allowed'])
 def test_missing(self):
  with self.assertRaises(ValueError):classify({},self.baseline())
if __name__=='__main__':unittest.main()
