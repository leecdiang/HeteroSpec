"""CPU-only prospective OFF cohort identity/count/order tests."""
import copy,unittest
from producer_rtx import make_producer_plan
from plan import make_plan,validate
class Producer(unittest.TestCase):
    def test_full_plan_counts(self):
        p=make_producer_plan(make_plan());self.assertEqual(len(p['tasks']),176);self.assertEqual(sum(t['warmups']+t['measured_calls'] for t in p['tasks']),5968);self.assertEqual(p['counts']['reference']['hosts'],16);self.assertEqual(p['counts']['producer_qualification']['hosts'],32);self.assertEqual(p['counts']['producer']['hosts'],128)
    def test_no_change_to_core(self):
        old=make_plan();saved=copy.deepcopy(old);p=make_producer_plan(old);self.assertEqual(old,saved);self.assertNotEqual(old['plan_sha256'],p['plan_sha256']);self.assertEqual(p['parent_B0_plan_sha256'],old['plan_sha256'])
    def test_uniform_off_and_distinct_ids(self):
        old=make_plan();p=make_producer_plan(old);self.assertEqual({t['graph_mode'] for t in p['tasks']},{'OFF'});self.assertFalse(set(t['task_id'] for t in old['tasks'])&set(t['task_id'] for t in p['tasks']));validate(p)
    def test_mutation_rejected(self):
        p=make_producer_plan(make_plan());p['tasks'][0]['graph_mode']='ON'
        with self.assertRaises(ValueError):validate(p)
if __name__=='__main__':unittest.main(verbosity=2)
