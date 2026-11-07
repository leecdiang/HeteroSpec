"""Post-hoc arithmetic, finite-logic and claim-boundary regression checks."""
from __future__ import annotations
import importlib.util
import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('targeted',ROOT/'scripts/analyze_targeted_revision.py')
gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)

class TargetedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.a=gen.reconstruct(ROOT)
    def test_scope_factorization(self):
        for f in self.a['rtx'].values():
            self.assertAlmostEqual(f['scope_factor']*f['layout_draft_factor'],f['ratios']['I_QB_vs_GS'],places=12)
    def test_layout_factor_independent_identity(self):
        for f in self.a['rtx'].values():
            self.assertAlmostEqual(f['layout_draft_factor'],f['ratios']['M_QB_over_M_PQ']/f['ratios']['C_QB_over_C_PQ'],places=12)
    def test_original_dates_and_weights(self):
        for f in self.a['rtx'].values():
            self.assertEqual([d['date'] for d in f['dates']],list(gen.DATES))
            self.assertAlmostEqual(math.exp(sum(d['log_means']['D_QB'] for d in f['dates'])/3),f['ratios']['D_QB'],places=12)
    def test_smol_common_path_saving_not_profitable_draft(self):
        f=self.a['rtx']['SmolLM2']
        self.assertGreater(f['draft_off_reduction_percent'],6)
        self.assertGreater(f['draft_on_reduction_percent'],6)
        self.assertLess(f['ratios']['D_QB'],1)
        self.assertLess(abs(f['layout_draft_factor']-1),.001)
    def test_three_baselines_not_collapsed(self):
        for f in self.a['rtx'].values():
            c=f['relative_to_R']
            self.assertEqual(c['R'],1)
            self.assertAlmostEqual(c['M_QB']/c['C_QB'],f['ratios']['D_QB'],places=12)
        c=self.a['rtx']['SmolLM2']['relative_to_R']
        self.assertLess(c['C_QB'],1);self.assertGreater(c['C_QB'],c['M_QB'])
    def test_witness_is_not_rectangular(self):
        self.assertEqual(gen.independent_labels([[1,0],[1,1]]),[])
        self.assertEqual(len(self.a['b570']['independent_label_counterexamples']),2)
    def test_label_solver_positive_control(self):
        self.assertEqual(gen.independent_labels([[1,1],[1,1]]),[((1,1),(1,1))])
        self.assertTrue(gen.independent_labels([[1,0],[1,0]]))
    def test_shared_reference_failure_count(self):
        b=self.a['b570'];self.assertEqual((b['cells'],b['strict_reference_matches'],b['local_pairs']),(48,39,16))
        self.assertEqual(len(b['jointly_divergent_pairs']),4)
    def test_generated_tables_current(self):
        for name,text in gen.outputs(ROOT).items():self.assertEqual((ROOT/name).read_text(),text)
    def mutate(self, rel, fn):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for f in gen.SOURCE_HASHES:
                p=root/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/f,p)
            p=root/rel;p.write_text(fn(p.read_text()))
            return gen.reconstruct(root)
    def test_missing_session_rejected(self):
        with self.assertRaises(ValueError):self.mutate('anc/final_20261101/rtx_session_logs.csv',lambda t:'\n'.join(t.splitlines()[:-1])+'\n')
    def test_matrix_outcome_mutation_rejected(self):
        with self.assertRaises(ValueError):self.mutate('anc/final_20261101/b570_MATRIX.csv',lambda t:t.replace('True,False','True,True',1))
    def test_primary_summary_mutation_rejected(self):
        def change(t):
            a=json.loads(t);a['rtx']['SmolLM2']['ratios']['D_QB']=1.2;return json.dumps(a)
        with self.assertRaises(ValueError):self.mutate('anc/final_20261101/DERIVED.json',change)
    def test_offline_online_boundary(self):
        text=(ROOT/'sections/02_problem.tex').read_text()
        self.assertIn('running $R$ online',text)
        self.assertIn('explicit generalization assumption',text)
        self.assertNotIn('decision rule retains $R$ for inputs outside',text)
        text=(ROOT/'sections/07_architecture.tex').read_text()
        self.assertIn('neither a classifier for new requests nor an online policy',text)
    def test_strong_related_work_in_comparison_table(self):
        text=(ROOT/'sections/08_related_limits.tex').read_text()
        table=text.split(r'\begin{table*}')[1].split(r'\end{table*}')[0]
        self.assertIn(r'Vosti~\cite{vosti}',table)
        self.assertIn('relational contracts',table)
        self.assertIn('acceptance as well as rollback',table)
    def test_no_promotion_to_universal_oracle(self):
        text=(ROOT/'supplement/11_final_transfer.tex').read_text()
        self.assertIn('does not preclude modular verification',text)
        self.assertIn('not a deployment failure rate',text)
        self.assertIn('post-hoc arithmetic descriptions',text)

if __name__=='__main__':unittest.main(verbosity=2)
