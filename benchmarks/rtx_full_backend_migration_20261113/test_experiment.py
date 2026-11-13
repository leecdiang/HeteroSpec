import copy
import tempfile
import unittest
from pathlib import Path
from experiment import panel, schedule, prepare, analyze, collect, length_bin

def candidates():
    return [dict(root=f'{b}-{d}-{i}', domain=d, prompt_ids=[1]*n,
                 continuation_ids=[2]*128, source='CPU_TEST_ONLY', tokenizer_identity='mock')
            for b,n in enumerate((16,140,300,600)) for d in ('code','math') for i in range(2)]

def measurements():
    return [dict(r, seconds=1.0 if r['arm']=='R' else .8, status='ok', rows=len(r['prompt_ids'])+128)
            for s in schedule(panel(candidates())) for r in s]

class Tests(unittest.TestCase):
    def test_boundaries(self): self.assertEqual([length_bin(n) for n in [1,128,129,256,257,512,513,768]],[0,0,1,1,2,2,3,3])
    def test_missing(self):
        with self.assertRaises(ValueError): panel(candidates()[:-1])
    def test_duplicate(self):
        c=candidates(); c.append(c[0])
        with self.assertRaises(ValueError): panel(c)
    def test_bool_token(self):
        c=candidates();c[0]['prompt_ids']=[True]
        with self.assertRaises(ValueError): panel(c)
    def test_tokenizer(self):
        c=candidates();c[0]['tokenizer_identity']='different'
        with self.assertRaises(ValueError): panel(c)
    def test_deterministic(self): self.assertEqual(panel(candidates()),panel(list(reversed(candidates()))))
    def test_schedule(self):
        s=schedule(panel(candidates()));self.assertEqual(len(s),12);self.assertEqual(sum(map(len,s)),204)
        self.assertEqual(''.join(x[0]['arm'] for x in s),'RMMRMRRMRMMR')
        for i in range(0,12,2):self.assertEqual([x['root'] for x in s[i]],[x['root'] for x in s[i+1]])
    def test_prepare(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(prepare(candidates(),Path(d)/'panel')['sessions'],12)
            self.assertEqual(len(list((Path(d)/'panel').glob('*.tsv'))),12)
    def test_primary(self):
        a=analyze(measurements(),draws=100);self.assertAlmostEqual(a['ratio_M_over_R'],.8)
        self.assertAlmostEqual(a['ci95'][0],.8)
    def test_greedy_separate(self): self.assertEqual(analyze(measurements(),'G',100)['blocks'],2)
    def test_missing_pair(self):
        m=measurements();m.pop(2)
        with self.assertRaises(ValueError):analyze(m,draws=100)
    def test_duplicate_measurement(self):
        m=measurements();m.append(m[1])
        with self.assertRaises(ValueError):analyze(m,draws=100)
    def test_failed(self):
        m=measurements();m[1]['status']='failed'
        with self.assertRaises(ValueError):analyze(m,draws=100)
    def test_work(self):
        m=measurements();m[1]['rows']+=1
        with self.assertRaises(ValueError):analyze(m,draws=100)
    def test_nan(self):
        m=measurements();m[1]['seconds']=float('nan')
        with self.assertRaises(ValueError):analyze(m,draws=100)
    def test_no_data(self):
        with self.assertRaises(ValueError):analyze([],draws=100)
if __name__=='__main__':unittest.main()
