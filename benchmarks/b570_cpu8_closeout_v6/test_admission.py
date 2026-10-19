import hashlib,json,unittest
from admission import *
def event(i,operation,request,response):
 return json.dumps(dict(call_id=str(i),invocation_id='run-1',operation=operation,request=request,response=response),sort_keys=True).encode()
class Guards(unittest.TestCase):
 def setUp(self):
  self.intent={'invocation_id':'run-1','request':{'cmd':'exact','workdir':'D:/new','login':False}}
  self.events=[event(1,'exec',self.intent['request'],{'session_id':12,'output':''}),event(2,'poll',{'session_id':12},{'exit_code':0,'output':'real output'})]
 def check_events(self,events):return bind_invocation(self.intent,events,list(map(digest,events)))
 def test_actual_chain(self):self.assertEqual(self.check_events(self.events)['output'],'real output')
 def test_fabricated_receipt_cannot_replace_export(self):
  altered=self.events.copy();altered[-1]=altered[-1].replace(b'real output',b'fake output')
  with self.assertRaises(ValueError):bind_invocation(self.intent,altered,list(map(digest,self.events)))
 def test_wrong_command_or_session(self):
  for bad in [self.events[0].replace(b'exact',b'wrong'),self.events[1].replace(b'12',b'13')]:
   e=self.events.copy();e[0 if b'wrong' in bad else 1]=bad
   with self.assertRaises(ValueError):self.check_events(e)
 def test_incomplete_and_duplicate(self):
  for e in [self.events[:1],self.events+[self.events[-1]]]:
   with self.assertRaises(ValueError):self.check_events(e)
 def test_original_root_no_relocation_bypass(self):
  self.assertEqual(role_guard('reconstruct','D:/old','D:/old'),'RECONSTRUCTION_ONLY')
  with self.assertRaises(ValueError):role_guard('live','D:/copy','D:/old')
 def test_development_preserves_execution_and_delivery(self):
  reserve('development',14000,400,100,10)
  with self.assertRaises(ValueError):reserve('development',14401,0,100,10)
  with self.assertRaises(ValueError):reserve('development',True,0,100,10)
 def test_pending_is_not_pass(self):
  kw=dict(mode='live',live_budget_checked=True,cases=[{'id':x,'native_qualified':True} for x in CASES],review_clean=True,delivery_verified=False,tool_bound=True)
  self.assertEqual(final_gate(**kw),'CPU8_CASES_PASS_DELIVERY_PENDING')
  kw['delivery_verified']=True;self.assertEqual(final_gate(**kw),'CPU8_INTEGRATION_PASS')
  kw['mode']='reconstruct';self.assertEqual(final_gate(**kw),'RECONSTRUCTION_ONLY')
  kw['mode']='live';kw['live_budget_checked']=False
  with self.assertRaises(ValueError):final_gate(**kw)
 def test_download_and_missing_case(self):
  b=b'actual response body';sha=digest(b);git=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
  self.assertEqual(bind_download(b,git,sha,len(b)),sha)
  with self.assertRaises(ValueError):bind_download(b+b'!',git,sha,len(b))
  with self.assertRaises(ValueError):final_gate(mode='live',live_budget_checked=True,cases=[],review_clean=True,delivery_verified=True,tool_bound=True)
if __name__=='__main__':unittest.main()
