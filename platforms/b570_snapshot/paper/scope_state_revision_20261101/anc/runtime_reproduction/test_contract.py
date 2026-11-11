import unittest
from itertools import product
from contract import View,lift,phase_active,graph_key
class ContractTests(unittest.TestCase):
    def pair(self,q): return View((4,q,2,1),(4,20,20*q,40*q),40*q),View((5,q,1,1),(4,24,24*q,24*q),24*q)
    def test_all_query_addresses(self):
        for q in range(1,5):
            x,m=self.pair(q);y,_=lift(x,m)
            for i,j,a in product(range(4),range(q),range(2)):self.assertEqual(x.address((i,j,a,0)),y.address((i,0,a,j)))
    def test_mask_addresses(self):
        for q in range(1,5):
            x,m=self.pair(q);_,n=lift(x,m)
            for i,j in product(range(5),range(q)):self.assertEqual(m.address((i,j,0,0)),n.address((i,0,0,j)))
    def test_q1(self): self.assertEqual(lift(*self.pair(1))[0].shape,(4,1,2,1))
    def test_reject_q5(self):
        with self.assertRaises(ValueError):lift(*self.pair(5))
    def test_reject_mask_extent(self):
        x,_=self.pair(2);_,m=self.pair(3)
        with self.assertRaises(ValueError):lift(x,m)
    def test_reject_backing(self):
        with self.assertRaises(ValueError):View((4,2,2,1),(4,20,40,80),60)
    def test_reject_negative_stride(self):
        with self.assertRaises(ValueError):View((1,1,1,1),(-1,4,4,4),4)
    def test_reject_bool(self):
        with self.assertRaises(ValueError):phase_active(True,'target','prefill')
    def test_phase(self):
        self.assertTrue(phase_active(3,'target','prefill'));self.assertTrue(phase_active(3,'target','continuation'));self.assertFalse(phase_active(3,'draft','prefill'))
    def test_invalid_role(self):
        with self.assertRaises(ValueError):phase_active(3,'other','prefill')
    def test_cache_layout(self):
        args=dict(reference='r',state_recipe='p',role='target',phase='prefill',signature=(4,))
        self.assertNotEqual(graph_key(layout='PQ',**args),graph_key(layout='QB',**args))
    def test_cache_state_recipe(self):
        args=dict(reference='r',role='target',phase='prefill',layout='QB',signature=(4,))
        self.assertNotEqual(graph_key(state_recipe='serial',**args),graph_key(state_recipe='bulk',**args))
if __name__=='__main__':unittest.main()
