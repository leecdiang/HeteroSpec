import dataclasses
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from query_layout.state_lineage import Capsule,Deployment,Verification,StateOwner,StateError,Trust,ExactRecipeCache,Checkpoint

D=Deployment('cuda','device','build','runtime','model','reference','dense')
def capsule(**kw):
    v=dict(deployment=D,recipe='scalar',tokens=(1,2),positions=(0,1),pending=(3,),kv=b'KV',initial_logits=b'\0'*16)
    v.update(kw);return Capsule(**v)
def verified(c):return Verification('synthetic-test-only',True,True,True)
class Native:
    def __init__(self):self.value=capsule();self.fail=False;self.partial=False;self.calls=0
    def export(self):return self.value
    def synchronize(self):pass
    def import_full(self,c):
        self.calls+=1
        if self.fail:raise RuntimeError('import failed')
        self.value=dataclasses.replace(c,initial_logits=b'\1'*16) if self.partial else c

class StateTests(unittest.TestCase):
    def setUp(self):self.native=Native();self.owner=StateOwner(self.native,D)
    def clean(self):return self.owner.qualify(verified)
    def admitted(self,**kw):
        args=dict(deployment=D,recipe='scalar',tokens=(1,2),positions=(0,1));args.update(kw)
        return self.owner.admit(**args)
    def test_unknown_not_admitted(self):self.assertFalse(self.admitted())
    def test_clean(self):self.clean();self.assertTrue(self.admitted())
    def test_different_recipe(self):self.clean();self.assertFalse(self.admitted(recipe='bulk'))
    def test_exact_tokens(self):self.clean();self.assertFalse(self.admitted(tokens=(1,3)))
    def test_exact_positions(self):self.clean();self.assertFalse(self.admitted(positions=(1,2)))
    def test_different_build(self):self.clean();self.assertFalse(self.admitted(deployment=dataclasses.replace(D,build='new')))
    def test_policy_switch_does_not_clean(self):
        self.clean();self.owner.invalidate();self.native.value=capsule();self.assertFalse(self.admitted())
    def test_bad_verification(self):
        with self.assertRaises(StateError):self.owner.qualify(lambda c:Verification('x',True,False,True))
        self.assertEqual(self.owner.trust,Trust.TAINTED)
    def test_restore_complete(self):
        self.clean();self.owner.invalidate();self.native.value=capsule(kv=b'bad',pending=(9,));self.owner.restore_checkpoint()
        self.assertEqual(self.native.value,capsule());self.assertTrue(self.admitted())
    def test_restore_import_failure(self):
        self.clean();self.native.fail=True
        with self.assertRaises(RuntimeError):self.owner.restore_checkpoint()
        self.assertEqual(self.owner.trust,Trust.TAINTED)
    def test_restore_logits_mismatch(self):
        self.clean();self.native.partial=True
        with self.assertRaises(StateError):self.owner.restore_checkpoint()
        self.assertEqual(self.owner.trust,Trust.TAINTED)
    def test_no_checkpoint(self):
        with self.assertRaises(StateError):self.owner.restore_checkpoint()
    def test_stale_generation(self):
        self.clean();g=self.owner.generation;self.owner.invalidate();self.owner.restore_checkpoint()
        with self.assertRaises(StateError):self.owner.execute(lambda:True,verified,expected_generation=g)
    def test_execute_success(self):
        self.clean()
        def run():self.native.value=capsule(tokens=(1,2,3),positions=(0,1,2),pending=());return True
        self.owner.execute(run,verified,expected_generation=self.owner.generation)
        self.assertTrue(self.admitted(tokens=(1,2,3),positions=(0,1,2)))
    def test_failed_decode_restored(self):
        self.clean()
        def run():self.native.value=capsule(kv=b'bad');return False
        with self.assertRaises(StateError):self.owner.execute(run,verified,expected_generation=self.owner.generation)
        self.assertEqual(self.native.value,capsule());self.assertTrue(self.admitted())
    def test_late_rejection_restored(self):
        self.clean()
        def run():self.native.value=capsule(kv=b'changed');raise RuntimeError('graph reject')
        with self.assertRaises(RuntimeError):self.owner.execute(run,verified,expected_generation=self.owner.generation)
        self.assertEqual(self.native.value,capsule());self.assertTrue(self.admitted())
    def test_failure_without_restore_stays_tainted(self):
        self.clean()
        with self.assertRaises(StateError):self.owner.execute(lambda:False,verified,expected_generation=self.owner.generation,restore_on_failure=False)
        self.assertEqual(self.owner.trust,Trust.TAINTED)
    def test_two_failures_stay_tainted(self):
        self.clean();self.native.fail=True
        with self.assertRaises(StateError):self.owner.execute(lambda:False,verified,expected_generation=self.owner.generation)
        self.assertEqual(self.owner.trust,Trust.TAINTED)
    def test_failed_output_verification_restores(self):
        self.clean()
        with self.assertRaises(StateError):self.owner.execute(lambda:True,lambda c:Verification('',True,True,True),expected_generation=self.owner.generation)
        self.assertTrue(self.admitted())
    def test_scalar_restores_first(self):
        self.clean();self.owner.invalidate();self.native.value=capsule(kv=b'bad')
        def scalar():self.assertEqual(self.native.value,capsule());return True
        self.owner.scalar_fallback(scalar,verified);self.assertTrue(self.admitted())
    def test_external_mutation_denied(self):
        self.clean();self.native.value=capsule(kv=b'external')
        with self.assertRaises(StateError):self.owner.scalar_fallback(lambda:True,verified)
        self.assertTrue(self.admitted())
        self.assertEqual(self.native.value,capsule())
    def test_reentrant_operation(self):
        self.clean()
        def run():self.owner.restore_checkpoint();return True
        with self.assertRaises(StateError):self.owner.execute(run,verified,expected_generation=self.owner.generation)
    def test_verifier_cannot_clear_invalidation(self):
        self.clean()
        def verify(c):self.owner.invalidate();return verified(c)
        with self.assertRaises(StateError):self.owner.execute(lambda:True,verify,expected_generation=self.owner.generation,restore_on_failure=False)
        self.assertEqual(self.owner.trust,Trust.TAINTED)
    def test_preexport_reentrancy_rejected(self):
        self.clean()
        original=self.native.export
        self.native.export=lambda:self.owner.restore_checkpoint()
        with self.assertRaises(StateError):self.owner.execute(lambda:True,verified,expected_generation=self.owner.generation,restore_on_failure=False)
        self.native.export=original
        self.assertEqual(self.owner.trust,Trust.TAINTED)
    def test_preexport_failure_taints_without_restore(self):
        self.clean()
        def fail():raise RuntimeError('synchronize failed')
        self.native.synchronize=fail
        with self.assertRaises(RuntimeError):self.owner.execute(lambda:True,verified,expected_generation=self.owner.generation,restore_on_failure=False)
        self.assertEqual(self.owner.trust,Trust.TAINTED)
    def test_cache_full_equality(self):
        cache=ExactRecipeCache();cp=self.clean();key=cache.put(cp)
        self.assertEqual(cache.get(key,capsule()),cp)
        for change in ({'recipe':'bulk'},{'kv':b'x'},{'initial_logits':b'\1'*16},{'pending':()},{'deployment':dataclasses.replace(D,model='other')}):
            self.assertIsNone(cache.get(key,capsule(**change)))
    def test_cache_collision_not_authority(self):
        cache=ExactRecipeCache();cp=self.clean();key=cache.put(cp)
        self.assertIsNone(cache.get(key,capsule(tokens=(1,3))))
    def test_invalid_receipt_rejected(self):
        cache=ExactRecipeCache()
        with self.assertRaises(StateError):cache.put(Checkpoint(capsule(),Verification('x',False,True,True),0))
    def test_capsule_validation(self):
        for changes in ({'tokens':[1,2]},{'tokens':(True,2)},{'positions':(0,2)},{'initial_logits':b'12'},{'kv':bytearray(b'kv')}):
            with self.assertRaises(ValueError):capsule(**changes)
    def test_digest_includes_logits_pending_and_recipe(self):
        c=capsule()
        for change in ({'recipe':'bulk'},{'kv':b'x'},{'initial_logits':b'\1'*16},{'pending':()}):
            self.assertNotEqual(c.digest(),capsule(**change).digest())

if __name__=='__main__':unittest.main()
