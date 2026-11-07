import collections
import unittest
from plan import build,visibility

class PlanTests(unittest.TestCase):
    def test_logical_visibility_not_physical(self):
        base=visibility(1023,1023,2)
        for physical in (1024,1025):
            padded=visibility(1023,physical,2)
            self.assertEqual([r[:1023] for r in padded],base)
            self.assertTrue(all(not any(r[1023:]) for r in padded))
        self.assertEqual(list(map(sum,base)),[1022,1023])
        self.assertNotEqual(visibility(1024,1024,2)[0][:1023],base[0])
    def test_invalid(self):
        for args in [(True,1024,2),(1024,1023,2),(1,1,2),(1,4097,1)]:
            with self.assertRaises(ValueError):visibility(*args)
    def test_budget_identity_and_determinism(self):
        p=build();self.assertEqual(p,build());j=p['timed_jobs']
        self.assertEqual(len(j),256);self.assertEqual(len({r['task_id'] for r in j}),256)
        self.assertEqual(sum(r['calls']+r['warmups'] for r in j)+48*34+40,11400)
    def test_each_session_position_and_carryover_balance(self):
        p=build()
        for c in p['cells']:
            for s in (0,1):
                rows=[r for r in p['timed_jobs'] if r['cell']==c['id'] and r['session']==s]
                positions=collections.Counter((r['arm'],r['slot']) for r in rows)
                self.assertEqual(len(positions),16);self.assertEqual(set(positions.values()),{1})
                edges=[]
                for b in range(s*4,s*4+4):
                    order=[r['arm'] for r in rows if r['block']==b]
                    edges.extend(zip(order,order[1:]))
                self.assertEqual(len(set(edges)),12)
    def test_duplicate_controls_and_physical_intervention(self):
        for c in build()['cells']:
            a,b=c['arms'][:2]
            self.assertEqual({k:v for k,v in a.items() if k!='name'},
                             {k:v for k,v in b.items() if k!='name'})
            if c['panel']=='B0':
                self.assertEqual([a['physical'] for a in c['arms']],
                                 [c['logical'],c['logical'],c['logical']+1,c['logical']+2])
if __name__=='__main__':unittest.main()
