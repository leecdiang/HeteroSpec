import os,tempfile,unittest
from pathlib import Path
import adapter as a
class Test(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name);self.src=Path(os.environ['S3_ARCHIVE']);a.freeze(self.src,self.p/'inputs');self.r=self.p/'inputs/R_ROOTS.json'
 def tearDown(self):self.t.cleanup()
 def test_tokens(self):self.assertEqual([x['prompt_ids'] for x in a.read(self.r)['inputs']],[x['prompt_ids'] for x in a.read(self.src/'roots/ROOTS.json')['inputs']])
 def test_new(self):
  h=a.read(self.p/'inputs/H_CANDIDATE_ROOTS.json');self.assertEqual(h['later_project_exposure'],'NOT_CHECKED');self.assertFalse({x['id'] for x in h['inputs']}&{x['id'] for x in a.read(self.r)['inputs']})
 def test_bad_token(self):
  for bad in (True,-1,151936,1.2):
   r=a.read(self.r);r['inputs'][0]['prompt_ids'][0]=bad
   with self.assertRaises(ValueError):a.roots_check(r)
 def test_duplicate(self):
  r=a.read(self.r);r['inputs'][1]['prompt_ids']=r['inputs'][0]['prompt_ids']
  with self.assertRaises(ValueError):a.roots_check(r)
 def test_cap(self):
  r=a.read(self.r);r['inputs'][0]['cap']=127
  with self.assertRaises(ValueError):a.roots_check(r)
 def test_counts_abi(self):
  total=0
  for c,d,n in [('R',1,168),('R',2,108),('H',1,168)]:
   rf=self.r if c=='R' else self.p/'inputs/H_CANDIDATE_ROOTS.json';out=self.p/(c+str(d));ws=a.materialize(self.src,rf,c,d,Path('/model'),out);self.assertEqual(sum(w['requests'] for w in ws),n);total+=n
   for w in ws:
    j=a.read(out/w['job'])
    if w['arm']!='R':
     old=a.read(self.src/f"prospective/jobs/s3-v1-panel-root00-r0-{w['arm']}.json")
     self.assertEqual({k:v for k,v in j.items() if k not in ('inputs','target_model')},{k:v for k,v in old.items() if k not in ('inputs','target_model')})
     if w['stage']=='qualification':self.assertEqual([e['capture'] for e in j['inputs']],[True,False])
   self.assertFalse(a.read(out/'MANIFEST.json')['GPU_authorized'])
  self.assertEqual(total,444)
 def test_no_overwrite(self):
  with self.assertRaises(FileExistsError):a.freeze(self.src,self.p/'inputs')
 def test_day(self):
  with self.assertRaises(ValueError):a.materialize(self.src,self.r,'R',3,Path('/m'),self.p/'bad')
 def test_changed_R(self):
  r=a.read(self.r);r['inputs'][0]['prompt_ids'][0]=1;a.save(self.p/'bad.json',r)
  with self.assertRaises(ValueError):a.materialize(self.src,self.p/'bad.json','R',1,Path('/m'),self.p/'bad')
 def test_commands(self):
  out=self.p/'plan';a.materialize(self.src,self.r,'R',2,Path('/m'),out);a.save(self.p/'config',dict(executables={'R':'/missing/R','model':'/missing/model'},gpu_uuid='GPU-test',output_root='/tmp/future'));a.commands(out,self.p/'config',self.p/'commands');self.assertEqual(len(a.read(self.p/'commands')['commands']),56)
if __name__=='__main__':unittest.main()
