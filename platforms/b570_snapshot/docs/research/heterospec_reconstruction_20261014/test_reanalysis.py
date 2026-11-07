"""CPU-only arithmetic and scope-regression tests; never native qualification."""
import copy
from decimal import Decimal
from fractions import Fraction
import tempfile
from pathlib import Path
import unittest
import reanalysis as r

class ReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.obs = r.read_json(r.ROOT/'inputs/reported_observations.json')
        self.cost = r.load_cost(r.ROOT/'inputs/rtx_repair_cost.csv')
    def test_exact_cost_blob(self):
        self.assertEqual(r.git_blob((r.ROOT/'inputs/rtx_repair_cost.csv').read_bytes()),r.COST_BLOB)
    def test_cost_inventory(self):
        self.assertEqual(sum(map(len,self.cost.values())),21)
    def test_cost_pairing_required(self):
        with self.assertRaises(ValueError): r.derived_cost(self.cost,False)
    def test_local_draft_signs(self):
        out=r.derived_cost(self.cost,True)
        for f in ('Qwen3','Llama'):
            self.assertLess(Decimal(out[f]['D_GS']),1)
            self.assertGreater(Decimal(out[f]['D_PQ']),1)
            self.assertGreater(Decimal(out[f]['D_QB']),1)
    def test_smollm2_remains_unprofitable(self):
        out=r.derived_cost(self.cost,True)['SmolLM2']
        self.assertTrue(all(Decimal(out['D_'+k])<1 for k in ('GS','PQ','QB')))
    def test_rounding_not_change_sign(self):
        for family,out in r.derived_cost(self.cost,True).items():
            self.assertLess(Decimal(out['rounding_intervals_not_CI']['GS'][1]),1)
            lo,hi=map(Decimal,out['rounding_intervals_not_CI']['PQ'])
            self.assertTrue(hi<1 if family=='SmolLM2' else lo>1)
    def test_interim_no_final_estimates(self):
        rows=r.interim_rows(self.obs['rtx_interim'])
        self.assertEqual(len(rows),6)
        self.assertTrue(all(x['final_estimate'] is None and x['final_interval'] is None for x in rows))
    def test_interim_cannot_be_promoted(self):
        x=copy.deepcopy(self.obs['rtx_interim']);x['aggregate_qualified']=True
        with self.assertRaises(ValueError):r.interim_rows(x)
    def test_missing_session_rejected(self):
        x=copy.deepcopy(self.obs['rtx_interim']);x['comparisons'][0]['session_logs'].pop()
        with self.assertRaises(ValueError):r.interim_rows(x)
    def test_nonfinite_rejected(self):
        x=copy.deepcopy(self.obs['rtx_interim']);x['comparisons'][0]['session_logs'][0]=float('nan')
        with self.assertRaises(ValueError):r.interim_rows(x)
    def test_all_30_observed_session_directions(self):
        self.assertTrue(all(v>1 for row in r.interim_rows(self.obs['rtx_interim']) for v in row['session_ratios']))
    def test_exact_frontier_identity(self):
        out=r.analyze()['L0_exact_rational_arithmetic']
        self.assertEqual(Fraction(out['I']),Fraction('-0.1358642578125'))
        self.assertEqual(Fraction(out['additive_prediction']),Fraction('0.0813770294189453125'))
        self.assertTrue(out['opposite_pairwise_sign'])
    def test_reverse_pair_sign(self):
        self.assertEqual(r.canonical_scalar([220,832],'-0.09655952453613281'),r.canonical_scalar([832,220],'0.09655952453613281'))
    def test_invalid_pair(self):
        with self.assertRaises(ValueError):r.canonical_scalar([1,1],'1')
    def test_logical_counts_not_sample_size(self):
        out=r.analyze()['reported_dependence_accounting']
        self.assertEqual(out['canonical_logical_contrasts'],16)
        self.assertEqual(out['independent_inputs'],4)
    def test_norm_threshold_counterexample(self):
        out=r.threshold_fit(self.obs['b570_norm']['rows'])
        self.assertFalse(out['perfect_increasing_threshold_exists'])
        self.assertIn(('1248','1249'),out['rank_counterexamples'])
    def test_threshold_algorithm_can_find_positive_fixture(self):
        rows=[{'task':str(i),'norm':str(i),'different':i>=2} for i in range(4)]
        self.assertTrue(r.threshold_fit(rows)['perfect_increasing_threshold_exists'])
    def test_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';p.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):r.read_json(p)
    def test_tampered_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv';p.write_bytes((r.ROOT/'inputs/rtx_repair_cost.csv').read_bytes()+b'\n')
            with self.assertRaises(ValueError):r.load_cost(p)
    def test_deterministic_and_zero_native(self):
        a=r.analyze();self.assertEqual(a,r.analyze());self.assertEqual(a['new_gpu_requests'],0)

if __name__=='__main__':unittest.main(verbosity=2)
