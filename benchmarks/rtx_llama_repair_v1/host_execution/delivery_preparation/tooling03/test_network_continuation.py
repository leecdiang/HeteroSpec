import ast,datetime,hashlib,json,pathlib,tempfile,types,unittest
source=pathlib.Path(__file__).with_name('parallel_upload_bounded.py')
tree=ast.parse(source.read_text(encoding='utf-8'));main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');node=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='transfer')
class Checks(unittest.TestCase):
 def scenario(self,codes,matches,error='EOF'):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'commands').mkdir();p=root/'evidence-000.zip';p.write_bytes(b'bound test bytes');events=[];launches=[];clock=[0]
   class Process:
    def __init__(self,args,env,stdout,stderr):self.pid=123;self.code=codes[len(launches)];launches.append(args);stdout.write(error.encode())
    def wait(self,timeout):return self.code
   sub=types.SimpleNamespace(Popen=Process,STDOUT=-2,TimeoutExpired=TimeoutError,run=lambda *a,**k:types.SimpleNamespace(returncode=0,stdout=json.dumps([matches]),stderr=''))
   tm=types.SimpleNamespace(monotonic=lambda:clock[0],sleep=lambda n:clock.__setitem__(0,clock[0]+n))
   ns=dict(sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest(),out=root,deadline=10000,tag='test',repo='test/test',release_id=1,env={},subprocess=sub,read_only_api=sub.run,time=tm,datetime=datetime,json=json,journal=lambda n,e:events.append((n,e)))
   exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(source),'exec'),ns)
   result=ns['transfer'](p);return result,launches,events
 def test_network_absent_then_success(self):
  r,l,e=self.scenario([1,0],[]);self.assertEqual(len(l),2);self.assertEqual(r['exit_code'],0);self.assertEqual([x[1]['exit_code'] for x in e if x[0]=='ATTEMPTS.jsonl'],[1,0])
 def test_existing_object_never_blindly_retried(self):
  r,l,e=self.scenario([1],[{'name':'evidence-000.zip','state':'starter'}]);self.assertEqual(len(l),1);self.assertEqual(r['exit_code'],1)
 def test_non_network_error_not_retried(self):
  r,l,e=self.scenario([1],[],error='HTTP 403');self.assertEqual(len(l),1)
 def test_network_attempts_finite(self):
  r,l,e=self.scenario([1,1,1],[]);self.assertEqual(len(l),3);self.assertEqual(r['exit_code'],1);self.assertFalse(e[-1][1]['retry_only_after_verified_absence'])
 def query_scenario(self,errors,args=None):
  launches=[];events=[];clock=[0]
  def run(*a,**kw):
   error=errors[len(launches)];launches.append(a);return types.SimpleNamespace(returncode=int(bool(error)),stderr=error,stdout='[]' if not error else '')
  node=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='read_only_api')
  ns=dict(deadline=1000,subprocess=types.SimpleNamespace(run=run),time=types.SimpleNamespace(monotonic=lambda:clock[0],sleep=lambda n:clock.__setitem__(0,clock[0]+n)),datetime=datetime,journal=lambda n,e:events.append(e))
  exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(source),'exec'),ns)
  r=ns['read_only_api'](args or ['gh','api','repos/test/test/releases/1'],timeout=120);return r,launches,events
 def test_query_eof_then_success_keeps_failure(self):
  r,l,e=self.query_scenario(['EOF','']);self.assertEqual(r.returncode,0);self.assertEqual([x['exit_code'] for x in e],[1,0])
 def test_three_failed_queries_remain_unknown(self):
  r,l,e=self.query_scenario(['EOF']*3);self.assertEqual(len(l),3);self.assertNotEqual(r.returncode,0)
 def test_mutating_query_rejected_before_launch(self):
  with self.assertRaises(AssertionError):self.query_scenario([''],['gh','api','x','-X','DELETE'])
if __name__=='__main__':unittest.main(verbosity=2)
