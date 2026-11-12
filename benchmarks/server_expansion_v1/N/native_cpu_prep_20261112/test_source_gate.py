import tempfile,unittest
from pathlib import Path
from source_gate import inspect,FROZEN
class Test(unittest.TestCase):
 def test_missing_closed(self):
  r=inspect({});self.assertEqual(r['gpu_admission'],'DENIED');self.assertTrue(all(x['status']=='MISSING' for x in r['sources'].values()))
 def test_mismatch_closed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'reference.cpp';p.write_text('not the reference')
   r=inspect({'reference_frontend':str(p)});self.assertEqual(r['sources']['reference_frontend']['status'],'IDENTITY_CONFLICT');self.assertFalse(r['native_reference_qualified'])
if __name__=='__main__':unittest.main()
