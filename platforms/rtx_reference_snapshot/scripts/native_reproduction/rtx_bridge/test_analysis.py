import unittest,math
from analyze import compute,quantile,CELLS
class AnalysisTests(unittest.TestCase):
    def test_known_paired_factor_and_interaction(self):
        ratios=[.9,.8,1.,.95];blocks=[]
        for s in range(6):
            for t in range(12):
                for (k,l),r in zip(CELLS,ratios):blocks.append(dict(session=s,task=t,input=str(t),k=k,lifecycle=l,log_ratio=math.log(r),ratio=r,log_AA=0.,difference_ms=1000*(r-1),dual_PQ=1.,QB=r))
        x=compute(blocks,reps=300)
        for c,r in zip(x['cells'],ratios):
            self.assertAlmostEqual(c['ratio'],r);self.assertAlmostEqual(c['simultaneous_family95_interval'][0],r);self.assertAlmostEqual(c['simultaneous_family95_interval'][1],r)
        self.assertAlmostEqual(x['secondary_contrasts'][-1]['ratio_of_layout_ratios'],.95*.9/.8)
        self.assertEqual([c['practical_gain_established'] for c in x['cells']],[True,True,False,True])
    def test_quantile_linear(self):
        self.assertEqual(quantile([0,2],.25),.5)
if __name__=='__main__':unittest.main()
