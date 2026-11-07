import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import census as c
class Census(unittest.TestCase):
 def test_geometry_bound(self):
  for p in (16,32,64):
   for q in (1,2,4,8,16):
    for h in range(p*2):
     for a in (0,1,3,8,17,31,65,129):
      r=c.calls(h,a,q,p,True);self.assertEqual(sum(r),a);self.assertLessEqual(len(r),(a+q-1)//q+1)
 def test_counterexample_sequences(self):
  self.assertEqual(c.calls(205,84,32,256,False),[32,19,13,20]);self.assertEqual(c.calls(205,84,32,256,True),[32,19,32,1])
 def test_bad_observer(self):
  with self.assertRaises(ValueError):c.census({'rows':[]})
 def test_census(self):
  x={'no_latency_selection':True,'history_origin':'provided_conversation','source_sha256':'x','tokenizer_sha256':'y','rows':[dict(root='r',turn=1,dense_seq0=True,head_observed=True,head=255,append=65,q=32,padding=256)]}
  y=c.census(x);self.assertEqual(y['turns'],1);self.assertTrue(y['rows'][0]['active_local_split'])
 def test_prediction_is_not_native(self):
  x={'no_latency_selection':True,'history_origin':'provided_conversation','source_sha256':'x','tokenizer_sha256':'y','rows':[dict(root='r',turn=1,dense_seq0=True,head_source='token_geometry_prediction',head=255,append=65,q=32,padding=256)]}
  y=c.census(x);self.assertEqual(y['predicted_only_turns'],1)
 def test_unsupported_in_denominator(self):
  x={'no_latency_selection':True,'history_origin':'provided_conversation','source_sha256':'x','tokenizer_sha256':'y','rows':[dict(root='r',turn=1,dense_seq0=False)]}
  y=c.census(x);self.assertEqual(y['turns'],1);self.assertEqual(y['eligible_geometry_turns'],0)
if __name__=='__main__':unittest.main()
