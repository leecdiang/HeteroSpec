import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cost_gate import summarize
class Costs(unittest.TestCase):
 def test_upper_bound(self):
  x=summarize([dict(root='r',service_s=10.,target_prefill_s=5.,draft_prefill_s=1.,draft_total_s=2.)])['rows'][0]
  self.assertEqual(x['ideal_service_s'],9.);self.assertEqual(x['capacity_time_ratio'],1.8)
 def test_null(self):self.assertIsNone(summarize([dict(root='r',service_s=10.)])['coverage']['total_s'])
 def test_invalid(self):
  with self.assertRaises(ValueError):summarize([dict(root='r',service_s=10.,target_prefill_s=5.,draft_prefill_s=3.,draft_total_s=2.)])
 def test_overlapping_components_rejected(self):
  with self.assertRaises(ValueError):summarize([dict(root='r',service_s=10.,target_prefill_s=9.,draft_prefill_s=1.,draft_total_s=2.)])
if __name__=='__main__':unittest.main()
