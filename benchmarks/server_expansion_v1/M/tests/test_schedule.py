import collections, importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('experiment',ROOT/'shared/experiment.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)

class Schedule(unittest.TestCase):
    def test_actual_m1_balance_and_budget(self):
        study=e.read(ROOT/'M/study.json');p=e.schedule(study,'attribution',[{'root':str(i)} for i in range(16)])
        rows=[[w['arm'] for w in p['workers'] if w['session']==s] for s in range(4)]
        for a in p['arms']:
            self.assertEqual(sorted(r.index(a) for r in rows),list(range(4)))
        pairs=collections.Counter((a,b) for r in rows for a,b in zip(r,r[1:]));self.assertEqual(len(pairs),12);self.assertEqual(set(pairs.values()),{1})
        self.assertEqual((len(p['workers']),p['measurements'],p['primers']),(16,256,32))
    def test_reject_cyclic_order_labelled_balanced(self):
        s=e.read(ROOT/'M/study.json');a=s['panels']['attribution']['arms'];s['panels']['attribution']['worker_order_rows']=[a[i:]+a[:i] for i in range(4)]
        with self.assertRaises(ValueError):e.schedule(s,'attribution',[{'root':str(i)} for i in range(16)])

if __name__=='__main__':unittest.main()
