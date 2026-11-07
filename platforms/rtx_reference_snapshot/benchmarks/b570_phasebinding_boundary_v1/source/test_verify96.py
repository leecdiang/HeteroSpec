"""Synthetic rejection checks for independent auditor, never runs a model."""
import copy,json,pathlib,unittest
import verify96 as v
R=pathlib.Path(__file__).resolve().parent.parent
P=v.read(R/'PLAN.json')
class Rejection(unittest.TestCase):
 def grid(self):
  return [dict(slot=s['slot'],task=s['task'],arm=b['arm'],phase=b['phase'],repeat=b['repeat'],observation_mode=b['observation_mode'],own_bind_sham=b['own_bind_sham'],actual_recipe=P['arms'][b['arm']],paid_formal_latency=False) for b in P['blocks'] for s in b['slots']]
 def native(self,heavy=False):
  for p in sorted((R/'records').glob('*.json')):
   r=v.read(p)
   if (r['observation_mode']=='heavy')==heavy:return v.read(R/r['raw_path']),r
  raise AssertionError('actual evidence required')
 def test_missing_coordinate(self):
  with self.assertRaises(AssertionError):v.coordinates(self.grid()[:-1],P)
 def test_duplicate_coordinate(self):
  rs=self.grid();rs[-1]=copy.deepcopy(rs[0])
  with self.assertRaises(AssertionError):v.coordinates(rs,P)
 def test_fake_physical_width_two(self):
  with self.assertRaises(AssertionError):v.histogram({'2':1},2,2)
 def test_cropped_cap_output(self):
  x,_=self.native();x['ids']=x['ids'][:-1];x['eog']=x['eog'][:-1];x['length']-=1;x['terminal_id']=x['ids'][-1]
  with self.assertRaises(AssertionError):v.endpoint(x)
 def test_no_suffix_cropping_in_equality(self):
  x,_=self.native();y=copy.deepcopy(x);y['ids'][-2]=14 if x['ids'][-2]!=14 else 15
  self.assertNotEqual(v.endpoint(x),v.endpoint(y))
  with self.assertRaises(AssertionError):v.observer_equal([x,y])
 def test_diagnostic_fee_promoted(self):
  rs=self.grid();rs[0]['paid_formal_latency']=True
  with self.assertRaises(AssertionError):v.coordinates(rs,P)
 def test_wrong_owned_memory_pid(self):
  x,r=self.native();e=v.read(R/r['evidence_path']);s=e['samples']
  with self.assertRaises(AssertionError):v.memory(s,x['pid']+1)
 def test_unsigned_or_negative_headroom(self):
  x,r=self.native();e=v.read(R/r['evidence_path']);s=copy.deepcopy(e['samples']);s[0]['heaps'][0]['budget_bytes']=0
  with self.assertRaises(AssertionError):v.memory(s,x['pid'])
 def test_nonfinite_top2_margin(self):
  x,r=self.native(True);x['phase96']['boundaries'][0]['top2_logit']=float('nan');cases={c['id']:c for c in v.read(R/'INPUTS.json')['cases']}
  with self.assertRaises(AssertionError):v.boundarycheck(x,cases[r['task']],r['own_bind_sham'])
 def test_forced_prefix_not_native(self):
  x,r=self.native(True);x['phase96']['boundaries'][0]['naturally_committed_prefix_ids']=[42];cases={c['id']:c for c in v.read(R/'INPUTS.json')['cases']}
  with self.assertRaises(AssertionError):v.boundarycheck(x,cases[r['task']],r['own_bind_sham'])
if __name__=='__main__':unittest.main()
