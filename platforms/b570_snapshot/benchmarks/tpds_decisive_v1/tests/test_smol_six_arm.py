"""Six-control secondary design: known ratios and rejection of partial panels."""
import copy,math,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import design
from analyze import analyze
from common import digest

class SixArmAnalysis(unittest.TestCase):
 def test_known_all_control_ratios_and_partial_rejection(self):
  lane='b570-smol-draft';arms=['M','H1','C1U1','C4U1','C4U2','C4U4']
  self.assertNotIn(lane,design.ARMS)
  design.ARMS[lane]=arms;design.SESSIONS[lane]=6
  try:
   panel={'development':[{'id':'dev','root_id':'dev'}],'test':[{'id':str(i),'root_id':'root'+str(i)} for i in range(12)]}
   plan=design.schedule(panel,lane);self.assertEqual(len(plan['slots']),864)
   records={'panel_sha256':digest(panel),'lane':lane,'frozen_before_test':True,'qualification_status':'FINITE_NATIVE_CAPTURE_MATCH','source_freeze_sha256':'a'*64,'numeric_profile_sha256':'b'*64,'records':[]}
   for x in plan['slots']:records['records'].append(dict(x,status='COMPLETE',endpoint_equal=True,fallback_count=0,source_freeze_sha256='a'*64,numeric_profile_sha256='b'*64,service_s=float(arms.index(x['arm'])+1),endpoint_sha256=digest(x['root_id'])))
   result=analyze(panel,lane,records,100)
   self.assertEqual((result['independent_roots'],result['measurements'],result['warmups'],len(result['contrasts'])),(12,432,432,15))
   self.assertEqual(result['best_fixed_by_primary'],'M')
   for c in result['contrasts']:
    expected=(arms.index(c['numerator'])+1)/(arms.index(c['denominator'])+1)
    for key in ('total_service_ratio','paired_geometric_ratio'):self.assertTrue(math.isclose(c[key],expected,rel_tol=1e-12))
    for key in ('total_family95','geometric_family95'):self.assertTrue(all(math.isclose(v,expected,rel_tol=1e-12) for v in c[key]))
   partial=copy.deepcopy(records);partial['records'].pop()
   with self.assertRaises(ValueError):analyze(panel,lane,partial,100)
  finally:del design.ARMS[lane];del design.SESSIONS[lane]

if __name__=='__main__':unittest.main()
