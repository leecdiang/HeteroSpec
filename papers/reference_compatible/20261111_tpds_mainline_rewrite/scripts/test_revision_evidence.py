"""Numerical evidence checks retained from PR220 for the TPDS rewrite.

The editorial assertions in the older revision locked exact prose, filenames,
page-specific table references and a single-axis figure design. Those historical
checks remain with the original manuscript; this suite keeps data, dependence,
interval and adverse-observation checks applicable to the new structure.
"""
from pathlib import Path
import csv,hashlib,json,math,re,unittest
import numpy as np
P=Path(__file__).resolve().parents[1]
def read(n):return json.loads((P/n).read_text())
class RevisionEvidence(unittest.TestCase):
 def test_equal_work_exact_origins(self):
  d=read('data/q8_equal_work.json');self.assertEqual(set(d['origins']),{'APPS/train/65','GSM8K/test/70','GSM8K/test/806','GSM8K/test/986'})
 def test_equal_work_separate_from_live(self):
  a=set(read('data/q8_equal_work.json')['origins']);b=set(read('data/q8_root_sums.json')['roots']);self.assertFalse(a&b)
 def test_equal_work_adverse_origin_retained(self):
  d=read('generated/analysis.json')['equal_work'];self.assertTrue(any(v>1 for c in d for v in c['root_ratios']));self.assertTrue(all(c['ratio']<1 for c in d))
 def test_eight_pilot_arms_retained(self):
  d=read('data_added/a5000_pilot_source_projection.json');self.assertEqual(len(d['live']),8);self.assertEqual(d['root_count'],4);self.assertEqual(d['measurements_per_arm'],8)
 def test_pilot_cost_reconciles(self):
  d=read('generated/A5000_PILOT_RECHECK.json')['local_k7_minus_k3'];self.assertAlmostEqual(d['service_s'],sum(d[x] for x in ('prefill_s','verify_s','draft_s','residual_s')),places=12)
 def test_pilot_not_population_CI(self):
  d=read('generated/A5000_PILOT_RECHECK.json');self.assertEqual(d['intervals'],'None: descriptive pilot');self.assertFalse(d['raw_GPU_replay'])
 def test_all_published_application_points(self):
  d=read('data_added/application_root_ratios.json');self.assertEqual(sum(sum(map(len,s['ratios'])) for s in d['studies']),176)
 def test_application_geometric_field_checks(self):
  for s in read('data_added/application_root_ratios.json')['studies']:
   for row,expected in zip(s['ratios'],s['published_geometric']):self.assertAlmostEqual(math.exp(sum(map(math.log,row))/len(row)),expected,places=14)
 def test_llama_adverse_root_visible(self):
  s=read('data_added/application_root_ratios.json')['studies'][2];self.assertTrue(any(v>1 for x in s['ratios'] for v in x))
 def test_factor_reconstruction_levels(self):
  d=read('generated/FACTOR_RECHECK.json');self.assertEqual(d['recomputed_interval_endpoints'],12);self.assertIsInstance(d['studies']['8B']['primary_intervals'],list);self.assertIsInstance(d['studies']['14B']['primary_intervals'],str)
 def test_sensitivity_does_not_replace_primary(self):
  d=read('generated/SUPPLEMENTARY_SENSITIVITY.json');self.assertIn('Post-hoc',d['label']);self.assertEqual(len(d['q8_live']),4);self.assertEqual(len(d['q32']),3)
 def test_s2_all_36_public_ratios(self):
  d=read('generated/STRONG_S2_RECHECK.json');self.assertEqual(d['published_paired_ratios_checked'],36);self.assertEqual(d['per_cell_estimates_recomputed'],12)
 def test_s2_q6_q4_adverse_block(self):
  d=read('data_added/strong_s2_source_projection.json');self.assertTrue(any(x>1 for x in d['contrasts'][0]['block_ratios'][2]))
 def test_s2_is_not_native_reproduction(self):
  d=read('generated/STRONG_S2_RECHECK.json');self.assertFalse(d['raw_time_receipts_read_this_revision']);self.assertFalse(d['full_model_S3_completed']);self.assertEqual(d['new_GPU_requests'],0)
 def test_s2_unmerged_status(self):
  d=read('data_added/strong_s2_source_projection.json');self.assertTrue(d['PR_status']['draft']);self.assertFalse(d['PR_status']['merged'])
 def test_no_control_chars_in_tex(self):
  for f in [*P.glob('*.tex'),*(P/'sections').glob('*.tex'),*(P/'figures').glob('*.tex')]:
   self.assertFalse(any(ord(c)<32 and c not in '\n\t\r' for c in f.read_text()),f.name)
 def test_all_48_structural_values_after_reflow(self):
  s=(P/'supplement_body.tex').read_text();records=read('data/rtx_factor_cells.json');lookup={r['cell']:r for r in records};count=0
  for q,state,nums in re.findall(r'^(q\d+) / (inside|crossing) & ([0-9 .&]+) \\\\',s,re.M):
   actual=[float(x.strip()) for x in nums.split('&')];self.assertEqual(len(actual),8)
   expected=[]
   for model in ('Qwen','Smol'):
    row=lookup[f'{model}-{q}-{state}']
    expected += [float(f"{row[a+'_mean_ms']:.2f}") for a in ('W_L4','W_P','L_L4','L_P')]
   self.assertEqual(actual,expected);count+=len(actual)
  self.assertEqual(count,48)
if __name__=='__main__':unittest.main()
