import json
from pathlib import Path
import tempfile
import unittest
import adapter as a

class AdapterTests(unittest.TestCase):
    def context(self,q=4):return dict(layer=31,phase='continuation',q=q,min_key=128 if q in (2,4) else 0)
    def body(self):return dict(prompt=[1,2,3],n_predict=128,cache_prompt=False,hs_closeout_mode='heavy')
    def test_all_selectors_survive_real_sanitizer_and_serialization(self):
        for q in (1,2,3,4):
            c=self.context(q);env=a.clean_environment(dict(HS_E1_LAYER='WRONG',CUDA_VISIBLE_DEVICES='0',HS_UNAPPROVED='x',PATH='kept'),0,Path('case/trace.jsonl'),c)
            self.assertNotIn('CUDA_VISIBLE_DEVICES',env);self.assertNotIn('HS_UNAPPROVED',env)
            self.assertEqual(env['PATH'],'kept');self.assertEqual({k:env[k] for k in a.NAMES},a.selectors(c))
            binding=a.serialized_binding(self.body(),json.loads(json.dumps(c)),env)
            self.assertEqual(json.loads(binding['wire_utf8']),self.body())
    def test_lost_or_poisoned_selector_fails_before_request(self):
        c=self.context();env=a.clean_environment({},0,Path('trace'),c)
        for name in a.NAMES:
            bad=env.copy();bad.pop(name)
            with self.assertRaises(ValueError):a.serialized_binding(self.body(),c,bad)
    def test_illegal_coordinate_or_repaired_capture_rejected(self):
        for key,value in [('layer',256),('phase','other'),('q',5),('min_key',0)]:
            c=self.context();c[key]=value
            with self.assertRaises(ValueError):a.selectors(c)
        with self.assertRaises(ValueError):a.clean_environment({},3,Path('x'),self.context())
    def test_q1_is_ordinary_negative_control(self):
        c=a.condition(self.context(1));self.assertFalse(c['spec']);self.assertEqual(c['prefill_ub'],1);self.assertEqual(c['maximum_k'],0)
    def test_cache_or_mode_mismatch_rejected(self):
        c=self.context();env=a.clean_environment({},0,Path('x'),c)
        for key,value in [('cache_prompt',True),('hs_closeout_mode','lite')]:
            b=self.body();b[key]=value
            with self.assertRaises(ValueError):a.serialized_binding(b,c,env)
if __name__=='__main__':unittest.main(verbosity=2)
