"""Independent fail-closed mutations for final report reconstruction; no model calls."""
import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('finalgen',ROOT/'scripts/analyze_final_revision.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class FinalRevisionChecks(unittest.TestCase):
 def run_case(self,mutation=None):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td)/'src';shutil.copytree(ROOT,r,ignore=shutil.ignore_patterns('*.pdf','*.aux','*.log','*.out','build_logs','__pycache__'))
   if mutation:mutation(r)
   return mod.reconstruct(r)
 def edit(self,r,name,old,new):
  p=r/name;p.write_text(p.read_text().replace(old,new,1))
 def test_complete(self):self.assertEqual(self.run_case()['status'],'PASS')
 def test_rtx_changed_log_rejected(self):
  with self.assertRaises(ValueError):self.run_case(lambda r:self.edit(r,'anc/final_20261101/rtx_session_logs.csv','-0.186196331696774','-0.086196331696774'))
 def test_missing_session_rejected(self):
  def m(r):
   p=r/'anc/final_20261101/rtx_session_logs.csv';p.write_text('\n'.join(p.read_text().splitlines()[:-1])+'\n')
  with self.assertRaises(ValueError):self.run_case(m)
 def test_duplicate_session_rejected(self):
  def m(r):
   p=r/'anc/final_20261101/rtx_session_logs.csv';p.write_text(p.read_text()+p.read_text().splitlines()[1]+'\n')
  with self.assertRaises(ValueError):self.run_case(m)
 def test_b570_failure_not_promoted(self):
  with self.assertRaises(ValueError):self.run_case(lambda r:self.edit(r,'anc/final_20261101/b570_MATRIX.csv','True,False,False','True,True,True'))
 def test_b570_state_cannot_be_kv_only(self):
  with self.assertRaises(ValueError):self.run_case(lambda r:self.edit(r,'anc/final_20261101/b570_STATE_EFFECTS.csv','False,False,False','False,True,False'))
 def test_reference_count_distinct(self):
  r=self.run_case();self.assertEqual(sum(v for x in r['b570']['counts'].values() for v in x.values()),39)
 def test_smol_never_profitable_dates(self):
  r=self.run_case();self.assertTrue(all(d['ratios'][k]<1 for d in r['rtx']['SmolLM2']['dates'] for k in ('D_GS','D_PQ','D_QB')))
 def test_interaction_not_latency_gain(self):
  r=self.run_case()['rtx']['Qwen'];self.assertGreater(r['ratios']['I_QB_vs_GS'],1.4);self.assertAlmostEqual(r['draft_latency_change_percent'],-15.855968947369492)
 def test_e2_quartets_preserved(self):
  r=self.run_case();self.assertAlmostEqual(r['e2_retrospective']['Qwen']['QB']['ratio'],1.083665770408492)
if __name__=='__main__':unittest.main(verbosity=2)
