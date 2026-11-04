import dataclasses
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from query_layout.state_lineage import Capsule,Deployment,Verification,Checkpoint,CacheIdentity,PrefixCheckpointCache,StateError,StateOwner,Trust
D=Deployment('cpu','device','build','runtime','model','reference','dense')
def checkpoint(**changes):
    v=dict(deployment=D,recipe='frozen-scalar',tokens=(1,2),positions=(0,1),pending=(3,),kv=b'state',initial_logits=b'\0'*16)
    v.update(changes)
    return Checkpoint(Capsule(**v),Verification('test-only',True,True,True),1)
class PrefixCacheTests(unittest.TestCase):
    def test_lookup_without_kv(self):
        c=PrefixCheckpointCache();cp=checkpoint();c.put(cp)
        identity=CacheIdentity(D,'frozen-scalar',(1,2),(0,1),(3,))
        self.assertEqual(c.get(identity),cp)
    def test_identity_components(self):
        c=PrefixCheckpointCache();cp=checkpoint();c.put(cp);i=CacheIdentity.from_capsule(cp.capsule)
        for change in [dict(recipe='wide'),dict(tokens=(1,4)),dict(positions=(1,2)),dict(pending=(4,)),dict(deployment=dataclasses.replace(D,build='new'))]:
            self.assertIsNone(c.get(dataclasses.replace(i,**change)))
    def test_full_identity_after_hash_collision(self):
        c=PrefixCheckpointCache();a=checkpoint();b=checkpoint(tokens=(4,5))
        with patch.object(CacheIdentity,'digest',return_value='collision'):
            c.put(a);c.put(b)
            self.assertEqual(c.get(CacheIdentity.from_capsule(a.capsule)),a)
            self.assertEqual(c.get(CacheIdentity.from_capsule(b.capsule)),b)
            self.assertIsNone(c.get(CacheIdentity(D,'frozen-scalar',(6,7),(0,1),(3,))))
    def test_conflicting_state_quarantined(self):
        c=PrefixCheckpointCache();cp=checkpoint();c.put(cp)
        with self.assertRaises(StateError):c.put(checkpoint(kv=b'different'))
        self.assertIsNone(c.get(CacheIdentity.from_capsule(cp.capsule)))
        with self.assertRaises(StateError):c.put(cp)
    def test_duplicate_and_unrelated_identity(self):
        c=PrefixCheckpointCache();cp=checkpoint();self.assertEqual(c.put(cp),c.put(cp))
        other=checkpoint(recipe='different');c.put(other)
        self.assertEqual(c.get(CacheIdentity.from_capsule(other.capsule)),other)
    def test_unverified_rejected(self):
        c=PrefixCheckpointCache();cp=dataclasses.replace(checkpoint(),verification=Verification('',False,False,False))
        with self.assertRaises(StateError):c.put(cp)
    def test_invalid_identity(self):
        for args in [(D,'',(1,),(0,),()),(D,'x',[1],(0,),()),(D,'x',(1,2),(0,2),()),(D,'x',(1,),(0,),(-1,)),('wrong','x',(),(),())]:
            with self.assertRaises(ValueError):CacheIdentity(*args)
    def test_corrupt_stored_integrity(self):
        c=PrefixCheckpointCache();cp=checkpoint();key=c.put(cp)
        identity,stored,_=c._items[key][0];c._items[key][0]=(identity,stored,'corrupt')
        with self.assertRaises(StateError):c.get(identity)
        self.assertIsNone(c.get(identity))
class CacheImportTests(unittest.TestCase):
    class Adapter:
        def __init__(self):self.value=checkpoint().capsule;self.partial=False
        def synchronize(self):pass
        def export(self):return self.value
        def import_full(self,c):self.value=dataclasses.replace(c,kv=b'bad') if self.partial else c
    def setUp(self):
        self.adapter=self.Adapter();self.owner=StateOwner(self.adapter,D)
        self.owner.qualify(lambda c:Verification('test-only',True,True,True))
        self.old=self.owner.current
        self.hit=checkpoint(tokens=(4,5),kv=b'other')
        self.identity=CacheIdentity.from_capsule(self.hit.capsule)
    def test_successful_import_commits(self):
        result=self.owner.restore_cached_checkpoint(self.hit,self.identity)
        self.assertEqual(result,self.hit.capsule);self.assertIs(self.owner.trust,Trust.CLEAN)
        self.assertTrue(self.owner.admit(deployment=D,recipe=self.identity.recipe,tokens=(4,5),positions=(0,1)))
    def test_failed_import_preserves_recovery_checkpoint(self):
        self.adapter.partial=True
        with self.assertRaises(StateError):self.owner.restore_cached_checkpoint(self.hit,self.identity)
        self.assertIs(self.owner.trust,Trust.TAINTED)
        self.adapter.partial=False;self.owner.restore_checkpoint()
        self.assertEqual(self.owner.current,self.old)
    def test_wrong_identity_no_mutation(self):
        with self.assertRaises(StateError):self.owner.restore_cached_checkpoint(self.hit,dataclasses.replace(self.identity,recipe='wrong'))
        self.assertEqual(self.adapter.value,self.old);self.assertIs(self.owner.trust,Trust.CLEAN)


class FailureTaintTests(unittest.TestCase):
    def setUp(self):
        self.adapter=CacheImportTests.Adapter();self.owner=StateOwner(self.adapter,D)
        self.owner.qualify(lambda c:Verification('test-only',True,True,True))
    def resurrect_then_fail(self):
        self.owner.trust=Trust.CLEAN
        self.adapter.value=dataclasses.replace(self.adapter.value,kv=b'changed')
        return False
    def test_execute_false_and_exception_preserve_taint(self):
        for throws in (False,True):
            self.owner.restore_checkpoint()
            def operation():
                self.resurrect_then_fail()
                if throws:raise RuntimeError('late exception')
                return False
            with self.assertRaises((RuntimeError,StateError)):
                self.owner.execute(operation,lambda c:Verification('test-only',True,True,True),
                                   expected_generation=self.owner.generation,restore_on_failure=False)
            self.assertIs(self.owner.trust,Trust.TAINTED)
    def test_qualify_verifier_failure_preserves_taint(self):
        def verify(c):
            self.owner.trust=Trust.CLEAN
            return Verification('',False,False,False)
        with self.assertRaises(StateError):self.owner.qualify(verify)
        self.assertIs(self.owner.trust,Trust.TAINTED)
    def test_both_restore_failures_preserve_taint(self):
        cp=checkpoint();identity=CacheIdentity.from_capsule(cp.capsule)
        def fail(c):
            self.owner.trust=Trust.CLEAN
            raise RuntimeError('partial import')
        self.adapter.import_full=fail
        with self.assertRaises(RuntimeError):self.owner.restore_checkpoint()
        self.assertIs(self.owner.trust,Trust.TAINTED)
        with self.assertRaises(RuntimeError):self.owner.restore_cached_checkpoint(cp,identity)
        self.assertIs(self.owner.trust,Trust.TAINTED)

if __name__=='__main__':unittest.main()
