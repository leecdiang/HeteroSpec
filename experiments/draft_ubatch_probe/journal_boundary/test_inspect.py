import copy,hashlib,json,pathlib,subprocess,sys,tempfile,unittest
from inspect_journal import inspect,derive
ROOT=pathlib.Path(__file__).resolve().parents[1]
PROMPT=[1,2,3,4,5,6,7]
class JournalTests(unittest.TestCase):
 def setUp(self):
  self.path=ROOT/'evidence/stress-q8-attempts.jsonl';self.raw=self.path.read_bytes()
  self.results=[x['result'] for x in map(json.loads,self.raw.splitlines()) if x['status']=='COMPLETED']
 def test_legacy_journals_unchanged(self):
  for name in ['release-q8','release-dense','stress-q8','stress-dense']:
   path=ROOT/'evidence'/(name+'-attempts.jsonl')
   raw=path.read_bytes();before=hashlib.sha256(raw).hexdigest();side=inspect(raw,PROMPT)
   self.assertEqual(side['completed_attempts'],75);self.assertEqual(side['terminal_branch_counts'],{'initial':18,'accepted':27,'bonus':15,'correction':15})
   self.assertEqual(before,hashlib.sha256(path.read_bytes()).hexdigest())
   for item in side['records']:
    a=item['annotation'];self.assertEqual(a['recovery']['status'],'UNPROVEN');self.assertFalse(a['recovery']['resume_authorized'])
    self.assertEqual(len(a['emitted_unconsumed_suffix']),a['terminal_branch']!='accepted')
 def test_does_not_mutate_old_fields(self):
  for r in self.results:
   old=copy.deepcopy(r);derive(r,PROMPT);self.assertEqual(r,old)
 def test_partial_and_unknown(self):
  first=self.raw.splitlines()[0]+b'\n';x=inspect(first,PROMPT);self.assertEqual(x['completed_attempts'],0);self.assertIsNotNone(x['incomplete_attempt'])
  for bad in [b'{"status":"CHECKPOINT"}\n',self.raw.splitlines()[1]+b'\n',first+first]:
   with self.assertRaises(ValueError):inspect(bad,PROMPT)
 def test_initial_retains_unconsumed_output(self):
  r=next(x for x in self.results if not x['cycles']);a=derive(r,PROMPT)
  self.assertEqual(a['logical_committed_prefix_ids'],PROMPT);self.assertEqual(a['emitted_unconsumed_suffix'][0]['id'],r['ids'][-1])
 def test_accepted_does_not_invent_pending(self):
  r=next(x for x in self.results if x['cycles'] and x['cycles'][-1]['last']=='accepted');a=derive(r,PROMPT)
  self.assertIsNone(r['cycles'][-1]['pending']);self.assertEqual(a['emitted_unconsumed_suffix'],[])
  self.assertEqual(a['logical_committed_prefix_ids'],PROMPT+r['ids'])
 def test_wrong_frontier_and_branch_rejected(self):
  r=next(x for x in self.results if x['cycles'])
  for field,value in [('keep',7),('base',0),('last','checkpoint'),('pending',1),('accepted',True),('base',float(r['cycles'][-1]['base'])),('keep',float(r['cycles'][-1]['keep']))]:
   x=copy.deepcopy(r);x['cycles'][-1][field]=value
   with self.assertRaises(ValueError):derive(x,PROMPT)
 def test_endpoint_and_geometry_rejected(self):
  r=next(x for x in self.results if x['cycles'])
  for mutation in ('ids','decisions','proposals'):
   x=copy.deepcopy(r)
   if mutation=='ids':x['ids'][-1]+=1
   else:x['cycles'][-1][mutation].pop()
   with self.assertRaises(ValueError):derive(x,PROMPT)
 def test_prompt_is_explicit_but_not_certified(self):
  different=[9,8,7,6,5,4,3];x=inspect(self.raw,different)
  self.assertEqual(x['prompt_binding_status'],'CALLER_SUPPLIED_NOT_VERIFIED_BY_JOURNAL')
  self.assertEqual(x['records'][0]['annotation']['logical_committed_prefix_ids'],different)
  self.assertEqual(x['recovery_status'],'UNPROVEN')
 def test_cli_never_overwrites_journal(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'journal.jsonl';p.write_bytes(self.raw)
   cmd=[sys.executable,str(ROOT/'journal_boundary/inspect_journal.py'),'--journal',str(p),'--prompt-ids',','.join(map(str,PROMPT)),'--output',str(p)]
   z=subprocess.run(cmd,capture_output=True);self.assertNotEqual(z.returncode,0);self.assertEqual(p.read_bytes(),self.raw)
if __name__=='__main__':unittest.main()
