"""Portability and sensitivity checks; source mutations remain fail-closed."""
from pathlib import Path
import importlib.util
import json
import math
import shutil
import tempfile
import unittest

import check_closure
import test_release

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


SENSITIVITY = module('e2_sensitivity', ROOT / 'scripts/generate_e2_sensitivity.py')
ABSOLUTE = module('e2_absolute_cost', ROOT / 'scripts/generate_e2_absolute_cost.py')


class DerivedSummaryPortability(unittest.TestCase):
    def test_accepts_one_ulp_but_rejects_two(self):
        # Include a power-of-two boundary where adjacent float spacings differ.
        for x in (.5823251109757973, 1.0):
            adjacent = math.nextafter(x, -math.inf)
            self.assertTrue(check_closure.derived_json_equal({'x': [x]}, {'x': [adjacent]}))
            beyond = math.nextafter(adjacent, -math.inf)
            self.assertFalse(check_closure.derived_json_equal({'x': [x]}, {'x': [beyond]}))

    def test_structure_types_and_nonfinite_values_stay_exact(self):
        equal = check_closure.derived_json_equal
        for a, b in [({'x': 1}, {'y': 1}), ([1, 2], [2, 1]),
                     ([1], [1, 2]), (1, 1.0), (True, 1), ('RTX', 'B570'),
                     (float('nan'), float('nan')), (float('inf'), float('inf'))]:
            with self.subTest(a=a, b=b):
                self.assertFalse(equal(a, b))
        self.assertTrue(equal({'x': [1, True, 'RTX']}, {'x': [1, True, 'RTX']}))

    def test_json_duplicates_and_extensions_rejected(self):
        for body in ('{"x": 1, "x": 1}', '{"x": NaN}', '{"x": Infinity}'):
            with self.assertRaises(ValueError):
                check_closure.read_derived_json(body)

    def exercise_generated_float(self, steps):
        def mutate(root):
            generator = module('followup_fixture', root / 'scripts/generate_followup_figures.py')
            data = json.loads(generator.outputs()['anc/closure/derived_summary.json'])
            x = data['RTX']['economics']
            for _ in range(steps):
                x = math.nextafter(x, -math.inf)
            data['RTX']['economics'] = x
            (root / 'anc/closure/derived_summary.json').write_text(json.dumps(data))
        return test_release.ReleaseChecks().exercise(mutate)

    def test_one_ulp_summary_passes_full_audit(self):
        self.assertEqual(self.exercise_generated_float(1)['status'], 'PASS')

    def test_two_ulp_summary_fails_full_audit(self):
        with self.assertRaisesRegex(ValueError, 'Derived summary numerical consistency'):
            self.exercise_generated_float(2)


class E2SessionSensitivity(unittest.TestCase):
    def test_closed_form_symmetric_sample(self):
        # For [-2,-1,0,0,1,2], mean=0 and sample variance=2.
        result = SENSITIVITY.estimate([-2, -1, 0, 0, 1, 2])
        self.assertEqual(result['ratio'], 1)
        self.assertAlmostEqual(result['session_log_standard_error'], math.sqrt(1 / 3), places=15)
        self.assertAlmostEqual(result['secondary_t95_lower'] * result['secondary_t95_upper'], 1, places=15)
        self.assertAlmostEqual(result['leave_one_session_min'], math.exp(-.4), places=15)
        self.assertAlmostEqual(result['leave_one_session_max'], math.exp(.4), places=15)

    def test_incomplete_or_nonfinite_sessions_rejected(self):
        for logs in ([.1] * 5, [.1] * 7, [.1] * 5 + [float('nan')], [.1] * 5 + [float('inf')]):
            with self.assertRaises(ValueError):
                SENSITIVITY.estimate(logs)

    def test_secondary_analysis_preserves_primary_and_llama_threshold_sensitivity(self):
        result = SENSITIVITY.analyse()
        groups = {(r['family'], r['path']): r for r in result['estimates']}
        llama = groups['Llama', 'C']
        self.assertEqual(result['analysis_status'], 'secondary_post_review_sensitivity')
        self.assertEqual(result['new_model_executions'], 0)
        self.assertGreater(llama['primary_bootstrap95_lower'], 1.02)
        self.assertLess(llama['secondary_t95_lower'], 1.02)
        self.assertGreater(llama['secondary_t95_lower'], 1)
        self.assertGreater(llama['leave_one_session_min'], 1.02)
        for family in ('Qwen', 'SmolLM2'):
            self.assertGreater(groups[family, 'C']['secondary_t95_lower'], 1.02)
        self.assertTrue(all(r['observed_sessions_above_one'] == 6 for r in result['estimates']))

    def test_generated_json_and_table_reproduce(self):
        for name, expected in SENSITIVITY.outputs().items():
            actual = (ROOT / name).read_text()
            if name.endswith('.json'):
                self.assertTrue(check_closure.derived_json_equal(
                    check_closure.read_derived_json(actual), check_closure.read_derived_json(expected)))
            else:
                self.assertEqual(actual, expected)

    def test_changed_source_cannot_be_reanalysed_as_frozen_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(ROOT / 'anc/rtx104', root / 'anc/rtx104')
            source = root / 'anc/rtx104/E2_SESSION_CONTRASTS.csv'
            source.write_bytes(source.read_bytes().replace(b'0.02199742807216179', b'0.12199742807216179'))
            with self.assertRaisesRegex(ValueError, 'source Git blob mismatch'):
                SENSITIVITY.analyse(root)


class E2AbsoluteCost(unittest.TestCase):
    @staticmethod
    def check(name, ok):
        if not ok:
            raise ValueError(name)

    def test_absolute_cost_matches_saved_outputs_and_published_ratios(self):
        self.assertEqual(ABSOLUTE.verify(self.check)['published_ratio_crosschecks'], 6)
        self.assertIn('Qwen3 &', (ROOT / 'tables/e2_absolute_cost.tex').read_text())

    def test_source_latency_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(ROOT / 'anc/rtx104', root / 'anc/rtx104')
            source = root / 'anc/rtx104/E2_REQUEST_LATENCIES.csv'
            body = source.read_bytes()
            changed = body.replace(b'4237.8781', b'1237.8781', 1)
            self.assertNotEqual(body, changed)
            source.write_bytes(changed)
            with self.assertRaisesRegex(ValueError, 'pinned Git blob'):
                ABSOLUTE.generate(root)

    def test_changed_absolute_result_or_table_rejected_without_rewriting(self):
        for name in ('anc/rtx104/e2_absolute_cost.json', 'tables/e2_absolute_cost.tex'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                shutil.copytree(ROOT / 'anc/rtx104', root / 'anc/rtx104')
                shutil.copytree(ROOT / 'tables', root / 'tables')
                destination = root / name
                if name.endswith('.json'):
                    data = json.loads(destination.read_text())
                    data['rows'][0]['C_QB'] *= .9
                    destination.write_text(json.dumps(data))
                else:
                    destination.write_text(destination.read_text().replace('1926.3', '1726.3'))
                before = destination.read_bytes()
                with self.assertRaisesRegex(ValueError, 'Absolute E2 latency'):
                    ABSOLUTE.verify(self.check, root)
                self.assertEqual(destination.read_bytes(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
