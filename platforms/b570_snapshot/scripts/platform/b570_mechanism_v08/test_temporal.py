"""Synthetic-only adversarial tests; never invokes a model or real task."""
import unittest
from verify import temporal_audit, divergence

class TemporalTests(unittest.TestCase):
    def fixture(self):
        return ['2026-09-01T00:00:00+00:00','2026-09-01T00:02:00+00:00',
                [{'start_utc':'2026-09-01T00:01:00+00:00','end_utc':'2026-09-01T00:01:30+00:00'}],
                [{'start_utc':'2026-09-01T00:03:00+00:00','end_utc':'2026-09-01T00:04:00+00:00'}],'frozen','frozen']
    def test_valid(self):self.assertEqual(temporal_audit(*self.fixture()),[])
    def test_outcome_before_prediction(self):
        args=self.fixture();args[1]='2026-09-01T00:03:01+00:00'
        self.assertIn('prediction generated after actual outcome',temporal_audit(*args))
    def test_predictor_after_outcome(self):
        args=self.fixture();args[2][0]['end_utc']='2026-09-01T00:03:30+00:00'
        self.assertIn('predictor execution after actual outcome started',temporal_audit(*args))
    def test_reserved_before_hypothesis(self):
        args=self.fixture();args[0]='2026-09-01T00:01:01+00:00'
        self.assertIn('reserved inference before hypothesis freeze',temporal_audit(*args))
    def test_prediction_mutation(self):
        args=self.fixture();args[5]='changed'
        self.assertIn('prediction bytes changed after outcome start',temporal_audit(*args))
    def test_length_divergence(self):
        self.assertEqual(divergence([1,2],[1])['first_divergence_index'],1)
    def test_first_of_multiple_divergences(self):
        self.assertEqual(divergence([1,2,3],[1,4,5])['first_divergence_index'],1)

if __name__=='__main__':unittest.main()
