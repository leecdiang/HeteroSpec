"""Mutation tests for the new service panel audit (no model execution)."""
from pathlib import Path
import json,shutil,tempfile,unittest
import check
from unittest.mock import patch

class ClosureChecks(unittest.TestCase):
 def exercise(self, mutate=None):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/'source'
   shutil.copytree(check.ROOT,root,ignore=shutil.ignore_patterns('*.pdf','*.aux','*.log','*.out','*.spl','__pycache__'))
   if mutate:mutate(root)
   with patch.object(check,'ROOT',root),patch.object(check,'DATA',root/'anc'):
    check.checks.clear();return check.test()
 def edit(self,r,name,fn):
  p=r/'anc/closure'/name;v=json.loads(p.read_text());fn(v);p.write_text(json.dumps(v))
 def test_complete(self):self.assertEqual(self.exercise()['status'],'PASS')
 def test_changed_service(self):
  def m(r):
   p=r/'anc/closure/rtx_blocks.csv';p.write_text(p.read_text().replace('0.9385494','0.6385494'))
  with self.assertRaises(ValueError):self.exercise(m)
 def test_omitted_block(self):
  def m(r):
   p=r/'anc/closure/b570_blocks.csv';p.write_text('\n'.join(p.read_text().splitlines()[:-1])+'\n')
  with self.assertRaises(ValueError):self.exercise(m)
 def test_wrong_denominator(self):
  with self.assertRaises(ValueError):self.exercise(lambda r:self.edit(r,'reported_summary.json',lambda x:x['rtx'].__setitem__('layout',.5823251109757973)))
 def test_hidden_noise(self):
  with self.assertRaises(ValueError):self.exercise(lambda r:self.edit(r,'reported_summary.json',lambda x:x['rtx'].__setitem__('aa',.005)))
 def test_wrong_figure_coordinate(self):
  def m(r):
   p=r/'figures/service_panels.tex';p.write_text(p.read_text().replace('0.989283832162','0.950000000000'))
  with self.assertRaises(ValueError):self.exercise(m)
 def test_prefill_not_timed(self):
  with self.assertRaises(ValueError):self.exercise(lambda r:self.edit(r,'reported_summary.json',lambda x:x['prefill_followup'].__setitem__('status','TIMING_PASS')))
 def test_wrong_input_ratio(self):
  def m(r):
   p=r/'anc/closure/service_input_table.tex';p.write_text(p.read_text().replace('0.992003','0.992060'))
  with self.assertRaises(ValueError):self.exercise(m)
 def test_abstract_truncation(self):
  def m(r):
   p=r/'abstract.tex';p.write_text(p.read_text().replace('\\%','%',1))
  with self.assertRaises(ValueError):self.exercise(m)
if __name__=='__main__':unittest.main(verbosity=2)
