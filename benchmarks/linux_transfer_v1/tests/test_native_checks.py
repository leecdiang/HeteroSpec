"""Regression checks for the host adapter, never native-model qualification."""
from pathlib import Path
import sys, tempfile, unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from native_checks import vector_pair, legacy_readers

class NativeAdapterChecks(unittest.TestCase):
 def test_one_ulp_is_a_failure(self):
  with tempfile.TemporaryDirectory() as d:
   a,b=Path(d)/'actual.f32',Path(d)/'reference.f32'
   values=np.array([1.,-1.],dtype='<f4');b.write_bytes(values.tobytes())
   values[0]=np.nextafter(values[0],np.float32(2.));a.write_bytes(values.tobytes())
   result=vector_pair(a,b,2)
   self.assertFalse(result['equal']);self.assertEqual(result['first_difference']['actual_bits']-result['first_difference']['reference_bits'],1)

 def test_identical_nonfinite_bytes_are_not_a_pass(self):
  with tempfile.TemporaryDirectory() as d:
   a,b=Path(d)/'a.f32',Path(d)/'b.f32';raw=np.array([np.nan,1.],dtype='<f4').tobytes();a.write_bytes(raw);b.write_bytes(raw)
   with self.assertRaises(RuntimeError):vector_pair(a,b,2)

 def test_reviewed_import_route_preserves_pending_contract(self):
  trace,_=legacy_readers(Path(__file__).resolve().parents[3])
  row={'ids':[3,4,5],'cycles':[],'draft_enabled':False,'k':0,'stop_reason':'CAP','study_cap':3}
  _,actual=trace(row,[1,2],8,[7],'rtx')
  self.assertEqual(actual['states'][-1]['prefix'],[1,2,3,4]);self.assertEqual(actual['states'][-1]['unmaterialized_suffix'],[5])
  self.assertTrue(actual['states'][-1]['terminal'])

if __name__=='__main__':unittest.main()
