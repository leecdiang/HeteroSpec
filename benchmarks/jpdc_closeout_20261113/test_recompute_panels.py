import unittest

from recompute_panels import estimate, compare


class StatisticsBoundaries(unittest.TestCase):
    def setUp(self):
        self.plan = dict(roots=['r0', 'r1'], arms=['A', 'B'], sessions=2,
                         contrasts=[['B', 'A']], interaction=None,
                         seed=17, bootstrap_draws=32, sample_scope='test',
                         metric='service_s', inference='conditional_root_bootstrap')
        self.rows = [dict(root=r, session=s, arm=a, service_s=1 if a == 'A' else 2)
                     for r in self.plan['roots'] for s in range(2) for a in ['A', 'B']]

    def test_constant_root_ratio_and_interval(self):
        result = estimate(self.plan, self.rows)['all_fixed_controls'][0]
        self.assertEqual(result['total_ratio'], 2)
        self.assertEqual(result['interval'], [2, 2])

    def test_missing_and_duplicate_slots_reject(self):
        for rows in (self.rows[:-1], self.rows + [self.rows[0]]):
            with self.assertRaises(ValueError):
                estimate(self.plan, rows)

    def test_nonfinite_and_negative_reject(self):
        for value in (float('nan'), float('inf'), -1, 0):
            bad = [dict(x) for x in self.rows]
            bad[0]['service_s'] = value
            with self.assertRaises(ValueError):
                estimate(self.plan, bad)

    def test_changed_metric_does_not_match_saved_result(self):
        expected = estimate(self.plan, self.rows)
        altered = [dict(x) for x in self.rows]
        altered[0]['service_s'] = 1.1
        with self.assertRaises(ValueError):
            compare(estimate(self.plan, altered), expected)


if __name__ == '__main__':
    unittest.main()
