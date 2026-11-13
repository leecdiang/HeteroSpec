import unittest

from recompute_service import estimate_free, estimate_s3


class ServiceInferenceBoundaries(unittest.TestCase):
    def setUp(self):
        self.s3 = [dict(root='r'+str(s), domain='code' if s < 6 else 'math', slot=s,
                        round=r, arm=a, role=role,
                        service_s=(1000 if role == 'warm' else {'G': 4, 'B': 2, 'C': 1}[a]))
                   for s in range(12) for r in range(4) for a in 'GBC'
                   for role in ('warm', 'measured')]

    def test_warm_excluded_and_stratified_constant_ratio(self):
        result = estimate_s3(self.s3)
        self.assertEqual(result['totals'], {'G': 192, 'B': 96, 'C': 48})
        primary = result['contrasts'][0]
        self.assertAlmostEqual(primary['ratio'], .5)
        for bound in primary['interval']:
            self.assertAlmostEqual(bound, .5)

    def test_missing_or_repeated_root_reject(self):
        repeated = [dict(x, root='same') for x in self.s3]
        for rows in (self.s3[:-1], repeated):
            with self.assertRaises(ValueError):
                estimate_s3(rows)

    def test_root_identity_change_reject(self):
        self.s3[0]['root'] = 'replacement'
        with self.assertRaises(ValueError):
            estimate_s3(self.s3)

    def test_invalid_component_not_hidden_by_valid_total(self):
        rows = [dict(case=c, round=r, arm=a, response_s=1, reset_s=0, service_s=1)
                for c in ('C0', 'C1') for r in range(2) for a in 'WL']
        for invalid in (float('nan'), float('inf'), -1):
            bad = [dict(x) for x in rows]
            bad[0].update(reset_s=invalid)
            with self.assertRaises(ValueError):
                estimate_free(bad)


if __name__ == '__main__':
    unittest.main()
