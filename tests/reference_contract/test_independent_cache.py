import sys, dataclasses, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from query_layout.state_lineage import *
d=Deployment('cpu','device','build','runtime','model','ref','dense')
receipt=Verification('synthetic-independent-test',True,True,True)
def capsule(**changes):
 v=dict(deployment=d,recipe='r',tokens=(1,2),positions=(0,1),pending=(3,),kv=b'KV',initial_logits=b'\0'*8);v.update(changes);return Capsule(**v)
class Adapter:
 def __init__(self):self.value=capsule();self.behavior=lambda c:c;self.exports=0
 def synchronize(self):pass
 def export(self):self.exports+=1;return self.value
 def import_full(self,c):self.value=self.behavior(c)
class Checks(unittest.TestCase):
 def setUp(self):
  self.a=Adapter();self.o=StateOwner(self.a,d);self.old=self.o.qualify(lambda c:receipt)
  self.new=Checkpoint(capsule(tokens=(4,5),kv=b'NEW'),receipt,1000);self.ident=CacheIdentity.from_capsule(self.new.capsule)
 def test_all_import_fields(self):
  changes=[{'deployment':dataclasses.replace(d,model='other')},{'recipe':'other'},{'tokens':(1,9)},{'positions':(1,2)},{'pending':(4,)},{'kv':b'broken'},{'initial_logits':b'\1'*8}]
  for change in changes:
   with self.subTest(change=change):
    self.a.behavior=lambda c:dataclasses.replace(c,**change)
    with self.assertRaises(StateError):self.o.restore_cached_checkpoint(self.new,self.ident)
    self.assertIs(self.o.trust,Trust.TAINTED);self.assertEqual(self.o.current,self.old.capsule)
    self.a.behavior=lambda c:c;self.o.restore_checkpoint();self.assertEqual(self.o.current,self.old.capsule)
 def test_exception_every_boundary(self):
  for boundary in ('import_full','synchronize','export'):
   with self.subTest(boundary=boundary):
    original=getattr(self.a,boundary)
    def broken(*args):raise RuntimeError('independent fault')
    setattr(self.a,boundary,broken)
    with self.assertRaises(RuntimeError):self.o.restore_cached_checkpoint(self.new,self.ident)
    self.assertIs(self.o.trust,Trust.TAINTED);self.assertEqual(self.o.current,self.old.capsule)
    setattr(self.a,boundary,original);self.o.restore_checkpoint();self.assertEqual(self.o.current,self.old.capsule)
 def test_reentrant_import(self):
  self.a.behavior=lambda c:self.o.restore_cached_checkpoint(self.new,self.ident)
  with self.assertRaises(StateError):self.o.restore_cached_checkpoint(self.new,self.ident)
  self.assertIs(self.o.trust,Trust.TAINTED)
 def test_monotone_generation_on_cache_restore(self):
  old=self.o.generation;self.o.restore_cached_checkpoint(self.new,self.ident)
  self.assertEqual(self.o.generation,old+1)
  with self.assertRaises(StateError):self.o.execute(lambda:True,lambda c:receipt,expected_generation=old)
 def test_quarantine_covers_all_state_conflicts(self):
  for change in ({'kv':b'bad'},{'initial_logits':b'\1'*8}):
   cache=PrefixCheckpointCache();cache.put(self.new)
   with self.assertRaises(StateError):cache.put(dataclasses.replace(self.new,capsule=dataclasses.replace(self.new.capsule,**change)))
   self.assertIsNone(cache.get(self.ident))
 def test_receipt_duplicate_retains_first_verified(self):
  cache=PrefixCheckpointCache();cache.put(self.new)
  duplicate=dataclasses.replace(self.new,verification=Verification('other-trusted',True,True,True),generation=50000)
  cache.put(duplicate);self.assertEqual(cache.get(self.ident),self.new)
if __name__=='__main__':unittest.main(verbosity=2)
