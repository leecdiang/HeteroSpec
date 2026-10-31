"""Presentation guards; no new data or native execution."""
import importlib.util,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('visgen',ROOT/'scripts/analyze_final_revision.py')
gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
class VisualRevisionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.a=gen.reconstruct(ROOT);cls.out=gen.outputs(ROOT)
 def test_scope_all_dates_and_means(self):
  text=self.out['figures/scope_transfer.tex']
  for f in self.a['rtx'].values():
   for k in ('D_GS','D_PQ','D_QB','I_QB_vs_GS'):
    for v in [d['ratios'][k] for d in f['dates']]+[f['ratios'][k]]:
     self.assertIn(f'{v:.12f}',text)
  self.assertEqual(text.count('only marks'),32)
 def test_shared_profitability_scale(self):
  text=self.out['figures/scope_transfer.tex']
  self.assertEqual(text.count('xmin=0.64,xmax=1.3'),2)
  for f in self.a['rtx'].values():
   for d in f['dates']:
    for k in ('D_GS','D_PQ','D_QB'):self.assertTrue(.64<d['ratios'][k]<1.30)
 def test_interaction_axis_contains_all_dates(self):
  for f in self.a['rtx'].values():
   for d in f['dates']:self.assertTrue(.98<d['ratios']['I_QB_vs_GS']<1.56)
 def test_date_range_is_not_ci(self):
  self.assertIn('Date range (not CI)',self.out['figures/scope_transfer.tex'])
  self.assertIn('not confidence intervals',(ROOT/'sections/05_evaluation.tex').read_text())
 def test_complete_reference_matrix(self):
  text=self.out['figures/producer_boundary.tex'].split(r'\draw[aux!40')[0]
  cells=re.findall(r'\{(\$=\$|\$\\ne\$)\};',text)
  self.assertEqual(len(cells),48);self.assertEqual(cells.count('$=$'),39)
 def test_same_reference_switch_cases(self):
  self.assertEqual(self.a['b570']['fixed_reference_switches'],[
   'MATH500/test/prealgebra/1865.json','MATH500/test/prealgebra/1804.json'])
  text=self.out['figures/producer_boundary.tex']
  self.assertIn('each input keeps the same $R$',text)
  self.assertIn('KV \\emph{and} initial logits',text)
 def test_arrow_is_not_runtime_recovery(self):
  self.assertIn('not temporal recovery',(ROOT/'sections/06_boundaries.tex').read_text())
 def test_all_generated_figures_current(self):
  for name in ('figures/scope_transfer.tex','figures/producer_boundary.tex'):
   self.assertEqual((ROOT/name).read_text(),self.out[name])
if __name__=='__main__':unittest.main(verbosity=2)
