import pathlib, unittest, hashlib, tempfile, subprocess, sys
from stage import stage, PIN
ROOT=pathlib.Path(__file__).resolve().parent
class StageTests(unittest.TestCase):
 def setUp(self): self.src=(ROOT/'frozen-worker.cpp').read_bytes().decode('utf-8')
 def test_exact_source(self): self.assertEqual(hashlib.sha256(self.src.encode()).hexdigest(),PIN)
 def test_unknown_refused(self):
  for bad in ('',self.src+'\n',self.src.replace('d,1,false','d,4,false')):
   with self.assertRaises(ValueError):stage(bad,2)
 def test_crlf_cli_refused(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'worker.cpp').write_bytes(self.src.replace('\n','\r\n').encode())
   result=subprocess.run([sys.executable,str(ROOT/'stage.py'),'--worker',str(p/'worker.cpp'),'--draft-ubatch','2','--output',str(p/'out')],capture_output=True)
   self.assertNotEqual(result.returncode,0);self.assertIn(b'unexpected worker bytes',result.stderr);self.assertFalse((p/'out').exists())
 def test_width_refused(self):
  for ub in (-1,0,3,8):
   with self.assertRaises(ValueError):stage(self.src,ub)
 def test_target_context_unchanged(self):
  for ub in (1,2,4):
   out=stage(self.src,ub)
   context=out.split('struct Context {')[1].split('struct Pair ')[0]
   context=context.replace('const fs::path&dir,int layout,int draft_physical=1):model(m)','const fs::path&dir,int layout):model(m)').replace('p.n_ubatch=istarget?ub:draft_physical;','p.n_ubatch=ub;')
   self.assertEqual(self.src.split('struct Context {')[1].split('struct Pair ')[0],context)
   self.assertEqual([s for s in self.src.splitlines() if 'std::make_unique<Context>(t,' in s],[s for s in out.splitlines() if 'std::make_unique<Context>(t,' in s])
 def test_protocol_unchanged(self):
  for ub in (1,2,4):
   out=stage(self.src,ub)
   a='    double setup=since(start);';b='    llama_synchronize(target->c);'
   self.assertEqual(self.src.split(a)[1].split(b)[0],out.split(a)[1].split(b)[0])
 def test_two_constructors_only(self):
  for ub in (1,2,4):
   out=stage(self.src,ub);self.assertEqual(out.count('std::make_unique<Context>(d,1,false,false'),2)
   self.assertEqual(out.count('spec.selector,draft_ubatch);'),2)
 def test_independent_study_and_bindings(self):
  for ub in (1,2,4):
   out=stage(self.src,ub)
   for anchor in ('slot.at("draft_ubatch")==draft_ubatch','plan.at("context").at("draft_ubatch")==draft_ubatch','identity.at("draft_ubatch")==draft_ubatch','int(llama_n_ubatch(draft->c))==draft_ubatch','rtx_draft_ubatch_probe_v1'):self.assertIn(anchor,out)
   self.assertNotIn('"rtx_scope_transfer_v1"',out)
 def test_retention_and_identity_unchanged(self):
  out=stage(self.src,4)
  for line in self.src.splitlines():
   if any(x in line for x in ('hash_file(', 'result["requests"].push_back','host stopped after retained request','ACTIVE_SLOT.json')):self.assertIn(line,out)
if __name__=='__main__':unittest.main()
