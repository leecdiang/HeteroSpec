"""Regression tests for release-data checks. No model or native inference."""
from pathlib import Path
import copy,json,shutil,tempfile,unittest
from unittest.mock import patch
import check,check_portability,check_rtx104

class ReleaseChecks(unittest.TestCase):
    def exercise(self, mutate=None):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'source'
            shutil.copytree(check.ROOT,root,ignore=shutil.ignore_patterns('*.pdf','*.aux','*.log','*.out','*.spl','__pycache__'))
            if mutate:mutate(root)
            with patch.object(check,'ROOT',root),patch.object(check,'DATA',root/'anc'),patch.object(check_portability,'ROOT',root):
                check.checks.clear();return check.test()
    @staticmethod
    def edit_json(root,name,fn):
        p=root/'anc'/name;x=json.loads(p.read_text());fn(x);p.write_text(json.dumps(x))
    def test_valid_package(self):self.assertEqual(self.exercise()['status'],'PASS')
    def test_cost_change_is_rejected(self):
        def m(r):
            p=r/'anc/rtx_repair_cost.csv';p.write_bytes(p.read_bytes().replace(b'1.043676',b'1.543676'))
        with self.assertRaises(ValueError):self.exercise(m)
    def test_subset_outcome_is_rejected(self):
        def m(r):self.edit_json(r,'state_and_pilot.json',lambda x:x['subsets']['V0'].__setitem__(1,'D'))
        with self.assertRaises(ValueError):self.exercise(m)
    def test_pilot_cannot_be_qualified(self):
        def m(r):self.edit_json(r,'state_and_pilot.json',lambda x:x['pilot'].__setitem__('qualified_speedup',1.3))
        with self.assertRaises(ValueError):self.exercise(m)
    def test_missing_vectors_cannot_be_filled(self):
        def m(r):self.edit_json(r,'state_and_pilot.json',lambda x:x['coverage'].__setitem__('missing_unique_vectors',0))
        with self.assertRaises(ValueError):self.exercise(m)
    def test_session_source_change_is_rejected(self):
        def m(r):
            p=r/'anc/rtx104/E2_SESSION_CONTRASTS.csv';p.write_bytes(p.read_bytes().replace(b'0.02199742807216179',b'0.12199742807216179'))
        with self.assertRaises(ValueError):self.exercise(m)
    def test_bootstrap_change_is_rejected(self):
        def m(r):
            p=r/'anc/rtx104/e2_summary.csv';p.write_text(p.read_text().replace('1.0130228000033625','1.0202228000033625'))
        with self.assertRaises(ValueError):self.exercise(m)
    def test_visible_padding_cannot_be_context(self):
        def m(r):
            p=r/'anc/rtx104/E1_CONTEXTS.csv';p.write_bytes(p.read_bytes().replace(b'[106]',b'[256]',1))
        with self.assertRaises(ValueError):self.exercise(m)
    def test_task_regression_cannot_be_deleted(self):
        def m(r):
            p=r/'anc/rtx104/task_ratios.csv';p.write_text(p.read_text().replace('0.9936177742870547','1.0036177742870547'))
        with self.assertRaises(ValueError):self.exercise(m)
    def test_source_dependency_missing(self):
        def m(r):(r/'figures/composition.tex').unlink()
        with self.assertRaises(ValueError):self.exercise(m)
    def test_plot_point_mutation(self):
        def m(r):
            p=r/'figures/sessions.tex';p.write_text(p.read_text().replace('1.031613690048,5','1.081613690048,5'))
        with self.assertRaises(ValueError):self.exercise(m)
    def test_numeric_figure_not_promoted(self):
        def m(r):
            p=r/'figures/numeric.tex';p.write_text(p.read_text().replace('18 / 72','72 / 72'))
        with self.assertRaises(ValueError):self.exercise(m)
    def test_unknown_backend_not_positive(self):
        self.assertEqual(check_portability.evaluate_necessary_condition(1,2,False),{'batch_equal':None,'full_support':None})
    def test_necessary_is_not_sufficient(self):
        self.assertEqual(check_portability.evaluate_necessary_condition(1,1),{'batch_equal':True,'full_support':None})
    def test_source_violation_rejects(self):
        self.assertEqual(check_portability.evaluate_necessary_condition(1,2),{'batch_equal':False,'full_support':False})
    def test_bootstrap_needs_six_finite_logs(self):
        for v in ([0.1]*5,[0.1]*5+[float('nan')]):
            with self.assertRaises(ValueError):check_rtx104.estimate(v)

if __name__=='__main__':unittest.main(verbosity=2)
