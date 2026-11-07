import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from recipe_inventory import review
class Types(unittest.TestCase):
 def inv(self):return dict(tensor_type_counts={'12':1},tensors=[dict(name='q',shape=[32,32],type=12)])
 def test_missing_recipe(self):self.assertEqual(review(self.inv(),{'recipes':{}})['tensors'][0]['status'],'NO_RECIPE')
 def test_recipe_is_not_proof(self):self.assertFalse(review(self.inv(),{'recipes':{'12':dict(source_sha256='abc',activation_input='F32')}})['numeric_qualified'])
 def test_incomplete(self):
  with self.assertRaises(ValueError):review(self.inv(),{'recipes':{'12':{'source_sha256':'abc'}}})
if __name__=='__main__':unittest.main()
