"""Distinct fixed controls are admissible; an attempted slot is never replayed."""
from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import save,sha
from host import confirmation_identity

class ConfirmationIdentity(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.job=self.root/'same-request.json';save(self.job,{'same_original_request_bytes':True})
  self.builds={};self.freeze={'executables':{}}
  for core in ('loop4','packed'):
   p=self.root/(core+'.json');b={'role':core,'executable_sha256':core};save(p,b);self.builds[core]=(p,b)
   self.freeze['executables'][core]={'build':{'sha256':sha(p)}}
  self.workers=[{'id':f's{i//2}-{i%2}','core':('loop4' if i%2==0 else 'packed'),'job':self.job.name,'job_sha256':sha(self.job)} for i in range(24)]
  self.plan=self.root/'PLAN.json';save(self.plan,{'workers':self.workers});self.freeze['plan']={'path':str(self.plan),'sha256':sha(self.plan)}
 def admit(self,i,reserved=(),core=None,out=None):
  w=self.workers[i];p,b=self.builds[core or w['core']]
  return confirmation_identity(self.freeze,p,b,self.job,out or self.root/'runs'/w['id'],reserved)
 def reservation(self,i):
  w=self.workers[i];return {'phase':'confirmation','out':str(self.root/'runs'/w['id']),'job_sha256':sha(self.job)}
 def test_identical_request_different_core_and_slot_are_distinct(self):
  self.assertEqual(self.admit(1,[self.reservation(0)])['confirmation_slot_id'],self.workers[1]['id'])
 def test_identical_request_and_core_in_distinct_declared_sessions_are_distinct(self):
  self.assertEqual(self.admit(2,[self.reservation(0)])['confirmation_slot_id'],self.workers[2]['id'])
 def test_legacy_reservation_blocks_same_slot_without_rewriting_ledger(self):
  with self.assertRaisesRegex(RuntimeError,'already reserved'):self.admit(0,[self.reservation(0)])
 def test_wrong_core_cannot_enter_frozen_slot(self):
  with self.assertRaisesRegex(RuntimeError,'Different numerical core'):self.admit(1,core='loop4')
 def test_new_output_name_cannot_bypass_slot_identity(self):
  with self.assertRaisesRegex(RuntimeError,'Unregistered'):self.admit(0,out=self.root/'runs/retry')
 def test_changed_plan_is_rejected(self):
  self.plan.write_text('{}')
  with self.assertRaisesRegex(RuntimeError,'Frozen plan changed'):self.admit(0)

if __name__=='__main__':unittest.main()
