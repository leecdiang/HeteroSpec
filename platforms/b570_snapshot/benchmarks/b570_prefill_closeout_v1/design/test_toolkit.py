import unittest,copy
import toolkit as t
class PlanTests(unittest.TestCase):
    def fixture(self,p='B570'):
        return [dict(r,seconds=1.,qualified=True,exit_ok=True) for r in t.timing_plan(p) if r['family']=='Qwen3']
    def test_rtx_count(self): self.assertEqual(len(t.timing_plan('RTX')),1152)
    def test_rtx_fast_count(self): self.assertEqual(len(t.timing_plan('RTX',True)),1440)
    def test_b570_count(self): self.assertEqual(len(t.timing_plan('B570')),128)
    def test_unique(self):
        for p in t.CONFIG:
            x=t.timing_plan(p);self.assertEqual(len(x),len({r['slot'] for r in x}))
    def test_core_order_balanced(self):
        for p in t.CONFIG:
            x=t.timing_plan(p)
            for i in range(t.CONFIG[p]['inputs']):
                orders=[[r['arm'] for r in x if r['session']==s and r['input_index']==i and r['family']=='Qwen3' and r['category']=='measured'] for s in range(4)]
                for a in t.CONFIG[p]['arms']: self.assertEqual({o.index(a) for o in orders},set(range(4)))
    def test_warmups_paired(self):
        x=t.timing_plan('RTX',True)
        for a,b in zip(x[::2],x[1::2]):self.assertEqual(a['slot'].rsplit('/',1)[0],b['slot'].rsplit('/',1)[0])
    def test_template_not_executable(self):
        with self.assertRaises(ValueError):t.validate_registration({'platform':'RTX','status':'TEMPLATE_NOT_EXECUTABLE'})
    def test_missing_budget(self):
        d={'platform':'B570','status':'FROZEN_FOR_HOST_REVIEW'}
        with self.assertRaises(ValueError):t.validate_registration(d)
    def test_parity_not_benefit(self):self.assertFalse(t.analyze('B570','Qwen3',self.fixture())['practical_screen_pass'])
    def test_clear_gain(self):
        x=self.fixture()
        for r in x:
            if r['arm']=='SUBMIT':r['seconds']=.9
        self.assertTrue(t.analyze('B570','Qwen3',x)['practical_screen_pass'])
    def test_incomplete(self):
        with self.assertRaises(ValueError):t.analyze('B570','Qwen3',self.fixture()[:-1])
    def test_duplicate(self):
        x=self.fixture()
        with self.assertRaises(ValueError):t.analyze('B570','Qwen3',x+[x[0]])
    def test_wrong_output(self):
        x=self.fixture();x[0]['qualified']=False
        with self.assertRaises(ValueError):t.analyze('B570','Qwen3',x)
    def test_nan(self):
        x=self.fixture();x[0]['seconds']=float('nan')
        with self.assertRaises(ValueError):t.analyze('B570','Qwen3',x)
    def test_session_reversal(self):
        x=self.fixture()
        for r in x:
            if r['arm']=='SUBMIT':r['seconds']=1.01 if r['session']==0 else .8
        self.assertFalse(t.analyze('B570','Qwen3',x)['practical_screen_pass'])
    def test_noise(self):
        x=self.fixture()
        for r in x:
            if r['arm']=='BASE_A':r['seconds']=1.12
            if r['arm']=='SUBMIT':r['seconds']=.99
        self.assertFalse(t.analyze('B570','Qwen3',x)['practical_screen_pass'])
if __name__=='__main__':unittest.main(verbosity=2)
