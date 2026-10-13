import unittest,copy,json,math,struct,tempfile,hashlib
from pathlib import Path
import verify98 as v
ROOT=Path(__file__).resolve().parents[1]
class RejectMalformedEvidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  rs=v.load(ROOT/'STUDY_RECORDS.json')
  r=next(r for r in rs if r['arm']=='B' and r['repeat']==1 and r['task']=='GSM8K/test/831')
  cls.x=v.load(ROOT/r['raw_path']);cls.trace=v.load(ROOT/r['evidence_path']);cls.ids=cls.x['prompt_ids'];cls.pid=cls.x['pid']
 def ep(self,x):v.endpoint(x,self.ids,512,self.pid)
 def test_missing_coordinate(self):
  with self.assertRaises(AssertionError):v.compare_slots(['a'],['a','b'])
 def test_duplicate_coordinate(self):
  with self.assertRaises(AssertionError):v.compare_slots(['a','a'],['a','b'])
 def test_cropped_CAP_suffix(self):
  x=copy.deepcopy(self.x);x['ids']=x['ids'][:-1];x['eog']=x['eog'][:-1];x['length']-=1;x['terminal_id']=x['ids'][-1]
  with self.assertRaises(AssertionError):self.ep(x)
 def test_wrong_owned_PID(self):
  x=copy.deepcopy(self.x);x['pid']+=1
  with self.assertRaises(AssertionError):self.ep(x)
 def test_extra_intermediate_logits_request(self):
  t=copy.deepcopy(self.trace);t['target'][0]['logits_requested_positions']=[127]
  with self.assertRaises(AssertionError):v.geometry(t,self.x,self.ids,512,128)
 def test_false_width(self):
  t=copy.deepcopy(self.trace);t['target'][0]['physical_width_hist']={'64':2}
  with self.assertRaises(AssertionError):v.geometry(t,self.x,self.ids,512,128)
 def test_shifted_KV_position(self):
  t=copy.deepcopy(self.trace);t['target'][0]['kv_max']+=1
  with self.assertRaises(AssertionError):v.geometry(t,self.x,self.ids,512,128)
 def test_changed_output_reservation(self):
  x=copy.deepcopy(self.x);x['actual_condition']['output_capacity']=4
  with self.assertRaises(AssertionError):self.ep(x)
 def test_wrong_signed_headroom(self):
  m=copy.deepcopy(self.trace['memory']['samples'][0]);m['device_local_headroom_bytes']=-1
  with self.assertRaises(AssertionError):v.memory(m,self.pid)
 def test_nonfinite_logits_payload(self):
  b=struct.pack('<128256f',*([0.0]*128255+[float('nan')]))
  with self.assertRaises(AssertionError):v.top2(b)
 def test_invalid_KV_serialization_header(self):
  p=self.x['partition98']['full_payloads']['0']['sequence_KV'];b=bytearray(v.payload(ROOT,p));b[0]^=1
  with self.assertRaises(AssertionError):v.parse_kv(b,len(self.ids))
 def test_tampered_full_raw_payload(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'receipts') as d:
   r=Path(d);(r/'payload').write_bytes(b'changed')
   with self.assertRaises(AssertionError):v.payload(r,dict(path='payload',bytes=7,sha256=hashlib.sha256(b'correct').hexdigest()))
if __name__=='__main__':unittest.main(verbosity=2)
