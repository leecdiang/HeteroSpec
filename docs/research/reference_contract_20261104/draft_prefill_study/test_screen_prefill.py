"""CPU-only arithmetic and fail-closed I/O tests; no model or network access."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('screen_prefill', HERE/'screen_prefill.py')
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)

class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.r = {'M':10.,'C':12.,'M_target_prefill':4.,'C_target_prefill':4.,'C_draft_prefill':3.}
    def test_builtin_checks(self): screen.test()
    def test_target_reuse_is_removed_on_both_sides(self):
        self.assertEqual(screen.costs(self.r,1,0),(6.,8.))
    def test_warm_target_leaves_no_prefill_overlap(self):
        self.assertEqual(screen.overlap([self.r],1)['maximum_hidden_startup_s'],0)
    def test_overhead_increases_required_removal(self):
        a=screen.thresholds([self.r],0,h=0)
        b=screen.thresholds([self.r],0,h=.3)
        key='required_draft_phase_removal_fraction_strictly_greater_than'
        self.assertAlmostEqual(b[key]-a[key],.1)
    def test_three_percent_screen_is_stricter_than_break_even(self):
        key='required_draft_phase_removal_fraction_strictly_greater_than'
        self.assertGreater(screen.thresholds([self.r],0,.03)[key],screen.thresholds([self.r],0,0)[key])
    def test_invalid_fraction_rejected(self):
        with self.assertRaises(ValueError): screen.costs(self.r,1.1,0)
    def test_nonpositive_duration_rejected(self):
        with self.assertRaises(ValueError): screen.costs(self.r,0,0,-20)
    def test_infeasible_screen_not_reported_feasible(self):
        self.assertFalse(screen.thresholds([self.r],0,h=2)['feasible_under_fixed_components'])
    def test_input_authentication_active_under_python_optimized(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'input.json').write_text('{}')
            r=subprocess.run([sys.executable,'-O',str(HERE/'screen_prefill.py'),str(p/'input.json'),'--output',str(p/'out.json')],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('Input differs from pinned projection',r.stderr)
            self.assertFalse((p/'out.json').exists())
if __name__=='__main__': unittest.main(verbosity=2)
