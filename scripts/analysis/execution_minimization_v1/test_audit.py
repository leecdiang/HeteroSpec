"""Scientific denominator, endpoint, and missing-evidence safeguards."""
import unittest
import hashlib
from copy import deepcopy
from unittest.mock import patch
from audit import load_json, endpoint, index_context, pair_metrics, source_bytes


def context():
    records = []
    for c in ('R', 'N0', 'N1', 'U2'):
        for rep in (1, 2, 3):
            records.append(dict(task='anonymous', condition=c, rep=rep,
                                ids=[7, 151645], endpoint='EOS'))
    return dict(name='synthetic_validation_only', tasks=['anonymous'],
                known_conditions=['R','N0','N1','U2'], records=records)


class EvidenceRisks(unittest.TestCase):
    def test_duplicate_observation(self):
        c = context(); c['records'].append(deepcopy(c['records'][0]))
        with self.assertRaises(ValueError): index_context(c)

    def test_missing_repeat(self):
        c = context(); c['records'].pop()
        with self.assertRaises(ValueError): index_context(c)

    def test_repeats_are_not_independent_tasks(self):
        result = pair_metrics(context(), 'U2', 'N1')
        self.assertEqual(result['task_units'], 1)
        self.assertEqual(result['joint_equal_observations'], 3)
        c = context(); c['records'][-1]['ids'] = [9, 151645]
        result = pair_metrics(c, 'U2', 'N1')
        self.assertEqual(result['all_three_equal_tasks'], 0)
        self.assertEqual(result['joint_equal_observations'], 2)

    def test_equal_reason_does_not_hide_length_difference(self):
        c = context()
        for row in c['records']:
            if row['condition'] == 'U2': row['ids'] = [7, 8, 151645]
        result = pair_metrics(c, 'U2', 'N1')
        self.assertEqual(result['boundary_equal_observations'], 0)

    def test_unknown_keeps_denominator(self):
        c = context(); c['known_conditions'].remove('U2')
        c['records'] = [r for r in c['records'] if r['condition'] != 'U2']
        result = pair_metrics(c, 'U2', 'N1')
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['expected_paired_observations'], 3)
        self.assertIsNone(result['joint_equal_observations'])

    def test_bad_endpoint_and_duplicate_json(self):
        with self.assertRaises(ValueError): endpoint(dict(ids=[151645, 2], endpoint='EOS'))
        with self.assertRaises(ValueError): endpoint(dict(ids=[3, 4], endpoint='limit'))
        with self.assertRaises(ValueError): load_json('{"x":1,"x":2}')

    def test_bound_source_corruption_rejected(self):
        data = b'{"records":[]}'
        entry = dict(path='synthetic.json', git_blob_sha='synthetic', bytes=len(data),
                     sha256=hashlib.sha256(data).hexdigest())
        for corrupted in (data + b' ', b'{"records":{}}'):
            with self.subTest(corrupted=corrupted):
                with patch('audit.subprocess.check_output', return_value=corrupted):
                    with self.assertRaises(ValueError): source_bytes('.', entry)


if __name__ == '__main__':
    unittest.main(verbosity=2)
