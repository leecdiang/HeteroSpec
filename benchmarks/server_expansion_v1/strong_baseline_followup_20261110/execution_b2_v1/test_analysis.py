"""Artificial B2 process-cluster fixtures; zero native/GPU requests."""
import copy
import math
import unittest
from execute import analyze


def fixture():
    cells=[['loop4',248],['loop4',252],['packed',248],['packed',252]]
    records=[]
    for core,pos in cells:
        for round_ in range(4):
            # A is deliberately unequal within each process. Taking the mean
            # of individually paired operation ratios gives the wrong answer.
            operations=[dict(role='warm',item=dict(execution='q8'),receipt=dict(operation_s=1000))]
            operations += [dict(role='measured',item=dict(execution=path),receipt=dict(operation_s=seconds))
                           for path,seconds in [('q4pair',1),('q8',3),('q8',1),('q4pair',9)]]
            records.append(dict(worker=dict(id=f'{core}-{pos}-{round_}',core=core,boundary=pos,round=round_),
                                operations=operations,caller_s=1014))
    return records,dict(cells=cells)


class Analysis(unittest.TestCase):
    def test_sum_two_B_over_sum_two_A_cluster(self):
        rows,plan=fixture();actual=analyze(rows,plan)
        self.assertTrue(actual['descriptive_only'])
        for cell in actual['contrasts']:
            self.assertAlmostEqual(cell['geometric_B_over_A'],.4)
            self.assertEqual(len(cell['processes']),4)

    def test_geometric_mean_is_over_process_ratios(self):
        rows,plan=fixture()
        for i,record in enumerate(rows):
            for op in record['operations']:
                if op['role']=='measured' and op['item']['execution']=='q8':
                    op['receipt']['operation_s']*=2**(i%4)
        actual=analyze(rows,plan)
        self.assertAlmostEqual(actual['contrasts'][0]['geometric_B_over_A'],.4*2**1.5)

    def test_partial_is_not_full_result(self):
        rows,plan=fixture()
        with self.assertRaisesRegex(RuntimeError,'Partial'):
            analyze(rows[:-1],plan)

    def test_nonfinite_rejected(self):
        for bad in (math.nan,math.inf,0,-1):
            rows,plan=fixture();rows[0]['operations'][1]['receipt']['operation_s']=bad
            with self.assertRaisesRegex(RuntimeError,'Finite'):
                analyze(rows,plan)

    def test_duplicate_process_round_rejected(self):
        rows,plan=fixture();rows[1]['worker']['round']=0
        with self.assertRaisesRegex(RuntimeError,'Four original process'):
            analyze(rows,plan)


if __name__=='__main__':
    unittest.main()
